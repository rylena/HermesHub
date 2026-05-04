import time

import numpy as np


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


class DisabledWakeDetector:
    def __init__(self):
        self.triggered = False

    def detect(self, _frame):
        if self.triggered:
            return None
        self.triggered = True
        return {"name": "disabled", "score": 1.0}
