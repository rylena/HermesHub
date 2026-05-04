import logging
import time

from hermeshub.agent import HermesAgentClient, is_backend_error
from hermeshub.audio import SoundDeviceAudioSource
from hermeshub.sound import AckChime, WakeChime
from hermeshub.stt import build_speech_recognizer, describe_stt_engine
from hermeshub.tts import PiperSpeaker
from hermeshub.wake import VoskPhraseDetector, build_wake_detector

LOG = logging.getLogger(__name__)


class HermesHubAssistant:
    def __init__(self, config):
        self.config = config
        self.audio = SoundDeviceAudioSource(config.audio)
        self.wake = build_wake_detector(config.wake, config.stt, config.audio)
        self.stt = build_speech_recognizer(config.stt, config.audio)
        self.tts = PiperSpeaker(config.tts)
        self.interrupt_detector = self._build_interrupt_detector()
        self.chime = WakeChime(config.sound)
        self.ack = AckChime(config.sound)
        self.agent = HermesAgentClient(config.assistant)

    def run_forever(self):
        stt_engine, stt_detail = describe_stt_engine(self.config.stt)
        agent_mode = "command" if self.config.assistant.command else self.config.assistant.agent_url
        LOG.info(
            "HermesHub listening (wake=%s, stt=%s:%s, agent=%s)",
            self.config.wake.engine,
            stt_engine,
            stt_detail,
            agent_mode,
        )
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
            if is_backend_error(reply):
                LOG.warning("agent returned backend error: %s", reply)
                reply = self.config.assistant.fallback_reply

            elapsed = time.monotonic() - started
            print(f"Hermes ({elapsed:.1f}s): {reply}", flush=True)
            interrupted = self.tts.speak(
                reply,
                frames=frames,
                interrupt_detector=self.interrupt_detector,
            )
            if interrupted:
                LOG.info("speech interrupted by stop phrase")

            if not self.config.conversation.enabled:
                return

    def _build_interrupt_detector(self):
        if not self.config.tts.interrupt_enabled:
            return None
        if not self.config.tts.interrupt_phrases:
            return None
        return VoskPhraseDetector(
            self.config.stt.vosk_model_path,
            self.config.audio.sample_rate,
            self.config.tts.interrupt_phrases,
            model=self._vosk_stt_model(),
        )

    def _vosk_stt_model(self):
        model = getattr(self.stt, "model", None)
        return model if hasattr(model, "_handle") else None
