import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

START_MENU_DIRS = [
    Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
]
MAC_APP_DIRS = [
    Path("/Applications"),
    Path("/System/Applications"),
    Path("/System/Applications/Utilities"),
    Path.home() / "Applications",
]
LINUX_APP_DIRS = [
    Path("/usr/share/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
    Path("/var/lib/snapd/desktop/applications"),
    Path.home() / ".local/share/applications",
]

# แปลงชื่อคำสั่งพื้นฐานให้ตรงกับโปรแกรมเริ่มต้นของแต่ละ OS
APP_ALIASES = {
    "win32": {
        "calculator": "calc.exe",
        "textedit": "notepad.exe",
        "gedit": "notepad.exe",
    },
    "darwin": {
        "notepad": "TextEdit",
        "calc": "Calculator",
        "calculator": "Calculator",
        "explorer": "Finder",
        "mspaint": "Preview",
        "cmd": "Terminal",
        "powershell": "Terminal",
    },
    "linux": {
        "notepad": "gedit",
        "calc": "gnome-calculator",
        "calculator": "gnome-calculator",
        "explorer": "nautilus",
        "cmd": "x-terminal-emulator",
        "powershell": "x-terminal-emulator",
    },
}

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

    # ---------- โปรแกรม (รองรับ Windows, macOS, Linux) ----------

    @staticmethod
    def _best_path_match(candidates: list[Path], query: str) -> str | None:
        """เลือกไฟล์ที่ชื่อตรงกับคำค้นหามากที่สุด (ตรงเป๊ะ หรือชื่อสั้นที่สุดที่มีคำค้นหา)"""
        partial_matches = []
        for path in candidates:
            stem = path.stem.lower()
            if "uninstall" in stem:
                continue
            if stem == query:
                return str(path)
            if query in stem:
                partial_matches.append(path)
        if partial_matches:
            return str(min(partial_matches, key=lambda p: len(p.stem)))
        return None

    @classmethod
    def _find_start_menu_shortcut(cls, query: str) -> str | None:
        """[Windows] ค้นหา shortcut (.lnk) ของโปรแกรมใน Start Menu ตามชื่อ"""
        lnks = [lnk for base in START_MENU_DIRS if base.exists() for lnk in base.rglob("*.lnk")]
        return cls._best_path_match(lnks, query)

    @staticmethod
    def _find_store_app(query: str) -> str | None:
        """[Windows] ค้นหาแอปจาก Microsoft Store (UWP) ผ่าน Get-StartApps"""
        q = query.replace("'", "''")
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                f"Get-StartApps | Where-Object {{ $_.Name -like '*{q}*' -or $_.AppID -like '*{q}*' }} "
                "| Select-Object -First 1 -ExpandProperty AppID",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        app_id = result.stdout.strip()
        return f"shell:AppsFolder\\{app_id}" if app_id else None

    @classmethod
    def _find_mac_app(cls, query: str) -> str | None:
        """[macOS] ค้นหาแอปพลิเคชัน (.app) ในโฟลเดอร์ Applications"""
        apps = []
        for base in MAC_APP_DIRS:
            if base.exists():
                apps.extend(base.glob("*.app"))
                apps.extend(base.glob("*/*.app"))
        return cls._best_path_match(apps, query)

    @classmethod
    def _find_linux_desktop_app(cls, query: str) -> str | None:
        """[Linux] ค้นหาไฟล์ .desktop จากโฟลเดอร์แอปพลิเคชันของระบบ"""
        desktop_files = [
            f for base in LINUX_APP_DIRS if base.exists() for f in base.rglob("*.desktop")
        ]
        # 1. เทียบจากชื่อไฟล์ .desktop
        matched = cls._best_path_match(desktop_files, query)
        if matched:
            return matched

        # 2. เทียบจากฟิลด์ Name= หรือ Exec= ภายในไฟล์ .desktop
        for f in desktop_files:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore").lower()
                if re.search(rf"^(name|exec)=.*{re.escape(query)}", text, flags=re.MULTILINE):
                    return str(f)
            except OSError:
                continue
        return None

    def _resolve_app(self, target: str) -> str | None:
        """แปลงชื่อโปรแกรมให้เป็น path หรือคำสั่งที่เปิดได้จริงตามระบบปฏิบัติการ"""
        if Path(target).exists():
            return target

        clean_name = re.sub(r"\.exe$", "", target.strip(), flags=re.IGNORECASE)
        query = clean_name.lower()

        # แปลงชื่อโปรแกรมพื้นฐานให้ตรงกับ OS ปัจจุบัน (เช่น notepad -> TextEdit บน macOS)
        os_key = "win32" if IS_WINDOWS else ("darwin" if IS_MAC else "linux")
        mapped = APP_ALIASES.get(os_key, {}).get(query, clean_name)
        mapped_query = re.sub(r"\.exe$", "", mapped, flags=re.IGNORECASE).lower()

        # ค้นหาใน PATH ของระบบ
        for candidate in (mapped, clean_name, mapped_query, query):
            found = shutil.which(candidate) or (
                shutil.which(f"{candidate}.exe") if IS_WINDOWS else None
            )
            if found:
                return found

        if IS_WINDOWS:
            return self._find_start_menu_shortcut(mapped_query) or self._find_store_app(mapped_query)
        if IS_MAC:
            return self._find_mac_app(mapped_query) or self._find_mac_app(query)
        return self._find_linux_desktop_app(mapped_query) or self._find_linux_desktop_app(query)

    @staticmethod
    def _launch_resolved(resolved: str) -> None:
        """สั่งเปิดโปรแกรมหรือไฟล์ด้วยวิธีของแต่ละระบบปฏิบัติการ"""
        if IS_WINDOWS:
            os.startfile(resolved)
            return

        if IS_MAC:
            cmd = ["open", "-a", resolved] if resolved.endswith(".app") else ["open", resolved]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        # Linux
        if resolved.endswith(".desktop"):
            if shutil.which("gtk-launch"):
                cmd = ["gtk-launch", Path(resolved).name]
            elif shutil.which("gio"):
                cmd = ["gio", "launch", resolved]
            else:
                cmd = ["xdg-open", resolved]
        elif Path(resolved).exists() and not os.access(resolved, os.X_OK):
            cmd = ["xdg-open", resolved]
        else:
            cmd = [resolved]

        subprocess.Popen(
            cmd,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def open_app(self, target: str) -> str:
        """เปิดโปรแกรมหรือไฟล์ด้วยค่าเริ่มต้นของระบบ (Windows / macOS / Linux)"""
        if not target:
            return "ไม่ได้ระบุชื่อโปรแกรมหรือไฟล์ที่ต้องการเปิดค่ะ"
        resolved = self._resolve_app(target)
        if not resolved:
            print(f"[Actions] ไม่พบโปรแกรม: {target}")
            return f"ไม่พบโปรแกรม {target} ในเครื่องค่ะ"
        print(f"[Actions] กำลังเปิด: {target} -> {resolved}")
        self._launch_resolved(resolved)
        return f"เปิด {target} เรียบร้อยแล้ว"

    def close_app(self, process_name: str) -> str:
        """ปิดโปรแกรมตามชื่อโปรเซส (Windows ใช้ taskkill, macOS/Linux ใช้ pkill)"""
        if not process_name:
            return "ไม่ได้ระบุชื่อโปรแกรมที่ต้องการปิดค่ะ"

        clean_name = re.sub(r"\.exe$", "", process_name.strip(), flags=re.IGNORECASE)
        if IS_WINDOWS:
            exe_name = f"{clean_name}.exe"
            cmd = ["taskkill", "/F", "/IM", exe_name]
            display_name = exe_name
        else:
            cmd = ["pkill", "-i", "-f", clean_name]
            display_name = clean_name

        print(f"[Actions] กำลังปิดโปรเซส: {display_name}")
        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            return f"ไม่พบโปรแกรม {display_name} ที่กำลังทำงานอยู่ค่ะ"
        return f"สั่งปิด {display_name} เรียบร้อยแล้ว"

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
