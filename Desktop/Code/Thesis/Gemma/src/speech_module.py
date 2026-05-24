import os
import requests
import pyttsx3
import sounddevice as sd
import queue
import vosk
import json

class SpeechAssistant:
    def __init__(self, api_key=None, voice_id="Rachel", model_path="model"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.samplerate = 16000  # For speech recognition
        self.q = queue.Queue()
        self.model_path = model_path

        # Check for internet connection and choose API or offline method
        if self.is_connected():
            print("Internet connected. Using ElevenLabs.")
            self.use_internet = True
        else:
            print("No internet connection. Falling back to offline mode.")
            self.use_internet = False
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model path '{model_path}' not found.")

            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Set speech speed
            self.model = vosk.Model(model_path)

    def is_connected(self):
        """Check if the internet is connected by trying to reach ElevenLabs API."""
        try:
            response = requests.get("https://api.elevenlabs.io/voices/v1", timeout=5)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            return False
        return False

    def text_to_speech(self, text, output_file_path="output.mp3"):
        """Convert text to speech using ElevenLabs if connected, otherwise use pyttsx3."""
        if self.use_internet:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            data = json.dumps({"text": text})
            response = requests.post(url, headers=headers, data=data)

            if response.status_code == 200:
                with open(output_file_path, "wb") as f:
                    f.write(response.content)
                print(f"Audio saved as {output_file_path}")
            else:
                print(f"Error: {response.text}")
        else:
            # Offline TTS using pyttsx3
            self.engine.say(text)
            self.engine.runAndWait()

    def speech_to_text(self, duration=5):
        """Convert speech to text using ElevenLabs if connected, otherwise use Vosk."""
        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.q.put(bytes(indata))

        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, dtype='int16',
                                channels=1, callback=callback):
            print("Listening...")
            audio_data = b''
            try:
                for _ in range(int(self.samplerate / 8000 * duration)):
                    audio_data += self.q.get()
            except KeyboardInterrupt:
                pass

        if self.use_internet:
            # Send the audio data to ElevenLabs' speech-to-text API
            stt_url = "https://api.elevenlabs.io/v1/speech-to-text"
            headers = {
                "xi-api-key": self.api_key
            }
            files = {
                "audio": ("audio.wav", audio_data, "audio/wav")
            }
            response = requests.post(stt_url, headers=headers, files=files)

            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                print(f"Error: {response.text}")
                return ""
        else:
            # Offline STT using vosk
            recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
            recognizer.AcceptWaveform(audio_data)
            result = json.loads(recognizer.Result())
            return result.get("text", "")

if __name__ == "__main__":
    try:
        api_key = "sk_4470664f6689369435844fde2e502953131b8673600500d7"  # Replace with your ElevenLabs API key
        assistant = SpeechAssistant(api_key, model_path = os.path.abspath("Includes/model"))

        print("Say something...")
        text = assistant.speech_to_text(duration=5)  # Record for 5 seconds
        print(f"Recognized: {text}")

        if text:
            assistant.text_to_speech(f"You said: {text}")
    except Exception as e:
        print(f"Error: {e}")








# # # # speech_module.py

# import os
# import requests
# import pyttsx3
# import sounddevice as sd
# import queue
# import vosk
# import json

# class SpeechAssistant:
#     def __init__(self, api_key=None, voice_id="Rachel", model_path="model"):
#         self.api_key = "sk_fa20dffe664fb2eb851dd292734de8a1556367584ef8c4a6"
#         self.voice_id = voice_id
#         self.samplerate = 16000
#         self.q = queue.Queue()
#         self.model_path = model_path

#         if self.is_connected():
#             print("Internet connected. Using ElevenLabs.")
#             self.use_internet = True
#         else:
#             print("No internet connection. Falling back to offline mode.")
#             self.use_internet = False
#             if not os.path.exists(model_path):
#                 raise FileNotFoundError(f"Model path '{model_path}' not found.")

#             self.engine = pyttsx3.init()
#             self.engine.setProperty('rate', 150)
#             self.model = vosk.Model(model_path)

#     def is_connected(self):
#         """Check if ElevenLabs API is reachable with valid auth."""
#         try:
#             headers = {"xi-api-key": self.api_key}
#             response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=5)
#             return response.status_code == 200
#         except requests.RequestException:
#             return False


#     def text_to_speech(self, text, output_file_path="output.mp3"):
#         """Convert text to speech using ElevenLabs if connected, otherwise use pyttsx3."""
#         if self.use_internet:
#             url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
#             headers = {
#                 "Content-Type": "application/json",
#                 "xi-api-key": self.api_key
#             }
#             data = json.dumps({"text": text})
#             response = requests.post(url, headers=headers, data=data)

#             if response.status_code == 200:
#                 with open(output_file_path, "wb") as f:
#                     f.write(response.content)
#                 print(f"Audio saved as {output_file_path}")
#             else:
#                 print(f"Error: {response.text}")
#         else:
#             self.engine.say(text)
#             self.engine.runAndWait()

#     def speech_to_text(self, duration=5):
#         """Convert speech to text using ElevenLabs if connected, otherwise Vosk offline."""
#         def callback(indata, frames, time, status):
#             if status:
#                 print(f"Stream status: {status}")
#             self.q.put(bytes(indata))

#         with sd.RawInputStream(samplerate=self.samplerate,
#                                blocksize=8000,
#                                dtype='int16',
#                                channels=1,
#                                callback=callback):
#             print("🎙 Listening... Speak now.")
#             audio_data = b''
#             try:
#                 for _ in range(int(self.samplerate / 8000 * duration)):
#                     audio_data += self.q.get()
#             except KeyboardInterrupt:
#                 print("🛑 Interrupted by user.")
#                 return ""

#         if self.use_internet:
#             try:
#                 stt_url = "https://api.elevenlabs.io/v1/voices"

#                 headers = {
#                     "xi-api-key": self.api_key,
#                 }

#                 files = {
#                     "audio": ("audio.wav", audio_data, "audio/wav"),
#                     "model_id": (None, "whisper")  # Set model_id correctly here
#                 }

#                 print("🌐 Sending audio to ElevenLabs API...")
#                 response = requests.post(stt_url, headers=headers, files=files)

#                 if response.status_code == 200:
#                     result = response.json()
#                     return result.get("text", "")
#                 else:
#                     print(f"❌ ElevenLabs error: {response.status_code} - {response.text}")
#                     return ""
#             except Exception as e:
#                 print(f"❌ Network exception: {e}")
#                 return ""


#         else:
#             print("🧠 Processing with Vosk (offline)...")
#             try:
#                 recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
#                 recognizer.AcceptWaveform(audio_data)
#                 result = json.loads(recognizer.Result())
#                 return result.get("text", "")
#             except Exception as e:
#                 print(f"❌ Vosk error: {e}")
#                 return ""


# if __name__ == "__main__":
#     try:
#         # Just a quick test
#         api_key = "sk_672e930cab4d010cf2f639381b7c4e1cce7fccece930ed69"
#         assistant = SpeechAssistant(api_key=api_key, model_path = os.path.abspath("Includes/model"))

#         print("Say something...")
#         text = assistant.speech_to_text(duration=5)
#         print(f"Recognized: {text}")

#         if text:
#             assistant.text_to_speech(f"You said: {text}")
#     except Exception as e:
#         print(f"Error: {e}")
