from pathlib import Path

from hermeshub.config import load_config


def test_load_config_example():
    config = load_config(Path("config.example.yaml"))
    assert config.assistant.name == "Hermes"
    assert config.audio.sample_rate == 16000
    assert config.wake.model_names
    assert config.camera.capture_dir == "data/camera"
