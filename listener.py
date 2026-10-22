import speech_recognition as sr


class VoiceListener:
    """จัดการไมโครโฟนและแปลงเสียงพูดเป็นข้อความ (Speech-to-Text)"""

    def __init__(self, language: str = "th-TH"):
        self.recognizer = sr.Recognizer()
        self.language = language
        # ปรับค่าความไวต่อเสียงรบกวนอัตโนมัติ
        self.recognizer.dynamic_energy_threshold = True

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> str | None:
        """รับเสียงจากไมโครโฟนและแปลงเป็นข้อความ"""
        try:
            with sr.Microphone() as source:
                print("\n[Listener] กำลังปรับสมดุลเสียงรบกวนรอบข้าง...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("[Listener] กำลังฟัง... (พูดคำสั่งได้เลย)")

                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

            print("[Listener] กำลังประมวลผลเสียงพูด...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            print(f"[ User ] : {text}")
            return text

        except sr.WaitTimeoutError:
            print("[Listener] ไม่ได้รับเสียงพูดภายในเวลาที่กำหนด")
            return None
        except sr.UnknownValueError:
            print("[Listener] ไม่เข้าใจเสียงพูด กรุณาลองใหม่อีกครั้ง")
            return None
        except sr.RequestError as e:
            print(f"[Listener] ไม่สามารถเชื่อมต่อบริการแปลงเสียงได้: {e}")
            return None
        except Exception as e:
            print(f"[Listener] เกิดข้อผิดพลาดกับไมโครโฟน: {e}")
            return None
