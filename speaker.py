import asyncio
import os
import tempfile
import urllib.request
import json
import edge_tts
import pygame


class VoiceSpeaker:
    """สร้างเสียงตอบกลับด้วย Edge-TTS หรือ ElevenLabs และเล่นเสียงออกลำโพง"""

    def __init__(
        self,
        provider: str | None = None,
        voice: str | None = None,
        rate: str | None = None,
        elevenlabs_api_key: str | None = None,
        elevenlabs_voice_id: str | None = None,
        elevenlabs_model_id: str | None = None,
    ):
        self.provider = (provider or os.getenv("TTS_PROVIDER", "edge-tts")).lower()
        self.voice = voice or os.getenv("EDGE_TTS_VOICE", "th-TH-PremwadeeNeural")
        self.rate = rate or os.getenv("EDGE_TTS_RATE", "+0%")
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = elevenlabs_voice_id or os.getenv(
            "ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"
        )
        self.elevenlabs_model_id = elevenlabs_model_id or os.getenv(
            "ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"
        )
        pygame.mixer.init()

    async def _generate_edge_tts(self, text: str, output_path: str) -> None:
        communicate = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate)
        await communicate.save(output_path)

    def _generate_elevenlabs_tts(self, text: str, output_path: str) -> None:
        if not self.elevenlabs_api_key or self.elevenlabs_api_key == "your_elevenlabs_api_key_here":
            raise ValueError("ยังไม่ได้ตั้งค่า ELEVENLABS_API_KEY ในไฟล์ .env")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }
        payload = json.dumps(
            {
                "text": text,
                "model_id": self.elevenlabs_model_id,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())

    def speak(self, text: str) -> None:
        """แปลงข้อความเป็นเสียงพูดและเล่นออกลำโพง"""
        if not text:
            return

        print(f"[ AI ]   : {text}")
        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tmp_file = fp.name

            if self.provider == "elevenlabs":
                self._generate_elevenlabs_tts(text, tmp_file)
            else:
                asyncio.run(self._generate_edge_tts(text, tmp_file))

            pygame.mixer.music.load(tmp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()

        except Exception as e:
            print(f"[Speaker] เกิดข้อผิดพลาดในการสร้างหรือเล่นเสียง: {e}")
        finally:
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass
