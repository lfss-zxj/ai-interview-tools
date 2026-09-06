from pathlib import Path

from system_audio_asr.autostart import disable, enable, status


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "Project With Spaces"
    (project / ".venv" / "Scripts").mkdir(parents=True)
    (project / ".venv" / "Scripts" / "python.exe").write_bytes(b"")
    (project / "launch.ps1").write_text("", encoding="utf-8")
    return project


def test_enable_and_disable_autostart(tmp_path: Path) -> None:
    project = _project(tmp_path)
    startup = tmp_path / "Startup"
    enabled = enable(project, startup)
    assert enabled["enabled"] is True
    content = Path(enabled["path"]).read_text(encoding="utf-16")
    assert str(project / "launch.ps1") in content
    assert "WindowStyle Hidden" in content
    assert disable(project, startup)["enabled"] is False


def test_status_rejects_entry_for_different_project(tmp_path: Path) -> None:
    first = _project(tmp_path / "one")
    second = _project(tmp_path / "two")
    startup = tmp_path / "Startup"
    enable(first, startup)
    result = status(second, startup)
    assert result["exists"] is True
    assert result["enabled"] is False
