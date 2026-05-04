from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class AssistantConfig:
    name: str = "Hermes"
    agent_url: str = "http://127.0.0.1:8000"
    command: str | None = None
    system_prompt: str = (
        "You are Hermes, a voice assistant. Keep replies short, friendly, and easy to say "
        "out loud. Use one or two sentences unless the user asks for detail."
    )
    request_timeout_seconds: int = 60
    fallback_reply: str = "I could not reach Hermes right now."


@dataclass
class AudioConfig:
    sample_rate: int = 44100
    channels: int = 1
    block_ms: int = 80
    input_device: str | int | None = None


@dataclass
class WakeConfig:
    enabled: bool = True
    engine: str = "auto"
    model_names: list[str] = field(default_factory=list)
    model_paths: list[str] = field(default_factory=list)
    phrase: str = "hermes"
    aliases: list[str] = field(
        default_factory=lambda: [
            "hermes",
            "her mes",
            "her miss",
            "her knees",
            "harness",
            "armies",
        ]
    )
    inference_framework: str = "onnx"
    threshold: float = 0.5
    vad_threshold: float | None = 0.5
    cooldown_seconds: float = 2.0


@dataclass
class SttConfig:
    engine: str = "faster_whisper"
    vosk_model_path: str = "models/vosk-model-en-us-0.22-lgraph"
    faster_whisper_model: str = "base.en"
    faster_whisper_device: str = "cpu"
    faster_whisper_compute_type: str = "int8"
    faster_whisper_threads: int = 2
    faster_whisper_beam_size: int = 1
    faster_whisper_language: str = "en"
    faster_whisper_vad_filter: bool = False
    sherpa_model_dir: str = "models/sherpa-onnx-streaming-zipformer-en-20M-2023-02-17"
    sherpa_threads: int = 2
    sherpa_int8: bool = True
    parakeet_model: str = "nvidia/parakeet-tdt-0.6b-v2"
    parakeet_device: str = "auto"
    parakeet_sample_rate: int = 16000
    max_utterance_seconds: float = 12
    no_command_timeout_seconds: float = 10
    silence_seconds: float = 0.7
    silence_rms: int = 450


@dataclass
class ConversationConfig:
    enabled: bool = True
    followup_timeout_seconds: float = 10


@dataclass
class TtsConfig:
    piper_model_path: str = "voices/en_US-lessac-medium.onnx"
    piper_config_path: str = "voices/en_US-lessac-medium.onnx.json"
    output_wav: str = "data/last_reply.wav"
    speaker: str | int | None = None
    interrupt_enabled: bool = True
    interrupt_phrases: list[str] = field(default_factory=lambda: ["stop"])


@dataclass
class SoundConfig:
    wake_chime_enabled: bool = True
    wake_chime_wav: str = "data/wake_chime.wav"
    wake_chime_volume: float = 0.35
    ack_chime_enabled: bool = True
    ack_chime_wav: str = "data/ack_chime.wav"
    ack_chime_volume: float = 0.28


@dataclass
class ClockConfig:
    enabled: bool = True
    state_path: str = "data/clock.json"
    ringtone_wav: str = "data/alarm_ringtone.wav"
    ringtone_volume: float = 0.55
    check_interval_seconds: float = 0.5
    max_ring_seconds: float = 300


@dataclass
class CameraConfig:
    enabled: bool = False
    device_index: int | str = 0
    capture_dir: str = "data/camera"
    include_frame_with_prompt: bool = False
    jpeg_quality: int = 90


@dataclass
class AppConfig:
    assistant: AssistantConfig = field(default_factory=AssistantConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    wake: WakeConfig = field(default_factory=WakeConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)
    sound: SoundConfig = field(default_factory=SoundConfig)
    clock: ClockConfig = field(default_factory=ClockConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)


def _section(data, key):
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section {key!r} must be a mapping")
    return value


def load_config(path):
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ValueError("Config root must be a mapping")

    return AppConfig(
        assistant=AssistantConfig(**_section(raw, "assistant")),
        audio=AudioConfig(**_section(raw, "audio")),
        wake=WakeConfig(**_section(raw, "wake")),
        stt=SttConfig(**_section(raw, "stt")),
        conversation=ConversationConfig(**_section(raw, "conversation")),
        tts=TtsConfig(**_section(raw, "tts")),
        sound=SoundConfig(**_section(raw, "sound")),
        clock=ClockConfig(**_section(raw, "clock")),
        camera=CameraConfig(**_section(raw, "camera")),
    )
