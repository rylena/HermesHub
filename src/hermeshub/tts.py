import shutil
import subprocess
import sys
from pathlib import Path


class PiperSpeaker:
    def __init__(self, config):
        self.config = config

    def speak(self, text):
        if not text.strip():
            return None

        output = Path(self.config.output_wav)
        output.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            find_piper() or "piper",
            "--model",
            self.config.piper_model_path,
            "--config",
            self.config.piper_config_path,
            "--output_file",
            str(output),
        ]
        if self.config.speaker is not None:
            cmd.extend(["--speaker", str(self.config.speaker)])

        subprocess.run(cmd, input=text, text=True, check=True)

        if shutil.which("aplay"):
            subprocess.run(["aplay", "-q", str(output)], check=False)
        return str(output)

    def available(self):
        return find_piper() is not None


def find_piper():
    found = shutil.which("piper")
    if found:
        return found

    sibling = Path(sys.executable).with_name("piper")
    if sibling.is_file():
        return str(sibling)
    return None
