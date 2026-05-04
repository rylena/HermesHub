import json
import tempfile
import time
import wave
from pathlib import Path
from types import SimpleNamespace

from hermeshub.audio import pcm16_rms


def build_speech_recognizer(config, audio_config):
    engine = _resolve_stt_engine(config)
    if engine == "parakeet":
        return ParakeetSpeechRecognizer(config, audio_config)
    if engine == "vosk":
        return VoskSpeechRecognizer(config, audio_config)
    raise ValueError(f"Unsupported STT engine: {config.engine!r}")


def describe_stt_engine(config):
    requested = (config.engine or "auto").lower()
    resolved = _resolve_stt_engine(config)
    if requested != "auto":
        return resolved, requested
    if resolved == "parakeet":
        return resolved, "auto selected Parakeet because CUDA and NeMo are available"
    return resolved, "auto selected Vosk for fast local CPU/Raspberry Pi operation"


class VoskSpeechRecognizer:
    def __init__(self, config, audio_config):
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)
        self.config = config
        self.audio_config = audio_config
        self.model = Model(config.vosk_model_path)
        self.recognizer_factory = KaldiRecognizer

    def listen_once(self, audio_source, on_audio_captured=None):
        return self.listen_once_from_frames(audio_source.frames(), on_audio_captured=on_audio_captured)

    def listen_once_from_frames(self, frames, on_audio_captured=None):
        recognizer = self.recognizer_factory(self.model, self.audio_config.sample_rate)
        started = time.monotonic()
        last_loud = started
        heard_audio = False
        notified = False

        for frame in frames:
            now = time.monotonic()
            rms = pcm16_rms(frame)
            if rms >= self.config.silence_rms:
                heard_audio = True
                last_loud = now

            if recognizer.AcceptWaveform(frame):
                result = _parse_result(recognizer.Result())
                if result:
                    notified = _notify_audio_captured(
                        heard_audio, on_audio_captured, already_notified=notified
                    )
                    return result

            if not heard_audio and now - started >= self.config.no_command_timeout_seconds:
                return ""
            if heard_audio and now - last_loud >= self.config.silence_seconds:
                break
            if now - started >= self.config.max_utterance_seconds:
                break

        _notify_audio_captured(heard_audio, on_audio_captured, already_notified=notified)
        return _parse_result(recognizer.FinalResult())


class ParakeetSpeechRecognizer:
    def __init__(self, config, audio_config):
        try:
            import nemo.collections.asr as nemo_asr
        except ImportError as exc:
            raise RuntimeError(
                "Parakeet STT needs NVIDIA NeMo. Run scripts/install-parakeet.sh, "
                "or set stt.engine to 'auto'/'vosk' for Raspberry Pi."
            ) from exc

        self.config = config
        self.audio_config = audio_config
        self.model = nemo_asr.models.ASRModel.from_pretrained(model_name=config.parakeet_model)
        device = _select_parakeet_device(config.parakeet_device)
        if device:
            self.model = self.model.to(device)
        self.model.eval()

    def listen_once(self, audio_source, on_audio_captured=None):
        return self.listen_once_from_frames(audio_source.frames(), on_audio_captured=on_audio_captured)

    def listen_once_from_frames(self, frames, on_audio_captured=None):
        audio = _collect_utterance_audio(frames, self.config, on_audio_captured=on_audio_captured)
        if not audio:
            return ""

        wav_path = _write_temp_wav(
            audio,
            source_sample_rate=self.audio_config.sample_rate,
            target_sample_rate=self.config.parakeet_sample_rate,
        )
        try:
            output = self.model.transcribe([str(wav_path)])
        finally:
            wav_path.unlink(missing_ok=True)

        return _extract_parakeet_text(output)


def _parse_result(raw):
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    return (parsed.get("text") or "").strip()


def _resolve_stt_engine(config):
    engine = (config.engine or "auto").lower()
    if engine in {"vosk", "parakeet"}:
        return engine
    if engine in {"parakeet_v2", "parakeet-v2", "nvidia_parakeet"}:
        return "parakeet"
    if engine == "auto":
        if _parakeet_can_run_accelerated():
            return "parakeet"
        return "vosk"
    raise ValueError(f"Unsupported STT engine: {config.engine!r}")


def _parakeet_can_run_accelerated():
    try:
        import torch
        import nemo.collections.asr  # noqa: F401
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def _select_parakeet_device(device):
    requested = (device or "auto").lower()
    if requested == "auto":
        try:
            import torch
        except ImportError:
            return None
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested in {"none", "default"}:
        return None
    return requested


def _collect_utterance_audio(frames, config, on_audio_captured=None):
    started = time.monotonic()
    last_loud = started
    heard_audio = False
    chunks = []

    for frame in frames:
        now = time.monotonic()
        rms = pcm16_rms(frame)
        if rms >= config.silence_rms:
            heard_audio = True
            last_loud = now

        if heard_audio:
            chunks.append(frame)

        if not heard_audio and now - started >= config.no_command_timeout_seconds:
            return b""
        if heard_audio and now - last_loud >= config.silence_seconds:
            break
        if now - started >= config.max_utterance_seconds:
            break

    _notify_audio_captured(heard_audio, on_audio_captured)
    return b"".join(chunks) if heard_audio else b""


def _notify_audio_captured(heard_audio, callback, already_notified=False):
    if heard_audio and callback is not None and not already_notified:
        callback()
        return True
    return already_notified


def _write_temp_wav(audio, source_sample_rate, target_sample_rate):
    samples = _pcm16_resample(audio, source_sample_rate, target_sample_rate)
    handle = tempfile.NamedTemporaryFile(prefix="hermeshub-", suffix=".wav", delete=False)
    path = Path(handle.name)
    handle.close()

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(target_sample_rate)
        wav.writeframes(samples)
    return path


def _pcm16_resample(audio, source_sample_rate, target_sample_rate):
    if source_sample_rate == target_sample_rate:
        return audio

    import numpy as np

    samples = np.frombuffer(audio, dtype="<i2")
    if len(samples) == 0:
        return b""

    duration = len(samples) / float(source_sample_rate)
    target_length = max(1, int(duration * target_sample_rate))
    source_positions = np.linspace(0, len(samples) - 1, num=len(samples), dtype=np.float32)
    target_positions = np.linspace(0, len(samples) - 1, num=target_length, dtype=np.float32)
    resampled = np.interp(target_positions, source_positions, samples).astype("<i2")
    return resampled.tobytes()


def _extract_parakeet_text(output):
    if output is None:
        return ""
    if isinstance(output, str):
        return output.strip()
    if isinstance(output, SimpleNamespace):
        return _extract_parakeet_text(vars(output))
    if isinstance(output, dict):
        for key in ("text", "transcript"):
            value = output.get(key)
            if value:
                return str(value).strip()
        return ""
    if isinstance(output, (list, tuple)):
        if not output:
            return ""
        return _extract_parakeet_text(output[0])
    text = getattr(output, "text", None) or getattr(output, "transcript", None)
    return str(text).strip() if text else ""


def running_on_raspberry_pi():
    try:
        model = Path("/proc/device-tree/model").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "raspberry pi" in model.lower()
