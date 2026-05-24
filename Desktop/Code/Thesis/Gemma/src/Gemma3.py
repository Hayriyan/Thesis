import torch
from transformers import AutoTokenizer, pipeline

class Gemma3:
    def __init__(self, model_path="./Includes/gemma-3-1b-it", device="mps"):
        """
        model_path: path to your Gemma model
        device: 'cpu', 'cuda:0', 'mps', etc.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.gen_pipe = pipeline(
            "text-generation",
            model=model_path,
            tokenizer=self.tokenizer,
            device=device,    # Adjust for your environment
            torch_dtype="auto"
        )

    def generate(self, messages, max_new_tokens=50):
        """
        Takes a list of chat-style messages and returns a text response.
        Each element of `messages` might look like:
            [
              {"role": "system", "content": [{"type": "text", "text": "System prompt"}]},
              {"role": "user",   "content": [{"type": "text", "text": "User prompt"}]}
            ]

        Customize how you build the prompt string if needed.
        """
        # Convert messages to the raw text prompt that Gemma3 expects
        prompt_text = ""
        for conversation in messages:
            for message in conversation:
                if "content" in message and message["content"]:
                    for part in message["content"]:
                        prompt_text += part["text"] + "\n"

        result = self.gen_pipe(
            prompt_text,
            max_new_tokens=max_new_tokens
        )
        # The pipeline typically returns a list of dicts with a "generated_text" key
        generated_text = result[0]["generated_text"]
        return generated_text




