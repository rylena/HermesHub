import time
import wave
from pathlib import Path

import numpy as np

SHERPA_TEST_MODEL_DIR = "models/sherpa-onnx-streaming-zipformer-en-20M-2023-02-17"
SHERPA_SAMPLE_RATE = 16000


def run_sherpa_test(config, args):
    recognizer = build_sherpa_recognizer(
        model_dir=args.model_dir,
        threads=args.threads,
        int8=not args.fp32,
    )
    if args.wav:
        text = transcribe_wav(recognizer, args.wav)
    else:
        text = transcribe_microphone(recognizer, config.audio, args.seconds)

    print(f"Sherpa: {text}" if text else "Sherpa: no speech recognized.", flush=True)
    return 0 if text else 1


def build_sherpa_recognizer(model_dir=SHERPA_TEST_MODEL_DIR, threads=2, int8=True):
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise RuntimeError("Sherpa test needs sherpa-onnx. Run: .venv/bin/pip install sherpa-onnx") from exc

    paths = sherpa_model_paths(model_dir, int8=int8)
    return sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(paths["tokens"]),
        encoder=str(paths["encoder"]),
        decoder=str(paths["decoder"]),
        joiner=str(paths["joiner"]),
        num_threads=threads,
        provider="cpu",
        model_type="zipformer",
        enable_endpoint_detection=True,
        decoding_method="greedy_search",
    )


def sherpa_model_paths(model_dir, int8=True):
    root = Path(model_dir)
    suffix = ".int8.onnx" if int8 else ".onnx"
    paths = {
        "tokens": root / "tokens.txt",
        "encoder": root / f"encoder-epoch-99-avg-1{suffix}",
        "decoder": root / ("decoder-epoch-99-avg-1.onnx"),
        "joiner": root / f"joiner-epoch-99-avg-1{suffix}",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing Sherpa model files. Run scripts/download-sherpa-test-model.sh. "
            f"Missing: {', '.join(missing)}"
        )
    return paths


def transcribe_wav(recognizer, wav_path):
    with wave.open(str(wav_path), "rb") as handle:
        sample_rate = handle.getframerate()
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        samples = handle.readframes(handle.getnframes())

    if sample_width != 2:
        raise ValueError("Sherpa test WAV input must be 16-bit PCM")

    audio = np.frombuffer(samples, dtype="<i2")
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
    return transcribe_samples(recognizer, audio, source_sample_rate=sample_rate)


def transcribe_microphone(recognizer, audio_config, seconds):
    import sounddevice as sd

    device = _resolve_input_device(sd, audio_config)
    blocksize = int(audio_config.sample_rate * (audio_config.block_ms / 1000))
    stream = recognizer.create_stream()
    deadline = time.monotonic() + seconds
    last_partial = ""

    print(f"Listening with Sherpa for {seconds:.1f}s...", flush=True)
    with sd.RawInputStream(
        samplerate=audio_config.sample_rate,
        blocksize=blocksize,
        device=device,
        channels=audio_config.channels,
        dtype="int16",
    ) as audio_stream:
        while time.monotonic() < deadline:
            frame, overflowed = audio_stream.read(blocksize)
            if overflowed:
                continue

            samples = pcm16_to_float32(bytes(frame), audio_config.sample_rate)
            stream.accept_waveform(SHERPA_SAMPLE_RATE, samples)
            while recognizer.is_ready(stream):
                recognizer.decode_stream(stream)

            partial = recognizer.get_result(stream)
            if partial and partial != last_partial:
                print(f"\rSherpa partial: {partial}", end="", flush=True)
                last_partial = partial

    stream.input_finished()
    while recognizer.is_ready(stream):
        recognizer.decode_stream(stream)
    if last_partial:
        print(flush=True)
    return recognizer.get_result(stream).strip()


def transcribe_samples(recognizer, samples, source_sample_rate):
    stream = recognizer.create_stream()
    stream.accept_waveform(
        SHERPA_SAMPLE_RATE,
        int16_samples_to_float32(samples, source_sample_rate, SHERPA_SAMPLE_RATE),
    )
    stream.input_finished()
    while recognizer.is_ready(stream):
        recognizer.decode_stream(stream)
    return recognizer.get_result(stream).strip()


def pcm16_to_float32(frame, source_sample_rate):
    samples = np.frombuffer(frame, dtype="<i2")
    return int16_samples_to_float32(samples, source_sample_rate, SHERPA_SAMPLE_RATE)


def int16_samples_to_float32(samples, source_sample_rate, target_sample_rate):
    if len(samples) == 0:
        return np.array([], dtype=np.float32)

    mono = samples.astype(np.float32)
    if source_sample_rate != target_sample_rate:
        duration = len(mono) / float(source_sample_rate)
        target_length = max(1, int(duration * target_sample_rate))
        source_positions = np.linspace(0, len(mono) - 1, num=len(mono), dtype=np.float32)
        target_positions = np.linspace(0, len(mono) - 1, num=target_length, dtype=np.float32)
        mono = np.interp(target_positions, source_positions, mono)

    return (mono / 32768.0).astype(np.float32)


def _resolve_input_device(sounddevice, audio_config):
    from hermeshub.audio import resolve_input_device

    return resolve_input_device(sounddevice, audio_config)
