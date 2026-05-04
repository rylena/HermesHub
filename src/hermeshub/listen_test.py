from hermeshub.audio import SoundDeviceAudioSource
from hermeshub.stt import VoskSpeechRecognizer


def run_listen_test(config):
    audio = SoundDeviceAudioSource(config.audio)
    stt = VoskSpeechRecognizer(config.stt, config.audio)
    print("Listening for one command...")
    text = stt.listen_once(audio)
    print(f"You: {text}" if text else "No speech recognized.")
    return 0 if text else 1
