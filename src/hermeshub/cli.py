import argparse
import logging
import sys

from hermeshub.agent import HermesAgentClient
from hermeshub.assistant import HermesHubAssistant
from hermeshub.camera import Camera
from hermeshub.config import load_config
from hermeshub.doctor import print_doctor, run_doctor
from hermeshub.listen_test import run_listen_test
from hermeshub.sound import WakeChime
from hermeshub.tts import PiperSpeaker
from hermeshub.wake_test import run_wake_test


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hermeshub")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--log-level", default="INFO")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor")
    sub.add_parser("run")

    say_parser = sub.add_parser("say")
    say_parser.add_argument("text")

    ask_parser = sub.add_parser("ask")
    ask_parser.add_argument("text")

    sub.add_parser("capture")
    sub.add_parser("chime")
    wake_test_parser = sub.add_parser("wake-test")
    wake_test_parser.add_argument("--seconds", type=float, default=12)
    sub.add_parser("listen-test")

    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    config = load_config(args.config)

    if args.command == "doctor":
        return print_doctor(run_doctor(config))
    if args.command == "run":
        HermesHubAssistant(config).run_forever()
        return 0
    if args.command == "say":
        PiperSpeaker(config.tts).speak(args.text)
        return 0
    if args.command == "ask":
        print(f"You: {args.text}", flush=True)
        reply = HermesAgentClient(config.assistant).ask(args.text)
        print(f"Hermes: {reply}", flush=True)
        return 0
    if args.command == "capture":
        if not config.camera.enabled:
            print("camera disabled", file=sys.stderr)
            return 1
        path = Camera(config.camera).capture()
        if path:
            print(path)
            return 0
        print("camera capture failed", file=sys.stderr)
        return 1
    if args.command == "chime":
        path = WakeChime(config.sound).play()
        if path:
            print(path)
            return 0
        print("wake chime disabled")
        return 0
    if args.command == "wake-test":
        return run_wake_test(config, args.seconds)
    if args.command == "listen-test":
        return run_listen_test(config)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
