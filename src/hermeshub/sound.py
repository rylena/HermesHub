import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path


class WakeChime:
    def __init__(self, config):
        self.config = config

    def play(self):
        if not self.config.wake_chime_enabled:
            return None

        output = Path(self.config.wake_chime_wav)
        if not output.is_file():
            write_wake_chime(output, volume=self.config.wake_chime_volume)

        if shutil.which("aplay"):
            subprocess.run(["aplay", "-q", str(output)], check=False)
        return str(output)


class AckChime:
    def __init__(self, config):
        self.config = config

    def play(self):
        if not self.config.ack_chime_enabled:
            return None

        output = Path(self.config.ack_chime_wav)
        if not output.is_file():
            write_ack_chime(output, volume=self.config.ack_chime_volume)

        if shutil.which("aplay"):
            subprocess.run(["aplay", "-q", str(output)], check=False)
        return str(output)


def write_wake_chime(path, volume=0.35, sample_rate=44100):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    notes = [
        (659.25, 0.09),
        (830.61, 0.11),
        (987.77, 0.16),
    ]
    gap_seconds = 0.025
    samples = []
    for frequency, duration in notes:
        count = int(sample_rate * duration)
        for index in range(count):
            t = index / sample_rate
            envelope = _envelope(index, count)
            overtone = 0.25 * math.sin(2 * math.pi * frequency * 2 * t)
            sample = math.sin(2 * math.pi * frequency * t) + overtone
            samples.append(sample * envelope * volume)
        samples.extend([0.0] * int(sample_rate * gap_seconds))

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = b"".join(struct.pack("<h", _to_pcm16(sample)) for sample in samples)
        handle.writeframes(frames)
    return str(path)


def write_ack_chime(path, volume=0.28, sample_rate=44100):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    notes = [
        (1046.5, 0.055),
        (1318.51, 0.08),
    ]
    samples = []
    for frequency, duration in notes:
        count = int(sample_rate * duration)
        for index in range(count):
            t = index / sample_rate
            envelope = _envelope(index, count)
            sample = math.sin(2 * math.pi * frequency * t)
            samples.append(sample * envelope * volume)
        samples.extend([0.0] * int(sample_rate * 0.012))

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = b"".join(struct.pack("<h", _to_pcm16(sample)) for sample in samples)
        handle.writeframes(frames)
    return str(path)


def write_alarm_ringtone(path, volume=0.55, sample_rate=44100):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    notes = [
        (880.0, 0.18),
        (1174.66, 0.18),
        (880.0, 0.18),
        (1174.66, 0.32),
    ]
    samples = []
    for _repeat in range(3):
        for frequency, duration in notes:
            count = int(sample_rate * duration)
            for index in range(count):
                t = index / sample_rate
                envelope = _envelope(index, count)
                pulse = 0.65 + 0.35 * math.sin(2 * math.pi * 7 * t)
                sample = math.sin(2 * math.pi * frequency * t) * pulse
                samples.append(sample * envelope * volume)
            samples.extend([0.0] * int(sample_rate * 0.04))
        samples.extend([0.0] * int(sample_rate * 0.15))

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = b"".join(struct.pack("<h", _to_pcm16(sample)) for sample in samples)
        handle.writeframes(frames)
    return str(path)


def _envelope(index, total):
    attack = max(1, int(total * 0.18))
    release = max(1, int(total * 0.35))
    if index < attack:
        return index / attack
    if index > total - release:
        return max(0.0, (total - index) / release)
    return 1.0


def _to_pcm16(sample):
    sample = max(-1.0, min(1.0, sample))
    return int(sample * 32767)
