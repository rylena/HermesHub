from collections.abc import Iterator
from array import array
from math import sqrt
from sys import byteorder


class AudioSource:
    def frames(self) -> Iterator[bytes]:
        raise NotImplementedError


class SoundDeviceAudioSource(AudioSource):
    def __init__(self, config):
        import sounddevice as sd

        self.config = config
        self.sounddevice = sd
        self.blocksize = int(config.sample_rate * (config.block_ms / 1000))
        self.device = resolve_input_device(sd, config)

    def frames(self):
        with self.sounddevice.RawInputStream(
            samplerate=self.config.sample_rate,
            blocksize=self.blocksize,
            device=self.device,
            channels=self.config.channels,
            dtype="int16",
        ) as stream:
            while True:
                data, overflowed = stream.read(self.blocksize)
                if overflowed:
                    continue
                yield bytes(data)


def pcm16_rms(frame):
    audio = array("h")
    audio.frombytes(frame)
    if byteorder != "little":
        audio.byteswap()
    if not audio:
        return 0.0
    return sqrt(sum(sample * sample for sample in audio) / len(audio))


def resolve_input_device(sounddevice, config):
    if config.input_device is not None:
        return config.input_device

    candidates = _input_device_candidates(sounddevice)
    for device in candidates:
        if _can_open_input(sounddevice, config, device):
            return device
    return None


def describe_input_device(sounddevice, config):
    device = resolve_input_device(sounddevice, config)
    try:
        info = sounddevice.query_devices(device, "input")
    except Exception:
        return device, "default input"
    return device, f"{info['name']} @ {int(info['default_samplerate'])}Hz"


def _input_device_candidates(sounddevice):
    candidates = [None]
    try:
        default_input = sounddevice.default.device[0]
        if default_input is not None and default_input >= 0:
            candidates.append(default_input)
    except Exception:
        pass

    devices = sounddevice.query_devices()
    for index, device in enumerate(devices):
        if int(device.get("max_input_channels", 0)) > 0:
            candidates.append(index)

    unique = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def _can_open_input(sounddevice, config, device):
    try:
        stream = sounddevice.RawInputStream(
            samplerate=config.sample_rate,
            blocksize=int(config.sample_rate * (config.block_ms / 1000)),
            device=device,
            channels=config.channels,
            dtype="int16",
        )
        stream.close()
        return True
    except Exception:
        return False
