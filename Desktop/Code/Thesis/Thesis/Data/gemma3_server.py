# gemma3_server.py
import time
from transformers import AutoTokenizer, pipeline

def gemma3_process_func(child_conn, model_path="./Includes/gemma-3-1b-it", device="cpu"):
    """
    This function runs in its own process:
      - Loads the Gemma3 model once.
      - Waits for a message (a dict with key "prompt") on the Pipe.
      - When a prompt is received, generates a text response (which should be a valid shell command).
      - If the message "TERMINATE" is received, it shuts down.
    """
    print("[Gemma3 Process] Loading Gemma3 model...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    gen_pipe = pipeline(
        "text-generation",
        model=model_path,
        tokenizer=tokenizer,
        device=device,       # e.g. "cpu" or "cuda:0"
        torch_dtype="auto"
    )
    print("[Gemma3 Process] Model loaded and waiting for prompts.")

    while True:
        if child_conn.poll():
            msg = child_conn.recv()
            if msg == "TERMINATE":
                print("[Gemma3 Process] Terminate signal received. Shutting down.")
                break

            if not isinstance(msg, dict) or "prompt" not in msg:
                child_conn.send({"error": "Invalid message format"})
                continue

            prompt_text = msg["prompt"]
            if not prompt_text.strip():
                child_conn.send({"error": "Empty prompt"})
                continue

            try:
                # Generate text using your Gemma3 model.
                result = gen_pipe(prompt_text, max_new_tokens=50)
                generated_text = result[0]["generated_text"]
                child_conn.send({"generated_text": generated_text})
            except Exception as e:
                child_conn.send({"error": str(e)})
        else:
            time.sleep(0.02)  # Sleep a bit to avoid busy-waiting
