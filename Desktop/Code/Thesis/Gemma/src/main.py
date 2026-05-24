# # src/main.py

# import os
# import time
# import asyncio
# import multiprocessing
# import queue

# from speech_module import SpeechAssistant
# from Predict_command import TerminalAssistant
# from gui import GUIApp


# def terminal_assistant_worker(command_queue, response_queue, model_path, device):
#     from Predict_command import TerminalAssistant
#     assistant = TerminalAssistant(model_path=model_path, device=device)

#     print("[TerminalAssistant] Worker started.")
#     while True:
#         try:
#             user_text = command_queue.get()
#             if user_text == "EXIT":
#                 print("[TerminalAssistant] Exiting.")
#                 break

#             result_command = assistant.predict_command(user_text)
#             response_queue.put(result_command)
#         except Exception as e:
#             response_queue.put(f"[TerminalAssistant Error] {e}")
#         time.sleep(0.1)


# def run_hand_landmark():
#     try:
#         print("[Hand Landmark] Starting...")
#         import hand_landmark  # noqa: F401
#     except Exception as e:
#         print(f"[Hand Landmark Error] {e}")


# def run_gui():
#     try:
#         print("[GUI] Starting...")
#         gui_app = GUIApp()
#         gui_app.run()
#     except Exception as e:
#         print(f"[GUI Error] {e}")


# class MainSystem:
#     def __init__(self):
#         multiprocessing.set_start_method("spawn", force=True)

#         self.command_queue = multiprocessing.Queue()
#         self.response_queue = multiprocessing.Queue()

#         self.model_path = os.path.abspath("./Includes/gemma-3-1b-it")
#         self.vosk_model_path = os.path.abspath("Includes/model")
#         self.device = "mps"

#         self.terminal_process = None
#         self.hand_landmark_process = None
#         self.gui_process = None

#         self.init_speech_assistant()

#     def init_speech_assistant(self):
#         api_key = os.environ.get("OPENAI_API_KEY", "")
#         self.speech_assistant = SpeechAssistant(
#             api_key=api_key,
#             model_path=self.vosk_model_path
#         )

#     def start(self):
#         print("[System] Starting AI Assistant...")

#         # 1) Terminal assistant process
#         self.terminal_process = multiprocessing.Process(
#             target=terminal_assistant_worker,
#             args=(self.command_queue, self.response_queue, self.model_path, self.device),
#             daemon=True
#         )
#         self.terminal_process.start()

#         # 2) Hand‑landmark process
#         self.hand_landmark_process = multiprocessing.Process(
#             target=run_hand_landmark,
#             daemon=True
#         )
#         self.hand_landmark_process.start()

#         # 3) GUI process
#         self.gui_process = multiprocessing.Process(
#             target=run_gui,
#             daemon=True
#         )
#         self.gui_process.start()

#         # 4) Enter speech recognition loop (blocking)
#         try:
#             self.run_speech_recognition()
#         finally:
#             # If this loop ever exits, ensure we stop subprocesses
#             self.stop()

#     def run_speech_recognition(self):
#         print("[Speech] Recognition started...")
#         while True:
#             try:
#                 print("[Speech] Listening...")
#                 text = self.speech_assistant.speech_to_text(duration=5)

#                 if text and text.strip():
#                     print(f"[Speech] Recognized: {text}")
#                     self.process_user_input(text)
#                 time.sleep(0.5)

#             except KeyboardInterrupt:
#                 # allow Ctrl‑C to break out
#                 break
#             except Exception as e:
#                 print(f"[Speech Error] {e}")
#                 time.sleep(2)

#     def process_user_input(self, text):
#         # Send the text off to the terminal assistant worker
#         self.command_queue.put(text)

#         # Try to get back a command
#         try:
#             command = self.response_queue.get(timeout=10)
#             print(f"[Assistant] Command: {command}")
#         except queue.Empty:
#             print("[Assistant Error] No command received within 10 seconds.")
#             return
#         except Exception as e:
#             print(f"[Assistant Error] {e}")
#             return

#         # Execute the command asynchronously
#         asyncio.run(self.execute_command(command))

#         # Optionally speak back short outputs
#         if len(command) < 100:
#             self.speech_assistant.text_to_speech(f"The command is: {command}")

#     async def execute_command(self, command):
#         print(f"[Exec] Running: {command}")
#         proc = await asyncio.create_subprocess_shell(
#             command,
#             stdout=asyncio.subprocess.PIPE,
#             stderr=asyncio.subprocess.PIPE
#         )
#         stdout, stderr = await proc.communicate()

#         if stdout:
#             out = stdout.decode().strip()
#             print(f"[Exec] Output: {out}")
#             if len(out) < 100:
#                 self.speech_assistant.text_to_speech(f"Output: {out}")

#         if stderr:
#             err = stderr.decode().strip()
#             print(f"[Exec] Error: {err}")
#             if len(err) < 100:
#                 self.speech_assistant.text_to_speech(f"Error: {err}")

#         return proc.returncode

#     def stop(self):
#         print("[System] Shutting down...")

#         # Tell terminal worker to exit
#         self.command_queue.put("EXIT")

#         if self.terminal_process is not None:
#             self.terminal_process.join(timeout=5)

#         if self.hand_landmark_process is not None:
#             self.hand_landmark_process.terminate()

#         if self.gui_process is not None:
#             self.gui_process.terminate()

#         print("[System] Shutdown complete.")


# if __name__ == "__main__":
#     try:
#         print("[Main] Booting up...")
#         system = MainSystem()
#         system.start()
#     except KeyboardInterrupt:
#         print("\n[Main] Interrupted.")
#         system.stop()
#     except Exception as e:
#         print(f"[Main Error] {e}")
#         system.stop()


# mini_assistant.py

import os
from speech_module import SpeechAssistant
from Predict_command import TerminalAssistant
from Run_command import run_command
def main():
    # 1) Initialize speech‑to‑text (Vosk)
    vosk_model_path = os.path.abspath("Includes/model")
    speech = SpeechAssistant(
        api_key="sk_4470664f6689369435844fde2e502953131b8673600500d7",             
        model_path=vosk_model_path
    )

    # 2) Initialize local text‑to‑command model (Gemma‑3‑1B)
    gemma_model_path = os.path.abspath("Includes/gemma-3-1b-it")
    terminal = TerminalAssistant(
        model_path=gemma_model_path,
        device="mps"
    )

    print("=== Mini Assistant Started ===")
    try:
        while True:
            if input("You want say anything: ") != "No":
                print("\nListening for your command…")
                text = speech.speech_to_text(duration=5)
                if not text or not text.strip():
                    print("…no speech detected, retrying.")
                    

                print(f"You said: “{text}”")
                text = "list all in the desktop"
                cmd = terminal.predict_command(text)
                print(f"→ Generated command: {cmd}")
            else:
                break
        

    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
