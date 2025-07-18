# transcription_ai.py

import speech_recognition as sr
import os

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
    except sr.UnknownValueError:
        return "[Unintelligible]"
    except sr.RequestError as e:
        return f"[Error: {e}]"
    except Exception as e:
        return f"[Unexpected error: {e}]"

# Tip: You can also try using Whisper API (OpenAI) or AssemblyAI for better accuracy.
