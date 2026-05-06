# Hermes Hub

![Hermes Hub logo](assets/hermes-hub-logo.svg)

Hermes Hub is a voice-controlled smart speaker for a Hermes agent. It gives your
own AI agent the kind of interface people expect from Alexa or Google Home:
wake word detection, speech recognition, spoken replies, follow-up
conversation, and device-style controls.

What makes it different is that the "assistant" is not a closed cloud product.
Hermes Hub is just the room interface. The actual intelligence comes from the
Hermes agent you already run, so the same agent that can use your tools,
servers, scripts, email, smart home, or automation stack can now be talked to out
loud.

## Why I Made It

I use AI agents constantly, but they still mostly live inside a terminal or chat
window. I wanted Hermes to be available like a normal home assistant: sitting in
the room, listening for a wake word, and able to help without opening a laptop.

The problem I am solving is the gap between a powerful personal agent and a
physical device that feels natural to use. Google Home and Alexa are convenient,
but they are not my agent, they do not run my tools, and they are not built
around my workflow. Hermes Hub is my attempt to make that missing hardware layer.

## Features

- **Wake word activation**: listens for `hermes` using OpenWakeWord or a Vosk
  phrase fallback.
- **Speech to text**: records a command after wake detection and transcribes it
  with Faster Whisper by default.
- **Agent bridge**: sends the spoken command to a local or remote Hermes agent
  over HTTP, or through a configurable shell command.
- **Text to speech**: speaks Hermes replies through Piper TTS.
- **Conversational mode**: keeps listening for follow-up commands after a reply,
  without requiring the wake word every time.
- **Stop interruption**: lets you say `stop` while Hermes is speaking to cut off
  playback and continue the conversation.
- **Audio feedback**: plays wake and acknowledgement chimes so the device feels
  responsive.
- **Device checks**: includes doctor, wake-test, listen-test, chime, say, and ask
  commands for debugging microphones, speakers, models, and agent connectivity.
- **Raspberry Pi target**: designed to run on a Raspberry Pi 5 with local STT and
  TTS models.

## Demo

[![Hermes Hub demo](https://img.youtube.com/vi/ChLMnPi2ED0/hqdefault.jpg)](https://www.youtube.com/watch?v=ChLMnPi2ED0)

## Visuals

### Software Demo

The video above shows Hermes Hub running as a voice assistant: wake word,
spoken command, Hermes agent response, and TTS playback.

### Hardware Wiring

Hermes Hub currently uses off-the-shelf parts, so there is no PCB yet. The
current prototype wiring is:

![Hermes Hub wiring diagram](assets/wiring-diagram.svg)

### Hardware Assembly

The final Raspberry Pi enclosure is still being designed. This is the current
assembly concept:

![Hermes Hub assembly concept](assets/hardware-assembly-concept.svg)

A full assembled CAD/3D model render will replace this concept image once the
case dimensions are finalized around the Pi, microphone, speaker, and power
routing.

## How It Works

Hermes Hub runs a continuous voice loop:

1. The microphone stream is monitored for the wake word.
2. When `hermes` is detected, Hermes Hub plays a wake chime.
3. It records the user's command until speech ends or a timeout is reached.
4. The command is transcribed with the configured STT engine.
5. The transcript is sent to the Hermes agent.
6. Hermes Hub extracts the reply from the agent response.
7. Piper generates spoken audio and plays it through the configured speaker.
8. Conversational mode keeps the microphone open for follow-up commands.

```text
Microphone
   -> Wake detector
   -> Speech recorder
   -> STT transcription
   -> Hermes agent
   -> Reply parser
   -> Piper TTS
   -> Speaker
```

## Project Layout

```text
src/hermeshub/
  assistant.py      Main wake/listen/ask/speak loop
  cli.py            Command-line interface
  config.py         YAML config loading
  agent.py          Hermes agent HTTP/command client
  stt.py            Speech-to-text engines
  tts.py            Piper speech output
  wake.py           Wake word detection
  audio.py          Microphone stream handling
  sound.py          Wake and acknowledgement chimes
  doctor.py         Runtime/device diagnostics

config.example.yaml Example runtime configuration
scripts/            Installers and model download helpers
systemd/            User service file
tests/              Unit tests
```

## Requirements

- Python 3.10, 3.11, or 3.12
- Linux audio stack supported by `sounddevice`
- Microphone
- Speaker
- A running Hermes agent, either as an HTTP server or shell command

Recommended hardware target:

- Raspberry Pi 5, 4 GB
- USB or HAT microphone
- Small powered speaker

## Install

Install system dependencies on Ubuntu or Debian:

```bash
scripts/install-system-deps-ubuntu.sh
```

Create the virtual environment, install the package, and generate `config.yaml`:

```bash
scripts/install.sh
```

Download the default speech and voice models:

```bash
scripts/download-models.sh
```

Verify the install:

```bash
.venv/bin/hermeshub --config config.yaml doctor
```

## Configuration

Hermes Hub is configured with `config.yaml`. Start from
`config.example.yaml`, then point the assistant section at your Hermes agent.

HTTP agent:

```yaml
assistant:
  agent_url: "http://127.0.0.1:8000"
  command: null
```

Shell command agent:

```yaml
assistant:
  command: "ssh rylen@192.168.70.60 'hermes -z {prompt}'"
```

Default speech settings:

```yaml
stt:
  engine: "faster_whisper"
  faster_whisper_model: "base.en"
  faster_whisper_device: "cpu"
  faster_whisper_compute_type: "int8"

tts:
  piper_model_path: "voices/en_US-lessac-medium.onnx"
  piper_config_path: "voices/en_US-lessac-medium.onnx.json"
```

For lower latency on Raspberry Pi, switch the Whisper model to `tiny.en`:

```yaml
stt:
  faster_whisper_model: "tiny.en"
```

## Usage

Start the assistant:

```bash
.venv/bin/hermeshub --config config.yaml run
```

Then speak to it:

```text
hermes
set an alarm for 3 PM
```

Hermes Hub will play a wake chime, capture the command, send it to Hermes, and
speak the reply. After Hermes replies, conversational mode stays active for a
short follow-up window, so you can keep talking without saying the wake word
again.

Ask once from the terminal:

```bash
.venv/bin/hermeshub --config config.yaml ask "what time is it?"
```

Speak text through Piper:

```bash
.venv/bin/hermeshub --config config.yaml say "hello from Hermes"
```

Test wake detection:

```bash
.venv/bin/hermeshub --config config.yaml wake-test --seconds 12
```

Test microphone transcription:

```bash
.venv/bin/hermeshub --config config.yaml listen-test
```

Play the wake chime:

```bash
.venv/bin/hermeshub --config config.yaml chime
```

## Voice Commands

Examples of the intended interaction style:

```text
hey hermes set an alarm for 3 PM
hey hermes turn the volume down
hey hermes stop the music
hey hermes email my dad
hey hermes restart the Minecraft server
```

Hermes Hub handles the voice loop. The Hermes agent decides what those commands
mean and which tools or integrations to call.

## Detailed Setup Flow

1. Install system dependencies with `scripts/install-system-deps-ubuntu.sh`.
2. Run `scripts/install.sh` to create `.venv`, install Hermes Hub, and create
   `config.yaml`.
3. Run `scripts/download-models.sh` to download the default Vosk, Faster
   Whisper, OpenWakeWord, and Piper assets.
4. Edit `config.yaml` and set `assistant.agent_url` or `assistant.command`.
5. Run `.venv/bin/hermeshub --config config.yaml doctor` and confirm the
   microphone, speaker, model paths, and config are valid.
6. Run `.venv/bin/hermeshub --config config.yaml wake-test --seconds 12` and say
   `hermes` to verify wake detection.
7. Run `.venv/bin/hermeshub --config config.yaml listen-test` and speak a test
   command to verify STT.
8. Run `.venv/bin/hermeshub --config config.yaml ask "hello"` to verify Hermes
   agent connectivity.
9. Start the full assistant loop with `.venv/bin/hermeshub --config config.yaml
   run`.

If wake detection does not work, run `doctor` first. Most setup problems are
wrong microphone selection, wrong sample rate, missing model files, or the
Hermes agent URL pointing at the wrong machine.

## Agent API

When using `assistant.agent_url`, Hermes Hub sends a `POST` request to:

```text
{assistant.agent_url}/chat
```

Example payload:

```json
{
  "message": "System instructions:\nYou are Hermes, a voice assistant...\n\nUser said:\nturn the volume down\n\nAnswer:",
  "text": "turn the volume down",
  "source": "hermeshub",
  "system": "You are Hermes, a voice assistant...",
  "system_prompt": "You are Hermes, a voice assistant...",
  "instructions": "You are Hermes, a voice assistant...",
  "wake": {
    "name": "hermes",
    "score": 0.91
  }
}
```

Accepted response shapes:

```json
{"reply": "Done."}
{"response": "Done."}
{"text": "Done."}
{"message": "Done."}
{"content": "Done."}
```

OpenAI-style responses using `choices[0].message.content` are also supported.

## Wake Word

The default wake phrase is:

```text
hermes
```

Hermes Hub can use OpenWakeWord when a model is configured. Because the public
OpenWakeWord package does not include a built-in Hermes model, the default setup
also supports a Vosk phrase fallback with aliases such as `her mes`, `her miss`,
and `harness`.

Custom OpenWakeWord model example:

```yaml
wake:
  engine: "openwakeword"
  model_paths:
    - "models/hermes.onnx"
```

## Service Install

Install Hermes Hub as a user service:

```bash
scripts/install-systemd-user.sh
systemctl --user start hermeshub
systemctl --user status hermeshub
```

View logs:

```bash
journalctl --user -u hermeshub -f
```

## Current Status

Implemented:

- Core assistant loop
- Wake detection
- STT
- TTS
- Agent HTTP/command bridge
- Follow-up conversation mode
- Stop-word interruption
- Debug and test commands

In progress:

- Alarm and timer polish
- Spotify authentication and playback controls
- Smart home integration
- Raspberry Pi enclosure and hardware fit

## Roadmap

- Finish alarm and timer commands
- Add Spotify login, playback, and volume control
- Add Home Assistant integration
- Add reliable service startup on Raspberry Pi boot
- Tune STT latency on Pi hardware
- Design and build the physical case
- Revisit optional display support after the voice loop is stable
