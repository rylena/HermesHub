import shutil
import subprocess
import sys
import time
from pathlib import Path


class PiperSpeaker:
    def __init__(self, config):
        self.config = config

    def speak(self, text, frames=None, interrupt_detector=None):
        if not text.strip():
            return None

        output = self.synthesize(text)
        self.play(output, frames=frames, interrupt_detector=interrupt_detector)
        return str(output)

    def synthesize(self, text):
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
        return output

    def play(self, output, frames=None, interrupt_detector=None):
        if shutil.which("aplay"):
            if frames is not None and interrupt_detector is not None:
                return _play_interruptible(output, frames, interrupt_detector)
            subprocess.run(["aplay", "-q", str(output)], check=False)
        return False

    def available(self):
        return find_piper() is not None


def _play_interruptible(output, frames, interrupt_detector):
    process = subprocess.Popen(["aplay", "-q", str(output)])
    interrupted = False
    try:
        while process.poll() is None:
            try:
                frame = next(frames)
            except KeyboardInterrupt:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise
            except StopIteration:
                break
            if interrupt_detector.detect(frame):
                interrupted = True
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                break
            time.sleep(0.01)
    finally:
        if process.poll() is None:
            process.wait()
    return interrupted


def find_piper():
    found = shutil.which("piper")
    if found:
        return found

    sibling = Path(sys.executable).with_name("piper")
    if sibling.is_file():
        return str(sibling)
    return None
