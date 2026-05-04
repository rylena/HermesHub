import json
import time

from hermeshub.audio import pcm16_rms


class VoskSpeechRecognizer:
    def __init__(self, config, audio_config):
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)
        self.config = config
        self.audio_config = audio_config
        self.model = Model(config.vosk_model_path)
        self.recognizer_factory = KaldiRecognizer

    def listen_once(self, audio_source):
        return self.listen_once_from_frames(audio_source.frames())

    def listen_once_from_frames(self, frames):
        recognizer = self.recognizer_factory(self.model, self.audio_config.sample_rate)
        started = time.monotonic()
        last_loud = started
        heard_audio = False

        for frame in frames:
            now = time.monotonic()
            rms = pcm16_rms(frame)
            if rms >= self.config.silence_rms:
                heard_audio = True
                last_loud = now

            if recognizer.AcceptWaveform(frame):
                result = _parse_result(recognizer.Result())
                if result:
                    return result

            if not heard_audio and now - started >= self.config.no_command_timeout_seconds:
                return ""
            if heard_audio and now - last_loud >= self.config.silence_seconds:
                break
            if now - started >= self.config.max_utterance_seconds:
                break

        return _parse_result(recognizer.FinalResult())


def _parse_result(raw):
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    return (parsed.get("text") or "").strip()
