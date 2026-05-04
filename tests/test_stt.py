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


def test_vosk_notifies_when_audio_is_captured(monkeypatch):
    from hermeshub.stt import VoskSpeechRecognizer

    class Config:
        vosk_model_path = "unused"
        max_utterance_seconds = 1
        no_command_timeout_seconds = 1
        silence_seconds = 0.01
        silence_rms = 1

    class AudioConfig:
        sample_rate = 44100

    class Recognizer:
        def __init__(self, *_args):
            pass

        def AcceptWaveform(self, _frame):
            return False

        def FinalResult(self):
            return '{"text": "turn on lights"}'

    values = iter([20, 0, 0, 0])
    monkeypatch.setattr("hermeshub.stt.pcm16_rms", lambda _frame: next(values, 0))
    recognizer = object.__new__(VoskSpeechRecognizer)
    recognizer.config = Config()
    recognizer.audio_config = AudioConfig()
    recognizer.model = object()
    recognizer.recognizer_factory = Recognizer

    called = []

    def frames():
        while True:
            yield b"\x00\x00" * 1024

    assert recognizer.listen_once_from_frames(frames(), on_audio_captured=lambda: called.append(True))
    assert called == [True]


def test_extract_parakeet_text_from_hypothesis_object():
    from types import SimpleNamespace

    from hermeshub.stt import _extract_parakeet_text

    assert _extract_parakeet_text([SimpleNamespace(text="Hello Hermes.")]) == "Hello Hermes."


def test_auto_stt_engine_prefers_vosk_without_cuda(monkeypatch):
    from hermeshub.stt import describe_stt_engine

    class Config:
        engine = "auto"
        sherpa_model_dir = "unused"
        sherpa_int8 = True

    monkeypatch.setattr("hermeshub.stt._sherpa_available", lambda _config: False)
    monkeypatch.setattr("hermeshub.stt._parakeet_can_run_accelerated", lambda: False)
    assert describe_stt_engine(Config())[0] == "vosk"


def test_auto_stt_engine_prefers_sherpa_when_available(monkeypatch):
    from hermeshub.stt import describe_stt_engine

    class Config:
        engine = "auto"

    monkeypatch.setattr("hermeshub.stt._sherpa_available", lambda _config: True)
    assert describe_stt_engine(Config())[0] == "sherpa"
