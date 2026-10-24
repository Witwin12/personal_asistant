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


def _require_key(value: str | None, env_name: str) -> str:
    """ตรวจว่าตั้งค่า API Key แล้ว (ไม่ว่างและไม่ใช่ค่าตัวอย่าง your_..._here)"""
    if not value or value.startswith("your_"):
        raise ValueError(f"ยังไม่ได้ตั้งค่า {env_name} ในไฟล์ .env")
    return value


def _post_json(url: str, payload: dict, headers: dict) -> bytes:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


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

    def __init__(self, provider: str | None = None):
        # provider -> (ฟังก์ชันสร้างเสียง, นามสกุลไฟล์)
        self._providers = {
            "edge-tts": (self._generate_edge_tts, ".mp3"),
            "gtts": (self._generate_gtts, ".mp3"),
            "gemini": (self._generate_gemini_tts, ".wav"),
            "botnoi": (self._generate_botnoi_tts, ".mp3"),
            "aiforthai": (self._generate_aiforthai_tts, ".wav"),
            "elevenlabs": (self._generate_elevenlabs_tts, ".mp3"),
        }
        self.provider = (provider or os.getenv("TTS_PROVIDER", "edge-tts")).lower()
        if self.provider not in self._providers:
            print(f"[Speaker] ไม่รู้จัก TTS_PROVIDER '{self.provider}' -> ใช้ edge-tts แทน")
            self.provider = "edge-tts"

        self._gemini_client = None  # สร้างเมื่อใช้งานครั้งแรก
        pygame.mixer.init()

    # ---------- ผู้ให้บริการ TTS ----------

    def _generate_edge_tts(self, text: str, output_path: str) -> None:
        communicate = edge_tts.Communicate(
            text=text,
            voice=os.getenv("EDGE_TTS_VOICE", "th-TH-PremwadeeNeural"),
            rate=os.getenv("EDGE_TTS_RATE", "+0%"),
        )
        asyncio.run(communicate.save(output_path))

    def _generate_gtts(self, text: str, output_path: str) -> None:
        gTTS(text=text, lang="th", slow=False).save(output_path)

    def _generate_gemini_tts(self, text: str, output_path: str) -> None:
        if self._gemini_client is None:
            api_key = _require_key(os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY")
            self._gemini_client = genai.Client(api_key=api_key)

        response = self._gemini_client.models.generate_content(
            model=os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts"),
            contents=f"พูดข้อความต่อไปนี้ด้วยน้ำเสียงสุภาพเป็นธรรมชาติ: {text}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=os.getenv("GEMINI_TTS_VOICE", "Kore")
                        )
                    )
                ),
            ),
        )
        # Gemini ส่งกลับเป็น PCM 16-bit mono 24kHz ต้องห่อเป็นไฟล์ WAV เอง
        pcm_data = response.candidates[0].content.parts[0].inline_data.data
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)

    def _generate_botnoi_tts(self, text: str, output_path: str) -> None:
        api_key = _require_key(os.getenv("BOTNOI_API_KEY"), "BOTNOI_API_KEY")
        data = json.loads(
            _post_json(
                "https://api-voice.botnoi.ai/openapi/v1/generate_audio",
                {
                    "text": text,
                    "speaker": os.getenv("BOTNOI_SPEAKER_ID", "1"),
                    "volume": 1,
                    "speed": 1,
                    "type_media": "mp3",
                    "save_file": "true",
                    "language": "th",
                },
                {"Botnoi-Token": api_key},
            )
        )
        audio_url = data.get("audio_url")
        if not audio_url:
            raise RuntimeError(f"Botnoi ไม่ได้ส่ง audio_url กลับมา: {data}")
        urllib.request.urlretrieve(audio_url, output_path)

    def _generate_aiforthai_tts(self, text: str, output_path: str) -> None:
        api_key = _require_key(os.getenv("AIFORTHAI_API_KEY"), "AIFORTHAI_API_KEY")
        data = json.loads(
            _post_json(
                "https://api.aiforthai.in.th/vaja9/synth_audiovisual",
                {"input_text": text, "speaker": 1, "phrase_break": 0, "audiovisual": 0},
                {"Apikey": api_key},
            )
        )
        wav_url = data.get("wav_url")
        if not wav_url:
            raise RuntimeError(f"AI for Thai ไม่ได้ส่ง wav_url กลับมา: {data}")

        dl_req = urllib.request.Request(wav_url, headers={"Apikey": api_key})
        with urllib.request.urlopen(dl_req, timeout=15) as resp, open(output_path, "wb") as f:
            f.write(resp.read())

    def _generate_elevenlabs_tts(self, text: str, output_path: str) -> None:
        api_key = _require_key(os.getenv("ELEVENLABS_API_KEY"), "ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        audio = _post_json(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            {
                "text": text,
                "model_id": os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            {"Accept": "audio/mpeg", "xi-api-key": api_key},
        )
        with open(output_path, "wb") as f:
            f.write(audio)

    # ---------- เล่นเสียง ----------

    def _synthesize(self, provider: str, text: str) -> str:
        """สร้างไฟล์เสียงชั่วคราวด้วย provider ที่ระบุ แล้วคืน path ของไฟล์"""
        generate, suffix = self._providers[provider]
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            generate(text, path)
        except Exception:
            os.remove(path)
            raise
        return path

    @staticmethod
    def _play(path: str) -> None:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)
        pygame.mixer.music.unload()

    def speak(self, text: str) -> None:
        """แปลงข้อความเป็นเสียงพูดและเล่นออกลำโพง พร้อมระบบสำรอง (Fallback) อัตโนมัติ"""
        if not text:
            return

        print(f"[ AI ]   : {text}")
        audio_file = None
        try:
            try:
                audio_file = self._synthesize(self.provider, text)
            except Exception as provider_err:
                if self.provider == "gtts":
                    raise
                print(
                    f"[Speaker] ผู้ให้บริการ '{self.provider}' ขัดข้อง ({provider_err}) -> สลับไปใช้ gTTS สำรอง"
                )
                audio_file = self._synthesize("gtts", text)
            self._play(audio_file)
        except Exception as e:
            print(f"[Speaker] เกิดข้อผิดพลาดในการสร้างหรือเล่นเสียง: {e}")
        finally:
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except OSError:
                    pass
