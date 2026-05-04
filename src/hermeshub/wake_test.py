import time

from hermeshub.audio import SoundDeviceAudioSource, pcm16_rms
from hermeshub.sound import WakeChime
from hermeshub.wake import build_wake_detector


def run_wake_test(config, seconds):
    audio = SoundDeviceAudioSource(config.audio)
    wake = build_wake_detector(config.wake, config.stt, config.audio)
    chime = WakeChime(config.sound)
    deadline = time.monotonic() + seconds
    last_text = None

    print(f"Listening for {config.wake.phrase!r} for {seconds:.0f}s")
    print(f"input_device={config.audio.input_device!r} sample_rate={config.audio.sample_rate}")

    for frame in audio.frames():
        rms = pcm16_rms(frame)
        event = wake.detect(frame)
        text = getattr(wake, "last_text", "")
        if text and text != last_text:
            print(f"heard: {text!r} rms={rms:.0f}")
            last_text = text
        if event:
            print(f"WAKE: {event}")
            chime.play()
            return 0
        if time.monotonic() >= deadline:
            print("No wake detected.")
            return 1
    return 1
