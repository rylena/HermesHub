from hermeshub.tts import _play_interruptible


def test_play_interruptible_stops_playback(monkeypatch, tmp_path):
    calls = []

    class Process:
        stopped = False

        def poll(self):
            return 0 if self.stopped else None

        def terminate(self):
            calls.append("terminate")
            self.stopped = True

        def wait(self, timeout=None):
            calls.append(("wait", timeout))
            return 0

        def kill(self):
            calls.append("kill")
            self.stopped = True

    class Detector:
        def detect(self, _frame):
            return True

    monkeypatch.setattr("hermeshub.tts.subprocess.Popen", lambda _cmd: Process())

    def frames():
        yield b"\x00\x00" * 1024

    assert _play_interruptible(tmp_path / "reply.wav", frames(), Detector()) is True
    assert "terminate" in calls
    assert "kill" not in calls


def test_play_interruptible_cleans_up_on_keyboard_interrupt(monkeypatch, tmp_path):
    calls = []

    class Process:
        stopped = False

        def poll(self):
            return 0 if self.stopped else None

        def terminate(self):
            calls.append("terminate")
            self.stopped = True

        def wait(self, timeout=None):
            calls.append(("wait", timeout))
            return 0

        def kill(self):
            calls.append("kill")
            self.stopped = True

    class Detector:
        def detect(self, _frame):
            return False

    monkeypatch.setattr("hermeshub.tts.subprocess.Popen", lambda _cmd: Process())

    def frames():
        raise KeyboardInterrupt
        yield b""

    try:
        _play_interruptible(tmp_path / "reply.wav", frames(), Detector())
    except KeyboardInterrupt:
        pass

    assert "terminate" in calls
    assert "kill" not in calls
