import argparse
import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_VOSK_MODEL_PATH = os.path.join(PROJECT_ROOT, "Includes", "model")
DEFAULT_COMMAND_MODEL_PATH = os.path.join(PROJECT_ROOT, "Data", "text2linuxcommand-model")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Speech-driven AI assistant for translating natural language into terminal commands."
    )
    parser.add_argument(
        "--model-path",
        default=os.environ.get("COMMAND_MODEL_PATH", DEFAULT_COMMAND_MODEL_PATH),
        help="Path or Hugging Face id for the text-to-command model.",
    )
    parser.add_argument(
        "--vosk-model-path",
        default=os.environ.get("VOSK_MODEL_PATH", DEFAULT_VOSK_MODEL_PATH),
        help="Path to the offline Vosk speech-recognition model.",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("MODEL_DEVICE", "mps"),
        help="Model device, for example mps, cpu, cuda:0, or 0.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Seconds to listen for each spoken command.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Ask for confirmation and then execute generated terminal commands.",
    )
    return parser


def ask_yes_no(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def main() -> int:
    args = build_parser().parse_args()

    from Predict_command import TerminalAssistant
    from Run_command import run_command
    from speech_module import SpeechAssistant

    speech = SpeechAssistant(
        api_key=os.environ.get("ELEVENLABS_API_KEY"),
        model_path=args.vosk_model_path,
    )
    terminal = TerminalAssistant(model_path=args.model_path, device=args.device)

    print("=== Bachelor Thesis Assistant ===")
    print("Created in May 2025. Press Ctrl+C to stop.")
    print("Say a request, or type it when speech recognition is unavailable.")

    try:
        while True:
            if ask_yes_no("Use microphone for the next command?"):
                text = speech.speech_to_text(duration=args.duration)
            else:
                text = input("Type your command request: ").strip()

            if not text:
                print("No input detected. Try again.")
                continue

            print(f"You said: {text}")
            command = terminal.predict_command(text)
            print(f"Generated command: {command}")

            if args.execute and ask_yes_no("Execute this command now?"):
                output = run_command(command)
                if output.strip():
                    print(output)
                if len(output) < 200:
                    speech.text_to_speech(output or "Command finished.")

    except KeyboardInterrupt:
        print("\nGoodbye.")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
