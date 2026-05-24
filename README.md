# Bachelor Thesis AI Assistant

Created in May 2025 as a bachelor thesis project.

This project combines speech recognition, a local Gemma 3 text-to-command language model, hand-gesture control, and a browser-based particle GUI. The main assistant listens to a user request, translates the request into a Unix-like terminal command, and can optionally execute the command after confirmation.

The assistant is designed to work locally on the user's computer. After the required models are downloaded, the main command-generation workflow does not need a cloud model API.

## Main Features

- Speech input with offline Vosk support.
- Optional ElevenLabs text-to-speech when `ELEVENLABS_API_KEY` is configured.
- Local natural-language-to-terminal-command generation with Gemma 3 and Hugging Face Transformers.
- Optional command execution with explicit user confirmation.
- Hand landmark mouse control using OpenCV, MediaPipe, and PyAutoGUI.
- Three.js particle visualizer GUI launched through PySide6.

## Project Structure

```text
.
├── run.py                         # Python entry point
├── src/
│   ├── main.py                    # Main assistant loop
│   ├── speech_module.py           # Speech recognition and TTS helper
│   ├── Predict_command.py         # Text-to-command model wrapper
│   ├── Run_command.py             # Command execution helpers
│   ├── hand_landmark.py           # Gesture-based cursor control
│   └── gui.py                     # PySide6 wrapper for the GUI
├── GUI/                           # Three.js/Webpack visual interface
├── Data/text2linuxcommand-model/  # Model tokenizer/config/checkpoint metadata
└── Includes/                      # Optional local models, such as Vosk
```

## Setup

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install GUI dependencies only if you want to run the Three.js interface:

```bash
cd GUI
npm install
cd ..
```

Create a local environment file if you use online speech services:

```bash
cp .env.example .env
```

Then add your real `ELEVENLABS_API_KEY` inside `.env` or export it in your shell. Do not commit real API keys.

## Model Files

This project uses the Gemma 3 model locally. You can download Gemma 3 into the `Includes/` folder with the Hugging Face CLI:

```bash
pip install -U huggingface_hub
huggingface-cli login
huggingface-cli download google/gemma-3-1b-it --local-dir Includes/gemma-3-1b-it
```

Then run the project with:

```bash
export COMMAND_MODEL_PATH=Includes/gemma-3-1b-it
python run.py
```

The command model directory currently contains tokenizer/config files and checkpoint metadata, but no visible model weight files such as `*.safetensors` or `pytorch_model*.bin`. To run command generation on another machine, place the trained weights in `Data/text2linuxcommand-model/`, download Gemma 3 into `Includes/gemma-3-1b-it`, or set:

```bash
export COMMAND_MODEL_PATH=/path/to/your/model
```

For offline speech recognition, place a Vosk model in:

```text
Includes/model
```

or set:

```bash
export VOSK_MODEL_PATH=/path/to/vosk/model
```

## Running

Start the assistant:

```bash
python run.py
```

By default, the assistant prints generated terminal commands but does not execute them. To enable execution with confirmation:

```bash
python run.py --execute
```

Run the gesture controller:

```bash
python src/hand_landmark.py
```

Run the GUI wrapper:

```bash
python src/gui.py
```

Run the GUI directly in development mode:

```bash
cd GUI
npm run dev
```

## Safety Notes

Generated shell commands can delete files, change system settings, or install software. Keep `--execute` disabled during demonstrations unless you are sure about the generated command. When execution is enabled, the app asks for confirmation before running the command.

## Thesis Note

This repository was prepared and improved for a bachelor thesis project made in May 2025. It is intended as an educational prototype, not as production automation software.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
