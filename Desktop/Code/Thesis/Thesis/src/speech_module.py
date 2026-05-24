import json
import os
import queue
import wave
from io import BytesIO

import pyttsx3
import requests
import sounddevice as sd
import vosk


class SpeechAssistant:
    def __init__(self, api_key=None, voice_id="Rachel", model_path="model"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.samplerate = 16000
        self.q = queue.Queue()
        self.model_path = model_path
        self.use_internet = bool(api_key) and self._elevenlabs_is_available()

        if self.use_internet:
            print("ElevenLabs API configured. Online text-to-speech is enabled.")
            self.engine = None
            self.model = None
        else:
            print("Using offline speech mode.")
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)
            self.model = vosk.Model(model_path) if os.path.exists(model_path) else None

    def _elevenlabs_is_available(self):
        try:
            response = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": self.api_key},
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def text_to_speech(self, text, output_file_path="output.mp3"):
        """Convert text to speech using ElevenLabs when configured, otherwise pyttsx3."""
        if not text:
            return

        if self.use_internet:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key,
                },
                json={"text": text},
                timeout=30,
            )
            if response.status_code == 200:
                with open(output_file_path, "wb") as audio_file:
                    audio_file.write(response.content)
                print(f"Audio saved as {output_file_path}")
            else:
                print(f"ElevenLabs error: {response.status_code} - {response.text}")
            return

        self.engine.say(text)
        self.engine.runAndWait()

    def speech_to_text(self, duration=5):
        """Record speech and return recognized text using Vosk when the model exists."""
        audio_data = self._record_audio(duration)

        if self.use_internet:
            return self._speech_to_text_online(audio_data)

        if self.model is None:
            print(f"Offline speech model not found at '{self.model_path}'.")
            return ""

        recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
        recognizer.AcceptWaveform(audio_data)
        result = json.loads(recognizer.Result())
        return result.get("text", "")

    def _record_audio(self, duration):
        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.q.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=self.samplerate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            print("Listening...")
            audio_data = b""
            for _ in range(int(self.samplerate / 8000 * duration)):
                audio_data += self.q.get()
            return audio_data

    def _speech_to_text_online(self, audio_data):
        wav_data = BytesIO()
        with wave.open(wav_data, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.samplerate)
            wav_file.writeframes(audio_data)

        response = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": self.api_key},
            files={"audio": ("audio.wav", wav_data.getvalue(), "audio/wav")},
            timeout=60,
        )

        if response.status_code == 200:
            return response.json().get("text", "")

        print(f"ElevenLabs speech-to-text error: {response.status_code} - {response.text}")
        return ""


if __name__ == "__main__":
    assistant = SpeechAssistant(
        api_key=os.environ.get("ELEVENLABS_API_KEY"),
        model_path=os.path.abspath("Includes/model"),
    )
    text = assistant.speech_to_text(duration=5)
    print(f"Recognized: {text}")
    assistant.text_to_speech(f"You said: {text}")
