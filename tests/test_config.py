from pathlib import Path

from hermeshub.config import load_config


def test_load_config_example():
    config = load_config(Path("config.example.yaml"))
    assert config.assistant.name == "Hermes"
    assert config.audio.sample_rate == 44100
    assert config.wake.phrase == "hermes"
    assert "her mes" in config.wake.aliases
    assert config.wake.engine == "auto"
    assert config.wake.model_paths == []
    assert config.sound.wake_chime_enabled is True
    assert config.camera.capture_dir == "data/camera"
