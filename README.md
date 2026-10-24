# 🎙️ My Voice AI (ไอวี่ - ผู้ช่วยอัจฉริยะสั่งงานด้วยเสียง)

ระบบผู้ช่วยอัจฉริยะสั่งงานด้วยเสียงภาษาไทย **ทำงานได้ทั้ง Windows MacOS และ Linux** ที่รับคำสั่งผ่านไมโครโฟน ตีความคำสั่งด้วย **Google Gemini** สั่งงานระบบปฏิบัติการ (เปิด/ปิดโปรแกรม เปิดเว็บ ค้นหาข้อมูล เล่นเพลง YouTube จัดการไฟล์) และโต้ตอบกลับด้วยเสียงพูดภาษาไทยที่เป็นธรรมชาติ

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
my_voice_ai/
├── main.py            # ลูปหลัก: รับเสียง -> ตีความด้วย AI -> สั่งงานระบบ -> ตอบกลับด้วยเสียง
├── listener.py        # จัดการไมโครโฟนและแปลงเสียงพูดเป็นข้อความ (Speech-to-Text)
├── brain.py           # เชื่อมต่อ Gemini API เพื่อตีความคำสั่งและเลือก Action (JSON Schema)
├── actions.py         # คำสั่งควบคุมเครื่อง เปิด/ปิดแอป เปิดเว็บ เล่น YouTube และจัดการไฟล์
├── speaker.py         # สร้างเสียงพูดภาษาไทย (รองรับ 6 ผู้ให้บริการ + ระบบ Fallback อัตโนมัติ)
├── requirements.txt   # รายการไลบรารี Python ที่ต้องใช้งาน
├── .env.example       # ตัวอย่างไฟล์ตั้งค่า API Key และระบบ
└── .gitignore         # ไฟล์ที่ยกเว้นไม่นำขึ้น Git
```

---

## ✨ ฟังก์ชันการทำงานหลัก (Features & Functions)

### 1. ระบบรับเสียงพูด (`listener.py` - `VoiceListener`)
- **`listen(timeout, phrase_time_limit)`**: ปรับสมดุลเสียงรบกวนรอบข้างอัตโนมัติ รับเสียงพูดจากไมโครโฟน และแปลงเป็นข้อความภาษาไทย (`th-TH`) ด้วย Google Speech Recognition

### 2. ระบบประมวลผลและตีความคำสั่ง (`brain.py` - `AIBrain`)
- **`process(user_text)`**: ส่งข้อความให้โมเดล Gemini (`gemini-2.5-flash`) ตีความเจตนาของผู้ใช้และบังคับผลลัพธ์ผ่าน `RESPONSE_SCHEMA` ให้คืนค่ากลับมาเป็น JSON (`action`, `params`, `reply`) เสมอ

### 3. ระบบสั่งงานเครื่องและเบราว์เซอร์ (`actions.py` - `OSActions`)
รองรับคำสั่ง (`action`) ดังนี้:

| Action | ฟังก์ชันใน `OSActions` | รายละเอียดการทำงาน | ตัวอย่างคำสั่งเสียง |
| :--- | :--- | :--- | :--- |
| **`open_app`** | `open_app(target)` | ค้นหาและเปิดโปรแกรมอัตโนมัติตาม OS (Windows: `PATH`/Start Menu/Store, macOS: `Applications` `.app`, Linux: `PATH`/`.desktop`) | *"เปิดไลน์ให้หน่อย"*, *"เปิดเครื่องคิดเลข"*, *"เปิด Notepad"* |
| **`close_app`** | `close_app(process_name)` | ปิดโปรแกรมที่กำลังทำงานอยู่ (`taskkill` บน Windows / `pkill` บน macOS และ Linux) | *"ปิดโปรแกรม Notepad"* |
| **`open_website`** | `open_website(url)` | เปิดเว็บไซต์ด้วยเบราว์เซอร์หลักของเครื่อง | *"เปิดเว็บ github.com"*, *"เข้าเว็บยูทูป"* |
| **`search_google`** | `search_google(query)` | เปิดเบราว์เซอร์และค้นหาคำค้นใน Google | *"ค้นหากูเกิลว่า วิธีทำข้าวผัดกุ้ง"* |
| **`play_youtube`** | `play_youtube(query)` | ค้นหาและ**เปิดเล่น**วิดีโอ/เพลงแรกที่ตรงกับคำค้นบน YouTube ทันที | *"เปิดเพลงทรงอย่างแบด"*, *"อยากฟังเพลงแจ๊สเพราะๆ"* |
| **`search_youtube`** | `search_youtube(query)` | เปิดหน้าผลการค้นหาวิดีโอบน YouTube | *"หาช่องสอนเขียนโปรแกรมในยูทูป"* |
| **`create_file`** | `write_file(filepath, "")` | สร้างไฟล์เปล่าในโฟลเดอร์ `workspace` | *"สร้างไฟล์ชื่อ note.txt"* |
| **`write_file`** | `write_file(filepath, content)` | สร้างหรือเขียนข้อความลงในไฟล์ | *"เขียนไฟล์ test.txt ว่าสวัสดีชาวโลก"* |
| **`read_file`** | `read_file(filepath)` | อ่านเนื้อหาในไฟล์และนำมาพูดให้ฟัง | *"อ่านไฟล์ test.txt ให้ฟังหน่อย"* |
| **`delete_file`** | `delete_file(filepath)` | ลบไฟล์ออกจากเครื่อง | *"ลบไฟล์ test.txt"* |
| **`none`** | *(ไม่รันคำสั่ง OS)* | พูดคุยถาม-ตอบทั่วไปกับผู้ช่วย AI | *"วันนี้เหนื่อยจัง ชวนคุยหน่อย"* |
| **`exit`** | *(จบการทำงานลูปหลัก)* | บอกลาและปิดโปรแกรมผู้ช่วยสั่งงานด้วยเสียง | *"ปิดระบบ"*, *"เลิกทำงานได้แล้ว"* |

### 4. ระบบสร้างเสียงพูดภาษาไทย (`speaker.py` - `VoiceSpeaker`)
- **`speak(text)`**: สังเคราะห์เสียงพูดภาษาไทยและเล่นออกลำโพงด้วย `pygame` หากผู้ให้บริการหลักมีปัญหา ระบบจะสลับไปใช้ **`gtts`** สำรองให้อัตโนมัติ
- รองรับผู้ให้บริการ TTS ถึง **6 รูปแบบ** (ตั้งค่าได้ที่ `TTS_PROVIDER` ใน `.env`):
  1. **`edge-tts`** *(ค่าเริ่มต้น - ฟรี 100% ไม่ใช้คีย์)*: เสียง Microsoft Neural (`th-TH-PremwadeeNeural`, `th-TH-NiwatNeural`)
  2. **`gtts`** *(ฟรี 100% ไม่ใช้คีย์)*: เสียงภาษาไทยจาก Google Translate
  3. **`gemini`** *(Free Tier)*: ใช้ `GEMINI_API_KEY` เดียวกับระบบสมองกล (`gemini-2.5-flash-preview-tts`)
  4. **`aiforthai`** *(Free Tier)*: เสียงภาษาไทย **VAJA9** จาก NECTEC ([aiforthai.in.th](https://aiforthai.in.th))
  5. **`botnoi`** *(Free Tier)*: เสียงพากย์ภาษาไทยหลากหลายสไตล์จาก [voice.botnoi.ai](https://voice.botnoi.ai)
  6. **`elevenlabs`** *(Free Tier)*: เสียงพูดสมจริงหลายภาษาจาก [elevenlabs.io](https://elevenlabs.io)

---

## 🚀 วิธีติดตั้งและใช้งาน (Installation & Usage)

### 1. ติดตั้งไลบรารีเสียงระดับระบบ (เฉพาะ macOS / Linux สำหรับ PyAudio)
- **macOS (Homebrew)**:
  ```bash
  brew install portaudio
  ```
  *(หมายเหตุ: บน macOS ต้องอนุญาตให้ Terminal / IDE เข้าถึงไมโครโฟนที่ **System Settings > Privacy & Security > Microphone**)*
- **Linux (Ubuntu / Debian)**:
  ```bash
  sudo apt update && sudo apt install -y python3-pyaudio portaudio19-dev libasound2-dev
  ```

### 2. สร้างและเปิดใช้งาน Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux (Bash / Zsh)**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. ติดตั้งไลบรารีที่จำเป็น
```bash
pip install -r requirements.txt
```

### 4. ตั้งค่าไฟล์ `.env`
คัดลอกไฟล์ `.env.example` ไปเป็น `.env` แล้วใส่ค่า `GEMINI_API_KEY` ของคุณ (รับคีย์ฟรีได้ที่ [Google AI Studio](https://aistudio.google.com/)):
- **Windows**: `Copy-Item .env.example .env`
- **macOS / Linux**: `cp .env.example .env`

ตัวอย่างการตั้งค่าในไฟล์ `.env`:
```ini
GEMINI_API_KEY=ใส่_API_KEY_ของคุณที่นี่
GEMINI_MODEL=gemini-2.5-flash

# เลือกผู้ให้บริการเสียง: edge-tts | gtts | gemini | aiforthai | botnoi | elevenlabs
TTS_PROVIDER=edge-tts
EDGE_TTS_VOICE=th-TH-PremwadeeNeural
```

### 5. เริ่มต้นใช้งานผู้ช่วยสั่งงานด้วยเสียง
```bash
python main.py
```
- เมื่อขึ้นข้อความ **`[Listener] กำลังฟัง... (พูดคำสั่งได้เลย)`** สามารถพูดใส่ไมโครโฟนได้ทันที
- หากต้องการหยุดการทำงาน สามารถพูดว่า ***"ปิดระบบ"*** หรือกดปุ่ม **`Ctrl + C`** ที่คีย์บอร์ด
