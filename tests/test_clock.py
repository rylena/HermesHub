from datetime import datetime, timedelta

from hermeshub.clock import ClockManager, parse_clock_intent, parse_duration


class Config:
    enabled = True
    check_interval_seconds = 0.01
    ringtone_wav = "unused.wav"
    ringtone_volume = 0.55

    def __init__(self, state_path):
        self.state_path = str(state_path)


class Player:
    def __init__(self):
        self.started = 0
        self.stopped = 0

    def start(self):
        self.started += 1

    def stop(self):
        self.stopped += 1


def test_parse_timer_duration_words_and_numbers():
    assert parse_duration("set a timer for ten minutes") == timedelta(minutes=10)
    assert parse_duration("set a timer for 1 hour and 30 minutes") == timedelta(minutes=90)
    assert parse_duration("set a timer for half an hour") == timedelta(minutes=30)


def test_parse_alarm_time_tomorrow():
    now = datetime(2026, 5, 4, 21, 0)

    intent = parse_clock_intent("wake me up tomorrow at 6:30 am", now)

    assert intent["action"] == "set"
    assert intent["kind"] == "alarm"
    assert intent["due_at"] == datetime(2026, 5, 5, 6, 30)


def test_clock_manager_sets_lists_and_fires_timer(tmp_path):
    now = datetime(2026, 5, 4, 9, 0)
    player = Player()
    manager = ClockManager(Config(tmp_path / "clock.json"), now_func=lambda: now, player=player)

    assert manager.handle_text("set a timer for 5 minutes") == "Timer set for 5 minutes."
    assert "timer with 5 minutes left" in manager.handle_text("what timers are set")

    now = datetime(2026, 5, 4, 9, 5, 1)
    manager.tick()

    assert player.started == 1
    assert manager.describe() == "No alarms or timers are set."


def test_clock_manager_stops_ringing(tmp_path):
    manager = ClockManager(Config(tmp_path / "clock.json"), player=Player())

    assert manager.handle_text("stop the alarm") == "Stopped."
    assert manager.player.stopped == 1
