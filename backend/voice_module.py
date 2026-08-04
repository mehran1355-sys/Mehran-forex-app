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
# voice_module.py

# اگر قبلاً کدهای دیگری داری، همان‌ها بمانند
# فقط این بخش را اضافه کن:

from strategy_router import get_strategy_from_voice

def handle_voice_command(text: str):
    strategy_key = get_strategy_from_voice(text)
    if strategy_key is None:
        return "روش یا بازار نامعتبر است. لطفاً دوباره بگو."

    return f"استراتژی فعال شد: {strategy_key}"
