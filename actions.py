import os
import subprocess
from pathlib import Path


class OSActions:
    """คำสั่งเปิด/ปิดโปรแกรม และสร้าง/อ่าน/แก้ไข/ลบไฟล์ในเครื่อง (OS Commands)"""

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
