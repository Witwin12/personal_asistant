import os
import json
from google import genai
from google.genai import types

SYSTEM_PROMPT = """
คุณคือผู้ช่วยอัจฉริยะสั่งงานด้วยเสียง (Voice AI Assistant)
หน้าที่ของคุณคือตีความคำสั่งของผู้ใช้และตอบกลับเป็นรูปแบบ JSON เท่านั้น โดยมีโครงสร้างดังนี้:

{
  "action": "ชื่อคำสั่ง (none | open_app | close_app | open_website | search_google | search_youtube | create_file | read_file | write_file | delete_file | exit)",
  "params": {
    "target": "ชื่อโปรแกรม, URL เว็บไซต์, คำค้นหา หรือ path ของไฟล์ (ถ้ามี)",
    "content": "เนื้อหาที่ต้องการเขียนลงไฟล์ หรือรายละเอียดเพิ่มเติม (ถ้ามี)"
  },
  "reply": "ข้อความตอบกลับผู้ใช้เป็นภาษาไทยที่สุภาพและเป็นธรรมชาติ สำหรับนำไปแปลงเป็นเสียงพูด"
}

ตัวอย่าง:
ผู้ใช้: "เปิดโน้ตแพดให้หน่อย"
ตอบกลับ:
{
  "action": "open_app",
  "params": {"target": "notepad.exe", "content": ""},
  "reply": "กำลังเปิดโปรแกรม Notepad ให้ค่ะ"
}

ผู้ใช้: "เปิดเว็บยูทูปให้หน่อย" หรือ "เข้าเว็บ github.com"
ตอบกลับ:
{
  "action": "open_website",
  "params": {"target": "https://www.youtube.com", "content": ""},
  "reply": "กำลังเปิดเว็บไซต์ YouTube ให้ค่ะ"
}

ผู้ใช้: "ค้นหากูเกิลว่า วิธีทำข้าวผัดกุ้ง" หรือ "หาข้อมูลใน Google เรื่อง Python AI"
ตอบกลับ:
{
  "action": "search_google",
  "params": {"target": "วิธีทำข้าวผัดกุ้ง", "content": ""},
  "reply": "กำลังค้นหาวิธีทำข้าวผัดกุ้งใน Google ให้ค่ะ"
}

ผู้ใช้: "หาคลิปเพลงบรรเลงในยูทูปให้หน่อย"
ตอบกลับ:
{
  "action": "search_youtube",
  "params": {"target": "เพลงบรรเลง", "content": ""},
  "reply": "กำลังค้นหาเพลงบรรเลงใน YouTube ให้ค่ะ"
}

ผู้ใช้: "สร้างไฟล์ชื่อ test.txt แล้วเขียนว่าสวัสดีชาวโลก"
ตอบกลับ:
{
  "action": "write_file",
  "params": {"target": "test.txt", "content": "สวัสดีชาวโลก"},
  "reply": "สร้างไฟล์ test.txt และบันทึกข้อความเรียบร้อยแล้วค่ะ"
}

ผู้ใช้: "ปิดระบบ / เลิกทำงาน"
ตอบกลับ:
{
  "action": "exit",
  "params": {"target": "", "content": ""},
  "reply": "รับทราบค่ะ แล้วพบกันใหม่นะคะ สวัสดีค่ะ"
}
"""


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
