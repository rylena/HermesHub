import logging

from hermeshub.agent import HermesAgentClient
from hermeshub.audio import SoundDeviceAudioSource
from hermeshub.camera import Camera
from hermeshub.stt import VoskSpeechRecognizer
from hermeshub.tts import PiperSpeaker
from hermeshub.wake import DisabledWakeDetector, WakeDetector

LOG = logging.getLogger(__name__)


class HermesHubAssistant:
    def __init__(self, config):
        self.config = config
        self.audio = SoundDeviceAudioSource(config.audio)
        self.wake = WakeDetector(config.wake) if config.wake.enabled else DisabledWakeDetector()
        self.stt = VoskSpeechRecognizer(config.stt, config.audio)
        self.tts = PiperSpeaker(config.tts)
        self.camera = Camera(config.camera)
        self.agent = HermesAgentClient(config.assistant)

    def run_forever(self):
        LOG.info("HermesHub listening")
        for frame in self.audio.frames():
            wake = self.wake.detect(frame)
            if wake is None:
                continue
            self.handle_wake(wake)

    def handle_wake(self, wake):
        LOG.info("wake detected: %s", wake)
        text = self.stt.listen_once(self.audio)
        if not text:
            LOG.info("no speech recognized")
            return

        image_path = None
        if self.config.camera.include_frame_with_prompt:
            image_path = self.camera.capture()

        try:
            reply = self.agent.ask(text, image_path=image_path, wake=wake)
        except Exception as exc:
            LOG.warning("agent request failed: %s", exc)
            reply = self.config.assistant.fallback_reply

        self.tts.speak(reply)
