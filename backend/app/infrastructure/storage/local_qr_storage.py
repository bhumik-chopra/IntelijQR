import shutil
from pathlib import Path

from app.models.qr_generation import QrFileFormat


class LocalQrStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def save(
        self,
        storage_key: str,
        files: dict[QrFileFormat, bytes],
        logo: bytes | None = None,
    ) -> dict[QrFileFormat, str]:
        directory = (self._root / storage_key).resolve()
        if self._root not in directory.parents:
            raise ValueError("Invalid storage key")
        directory.mkdir(parents=True, exist_ok=False)
        stored: dict[QrFileFormat, str] = {}
        try:
            for file_format, content in files.items():
                path = directory / f"qr.{file_format}"
                path.write_bytes(content)
                stored[file_format] = path.relative_to(self._root).as_posix()
            if logo:
                (directory / "logo.png").write_bytes(logo)
            return stored
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def resolve(self, relative_path: str) -> Path:
        path = (self._root / relative_path).resolve()
        if self._root not in path.parents or not path.is_file():
            raise FileNotFoundError(relative_path)
        return path

    def delete(self, storage_key: str) -> None:
        directory = (self._root / storage_key).resolve()
        if self._root in directory.parents:
            shutil.rmtree(directory, ignore_errors=True)

    def read(self, relative_path: str) -> bytes:
        return self.resolve(relative_path).read_bytes()
