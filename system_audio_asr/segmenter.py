from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class AudioPacket:
    samples: np.ndarray
    is_final: bool


def dbfs(samples: np.ndarray) -> float:
    if samples.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))
    return max(-120.0, 20.0 * np.log10(max(rms, 1e-6)))


class SpeechSegmenter:
    """Energy gate and endpoint detector around fixed Paraformer chunks."""

    def __init__(
        self,
        sample_rate: int,
        stride_samples: int,
        silence_db: float,
        endpoint_silence_ms: int,
        preroll_ms: int,
    ) -> None:
        self.sample_rate = sample_rate
        self.stride_samples = stride_samples
        self.silence_db = silence_db
        self.endpoint_samples = endpoint_silence_ms * sample_rate // 1000
        self.preroll_samples = preroll_ms * sample_rate // 1000
        self._preroll: deque[np.ndarray] = deque()
        self._preroll_size = 0
        self._pending = np.empty(0, dtype=np.float32)
        self._active = False
        self._silence_samples = 0

    @property
    def active(self) -> bool:
        return self._active

    def feed(self, samples: np.ndarray) -> tuple[float, list[AudioPacket]]:
        block = np.ascontiguousarray(samples, dtype=np.float32).reshape(-1)
        level = dbfs(block)
        voiced = level >= self.silence_db

        if not self._active:
            self._push_preroll(block)
            if not voiced:
                return level, []
            self._active = True
            self._silence_samples = 0
            self._pending = (
                np.concatenate(tuple(self._preroll)) if self._preroll else block.copy()
            )
            self._preroll.clear()
            self._preroll_size = 0
        else:
            self._pending = np.concatenate((self._pending, block))

        self._silence_samples = 0 if voiced else self._silence_samples + block.size
        endpoint = self._silence_samples >= self.endpoint_samples
        packets: list[AudioPacket] = []

        while self._pending.size >= self.stride_samples:
            chunk = self._pending[: self.stride_samples].copy()
            self._pending = self._pending[self.stride_samples :]
            packets.append(AudioPacket(chunk, endpoint and self._pending.size == 0))

        if endpoint:
            if self._pending.size:
                packets.append(AudioPacket(self._pending.copy(), True))
            elif not packets or not packets[-1].is_final:
                # Give FunASR a small tail so it can flush an exact-stride endpoint.
                packets.append(AudioPacket(np.zeros(960, dtype=np.float32), True))
            self._reset()

        return level, packets

    def _push_preroll(self, block: np.ndarray) -> None:
        if self.preroll_samples == 0:
            return
        self._preroll.append(block.copy())
        self._preroll_size += block.size
        while self._preroll and self._preroll_size - self._preroll[0].size >= self.preroll_samples:
            self._preroll_size -= self._preroll.popleft().size

    def _reset(self) -> None:
        self._pending = np.empty(0, dtype=np.float32)
        self._active = False
        self._silence_samples = 0
        self._preroll.clear()
        self._preroll_size = 0


def merge_stream_text(previous: str, incoming: str) -> str:
    """Handle both incremental-token and cumulative-text FunASR versions."""
    incoming = incoming.strip()
    if not incoming:
        return previous
    if incoming.startswith(previous):
        return incoming
    if previous.endswith(incoming):
        return previous
    for size in range(min(len(previous), len(incoming)), 0, -1):
        if previous[-size:] == incoming[:size]:
            return previous + incoming[size:]
    return previous + incoming
