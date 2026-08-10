import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


class BulkZipStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def create(self, job_id: str, entries: list[tuple[Path, str]]) -> str:
        path = (self._root / f"{job_id}.zip").resolve()
        if path.parent != self._root: raise ValueError("Invalid bulk job identifier")
        with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
            for source, name in entries: archive.write(source, arcname=self.safe_name(name))
        return path.name

    def resolve(self, relative_path: str) -> Path:
        path = (self._root / relative_path).resolve()
        if path.parent != self._root or not path.is_file(): raise FileNotFoundError(relative_path)
        return path

    def delete(self, relative_path: str | None) -> None:
        if not relative_path: return
        try: self.resolve(relative_path).unlink()
        except FileNotFoundError: pass

    @staticmethod
    def safe_name(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
        return cleaned[:120] or "qr-code"
