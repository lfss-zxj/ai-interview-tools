from __future__ import annotations

import os
import re
import threading
import time
from typing import Any


class LocalEnglishChineseTranslator:
    """Lazy local OPUS-MT translator shared by all HTTP requests."""

    model_name = "Helsinki-NLP/opus-mt-en-zh"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokenizer: Any = None
        self._model: Any = None
        self._device = ""
        self._load_seconds: float | None = None
        self._last_latency_ms: float | None = None
        self._last_error = ""

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            started = time.perf_counter()
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                requested = os.environ.get("VOXRIBBON_TRANSLATION_DEVICE", "auto").strip()
                if requested == "auto":
                    requested = "cuda:0" if torch.cuda.is_available() else "cpu"
                tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                model.to(requested)
                if requested.startswith("cuda"):
                    model.half()
                model.eval()
                self._tokenizer = tokenizer
                self._model = model
                self._device = requested
                self._load_seconds = round(time.perf_counter() - started, 3)
                self._last_error = ""
            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                raise

    @staticmethod
    def _clean_chinese(text: str) -> str:
        text = " ".join(text.split()).strip()
        return re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)

    def translate(self, text: str) -> dict[str, Any]:
        source = " ".join(str(text or "").split()).strip()
        if not source:
            return {"translation": "", "latencyMs": 0.0, **self.status()}
        self._ensure_loaded()
        with self._lock:
            import torch

            started = time.perf_counter()
            encoded = self._tokenizer(
                ">>cmn_Hans<< " + source,
                return_tensors="pt",
                truncation=True,
                max_length=256,
            ).to(self._device)
            with torch.inference_mode():
                generated = self._model.generate(
                    **encoded,
                    num_beams=1,
                    do_sample=False,
                    max_new_tokens=128,
                )
            if self._device.startswith("cuda"):
                torch.cuda.synchronize()
            translated = self._clean_chinese(
                self._tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
            )
            self._last_latency_ms = round((time.perf_counter() - started) * 1000, 1)
            return {
                "translation": translated,
                "latencyMs": self._last_latency_ms,
                **self.status(),
            }

    def warmup(self) -> dict[str, Any]:
        result = self.translate("Welcome to the interview.")
        return {"ok": True, **result}

    def status(self) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "loaded": self._model is not None,
            "device": self._device,
            "loadSeconds": self._load_seconds,
            "lastLatencyMs": self._last_latency_ms,
            "error": self._last_error or None,
        }
