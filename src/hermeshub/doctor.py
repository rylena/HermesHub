import importlib.util
import shutil
from pathlib import Path

from hermeshub.camera import Camera
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
    checks.append(_path_check("Vosk model", config.stt.vosk_model_path, is_dir=True))
    checks.append(_path_check("Piper voice", config.tts.piper_model_path))
    checks.append(_path_check("Piper voice config", config.tts.piper_config_path))
    piper = find_piper()
    checks.append(("piper command", piper is not None, piper or "missing"))
    checks.append(("aplay command", shutil.which("aplay") is not None, shutil.which("aplay") or "missing"))

    for module in ("openwakeword", "vosk", "sounddevice", "cv2", "numpy", "yaml", "requests"):
        checks.append((f"python module {module}", importlib.util.find_spec(module) is not None, ""))

    try:
        import sounddevice as sd

        devices = sd.query_devices()
        checks.append(("audio devices", bool(devices), f"{len(devices)} device entries"))
    except Exception as exc:
        checks.append(("audio devices", False, str(exc)))

    try:
        camera_ok = Camera(config.camera).can_open()
        checks.append(("camera", camera_ok, f"device {config.camera.device_index}"))
    except Exception as exc:
        checks.append(("camera", False, str(exc)))

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
