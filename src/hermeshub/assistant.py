import logging
import time

from hermeshub.agent import HermesAgentClient
from hermeshub.audio import SoundDeviceAudioSource
from hermeshub.sound import AckChime, WakeChime
from hermeshub.stt import build_speech_recognizer
from hermeshub.tts import PiperSpeaker
from hermeshub.wake import build_wake_detector

LOG = logging.getLogger(__name__)


class HermesHubAssistant:
    def __init__(self, config):
        self.config = config
        self.audio = SoundDeviceAudioSource(config.audio)
        self.wake = build_wake_detector(config.wake, config.stt, config.audio)
        self.stt = build_speech_recognizer(config.stt, config.audio)
        self.tts = PiperSpeaker(config.tts)
        self.chime = WakeChime(config.sound)
        self.ack = AckChime(config.sound)
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
        self.conversation_loop(wake, frames)

    def conversation_loop(self, wake, frames):
        while True:
            text = self.stt.listen_once_from_frames(frames, on_audio_captured=self.ack.play)
            if not text:
                LOG.info("no speech recognized")
                return
            print(f"You: {text}", flush=True)

            started = time.monotonic()
            try:
                reply = self.agent.ask(text, wake=wake)
            except Exception as exc:
                LOG.warning("agent request failed: %s", exc)
                reply = self.config.assistant.fallback_reply

            elapsed = time.monotonic() - started
            print(f"Hermes ({elapsed:.1f}s): {reply}", flush=True)
            self.tts.speak(reply)

            if not self.config.conversation.enabled:
                return
