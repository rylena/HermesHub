import importlib.util
import shutil
from pathlib import Path

from hermeshub.audio import describe_input_device
from hermeshub.camera import Camera
from hermeshub.stt import describe_stt_engine, running_on_raspberry_pi
from hermeshub.tts import find_piper


def run_doctor(config):
    checks = []
    checks.append(("config loaded", True, "ok"))
    wake_engine = config.wake.engine.lower()
    if config.wake.model_paths:
        for model_path in config.wake.model_paths:
            checks.append(_path_check(f"wake model for {config.wake.phrase!r}", model_path))
    elif wake_engine in {"auto", "vosk_keyword"}:
        aliases = ", ".join(config.wake.aliases)
        checks.append(("wake phrase", True, f"{config.wake.phrase!r} via Vosk keyword fallback ({aliases})"))
    else:
        checks.append(("wake model", False, "openwakeword selected but no model_paths/model_names set"))

    resolved_stt, stt_detail = describe_stt_engine(config.stt)
    checks.append(("STT engine", True, f"{resolved_stt} ({stt_detail})"))
    checks.append(_path_check("Vosk model", config.stt.vosk_model_path, is_dir=True))
    if resolved_stt == "sherpa":
        checks.extend(_sherpa_checks(config.stt))
    if resolved_stt == "parakeet" or (config.stt.engine or "").lower().startswith("parakeet"):
        checks.extend(_parakeet_checks(config.stt))
    checks.append(_path_check("Piper voice", config.tts.piper_model_path))
    checks.append(_path_check("Piper voice config", config.tts.piper_config_path))
    piper = find_piper()
    checks.append(("piper command", piper is not None, piper or "missing"))
    checks.append(("aplay command", shutil.which("aplay") is not None, shutil.which("aplay") or "missing"))

    for module in ("openwakeword", "vosk", "sounddevice", "cv2", "numpy", "yaml", "requests"):
        checks.append((f"python module {module}", _module_exists(module), ""))

    try:
        import sounddevice as sd

        devices = sd.query_devices()
        checks.append(("audio devices", bool(devices), f"{len(devices)} device entries"))
        device, detail = describe_input_device(sd, config.audio)
        checks.append(("audio input", device is not None or bool(devices), f"{device!r} {detail}"))
    except Exception as exc:
        checks.append(("audio devices", False, str(exc)))

    if config.camera.enabled:
        try:
            camera_ok = Camera(config.camera).can_open()
            checks.append(("camera", camera_ok, f"device {config.camera.device_index}"))
        except Exception as exc:
            checks.append(("camera", False, str(exc)))
    else:
        checks.append(("camera", True, "disabled"))

    return checks


def _parakeet_checks(config):
    checks = []
    on_pi = running_on_raspberry_pi()
    checks.append(("Raspberry Pi Parakeet", not on_pi, "not recommended on Pi 4" if on_pi else "not Pi"))
    for module in ("torch", "torchaudio", "nemo.collections.asr"):
        checks.append((f"python module {module}", _module_exists(module), ""))

    try:
        import torch

        cuda = torch.cuda.is_available()
        checks.append(("Parakeet device", cuda or config.parakeet_device == "cpu", "cuda" if cuda else "cpu"))
    except Exception as exc:
        checks.append(("Parakeet device", False, str(exc)))

    checks.append(("Parakeet model", True, config.parakeet_model))
    return checks


def _sherpa_checks(config):
    checks = []
    checks.append(("python module sherpa_onnx", _module_exists("sherpa_onnx"), ""))
    checks.append(_path_check("Sherpa model dir", config.sherpa_model_dir, is_dir=True))
    root = Path(config.sherpa_model_dir)
    suffix = ".int8.onnx" if config.sherpa_int8 else ".onnx"
    for label, path in (
        ("Sherpa tokens", root / "tokens.txt"),
        ("Sherpa encoder", root / f"encoder-epoch-99-avg-1{suffix}"),
        ("Sherpa decoder", root / "decoder-epoch-99-avg-1.onnx"),
        ("Sherpa joiner", root / f"joiner-epoch-99-avg-1{suffix}"),
    ):
        checks.append(_path_check(label, path))
    return checks


def print_doctor(checks):
    failed = False
    for name, ok, detail in checks:
        status = "ok" if ok else "fail"
        print(f"{status:4} {name} {detail}".rstrip())
        failed = failed or not ok
    return 1 if failed else 0


def _path_check(label, path, is_dir=False):
    item = Path(path)
    ok = item.is_dir() if is_dir else item.is_file()
    return (label, ok, str(item))


def _module_exists(module):
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False
