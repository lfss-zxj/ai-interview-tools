import numpy as np

from system_audio_asr.segmenter import SpeechSegmenter, dbfs, merge_stream_text


def make_segmenter() -> SpeechSegmenter:
    return SpeechSegmenter(16_000, 7_680, -40, 300, 100)


def test_silence_does_not_start() -> None:
    segmenter = make_segmenter()
    for _ in range(5):
        assert segmenter.feed(np.zeros(1600, dtype=np.float32))[1] == []
    assert not segmenter.active


def test_speech_streams_then_finalizes() -> None:
    segmenter = make_segmenter()
    packets = []
    for _ in range(6):
        packets += segmenter.feed(np.full(1600, 0.1, dtype=np.float32))[1]
    for _ in range(3):
        packets += segmenter.feed(np.zeros(1600, dtype=np.float32))[1]
    assert packets[-1].is_final
    assert any(not packet.is_final for packet in packets)
    assert not segmenter.active


def test_level_and_text_merge() -> None:
    assert dbfs(np.zeros(10, dtype=np.float32)) == -120.0
    assert -20.1 < dbfs(np.full(10, 0.1, dtype=np.float32)) < -19.9
    assert merge_stream_text("你好世界", "世界和平") == "你好世界和平"
    assert merge_stream_text("你好", "你好世界") == "你好世界"
    assert merge_stream_text("would you", " in the") == "would you in the"
    assert merge_stream_text("tell me", "about") == "tell me about"


def test_zero_preroll_starts_without_error() -> None:
    segmenter = SpeechSegmenter(16_000, 7_680, -40, 300, 0)
    level, packets = segmenter.feed(np.full(1600, 0.1, dtype=np.float32))
    assert level > -40
    assert packets == []
    assert segmenter.active
