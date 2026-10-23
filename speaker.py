import asyncio
import json
import os
import tempfile
import urllib.request
import wave
import edge_tts
from gtts import gTTS
from google import genai
from google.genai import types
import pygame


class VoiceSpeaker:
    """
    สร้างเสียงตอบกลับภาษาไทย รองรับหลายผู้ให้บริการ (รวมถึงแบบฟรีและ Free Tier):
    - edge-tts   : ฟรี ไม่ใช้ API Key (Microsoft Neural: th-TH-PremwadeeNeural, th-TH-NiwatNeural)
    - gtts       : ฟรี ไม่ใช้ API Key (Google Translate TTS ภาษาไทย)
    - gemini     : ฟรีตามโควต้า Google AI Studio ใช้ GEMINI_API_KEY เดียวกับ Brain (gemini-2.5-flash-preview-tts)
    - botnoi     : มี Free Tier พอยต์ฟรีเมื่อสมัคร (https://voice.botnoi.ai)
    - aiforthai  : ฟรี API Key จาก NECTEC AI for Thai (VAJA9 - https://aiforthai.in.th)
    - elevenlabs : มี Free Tier 10,000 ตัวอักษร/เดือน (https://elevenlabs.io)
    """

    def __init__(self, provider: str | None = None, voice: str | None = None):
        self.provider = (provider or os.getenv("TTS_PROVIDER", "edge-tts")).lower()

        # Edge-TTS
        self.edge_voice = voice or os.getenv("EDGE_TTS_VOICE", "th-TH-PremwadeeNeural")
        self.edge_rate = os.getenv("EDGE_TTS_RATE", "+0%")

        # Gemini TTS (ใช้ GEMINI_API_KEY เดียวกับระบบหลักได้ทันที)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_tts_model = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
        self.gemini_voice = os.getenv("GEMINI_TTS_VOICE", "Kore")

        # Botnoi Voice (Thai TTS)
        self.botnoi_api_key = os.getenv("BOTNOI_API_KEY")
        self.botnoi_speaker = os.getenv("BOTNOI_SPEAKER_ID", "1")

        # AI for Thai (NECTEC VAJA9)
        self.aiforthai_api_key = os.getenv("AIFORTHAI_API_KEY")

        # ElevenLabs
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        self.elevenlabs_model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

        pygame.mixer.init()

    async def _generate_edge_tts(self, text: str, output_path: str) -> None:
        communicate = edge_tts.Communicate(
            text=text, voice=self.edge_voice, rate=self.edge_rate
        )
        await communicate.save(output_path)

    def _generate_gtts(self, text: str, output_path: str) -> None:
        tts = gTTS(text=text, lang="th", slow=False)
        tts.save(output_path)

    def _generate_gemini_tts(self, text: str, output_path: str) -> None:
        if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
            raise ValueError("ยังไม่ได้ตั้งค่า GEMINI_API_KEY ในไฟล์ .env")

        client = genai.Client(api_key=self.gemini_api_key)
        response = client.models.generate_content(
            model=self.gemini_tts_model,
            contents=f"พูดข้อความต่อไปนี้ด้วยน้ำเสียงสุภาพเป็นธรรมชาติ: {text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.gemini_voice
                        )
                    )
                ),
            ),
        )
        pcm_data = response.candidates[0].content.parts[0].inline_data.data
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)

    def _generate_botnoi_tts(self, text: str, output_path: str) -> None:
        if not self.botnoi_api_key or self.botnoi_api_key == "your_botnoi_api_key_here":
            raise ValueError("ยังไม่ได้ตั้งค่า BOTNOI_API_KEY ในไฟล์ .env")

        url = "https://api-voice.botnoi.ai/openapi/v1/generate_audio"
        headers = {
            "Botnoi-Token": self.botnoi_api_key,
            "Content-Type": "application/json",
        }
        payload = json.dumps(
            {
                "text": text,
                "speaker": str(self.botnoi_speaker),
                "volume": 1,
                "speed": 1,
                "type_media": "mp3",
                "save_file": "true",
                "language": "th",
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            audio_url = data.get("audio_url")
            if not audio_url:
                raise RuntimeError(f"Botnoi ไม่ได้ส่ง audio_url กลับมา: {data}")
        urllib.request.urlretrieve(audio_url, output_path)

    def _generate_aiforthai_tts(self, text: str, output_path: str) -> None:
        if not self.aiforthai_api_key or self.aiforthai_api_key == "your_aiforthai_api_key_here":
            raise ValueError("ยังไม่ได้ตั้งค่า AIFORTHAI_API_KEY ในไฟล์ .env")

        url = "https://api.aiforthai.in.th/vaja9/synth_audiovisual"
        headers = {
            "Apikey": self.aiforthai_api_key,
            "Content-Type": "application/json",
        }
        payload = json.dumps(
            {"input_text": text, "speaker": 1, "phrase_break": 0, "audiovisual": 0}
        ).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            wav_url = data.get("wav_url")
            if not wav_url:
                raise RuntimeError(f"AI for Thai ไม่ได้ส่ง wav_url กลับมา: {data}")

        dl_req = urllib.request.Request(wav_url, headers={"Apikey": self.aiforthai_api_key})
        with urllib.request.urlopen(dl_req, timeout=15) as audio_resp:
            with open(output_path, "wb") as f:
                f.write(audio_resp.read())

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
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())

    def speak(self, text: str) -> None:
        """แปลงข้อความเป็นเสียงพูดและเล่นออกลำโพง พร้อมระบบสำรอง (Fallback) อัตโนมัติ"""
        if not text:
            return

        print(f"[ AI ]   : {text}")
        suffix = ".wav" if self.provider in ("gemini", "aiforthai") else ".mp3"
        tmp_file = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fp:
                tmp_file = fp.name

            try:
                if self.provider == "gtts":
                    self._generate_gtts(text, tmp_file)
                elif self.provider == "gemini":
                    self._generate_gemini_tts(text, tmp_file)
                elif self.provider == "botnoi":
                    self._generate_botnoi_tts(text, tmp_file)
                elif self.provider == "aiforthai":
                    self._generate_aiforthai_tts(text, tmp_file)
                elif self.provider == "elevenlabs":
                    self._generate_elevenlabs_tts(text, tmp_file)
                else:
                    asyncio.run(self._generate_edge_tts(text, tmp_file))
            except Exception as provider_err:
                print(
                    f"[Speaker] ผู้ให้บริการ '{self.provider}' ขัดข้อง ({provider_err}) -> สลับไปใช้ gTTS สำรอง"
                )
                self._generate_gtts(text, tmp_file)

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
