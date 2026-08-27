from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    speaker: str | None = None
    capture_rate: int = 48_000
    capture_block_ms: int = 100
    target_rate: int = 16_000
    silence_db: float = -42.0
    endpoint_silence_ms: int = 900
    preroll_ms: int = 200
    model: str = "paraformer-zh-streaming"
    hub: str | None = None
    device: str = "auto"
    chunk_size: tuple[int, int, int] = (0, 8, 4)
    encoder_look_back: int = 4
    decoder_look_back: int = 1

    @property
    def model_stride_samples(self) -> int:
        return self.chunk_size[1] * 960

    def validate(self) -> None:
        if self.target_rate != 16_000:
            raise ValueError("Paraformer 中文流式模型要求 16 kHz 输入")
        if self.capture_rate <= 0 or self.capture_block_ms <= 0:
            raise ValueError("采样率和采集块时长必须为正数")
        if self.endpoint_silence_ms < self.capture_block_ms:
            raise ValueError("endpoint_silence_ms 不能小于 capture_block_ms")
        if self.preroll_ms < 0:
            raise ValueError("preroll_ms 不能为负数")
        if len(self.chunk_size) != 3 or self.chunk_size[1] <= 0:
            raise ValueError("chunk_size 必须是三个整数，且中间值大于 0")
