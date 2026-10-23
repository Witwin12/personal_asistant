import os
import json
from google import genai
from google.genai import types

# รายการ action ที่รองรับ: ชื่อ -> ความหมายของ target / content
ACTIONS = {
    "none": "คุยทั่วไป ไม่ต้องสั่งงาน",
    "open_app": "target=ชื่อโปรแกรม เช่น notepad.exe",
    "close_app": "target=ชื่อโปรเซส",
    "open_website": "target=URL",
    "search_google": "target=คำค้นหา",
    "search_youtube": "target=คำค้นหา (แสดงผลการค้นหา)",
    "play_youtube": "target=ชื่อเพลง/วิดีโอ (เปิดเล่นทันที)",
    "create_file": "target=path ไฟล์",
    "write_file": "target=path ไฟล์, content=ข้อความ",
    "read_file": "target=path ไฟล์",
    "delete_file": "target=path ไฟล์",
    "exit": "ปิดระบบ",
}

SYSTEM_PROMPT = (
    "คุณคือน้อง ไอ ผู้ช่วยสั่งงานด้วยเสียง ตีความคำสั่งผู้ใช้แล้วเลือก action:\n"
    + "\n".join(f"- {name}: {desc}" for name, desc in ACTIONS.items())
    + "\nreply = คำตอบภาษาไทยเป็นผู้หญิง สุภาพ เป็นธรรมชาติ สำหรับอ่านออกเสียง"
)

# บังคับรูปแบบ JSON ผ่าน schema แทนการใส่ตัวอย่างใน prompt
RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "action": types.Schema(type=types.Type.STRING, enum=list(ACTIONS)),
        "params": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "target": types.Schema(type=types.Type.STRING),
                "content": types.Schema(type=types.Type.STRING),
            },
        ),
        "reply": types.Schema(type=types.Type.STRING),
    },
    required=["action", "params", "reply"],
)


class AIBrain:
    """คุยกับ Gemini (Google AI Studio) เพื่อตีความคำสั่งและตัดสินใจเลือก Action"""

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ไม่พบ GEMINI_API_KEY กรุณาตั้งค่าใน Environment Variable หรือระบุในโค้ด"
            )
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def process(self, user_text: str) -> dict:
        """ส่งข้อความให้ Gemini ตีความและคืนค่าเป็น dict (action, params, reply)"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.2,
                ),
            )
            result = json.loads(response.text)
            return {
                "action": result.get("action", "none"),
                "params": result.get("params", {}),
                "reply": result.get("reply", "ขออภัยค่ะ ฉันไม่เข้าใจคำสั่ง"),
            }
        except Exception as e:
            print(f"[Brain] เกิดข้อผิดพลาดในการเชื่อมต่อ Gemini: {e}")
            return {
                "action": "none",
                "params": {},
                "reply": "ขออภัยค่ะ ระบบประมวลผลขัดข้องชั่วคราว",
            }
