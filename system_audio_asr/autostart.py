from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


STARTUP_NAME = "VoxRibbon-Autostart.vbs"


def default_project_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def startup_directory() -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def startup_path(directory: Path | None = None) -> Path:
    return (directory or startup_directory()) / STARTUP_NAME


def _vbs(project_dir: Path) -> str:
    launch = str((project_dir / "launch.ps1").resolve()).replace('"', '""')
    command = (
        'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass '
        f'-File ""{launch}""'
    )
    return (
        "' VoxRibbon managed autostart\r\n"
        'Set shell = CreateObject("WScript.Shell")\r\n'
        f'shell.Run "{command}", 0, False\r\n'
    )


def enable(project_dir: Path | None = None, directory: Path | None = None) -> dict[str, object]:
    project = (project_dir or default_project_dir()).resolve()
    launch = project / "launch.ps1"
    python = project / ".venv" / "Scripts" / "python.exe"
    if not launch.is_file():
        raise FileNotFoundError(f"找不到启动脚本：{launch}")
    if not python.is_file():
        raise FileNotFoundError("尚未安装项目，请先运行 install.ps1")
    target = startup_path(directory)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(_vbs(project), encoding="utf-16")
    os.replace(temporary, target)
    return status(project, directory)


def disable(project_dir: Path | None = None, directory: Path | None = None) -> dict[str, object]:
    target = startup_path(directory)
    try:
        target.unlink()
    except FileNotFoundError:
        pass
    return status(project_dir, directory)


def status(project_dir: Path | None = None, directory: Path | None = None) -> dict[str, object]:
    target = startup_path(directory)
    enabled = target.is_file()
    matches_project = False
    if enabled:
        try:
            content = target.read_text(encoding="utf-16")
            project = (project_dir or default_project_dir()).resolve()
            matches_project = str((project / "launch.ps1").resolve()) in content
        except (OSError, UnicodeError):
            matches_project = False
    return {
        "enabled": enabled and matches_project,
        "exists": enabled,
        "matchesProject": matches_project,
        "path": str(target),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="管理 VoxRibbon 当前用户开机自启")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--enable", action="store_true")
    group.add_argument("--disable", action="store_true")
    args = parser.parse_args()
    result = enable() if args.enable else disable() if args.disable else status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
