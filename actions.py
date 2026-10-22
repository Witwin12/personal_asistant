import os
import subprocess
import urllib.parse
import webbrowser
from pathlib import Path


class OSActions:
    """คำสั่งเปิด/ปิดโปรแกรม เปิดเว็บไซต์ ค้นหาข้อมูล และจัดการไฟล์ในเครื่อง (OS Commands)"""

    def __init__(self, workspace_dir: str | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()

    def _resolve_path(self, target: str) -> Path:
        path = Path(target)
        if not path.is_absolute():
            path = self.workspace_dir / path
        return path

    def execute(self, action: str, params: dict) -> str | None:
        """รันคำสั่งตาม action ที่ได้รับจาก Brain"""
        target = params.get("target", "").strip()
        content = params.get("content", "")

        try:
            if action == "open_app":
                return self.open_app(target)
            elif action == "close_app":
                return self.close_app(target)
            elif action == "open_website":
                return self.open_website(target)
            elif action == "search_google":
                query = target or content
                return self.search_google(query)
            elif action == "search_youtube":
                query = target or content
                return self.search_youtube(query)
            elif action == "create_file":
                return self.write_file(target, content="")
            elif action == "write_file":
                return self.write_file(target, content=content)
            elif action == "read_file":
                return self.read_file(target)
            elif action == "delete_file":
                return self.delete_file(target)
            elif action in ("none", "exit"):
                return None
            else:
                print(f"[Actions] ไม่รู้จักคำสั่ง action: {action}")
                return None
        except Exception as e:
            print(f"[Actions] เกิดข้อผิดพลาดระหว่างรันคำสั่ง {action}: {e}")
            return f"เกิดข้อผิดพลาดในการทำงาน: {e}"

    def open_website(self, url: str) -> str:
        """เปิดเว็บไซต์ด้วยเบราว์เซอร์เริ่มต้นของระบบ"""
        if not url:
            return "ไม่ได้ระบุเว็บไซต์ที่ต้องการเปิดค่ะ"
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        print(f"[Actions] กำลังเปิดเว็บไซต์: {url}")
        webbrowser.open(url)
        return f"เปิดเว็บไซต์ {url} เรียบร้อยแล้ว"

    def search_google(self, query: str) -> str:
        """เปิดเบราว์เซอร์และค้นหาข้อมูลใน Google"""
        if not query:
            return "ไม่ได้ระบุคำค้นหาค่ะ"
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        print(f"[Actions] กำลังค้นหาใน Google: {query} ({search_url})")
        webbrowser.open(search_url)
        return f"ค้นหา {query} ใน Google เรียบร้อยแล้ว"

    def search_youtube(self, query: str) -> str:
        """เปิดเบราว์เซอร์และค้นหาวิดีโอใน YouTube"""
        if not query:
            return "ไม่ได้ระบุคำค้นหาค่ะ"
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        print(f"[Actions] กำลังค้นหาใน YouTube: {query} ({search_url})")
        webbrowser.open(search_url)
        return f"ค้นหา {query} ใน YouTube เรียบร้อยแล้ว"

    def open_app(self, target: str) -> str:
        """เปิดโปรแกรมหรือไฟล์ด้วยค่าเริ่มต้นของระบบ"""
        if not target:
            return "ไม่ได้ระบุชื่อโปรแกรมหรือไฟล์ที่ต้องการเปิดค่ะ"
        print(f"[Actions] กำลังเปิด: {target}")
        os.startfile(target)
        return f"เปิด {target} เรียบร้อยแล้ว"

    def close_app(self, process_name: str) -> str:
        """ปิดโปรแกรมตามชื่อโปรเซส (บน Windows ใช้ taskkill)"""
        if not process_name:
            return "ไม่ได้ระบุชื่อโปรแกรมที่ต้องการปิดค่ะ"
        if not process_name.lower().endswith(".exe"):
            process_name += ".exe"
        print(f"[Actions] กำลังปิดโปรเซส: {process_name}")
        subprocess.run(
            ["taskkill", "/F", "/IM", process_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return f"สั่งปิด {process_name} เรียบร้อยแล้ว"

    def write_file(self, filepath: str, content: str = "") -> str:
        """สร้างหรือเขียนข้อความลงไฟล์"""
        if not filepath:
            return "ไม่ได้ระบุชื่อไฟล์ค่ะ"
        path = self._resolve_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"[Actions] บันทึกไฟล์ที่: {path}")
        return f"บันทึกไฟล์ {path.name} เรียบร้อยแล้ว"

    def read_file(self, filepath: str) -> str:
        """อ่านเนื้อหาจากไฟล์"""
        if not filepath:
            return "ไม่ได้ระบุชื่อไฟล์ที่ต้องการอ่านค่ะ"
        path = self._resolve_path(filepath)
        if not path.exists():
            return f"ไม่พบไฟล์ชื่อ {filepath} ค่ะ"
        data = path.read_text(encoding="utf-8")
        print(f"[Actions] เนื้อหาในไฟล์ {path.name}:\n{data}")
        return data

    def delete_file(self, filepath: str) -> str:
        """ลบไฟล์ในเครื่อง"""
        if not filepath:
            return "ไม่ได้ระบุชื่อไฟล์ที่ต้องการลบค่ะ"
        path = self._resolve_path(filepath)
        if not path.exists():
            return f"ไม่พบไฟล์ชื่อ {filepath} ค่ะ"
        path.unlink()
        print(f"[Actions] ลบไฟล์แล้ว: {path}")
        return f"ลบไฟล์ {path.name} เรียบร้อยแล้ว"
