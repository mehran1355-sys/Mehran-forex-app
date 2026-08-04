import speech_recognition as sr
import pyttsx3

recognizer = sr.Recognizer()
speaker = pyttsx3.init()


def say(text: str):
    try:
        speaker.say(text)
        speaker.runAndWait()
    except:
        pass


def listen(lang: str = "fa-IR") -> str | None:
    try:
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
        return recognizer.recognize_google(audio, language=lang)
    except:
        return None
