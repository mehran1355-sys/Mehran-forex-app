# backend/voice_alert.py

import os
from gtts import gTTS

class VoiceAlert:
    def __init__(self, folder="voice_alerts"):
        self.folder = folder
        if not os.path.exists(folder):
            os.makedirs(folder)

    def create_alert(self, text: str, filename: str):
        """ساخت فایل صوتی از متن"""
        try:
            tts = gTTS(text=text, lang="fa")
            path = os.path.join(self.folder, filename)
            tts.save(path)
            return {"status": "created", "path": path}
        except Exception as e:
            return {"status": "failed", "reason": str(e)}
