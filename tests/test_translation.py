from system_audio_asr.translation import LocalEnglishChineseTranslator


def test_chinese_spacing_is_normalized() -> None:
    assert LocalEnglishChineseTranslator._clean_chinese("你 好 世 界") == "你好世界"


def test_non_chinese_spacing_is_preserved() -> None:
    assert LocalEnglishChineseTranslator._clean_chinese("API response 正常") == "API response 正常"
