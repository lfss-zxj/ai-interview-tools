from __future__ import annotations

import queue
import os
import threading
import time
import traceback
from collections.abc import Callable

import numpy as np

from .capture import WasapiLoopbackCapture
from .config import AppConfig
from .segmenter import AudioPacket, SpeechSegmenter, merge_stream_text


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


class TranscriptionEngine:
    def __init__(self, config: AppConfig, publish: Callable[[dict], None]) -> None:
        self.config = config
        self.publish = publish
        self._stop = threading.Event()
        self._packets: queue.Queue[AudioPacket] = queue.Queue(maxsize=64)
        self._worker: threading.Thread | None = None
        self._capture_thread: threading.Thread | None = None
        self._capture: WasapiLoopbackCapture | None = None
        self._segment_id = 0
        self._last_level = 0.0

    def start(self) -> None:
        self._worker = threading.Thread(target=self._run, name="paraformer-worker", daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        if self._capture:
            self._capture.stop()
        if self._capture_thread:
            self._capture_thread.join(timeout=2)
        if self._worker:
            self._worker.join(timeout=5)

    def _run(self) -> None:
        try:
            if self.config.language == "en":
                self._run_english()
                return
            os.environ.setdefault("MODELSCOPE_DOWNLOAD_PARALLEL_WORKERS", "1")
            os.environ.setdefault("MODELSCOPE_DOWNLOAD_PART_SIZE_MB", "64")
            if self.config.hub == "hf":
                os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
                os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
            from funasr import AutoModel

            device = choose_device(self.config.device)
            self.publish(
                {"type": "status", "state": "loading_model", "model": self.config.model, "device": device}
            )
            model_options = {"model": self.config.model, "device": device}
            if self.config.hub:
                model_options["hub"] = self.config.hub
            model = AutoModel(**model_options)
            self.publish({"type": "status", "state": "model_ready", "device": device})

            segmenter = SpeechSegmenter(
                self.config.target_rate,
                self.config.model_stride_samples,
                self.config.silence_db,
                self.config.endpoint_silence_ms,
                self.config.preroll_ms,
            )
            self._capture = WasapiLoopbackCapture(
                self.config.speaker,
                self.config.capture_rate,
                self.config.target_rate,
                self.config.capture_block_ms,
                lambda audio: self._on_audio(segmenter, audio),
                self.publish,
                self._on_capture_error,
            )
            self._capture_thread = threading.Thread(
                target=self._capture.run, name="wasapi-loopback", daemon=True
            )
            self._capture_thread.start()

            cache: dict = {}
            utterance = ""
            while not self._stop.is_set():
                try:
                    packet = self._packets.get(timeout=0.2)
                except queue.Empty:
                    if self._capture_thread and not self._capture_thread.is_alive():
                        break
                    continue

                result = model.generate(
                    input=packet.samples,
                    cache=cache,
                    is_final=packet.is_final,
                    chunk_size=list(self.config.chunk_size),
                    encoder_chunk_look_back=self.config.encoder_look_back,
                    decoder_chunk_look_back=self.config.decoder_look_back,
                )
                incoming = "".join(
                    str(item.get("text", "")) for item in (result or []) if isinstance(item, dict)
                )
                utterance = merge_stream_text(utterance, incoming)
                if utterance:
                    self.publish(
                        {
                            "type": "final" if packet.is_final else "partial",
                            "segment_id": self._segment_id,
                            "text": utterance,
                        }
                    )
                if packet.is_final:
                    cache = {}
                    utterance = ""
                    self._segment_id += 1
        except BaseException as exc:
            traceback.print_exc()
            self.publish(
                {"type": "error", "where": "recognizer", "message": f"{type(exc).__name__}: {exc}"}
            )
        finally:
            if self._capture:
                self._capture.stop()
            self.publish({"type": "status", "state": "stopped"})

    def _run_english(self) -> None:
        os.environ.setdefault("MODELSCOPE_DOWNLOAD_PARALLEL_WORKERS", "4")
        from faster_whisper import WhisperModel
        from modelscope import snapshot_download

        requested = choose_device(self.config.device)
        device = "cuda" if requested.startswith("cuda") else "cpu"
        device_index = int(requested.split(":", 1)[1]) if ":" in requested else 0
        compute_type = "float16" if device == "cuda" else "int8"
        model_name = "pengzhendong/faster-whisper-tiny.en"
        self.publish(
            {
                "type": "status",
                "state": "loading_model",
                "model": model_name,
                "device": requested,
                "language": "en",
            }
        )
        configured_dir = os.environ.get("VOXRIBBON_ENGLISH_MODEL_DIR", "").strip()
        app_root = os.environ.get(
            "LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local")
        )
        persistent_dir = os.path.join(
            app_root, "VoxRibbon", "models", "faster-whisper-tiny.en"
        )
        if configured_dir and os.path.isfile(os.path.join(configured_dir, "model.bin")):
            model_dir = configured_dir
        elif os.path.isfile(os.path.join(persistent_dir, "model.bin")):
            model_dir = persistent_dir
        else:
            model_dir = snapshot_download(model_name, local_dir=persistent_dir)
        model = WhisperModel(
            model_dir,
            device=device,
            device_index=device_index,
            compute_type=compute_type,
        )
        self.publish(
            {"type": "status", "state": "model_ready", "device": requested, "language": "en"}
        )

        segmenter = SpeechSegmenter(
            self.config.target_rate,
            self.config.model_stride_samples,
            self.config.silence_db,
            self.config.endpoint_silence_ms,
            self.config.preroll_ms,
        )
        self._capture = WasapiLoopbackCapture(
            self.config.speaker,
            self.config.capture_rate,
            self.config.target_rate,
            self.config.capture_block_ms,
            lambda audio: self._on_audio(segmenter, audio),
            self.publish,
            self._on_capture_error,
        )
        self._capture_thread = threading.Thread(
            target=self._capture.run, name="wasapi-loopback", daemon=True
        )
        self._capture_thread.start()

        utterance = np.empty(0, dtype=np.float32)
        last_text = ""
        while not self._stop.is_set():
            try:
                packet = self._packets.get(timeout=0.2)
            except queue.Empty:
                if self._capture_thread and not self._capture_thread.is_alive():
                    break
                continue
            utterance = np.concatenate((utterance, packet.samples))
            # Whisper accepts at most 30 seconds. Keep the newest context for unusually long turns.
            if utterance.size > self.config.target_rate * 30:
                utterance = utterance[-self.config.target_rate * 30 :]
            if utterance.size < self.config.target_rate and not packet.is_final:
                continue
            segments, _info = model.transcribe(
                utterance,
                language="en",
                beam_size=1,
                best_of=1,
                temperature=0.0,
                vad_filter=False,
                condition_on_previous_text=False,
                without_timestamps=True,
            )
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
            if text and (text != last_text or packet.is_final):
                self.publish(
                    {
                        "type": "final" if packet.is_final else "partial",
                        "segment_id": self._segment_id,
                        "text": text,
                        "language": "en",
                    }
                )
                last_text = text
            if packet.is_final:
                utterance = np.empty(0, dtype=np.float32)
                last_text = ""
                self._segment_id += 1

    def _on_audio(self, segmenter: SpeechSegmenter, audio: np.ndarray) -> None:
        level, packets = segmenter.feed(audio)
        now = time.monotonic()
        if now - self._last_level >= 0.1:
            self._last_level = now
            self.publish({"type": "audio_level", "dbfs": round(level, 1), "active": segmenter.active})
        for packet in packets:
            try:
                self._packets.put(packet, timeout=0.5)
            except queue.Full:
                self.publish(
                    {"type": "error", "where": "audio_queue", "message": "识别跟不上音频，已丢弃一块音频"}
                )

    def _on_capture_error(self, exc: BaseException) -> None:
        self.publish({"type": "error", "where": "wasapi", "message": f"{type(exc).__name__}: {exc}"})
