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


def test_deepseek_translation_mode_is_preserved() -> None:
    assert normalize_settings({"aiMode": "translate"})["aiMode"] == "translate"
    assert normalize_settings({"aiMode": "translate_zh"})["aiMode"] == "auto"


def test_live_translation_flag_is_normalized() -> None:
    assert normalize_settings({"liveTranslateEnabled": True})["liveTranslateEnabled"] is True
    assert normalize_settings({"liveTranslateEnabled": False})["liveTranslateEnabled"] is False


def test_asr_language_is_normalized() -> None:
    assert normalize_settings({"asrLanguage": "en"})["asrLanguage"] == "en"
    assert normalize_settings({"asrLanguage": "invalid"})["asrLanguage"] == "zh"


def test_frame_appearance_is_normalized() -> None:
    assert normalize_settings({"frameMode": "always"})["frameMode"] == "always"
    assert normalize_settings({"frameMode": "bad"})["frameMode"] == "hover"
    assert normalize_settings({"frameOpacity": 2})["frameOpacity"] == 1.0
    assert normalize_settings({"frameColor": "invalid"})["frameColor"] == "#7DBEFF"
