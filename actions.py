import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

START_MENU_DIRS = [
    Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
]
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class OSActions:
    """คำสั่งเปิด/ปิดโปรแกรม เปิดเว็บไซต์ ค้นหาข้อมูล เล่นเพลง/วิดีโอ และจัดการไฟล์ในเครื่อง (OS Commands)"""

    def __init__(self, workspace_dir: str | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        # action -> ฟังก์ชันที่รับ (target, content)
        self._handlers = {
            "open_app": lambda t, c: self.open_app(t),
            "close_app": lambda t, c: self.close_app(t),
            "open_website": lambda t, c: self.open_website(t),
            "search_google": lambda t, c: self.search_google(t or c),
            "search_youtube": lambda t, c: self.search_youtube(t or c),
            "play_youtube": lambda t, c: self.play_youtube(t or c),
            "create_file": lambda t, c: self.write_file(t, ""),
            "write_file": lambda t, c: self.write_file(t, c),
            "read_file": lambda t, c: self.read_file(t),
            "delete_file": lambda t, c: self.delete_file(t),
        }

    def execute(self, action: str, params: dict) -> str | None:
        """รันคำสั่งตาม action ที่ได้รับจาก Brain"""
        if action in ("none", "exit"):
            return None
        handler = self._handlers.get(action)
        if not handler:
            print(f"[Actions] ไม่รู้จักคำสั่ง action: {action}")
            return None

        target = (params.get("target") or "").strip()
        content = params.get("content") or ""
        try:
            return handler(target, content)
        except Exception as e:
            print(f"[Actions] เกิดข้อผิดพลาดระหว่างรันคำสั่ง {action}: {e}")
            return f"เกิดข้อผิดพลาดในการทำงาน: {e}"

    # ---------- เว็บไซต์ / การค้นหา ----------

    @staticmethod
    def _open_url(url: str, label: str) -> None:
        print(f"[Actions] {label}: {url}")
        webbrowser.open(url)

    def open_website(self, url: str) -> str:
        """เปิดเว็บไซต์ด้วยเบราว์เซอร์เริ่มต้นของระบบ"""
        if not url:
            return "ไม่ได้ระบุเว็บไซต์ที่ต้องการเปิดค่ะ"
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        self._open_url(url, "กำลังเปิดเว็บไซต์")
        return f"เปิดเว็บไซต์ {url} เรียบร้อยแล้ว"

    def search_google(self, query: str) -> str:
        """เปิดเบราว์เซอร์และค้นหาข้อมูลใน Google"""
        if not query:
            return "ไม่ได้ระบุคำค้นหาค่ะ"
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        self._open_url(url, f"กำลังค้นหาใน Google '{query}'")
        return f"ค้นหา {query} ใน Google เรียบร้อยแล้ว"

    def search_youtube(self, query: str) -> str:
        """เปิดเบราว์เซอร์และค้นหาวิดีโอใน YouTube"""
        if not query:
            return "ไม่ได้ระบุคำค้นหาค่ะ"
        self._open_url(self._youtube_search_url(query), f"กำลังค้นหาใน YouTube '{query}'")
        return f"ค้นหา {query} ใน YouTube เรียบร้อยแล้ว"

    @staticmethod
    def _youtube_search_url(query: str) -> str:
        return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"

    def play_youtube(self, query: str) -> str:
        """ค้นหาและเปิดเล่นวิดีโอหรือเพลงแรกที่ตรงกับคำค้นหาบน YouTube ทันที"""
        if not query:
            return "ไม่ได้ระบุชื่อเพลงหรือวิดีโอที่ต้องการเล่นค่ะ"

        # หากผู้ใช้ส่งเป็นลิงก์ YouTube มาโดยตรง ให้เปิดทันที
        if query.startswith(("http://", "https://")) and (
            "youtube.com/" in query or "youtu.be/" in query
        ):
            self._open_url(query, "กำลังเล่นวิดีโอจากลิงก์")
            return f"เปิดเล่นวิดีโอ {query} เรียบร้อยแล้ว"

        search_url = self._youtube_search_url(query)
        try:
            req = urllib.request.Request(search_url, headers={"User-Agent": BROWSER_USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode("utf-8", errors="ignore")
            match = re.search(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
            if match:
                watch_url = f"https://www.youtube.com/watch?v={match.group(1)}"
                self._open_url(watch_url, f"กำลังเปิดเล่นบน YouTube '{query}'")
                return f"กำลังเล่น {query} บน YouTube"
        except Exception as e:
            print(f"[Actions] ดึงลิงก์วิดีโอโดยตรงไม่สำเร็จ ใช้หน้าค้นหาแทน: {e}")

        # Fallback: หากดึง video_id ไม่ได้ ให้เปิดหน้าผลการค้นหาแทน
        self._open_url(search_url, "เปิดหน้าผลการค้นหา YouTube")
        return f"เปิดผลการค้นหา {query} บน YouTube เรียบร้อยแล้ว"

    # ---------- โปรแกรม ----------

    @staticmethod
    def _find_start_menu_shortcut(query: str) -> str | None:
        """ค้นหา shortcut (.lnk) ของโปรแกรมใน Start Menu ตามชื่อ"""
        partial_matches = []
        for base in START_MENU_DIRS:
            if not base.exists():
                continue
            for lnk in base.rglob("*.lnk"):
                stem = lnk.stem.lower()
                if "uninstall" in stem:
                    continue
                if stem == query:
                    return str(lnk)  # ชื่อตรงเป๊ะ ใช้ทันที
                if query in stem:
                    partial_matches.append(lnk)

        if partial_matches:
            # เลือกชื่อที่สั้นที่สุด (ใกล้เคียงคำค้นหามากที่สุด)
            return str(min(partial_matches, key=lambda p: len(p.stem)))
        return None

    @staticmethod
    def _find_store_app(query: str) -> str | None:
        """ค้นหาแอปจาก Microsoft Store (UWP) ผ่าน Get-StartApps"""
        q = query.replace("'", "''")
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                # เทียบทั้งชื่อที่แสดง และ AppID (กรณี Windows ภาษาไทยชื่อแอปจะเป็นภาษาไทย)
                f"Get-StartApps | Where-Object {{ $_.Name -like '*{q}*' -or $_.AppID -like '*{q}*' }} "
                "| Select-Object -First 1 -ExpandProperty AppID",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        app_id = result.stdout.strip()
        return f"shell:AppsFolder\\{app_id}" if app_id else None

    def _resolve_app(self, target: str) -> str | None:
        """แปลงชื่อโปรแกรมให้เป็น path/คำสั่งที่เปิดได้จริง"""
        # 1. path ที่มีอยู่จริง หรือโปรแกรมใน PATH (เช่น notepad.exe)
        if Path(target).exists():
            return target
        found = shutil.which(target) or shutil.which(f"{target}.exe")
        if found:
            return found
        # 2. shortcut ใน Start Menu (เช่น LINE, Discord, Chrome) 3. แอปจาก Microsoft Store
        query = target.lower().removesuffix(".exe").strip()
        return self._find_start_menu_shortcut(query) or self._find_store_app(query)

    def open_app(self, target: str) -> str:
        """เปิดโปรแกรมหรือไฟล์ด้วยค่าเริ่มต้นของระบบ"""
        if not target:
            return "ไม่ได้ระบุชื่อโปรแกรมหรือไฟล์ที่ต้องการเปิดค่ะ"
        resolved = self._resolve_app(target)
        if not resolved:
            print(f"[Actions] ไม่พบโปรแกรม: {target}")
            return f"ไม่พบโปรแกรม {target} ในเครื่องค่ะ"
        print(f"[Actions] กำลังเปิด: {target} -> {resolved}")
        os.startfile(resolved)
        return f"เปิด {target} เรียบร้อยแล้ว"

    def close_app(self, process_name: str) -> str:
        """ปิดโปรแกรมตามชื่อโปรเซส (บน Windows ใช้ taskkill)"""
        if not process_name:
            return "ไม่ได้ระบุชื่อโปรแกรมที่ต้องการปิดค่ะ"
        if not process_name.lower().endswith(".exe"):
            process_name += ".exe"
        print(f"[Actions] กำลังปิดโปรเซส: {process_name}")
        result = subprocess.run(
            ["taskkill", "/F", "/IM", process_name], capture_output=True, check=False
        )
        if result.returncode != 0:
            return f"ไม่พบโปรแกรม {process_name} ที่กำลังทำงานอยู่ค่ะ"
        return f"สั่งปิด {process_name} เรียบร้อยแล้ว"

    # ---------- ไฟล์ ----------

    def _resolve_path(self, target: str) -> Path:
        path = Path(target)
        return path if path.is_absolute() else self.workspace_dir / path

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
