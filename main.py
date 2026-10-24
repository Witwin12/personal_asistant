import os
from pathlib import Path
from dotenv import load_dotenv

from listener import VoiceListener
from brain import AIBrain
from actions import OSActions
from speaker import VoiceSpeaker

# โหลดค่าตั้งค่าจากไฟล์ .env ที่อยู่โฟลเดอร์เดียวกับไฟล์นี้
load_dotenv(Path(__file__).resolve().parent / ".env")


def main():
    """ลูปหลัก: รับเสียง -> ประมวลผล -> สั่งงาน -> ตอบเสียง"""
    print("==========================================")
    print("   เริ่มต้นระบบผู้ช่วยสั่งงานด้วยเสียง (My Voice AI)")
    print("==========================================")

    try:
        timeout = int(os.getenv("LISTEN_TIMEOUT", "5"))
        phrase_limit = int(os.getenv("PHRASE_TIME_LIMIT", "10"))

        listener = VoiceListener(language=os.getenv("STT_LANGUAGE", "th-TH"))
        brain = AIBrain(model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        actions = OSActions(workspace_dir=os.getenv("WORKSPACE_DIR", "./workspace"))
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
            action_name = decision["action"]
            reply_text = decision["reply"]

            # 3. สั่งงานระบบปฏิบัติการ/จัดการไฟล์ (OS Actions)
            action_result = actions.execute(action_name, decision["params"])

            # หากเป็นคำสั่งอ่านไฟล์ ให้นำเนื้อหาไฟล์มาพูดต่อท้ายด้วย
            if action_name == "read_file" and action_result:
                reply_text = f"{reply_text} เนื้อหาคือ {action_result}"

            # 4. สร้างเสียงตอบกลับผู้ใช้ (TTS ตาม TTS_PROVIDER)
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
