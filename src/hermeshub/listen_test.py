from hermeshub.audio import SoundDeviceAudioSource
from hermeshub.stt import build_speech_recognizer


def run_listen_test(config):
    audio = SoundDeviceAudioSource(config.audio)
    stt = build_speech_recognizer(config.stt, config.audio)
    print("Listening for one command...")
    text = stt.listen_once(audio)
    print(f"You: {text}" if text else "No speech recognized.")
    return 0 if text else 1
