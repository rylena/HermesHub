import argparse
import logging
import sys

from hermeshub.agent import HermesAgentClient
from hermeshub.assistant import HermesHubAssistant
from hermeshub.camera import Camera
from hermeshub.config import load_config
from hermeshub.doctor import print_doctor, run_doctor
from hermeshub.tts import PiperSpeaker


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
        print(HermesAgentClient(config.assistant).ask(args.text))
        return 0
    if args.command == "capture":
        path = Camera(config.camera).capture()
        if path:
            print(path)
            return 0
        print("camera capture failed", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
