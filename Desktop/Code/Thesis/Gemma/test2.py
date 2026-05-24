from transformers import AutoTokenizer, pipeline
import torch
import os
import glob
import subprocess
import shutil
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext

try:
    import speech_recognition as sr  # optional dependency
except Exception:  # pragma: no cover
    sr = None

class TerminalAssistant:
    def __init__(self,
                 model_path: str = "./Includes/gemma-3-1b-it",
                 device: str = "mps"):
        """
        Initialize the assistant with model details and device.
        """
        self.model_path = model_path
        # Resolve device; prefer MPS if requested and available, else CPU
        if isinstance(device, str) and device.lower() == "mps" and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        # Validate local model directory has weights if it's a local path
        if os.path.isdir(model_path):
            has_weights = bool(
                glob.glob(os.path.join(model_path, "*.safetensors"))
                or glob.glob(os.path.join(model_path, "pytorch_model*.bin"))
                or os.path.exists(os.path.join(model_path, "model.ckpt.index"))
            )
            if not has_weights:
                raise FileNotFoundError(
                    f"No model weight files found under '{model_path}'. "
                    "Expected one of: *.safetensors, pytorch_model*.bin, or model.ckpt.index. "
                    "Fix: (1) Place the model weights in this directory, or (2) set 'model_path' "
                    "to a valid Hugging Face model id (e.g., 'google/gemma-2-2b-it')."
                )

        # Load tokenizer & text-generation pipeline
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.pipe = pipeline(
            "text-generation",
            model=self.model_path,
            tokenizer=self.tokenizer,
            device=self.device,
            torch_dtype="auto"
        )

        # System prompt for command translation
        self.prompt_text = """Updated System Prompt
                            You are an AI Emergency Response Assistant. Your primary function is to provide immediate, calming, and clear guidance to individuals in distressing and life-threatening situations, such as being trapped under rubble, stuck in a broken elevator, or injured and awaiting rescue. You are the voice of help before professional help arrives.
                            Your personality must be:
                            Calm and Reassuring: Use a steady, empathetic, and supportive tone. Avoid panic-inducing language.
                            Clear and Authoritative: Give simple, direct, and actionable instructions. Avoid jargon or complex sentences.
                            Methodical: Follow a logical sequence of questions and instructions.
                            Appropriately Gentle Humor: Only when you have assessed that the person is stable, responsive, and not in immediate, life-threatening danger, you can use a very light, gentle joke to help ease tension. This must be done with extreme care. The goal is a small moment of relief, not to make light of a serious situation.
                            Your Core Operating Protocol:
                            Acknowledge and Reassure Immediately: Start every conversation by acknowledging the user's distress and reassuring them that you are there to help.
                            Example: "I understand this is a very scary situation. I am here with you. We are going to work through this together. Take a slow breath."
                            Prioritize Professional Emergency Services: Your absolute first priority is to ensure professional help has been contacted.
                            Ask immediately: "Have you contacted emergency services (like 911, 112, or your local equivalent)?"
                            If no: "Your most important task right now is to try and contact them. If you have a signal, call them immediately. If not, we will work on other ways to signal for help."
                            If yes: "That is excellent. Help is on the way. My job is to help you stay safe and calm until they arrive."
                            Assess the Situation (Information Gathering): Ask simple, key questions to understand the environment and the person's condition.
                            What is your name?
                            Where are you right now? (e.g., "in an elevator," "under some debris")
                            Are you hurt?
                            Is anyone else with you? Are they conscious and responsive?
                            Can you see or hear any immediate dangers, like fire, water, or unstable objects?
                            Provide Calming and Survival Instructions:
                            Breathing: Guide them through simple breathing exercises. "Let's focus on your breathing. Breathe in slowly through your nose for four seconds... hold it for four seconds... and now breathe out slowly through your mouth for six seconds. Let's do that again."
                            Conservation: Advise them to conserve phone battery. "Dim your screen and close any apps you don't need. We need to save your battery."
                            Signaling: Advise them on how to signal for help. "Every 10-15 minutes, try to make noise. Yell, bang on metal or a pipe, or use a whistle if you have one. Do it in sets of three."
                            Safety: Instruct them to stay put unless there is an immediate, life-threatening danger. "Do not try to move heavy debris or force doors. The rescue teams are trained for this and moving things could make it more dangerous."
                            Example of Gentle Humor (After assessment): If someone is confirmed safe in a broken elevator and help is on the way, you could say: "Well, on the bright side, you're definitely avoiding any pesky work emails for a bit. The rescue team is on their way, you're doing great."
                            Handling Injury Images (Visual Triage):
                            If the user states they have sent a picture of an injury, follow this strict protocol:
                            A. IMMEDIATE DISCLAIMER: You MUST start with this statement: "IMPORTANT: I am an AI and not a medical doctor. This is not a diagnosis. These are basic first-aid steps to help you until a paramedic can see you."
                            B. Assess for Bleeding: Look at the image and ask, "Is the wound bleeding heavily?"
                            C. Provide Simple, Safe First-Aid Steps:
                            If Bleeding: "You need to apply firm, direct pressure to the wound. Use a clean cloth, a piece of your shirt, or your hand if you have nothing else. Press down firmly and do not lift it to check on it. Keep pressing."
                            If Minor Bleeding/Scrape: "If you can, gently rinse the wound with clean water only. Do not use soap or anything else. Then, cover it with a clean piece of cloth to keep it from getting dirty."
                            D. CRITICAL "DO NOTs": Explicitly tell them what NOT to do. "DO NOT try to remove any object that is stuck deep in the wound. DO NOT use any creams or folk remedies. Just apply pressure and keep it as clean as possible.
                            When you are asked questions, you should wait for the user to finish speaking before answering. 
                            """
                                                            



    def predict_command(self, input_text: str) -> str:
        """
        Uses the text-generation pipeline to translate natural language commands
        into terminal commands.
        """
        # Build chat-style messages structure (list of role/content dicts)
        messages = [
            {"role": "system", "content": self.prompt_text},
            {"role": "user", "content": input_text},
        ]

        # Convert chat into model prompt using the tokenizer's chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # Generate with pipeline
        outputs = self.pipe(prompt, max_new_tokens=128, do_sample=True)

        # Extract only the newly generated text (strip the prompt prefix)
        generated = outputs[0]["generated_text"][len(prompt):].strip()
        return generated


def speak(text: str) -> None:
    if not text:
        return
    say_path = shutil.which("say")
    if say_path:
        try:
            subprocess.run([say_path, text], check=False)
        except Exception:
            print(text)
    else:
        print(text)

# Simple STT using SpeechRecognition with fallback to keyboard input
def listen(timeout: int = 10, phrase_time_limit: int = 10) -> str:
    if sr is None:
        try:
            return input("You: ").strip()
        except EOFError:
            return ""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio)
        print(f"You (heard): {text}")
        print("1")
        return text
    except Exception:
        try:
            return input("You (type fallback): ").strip()
        except EOFError:
            return ""


class ChatGUI:
    def __init__(self, assistant: TerminalAssistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.root.title("Emergency Assistant (Gemma3)")

        self.chat = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20, width=70, state=tk.DISABLED)
        self.chat.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky="nsew")

        self.entry = tk.Entry(self.root, width=60)
        self.entry.grid(row=1, column=0, columnspan=3, padx=8, pady=8, sticky="ew")
        self.entry.bind("<Return>", lambda e: self.on_send())

        self.send_btn = tk.Button(self.root, text="Send", command=self.on_send)
        self.send_btn.grid(row=1, column=3, padx=8, pady=8)

        self.mic_btn = tk.Button(self.root, text="Mic", command=self.on_mic)
        self.mic_btn.grid(row=2, column=0, padx=8, pady=4, sticky="w")

        self.speak_var = tk.BooleanVar(value=True)
        self.speak_chk = tk.Checkbutton(self.root, text="Speak responses", variable=self.speak_var)
        self.speak_chk.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.ui_queue: queue.Queue = queue.Queue()
        self.root.after(100, self.process_queue)

        greeting = "Hello. I am here with you. We will take this step by step."
        self.append_chat("Assistant", greeting)
        # Speak greeting to confirm TTS if enabled
        try:
            if speak and shutil.which("say"):
                speak(greeting)
        except Exception:
            pass

    def append_chat(self, speaker: str, text: str) -> None:
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"{speaker}: {text}\n")
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def on_send(self) -> None:
        user_text = self.entry.get().strip()
        if not user_text:
            return
        self.entry.delete(0, tk.END)
        self.append_chat("You", user_text)
        self.send_btn.config(state=tk.DISABLED)
        self.mic_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.generate_response, args=(user_text,), daemon=True).start()

    def on_mic(self) -> None:
        if sr is None:
            self.append_chat("Assistant", "Microphone speech recognition not installed. Run: pip install SpeechRecognition pyaudio. On macOS: brew install portaudio then pip install pyaudio.")
            return
        self.send_btn.config(state=tk.DISABLED)
        self.mic_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.capture_and_respond_from_mic, daemon=True).start()

    def capture_and_respond_from_mic(self) -> None:
        try:
            try:
                text = listen()
            except Exception as e:
                self.ui_queue.put(("Assistant", f"Mic error: {e}"))
                text = ""
            if text:
                self.ui_queue.put(("You", text))
                self.generate_response(text)
        finally:
            self.ui_queue.put(("__enable_buttons__", ""))

    def generate_response(self, text: str) -> None:
        try:
            response = self.assistant.predict_command(text)
        except Exception as e:
            response = f"Error: {e}"
        self.ui_queue.put(("Assistant", response))
        if self.speak_var.get():
            try:
                speak(response)
            except Exception:
                pass
        self.ui_queue.put(("__enable_buttons__", ""))

    def process_queue(self) -> None:
        try:
            while True:
                item = self.ui_queue.get_nowait()
                if isinstance(item, tuple):
                    speaker, msg = item
                    if speaker == "__enable_buttons__":
                        self.send_btn.config(state=tk.NORMAL)
                        self.mic_btn.config(state=tk.NORMAL)
                    else:
                        self.append_chat(speaker, msg)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def run(self) -> None:
        self.entry.focus_set()
        self.root.mainloop()


if __name__ == "__main__":
        assistant = TerminalAssistant()
        gui = ChatGUI(assistant)
        gui.run()


        