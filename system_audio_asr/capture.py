from __future__ import annotations

import threading
from collections.abc import Callable

import numpy as np


def list_speakers() -> list[dict[str, object]]:
    import soundcard as sc

    default = sc.default_speaker()
    return [
        {"id": str(item.id), "name": str(item.name), "default": str(item.id) == str(default.id)}
        for item in sc.all_speakers()
    ]


def _select_speaker(selector: str | None):
    import soundcard as sc

    if not selector:
        return sc.default_speaker()
    key = selector.casefold()
    speakers = sc.all_speakers()
    exact = [s for s in speakers if key in {str(s.id).casefold(), str(s.name).casefold()}]
    partial = [s for s in speakers if key in str(s.name).casefold()]
    matches = exact or partial
    if not matches:
        choices = "\n".join(f"  - {s.name}" for s in speakers)
        raise RuntimeError(f"找不到播放设备: {selector}\n可用设备:\n{choices}")
    if len(matches) > 1:
        raise RuntimeError("播放设备名称不唯一: " + ", ".join(str(s.name) for s in matches))
    return matches[0]


class WasapiLoopbackCapture:
    def __init__(
        self,
        speaker_selector: str | None,
        capture_rate: int,
        target_rate: int,
        block_ms: int,
        on_audio: Callable[[np.ndarray], None],
        on_status: Callable[[dict], None],
        on_error: Callable[[BaseException], None],
    ) -> None:
        self.speaker_selector = speaker_selector
        self.capture_rate = capture_rate
        self.target_rate = target_rate
        self.block_ms = block_ms
        self.on_audio = on_audio
        self.on_status = on_status
        self.on_error = on_error
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        try:
            import soundcard as sc
            import soxr

            speaker = _select_speaker(self.speaker_selector)
            loopback = sc.get_microphone(id=speaker.id, include_loopback=True)
            frames = max(1, self.capture_rate * self.block_ms // 1000)
            resampler = soxr.ResampleStream(
                self.capture_rate, self.target_rate, 1, dtype="float32", quality="HQ"
            )
            self.on_status(
                {
                    "type": "status",
                    "state": "capturing",
                    "speaker": str(speaker.name),
                    "capture_rate": self.capture_rate,
                    "pcm_rate": self.target_rate,
                }
            )
            # SoundCard has a Windows single-channel capture issue. Capture all
            # WASAPI channels first, then downmix ourselves.
            with loopback.recorder(
                samplerate=self.capture_rate, channels=None, blocksize=frames * 2
            ) as recorder:
                while not self._stop.is_set():
                    data = np.asarray(recorder.record(numframes=frames), dtype=np.float32)
                    if data.ndim == 2:
                        data = data.mean(axis=1, dtype=np.float32)
                    else:
                        data = data.reshape(-1)
                    pcm16k = resampler.resample_chunk(np.ascontiguousarray(data), last=False)
                    if pcm16k.size:
                        self.on_audio(pcm16k)
        except BaseException as exc:
            if not self._stop.is_set():
                self.on_error(exc)

