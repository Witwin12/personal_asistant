import os
from pathlib import Path
from dotenv import load_dotenv

from listener import VoiceListener
from brain import AIBrain
from actions import OSActions
from speaker import VoiceSpeaker

# โหลดค่าตั้งค่าจากไฟล์ .env
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


def main():
    """ลูปหลัก: รับเสียง -> ประมวลผล -> สั่งงาน -> ตอบเสียง"""
    print("==========================================")
    print("   เริ่มต้นระบบผู้ช่วยสั่งงานด้วยเสียง (My Voice AI)")
    print("==========================================")

    try:
        stt_lang = os.getenv("STT_LANGUAGE", "th-TH")
        timeout = int(os.getenv("LISTEN_TIMEOUT", "5"))
        phrase_limit = int(os.getenv("PHRASE_TIME_LIMIT", "10"))
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        workspace_dir = os.getenv("WORKSPACE_DIR", "./workspace")

        listener = VoiceListener(language=stt_lang)
        brain = AIBrain(model_name=gemini_model)
        actions = OSActions(workspace_dir=workspace_dir)
        speaker = VoiceSpeaker()
    except Exception as e:
        print(f"[System] ไม่สามารถเริ่มต้นระบบได้: {e}")
        return

    speaker.speak("สวัสดีค่ะ ไอวี่ ระบบผู้ช่วยสั่งงานด้วยเสียงพร้อมทำงานแล้วค่ะ")

    while True:
        try:
            # 1. รับเสียงและแปลงเป็นข้อความ (STT)
            user_text = listener.listen(timeout=timeout, phrase_time_limit=phrase_limit)
            if not user_text:
                continue

            # 2. ส่งให้ Gemini ตีความคำสั่ง (Brain)
            decision = brain.process(user_text)
            action_name = decision.get("action", "none")
            params = decision.get("params", {})
            reply_text = decision.get("reply", "")

            # 3. สั่งงานระบบปฏิบัติการ/จัดการไฟล์ (OS Actions)
            action_result = actions.execute(action_name, params)

            # หากเป็นคำสั่งอ่านไฟล์ ให้นำเนื้อหาไฟล์มาพูดต่อท้ายด้วย
            if action_name == "read_file" and action_result:
                reply_text = f"{reply_text} เนื้อหาคือ {action_result}"

            # 4. สร้างเสียงตอบกลับผู้ใช้ (Edge-TTS / ElevenLabs)
            speaker.speak(reply_text)

            # ตรวจสอบคำสั่งออกจากโปรแกรม
            if action_name == "exit":
                print("[System] ปิดการทำงานของระบบ...")
                break

        except KeyboardInterrupt:
            print("\n[System] หยุดการทำงานโดยผู้ใช้ (Ctrl+C)")
            break


if __name__ == "__main__":
    main()
