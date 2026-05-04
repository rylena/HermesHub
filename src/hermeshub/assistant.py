import logging

from hermeshub.agent import HermesAgentClient
from hermeshub.audio import SoundDeviceAudioSource
from hermeshub.sound import WakeChime
from hermeshub.stt import VoskSpeechRecognizer
from hermeshub.tts import PiperSpeaker
from hermeshub.wake import build_wake_detector

LOG = logging.getLogger(__name__)


class HermesHubAssistant:
    def __init__(self, config):
        self.config = config
        self.audio = SoundDeviceAudioSource(config.audio)
        self.wake = build_wake_detector(config.wake, config.stt, config.audio)
        self.stt = VoskSpeechRecognizer(config.stt, config.audio)
        self.tts = PiperSpeaker(config.tts)
        self.chime = WakeChime(config.sound)
        self.agent = HermesAgentClient(config.assistant)

    def run_forever(self):
        LOG.info("HermesHub listening")
        frames = self.audio.frames()
        for frame in frames:
            wake = self.wake.detect(frame)
            if wake is None:
                continue
            self.handle_wake(wake, frames)

    def handle_wake(self, wake, frames):
        LOG.info("wake detected: %s", wake)
        self.chime.play()
        text = self.stt.listen_once_from_frames(frames)
        if not text:
            LOG.info("no speech recognized")
            return
        print(f"You: {text}", flush=True)

        try:
            reply = self.agent.ask(text, wake=wake)
        except Exception as exc:
            LOG.warning("agent request failed: %s", exc)
            reply = self.config.assistant.fallback_reply

        print(f"Hermes: {reply}", flush=True)
        self.tts.speak(reply)
