from pathlib import Path

from app.core.vault import VaultCipher


class EncryptedShareStorage:
    def __init__(self, root: Path, cipher: VaultCipher) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._cipher = cipher

    def save(self, storage_key: str, content: bytes) -> str:
        path = (self._root / f"{storage_key}.vault").resolve()
        if path.parent != self._root: raise ValueError("Invalid share storage key")
        path.write_bytes(self._cipher.encrypt_bytes(content))
        return path.name

    def read(self, relative_path: str) -> bytes:
        path = self._resolve(relative_path)
        return self._cipher.decrypt_bytes(path.read_bytes())

    def delete(self, relative_path: str) -> None:
        try: self._resolve(relative_path).unlink()
        except FileNotFoundError: pass

    def _resolve(self, relative_path: str) -> Path:
        path = (self._root / relative_path).resolve()
        if path.parent != self._root or not path.is_file(): raise FileNotFoundError(relative_path)
        return path
