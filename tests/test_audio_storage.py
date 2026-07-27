"""Tests for PCM audio retention used by voice test sessions."""

import wave

from core.audio_storage import PcmWaveWriter


def test_pcm_wave_writer_preserves_format_and_frames(tmp_path):
    path = tmp_path / "doctor.wav"
    first = b"\x01\x00\xff\x7f"
    second = b"\x00\x80\x00\x00"

    writer = PcmWaveWriter(path, sample_rate=16000)
    writer.write(first)
    writer.write(second)
    metadata = writer.close()

    with wave.open(str(path), "rb") as recording:
        assert recording.getframerate() == 16000
        assert recording.getnchannels() == 1
        assert recording.getsampwidth() == 2
        assert recording.readframes(recording.getnframes()) == first + second

    assert metadata["complete"] is True
    assert metadata["bytes"] == len(first) + len(second)


def test_pcm_wave_writer_close_is_idempotent(tmp_path):
    writer = PcmWaveWriter(tmp_path / "patient.wav", sample_rate=24000)
    writer.write(b"\x00\x00")

    first = writer.close(complete=False)
    second = writer.close(complete=True)

    assert first == second
    assert second["complete"] is False
