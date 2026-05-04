import wave

from hermeshub.sound import write_ack_chime, write_wake_chime


def test_write_wake_chime(tmp_path):
    output = tmp_path / "wake.wav"
    write_wake_chime(output)

    with wave.open(str(output), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == 44100
        assert handle.getnframes() > 1000


def test_write_ack_chime(tmp_path):
    output = tmp_path / "ack.wav"
    write_ack_chime(output)

    with wave.open(str(output), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == 44100
        assert handle.getnframes() > 1000
