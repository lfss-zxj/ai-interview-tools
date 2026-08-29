from __future__ import annotations

import argparse
import json

from .config import AppConfig


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="系统播放声音 → 中文实时文字 → WebSocket")
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=8765)
    result.add_argument("--speaker", help="播放设备名或设备名中的一段")
    result.add_argument("--capture-rate", type=int, default=48000)
    result.add_argument("--capture-block-ms", type=int, default=100)
    result.add_argument("--silence-db", type=float, default=-42.0)
    result.add_argument("--endpoint-ms", type=int, default=900)
    result.add_argument("--preroll-ms", type=int, default=200)
    result.add_argument("--model", default="paraformer-zh-streaming")
    result.add_argument("--hub", choices=("ms", "hf"), help="模型仓库：ModelScope 或 Hugging Face")
    result.add_argument("--device", default="auto", help="auto、cpu 或 cuda:0")
    result.add_argument("--language", choices=("zh", "en"), help="识别语言；默认读取设置页")
    result.add_argument("--list-devices", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    if args.list_devices:
        from .capture import list_speakers

        print(json.dumps(list_speakers(), ensure_ascii=False, indent=2))
        return

    if args.language:
        language = args.language
    else:
        from .settings import load_settings

        language = load_settings().get("asrLanguage", "zh")

    config = AppConfig(
        host=args.host,
        port=args.port,
        speaker=args.speaker,
        capture_rate=args.capture_rate,
        capture_block_ms=args.capture_block_ms,
        silence_db=args.silence_db,
        endpoint_silence_ms=args.endpoint_ms,
        preroll_ms=args.preroll_ms,
        model=args.model,
        hub=args.hub,
        device=args.device,
        language=language,
    )
    config.validate()

    import uvicorn

    from .server import create_app

    uvicorn.run(create_app(config), host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    main()
