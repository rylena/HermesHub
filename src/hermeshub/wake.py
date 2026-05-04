import json
import time
from pathlib import Path


def build_wake_detector(wake_config, stt_config, audio_config):
    if not wake_config.enabled:
        return DisabledWakeDetector()

    engine = wake_config.engine.lower()
    if engine not in {"auto", "openwakeword", "vosk_keyword"}:
        raise ValueError("wake.engine must be auto, openwakeword, or vosk_keyword")

    has_openwakeword_model = bool(wake_config.model_names) or any(
        Path(path).is_file() for path in wake_config.model_paths
    )
    if engine == "openwakeword" or (engine == "auto" and has_openwakeword_model):
        return WakeDetector(wake_config)

    return VoskKeywordWakeDetector(wake_config, stt_config, audio_config)


class WakeDetector:
    def __init__(self, config):
        from openwakeword.model import Model

        args = {}
        wakeword_models = [*config.model_paths, *config.model_names]
        if wakeword_models:
            args["wakeword_models"] = wakeword_models
        args["inference_framework"] = config.inference_framework
        if config.vad_threshold is not None:
            args["vad_threshold"] = config.vad_threshold

        self.config = config
        self.model = Model(**args)
        self.last_wake = 0.0

    def detect(self, frame):
        import numpy as np

        now = time.monotonic()
        if now - self.last_wake < self.config.cooldown_seconds:
            return None

        pcm = np.frombuffer(frame, dtype=np.int16)
        scores = self.model.predict(pcm)
        for name, score in scores.items():
            if score >= self.config.threshold:
                self.last_wake = now
                return {"name": name, "score": float(score)}
        return None


class VoskKeywordWakeDetector:
    def __init__(self, wake_config, stt_config, audio_config):
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)
        self.config = wake_config
        self.phrases = [_normalize(item) for item in [wake_config.phrase, *wake_config.aliases] if item]
        self.model = Model(stt_config.vosk_model_path)
        self.recognizer = KaldiRecognizer(self.model, audio_config.sample_rate)
        self.last_wake = 0.0

    def detect(self, frame):
        now = time.monotonic()
        if now - self.last_wake < self.config.cooldown_seconds:
            return None

        if self.recognizer.AcceptWaveform(frame):
            text = _result_text(self.recognizer.Result(), "text")
        else:
            text = _result_text(self.recognizer.PartialResult(), "partial")

        if _matches_wake_phrase(text, self.phrases):
            self.last_wake = now
            self.recognizer.Reset()
            return {"name": self.config.phrase, "score": 1.0, "engine": "vosk_keyword"}
        return None


class DisabledWakeDetector:
    def __init__(self):
        self.triggered = False

    def detect(self, _frame):
        if self.triggered:
            return None
        self.triggered = True
        return {"name": "disabled", "score": 1.0}


def _result_text(raw, key):
    try:
        return json.loads(raw).get(key, "")
    except json.JSONDecodeError:
        return ""


def _normalize(text):
    return " ".join(text.lower().strip().split())


def _compact(text):
    return _normalize(text).replace(" ", "")


def _matches_wake_phrase(text, phrases):
    normalized = _normalize(text)
    compact = _compact(text)
    for phrase in phrases:
        if phrase and phrase in normalized:
            return True
        if phrase and _compact(phrase) in compact:
            return True
    return False
