import json
import logging
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from hermeshub.sound import write_alarm_ringtone

LOG = logging.getLogger(__name__)


_NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "ninety": 90,
}


@dataclass
class ClockItem:
    id: str
    kind: str
    due_at: str
    label: str = ""


class ClockManager:
    def __init__(self, config, now_func=None, player=None):
        self.config = config
        self.now_func = now_func or datetime.now
        self.player = player or RingtonePlayer(config)
        self._items = _load_items(config.state_path)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if not self.config.enabled:
            return
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="hermeshub-clock", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.player.stop()
        if self._thread is not None:
            self._thread.join(timeout=1)

    def handle_text(self, text):
        intent = parse_clock_intent(text, self.now_func())
        if intent is None:
            return None

        action = intent["action"]
        if action == "stop":
            self.player.stop()
            return "Stopped."
        if action == "list":
            return self.describe()
        if action == "cancel":
            return self.cancel(intent.get("kind"))
        if action == "set":
            item = self.add(intent["kind"], intent["due_at"], intent.get("label", ""))
            return _set_reply(item, self.now_func())
        return None

    def add(self, kind, due_at, label=""):
        item = ClockItem(
            id=f"{kind}-{int(time.time() * 1000)}",
            kind=kind,
            due_at=due_at.isoformat(timespec="seconds"),
            label=label,
        )
        with self._lock:
            self._items.append(item)
            self._save_locked()
        return item

    def cancel(self, kind=None):
        self.player.stop()
        with self._lock:
            before = len(self._items)
            self._items = [item for item in self._items if kind and item.kind != kind]
            removed = before - len(self._items)
            self._save_locked()
        if removed == 0:
            target = f"{kind}s" if kind else "alarms or timers"
            return f"No {target} are set."
        target = f"{kind}s" if kind else "alarms and timers"
        return f"Canceled {removed} {target}."

    def describe(self):
        now = self.now_func()
        with self._lock:
            items = sorted(self._items, key=lambda item: item.due_at)
        if not items:
            return "No alarms or timers are set."

        parts = []
        for item in items:
            due = datetime.fromisoformat(item.due_at)
            if item.kind == "timer":
                parts.append(f"timer with {_format_remaining(due - now)} left")
            else:
                parts.append(f"alarm for {_format_alarm_time(due, now)}")
        return "You have " + ", and ".join(parts) + "."

    def tick(self):
        now = self.now_func()
        due_items = []
        with self._lock:
            pending = []
            for item in self._items:
                due = datetime.fromisoformat(item.due_at)
                if due <= now:
                    due_items.append(item)
                else:
                    pending.append(item)
            if due_items:
                self._items = pending
                self._save_locked()

        for item in due_items:
            LOG.info("%s due: %s", item.kind, item.label or item.id)
            self.player.start()

    def _run(self):
        while not self._stop.wait(self.config.check_interval_seconds):
            self.tick()

    def _save_locked(self):
        path = Path(self.config.state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [item.__dict__ for item in self._items]
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class RingtonePlayer:
    def __init__(self, config):
        self.config = config
        self._process = None
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self.stop()
            path = Path(self.config.ringtone_wav)
            if not path.is_file():
                write_alarm_ringtone(path, volume=self.config.ringtone_volume)
            if not shutil.which("aplay"):
                LOG.warning("alarm due but aplay is missing")
                return None
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._play_loop,
                args=(path,),
                name="hermeshub-ringtone",
                daemon=True,
            )
            self._thread.start()
            return self._thread

    def stop(self):
        self._stop.set()
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.kill()
        self._process = None

    def _play_loop(self, path):
        deadline = time.monotonic() + self.config.max_ring_seconds
        while not self._stop.is_set() and time.monotonic() < deadline:
            self._process = subprocess.Popen(["aplay", "-q", str(path)])
            while self._process.poll() is None:
                if self._stop.wait(0.1):
                    self.stop()
                    return
            self._process = None


def parse_clock_intent(text, now=None):
    now = now or datetime.now()
    lowered = _normalize(text)

    if _mentions_clock(lowered) and re.search(r"\b(stop|dismiss|silence|shut up)\b", lowered):
        return {"action": "stop"}
    if re.search(r"\b(stop|dismiss|silence)\b", lowered) and not re.search(r"\b(set|create)\b", lowered):
        return {"action": "stop"}
    if _mentions_clock(lowered) and re.search(r"\b(cancel|delete|clear|remove)\b", lowered):
        return {"action": "cancel", "kind": _mentioned_kind(lowered)}
    if _mentions_clock(lowered) and re.search(r"\b(list|what|how long|how much|status|show)\b", lowered):
        return {"action": "list"}

    if _mentions_timer(lowered):
        duration = parse_duration(lowered)
        if duration is not None:
            return {
                "action": "set",
                "kind": "timer",
                "due_at": now + duration,
                "label": lowered,
            }

    if _mentions_alarm(lowered):
        duration = parse_duration(lowered)
        if duration is not None and " in " in f" {lowered} ":
            return {
                "action": "set",
                "kind": "alarm",
                "due_at": now + duration,
                "label": lowered,
            }
        due_at = parse_alarm_time(lowered, now)
        if due_at is not None:
            return {"action": "set", "kind": "alarm", "due_at": due_at, "label": lowered}

    return None


def parse_duration(text):
    total = timedelta()
    matched = False
    duration_text = text
    if "half an hour" in text or "half hour" in text:
        matched = True
        total += timedelta(minutes=30)
        duration_text = duration_text.replace("half an hour", "").replace("half hour", "")
    pattern = re.compile(
        r"\b(\d+(?:\.\d+)?|[a-z]+)\s*"
        r"(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b"
    )
    for raw_amount, unit in pattern.findall(duration_text):
        amount = _parse_number(raw_amount)
        if amount is None:
            continue
        matched = True
        if unit.startswith(("hour", "hr")):
            total += timedelta(hours=amount)
        elif unit.startswith(("minute", "min")):
            total += timedelta(minutes=amount)
        else:
            total += timedelta(seconds=amount)

    if matched and total.total_seconds() > 0:
        return total
    return None


def parse_alarm_time(text, now):
    match = re.search(
        r"\b(?:at|for|to|up at)?\s*(\d{1,2})(?::(\d{2}))?\s*"
        r"(a\.?m\.?|p\.?m\.?|am|pm)?\b",
        text,
    )
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    meridiem = (match.group(3) or "").replace(".", "")
    if minute > 59 or hour > 23:
        return None
    if meridiem:
        if hour < 1 or hour > 12:
            return None
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0

    due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if "tomorrow" in text:
        due += timedelta(days=1)
    elif due <= now:
        due += timedelta(days=1)
    return due


def _load_items(path):
    path = Path(path)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        LOG.warning("Could not read clock state from %s", path)
        return []
    return [ClockItem(**item) for item in data if isinstance(item, dict)]


def _set_reply(item, now):
    due = datetime.fromisoformat(item.due_at)
    if item.kind == "timer":
        return f"Timer set for {_format_remaining(due - now)}."
    return f"Alarm set for {_format_alarm_time(due, now)}."


def _format_remaining(delta):
    seconds = max(0, int(delta.total_seconds()))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds and not hours:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return " and ".join(parts) if parts else "now"


def _format_alarm_time(due, now):
    when = due.strftime("%-I:%M %p").lower()
    if due.date() == now.date():
        return when
    if due.date() == (now + timedelta(days=1)).date():
        return f"tomorrow at {when}"
    return due.strftime("%A at %-I:%M %p").lower()


def _parse_number(value):
    try:
        return float(value)
    except ValueError:
        return _NUMBER_WORDS.get(value)


def _mentions_clock(text):
    return _mentions_timer(text) or _mentions_alarm(text)


def _mentions_timer(text):
    return "timer" in text or "countdown" in text


def _mentions_alarm(text):
    return "alarm" in text or "wake me" in text or "wake up" in text


def _mentioned_kind(text):
    if _mentions_timer(text) and not _mentions_alarm(text):
        return "timer"
    if _mentions_alarm(text) and not _mentions_timer(text):
        return "alarm"
    return None


def _normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()
