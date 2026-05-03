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

    def frames(self):
        with self.sounddevice.RawInputStream(
            samplerate=self.config.sample_rate,
            blocksize=self.blocksize,
            device=self.config.input_device,
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
