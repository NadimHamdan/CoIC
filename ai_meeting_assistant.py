import openai
import sounddevice as sd
import numpy as np
import wave
import io
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AIMeetingAssistant:
    def __init__(self):
        self.transcript = []
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def record_audio(self, duration=5, fs=44100):
        print("Recording...")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        print("Recording finished.")
        return recording, fs

    def save_audio(self, recording, fs):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes((recording * 32767).astype(np.int16).tobytes())
        return temp_audio_file.name

    def transcribe(self, audio_file_path):
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript["text"]
        self.transcript.append(text)
        os.unlink(audio_file_path)  # Delete the temporary file
        return text

    def generate_response(self, prompt):
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()

    def speak(self, text):
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        audio_data = io.BytesIO(response.content)
        sd.play(np.frombuffer(audio_data.read(), dtype=np.float32), 24000)
        sd.wait()

    def summarize_meeting(self):
        full_transcript = " ".join(self.transcript)
        summary_prompt = f"Summarize the following meeting transcript:\n\n{full_transcript}"
        return self.generate_response(summary_prompt)

    def send_email(self, recipient, subject, body):
        # Configure this method with your email settings
        pass

    def run_meeting(self):
        print("Meeting started. Say 'AI contribute' to get AI input.")
        while True:
            recording, fs = self.record_audio()
            audio_file = self.save_audio(recording, fs)
            text = self.transcribe(audio_file)
            print(f"Transcribed: {text}")

            if "end meeting" in text.lower():
                break
            elif "ai contribute" in text.lower():
                response = self.generate_response(f"Based on the following context, provide a relevant contribution: {' '.join(self.transcript[-5:])}")
                print("AI: ", response)
                self.speak(response)

        summary = self.summarize_meeting()
        self.send_email("recipient@example.com", "Meeting Summary", summary)
        print("Meeting ended. Summary email sent.")

if __name__ == "__main__":
    assistant = AIMeetingAssistant()
    assistant.run_meeting()