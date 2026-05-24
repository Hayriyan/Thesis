import glob
import os

import torch
from transformers import AutoTokenizer, pipeline


class TerminalAssistant:
    def __init__(self, model_path: str = "./Data/text2linuxcommand-model", device: str = "mps"):
        self.model_path = model_path
        self.device = self._resolve_device(device)
        self._validate_model_path()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.pipe = pipeline(
            "text-generation",
            model=self.model_path,
            tokenizer=self.tokenizer,
            device=self.device,
            torch_dtype="auto",
        )

        self.prompt_text = """
You translate natural-language requests into Unix-like terminal commands.
Return only the command itself. Do not add explanations, Markdown, quotes, or extra text.

Examples:
User: list files in the current directory
ls
User: create a folder named projects
mkdir projects
User: open the Desktop folder
open ~/Desktop
User: show the current working directory
pwd
User: find files named report.txt
find . -name report.txt
"""

    def _resolve_device(self, device):
        if isinstance(device, str) and device.lower() == "mps":
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                return torch.device("mps")
            print("MPS is not available. Falling back to CPU.")
            return torch.device("cpu")

        if isinstance(device, str) and device.isdigit():
            return int(device)

        return device

    def _validate_model_path(self):
        if not os.path.isdir(self.model_path):
            return

        patterns = [
            "*.safetensors",
            "pytorch_model*.bin",
            "tf_model.h5",
            "model.ckpt.index",
        ]
        has_weights = any(glob.glob(os.path.join(self.model_path, pattern)) for pattern in patterns)
        if not has_weights:
            checkpoint_weights = glob.glob(os.path.join(self.model_path, "checkpoint-*", "*.safetensors"))
            checkpoint_weights += glob.glob(os.path.join(self.model_path, "checkpoint-*", "pytorch_model*.bin"))
            if checkpoint_weights:
                return

            raise FileNotFoundError(
                f"No model weights were found in '{self.model_path}'. "
                "Place the trained model weights there or set COMMAND_MODEL_PATH to a valid model directory/id."
            )

    def predict_command(self, input_text: str) -> str:
        messages = [
            {"role": "system", "content": self.prompt_text},
            {"role": "user", "content": input_text},
        ]

        if hasattr(self.tokenizer, "apply_chat_template") and self.tokenizer.chat_template:
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt = f"{self.prompt_text}\nUser: {input_text}\n"

        outputs = self.pipe(prompt, max_new_tokens=50, do_sample=False)
        generated = outputs[0]["generated_text"][len(prompt):].strip()
        return generated.splitlines()[0].strip()


if __name__ == "__main__":
    assistant = TerminalAssistant()
    command = assistant.predict_command("open the Desktop")
    print("Predicted command:", command)
