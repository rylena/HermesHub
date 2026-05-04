from hermeshub.stt import _parse_result


def test_parse_vosk_result_text():
    assert _parse_result('{"text": "hello hermes"}') == "hello hermes"


def test_parse_vosk_result_missing_text():
    assert _parse_result('{"partial": "hello"}') == ""


def test_parse_vosk_result_bad_json():
    assert _parse_result("not json") == ""


def test_no_command_timeout_returns_empty(monkeypatch):
    from hermeshub.stt import VoskSpeechRecognizer

    class Config:
        vosk_model_path = "unused"
        max_utterance_seconds = 12
        no_command_timeout_seconds = 0.01
        silence_seconds = 1.1
        silence_rms = 10_000

    class AudioConfig:
        sample_rate = 44100

    class Recognizer:
        def __init__(self, *_args):
            pass

        def AcceptWaveform(self, _frame):
            return False

        def PartialResult(self):
            return '{"partial": ""}'

        def FinalResult(self):
            return '{"text": ""}'

    monkeypatch.setattr("hermeshub.stt.pcm16_rms", lambda _frame: 0)
    recognizer = object.__new__(VoskSpeechRecognizer)
    recognizer.config = Config()
    recognizer.audio_config = AudioConfig()
    recognizer.model = object()
    recognizer.recognizer_factory = Recognizer

    def frames():
        while True:
            yield b"\x00\x00" * 1024

    assert recognizer.listen_once_from_frames(frames()) == ""
