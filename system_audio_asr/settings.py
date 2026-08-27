from __future__ import annotations

import ctypes
import json
import os
import re
import time
import urllib.error
import urllib.request
from ctypes import wintypes
from pathlib import Path
from typing import Any


APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "WasapiParaformerOverlay"
CONFIG_PATH = APP_DIR / "config.json"
KEY_PATH = APP_DIR / "deepseek.key"
ENTROPY = b"WasapiParaformerOverlay.DeepSeek.v1"

DEFAULTS: dict[str, Any] = {
    "left": None,
    "top": None,
    "width": 980.0,
    "height": 150.0,
    "fontSize": 36.0,
    "maxLines": 3,
    "opacity": 0.88,
    "fadeDelayMs": 1800,
    "fontFamily": "Microsoft YaHei UI",
    "textColor": "#FFFFFF",
    "locked": False,
    "screenName": "",
    "webSocketUrl": "ws://127.0.0.1:8765/ws",
    "aiEnabled": False,
    "aiModel": "deepseek-v4-flash",
    "aiMode": "auto",
    "aiSilenceSeconds": 0.6,
    "aiSystemPrompt": "",
    "aiBaseUrl": "https://api.deepseek.com",
}


class DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data, len(data))
    return DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def protect_secret(value: str) -> bytes:
    clear, clear_buffer = _blob(value.encode("utf-8"))
    entropy, entropy_buffer = _blob(ENTROPY)
    output = DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(clear), None, ctypes.byref(entropy), None, None, 0, ctypes.byref(output)
    )
    _ = (clear_buffer, entropy_buffer)
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


def unprotect_secret(data: bytes) -> str:
    encrypted, encrypted_buffer = _blob(data)
    entropy, entropy_buffer = _blob(ENTROPY)
    output = DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(encrypted), None, ctypes.byref(entropy), None, None, 0, ctypes.byref(output)
    )
    _ = (encrypted_buffer, entropy_buffer)
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


def load_api_key(path: Path = KEY_PATH) -> str:
    try:
        return unprotect_secret(path.read_bytes())
    except (OSError, UnicodeError):
        return ""


def save_api_key(value: str, path: Path = KEY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encrypted = protect_secret(value.strip())
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(encrypted)
    os.replace(temporary, path)


def clear_api_key(path: Path = KEY_PATH) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def load_settings(path: Path = CONFIG_PATH, *, strict: bool = False) -> dict[str, Any]:
    if not path.exists():
        return normalize_settings(dict(DEFAULTS))
    last_error: Exception | None = None
    for attempt in range(4):
        result = dict(DEFAULTS)
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(raw, dict):
                result.update({key: value for key, value in raw.items() if key in DEFAULTS})
            return normalize_settings(result)
        except (OSError, ValueError, TypeError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(0.04)
    if strict:
        raise RuntimeError("配置文件正在更新，请稍后重试") from last_error
    return normalize_settings(dict(DEFAULTS))


def normalize_settings(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULTS)
    result.update({key: item for key, item in value.items() if key in DEFAULTS})
    result["width"] = max(280.0, min(2200.0, float(result["width"])))
    result["height"] = max(72.0, min(800.0, float(result["height"])))
    result["fontSize"] = max(12.0, min(96.0, float(result["fontSize"])))
    result["maxLines"] = max(1, min(10, int(result["maxLines"])))
    result["opacity"] = max(0.45, min(0.98, float(result["opacity"])))
    result["aiSilenceSeconds"] = max(0.5, min(8.0, float(result["aiSilenceSeconds"])))
    result["aiEnabled"] = bool(result["aiEnabled"])
    result["locked"] = bool(result["locked"])
    if result["aiModel"] not in {"deepseek-v4-flash", "deepseek-v4-pro"}:
        result["aiModel"] = "deepseek-v4-flash"
    if result["aiMode"] not in {"auto", "summary", "qa", "explain", "translate"}:
        result["aiMode"] = "auto"
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(result["textColor"])):
        result["textColor"] = "#FFFFFF"
    for key in ("fontFamily", "screenName", "aiSystemPrompt", "aiBaseUrl", "webSocketUrl"):
        result[key] = str(result[key] or DEFAULTS[key])
    return result


def save_settings(value: dict[str, Any], path: Path = CONFIG_PATH) -> dict[str, Any]:
    normalized = normalize_settings(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
    return normalized


def public_settings() -> dict[str, Any]:
    return {
        "settings": load_settings(),
        "apiKeySet": bool(load_api_key()),
        "monitors": monitor_names(),
    }


def monitor_names() -> list[str]:
    monitors: list[tuple[bool, str]] = []

    class Rect(ctypes.Structure):
        _fields_ = [(name, wintypes.LONG) for name in ("left", "top", "right", "bottom")]

    class MonitorInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", Rect),
            ("rcWork", Rect),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]

    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(Rect), wintypes.LPARAM
    )

    def callback(monitor, _hdc, _rect, _data):
        info = MonitorInfo()
        info.cbSize = ctypes.sizeof(info)
        if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            monitors.append((bool(info.dwFlags & 1), info.szDevice))
        return True

    try:
        callback_ref = callback_type(callback)
        ctypes.windll.user32.EnumDisplayMonitors(None, None, callback_ref, 0)
    except (AttributeError, OSError):
        pass
    return [name for _primary, name in sorted(monitors, key=lambda item: (not item[0], item[1]))]


def update_from_web(payload: dict[str, Any]) -> dict[str, Any]:
    current = load_settings(strict=True)
    supplied = payload.get("settings", payload)
    if isinstance(supplied, dict):
        current.update({key: value for key, value in supplied.items() if key in DEFAULTS})
    api_key = payload.get("apiKey")
    if isinstance(api_key, str) and api_key.strip():
        save_api_key(api_key)
    if payload.get("clearApiKey") is True:
        clear_api_key()
    return save_settings(current)


def test_deepseek() -> dict[str, Any]:
    settings = load_settings()
    api_key = load_api_key()
    if not api_key:
        raise ValueError("请先保存 DeepSeek API Key")
    endpoint = settings["aiBaseUrl"].rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": settings["aiModel"],
            "messages": [
                {"role": "system", "content": "你是连接测试助手。"},
                {"role": "user", "content": "请只回复：连接成功"},
            ],
            "thinking": {"type": "disabled"},
            "stream": False,
            "max_tokens": 20,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {detail[:300]}") from exc
    content = result["choices"][0]["message"]["content"].strip()
    return {"ok": True, "message": content}
