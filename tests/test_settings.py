from system_audio_asr.settings import normalize_settings


def test_overlay_height_is_bounded() -> None:
    assert normalize_settings({"height": 20})["height"] == 72
    assert normalize_settings({"height": 320})["height"] == 320
    assert normalize_settings({"height": 9999})["height"] == 800


def test_lock_state_is_normalized() -> None:
    assert normalize_settings({"locked": True})["locked"] is True
    assert normalize_settings({"locked": False})["locked"] is False


def test_font_size_accepts_manual_range() -> None:
    assert normalize_settings({"fontSize": 12})["fontSize"] == 12
    assert normalize_settings({"fontSize": 17})["fontSize"] == 17
    assert normalize_settings({"fontSize": 120})["fontSize"] == 96
