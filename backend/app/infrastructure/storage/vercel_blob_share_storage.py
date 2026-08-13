from collections.abc import Callable

from vercel.blob import BlobClient

from app.core.vault import VaultCipher


class VercelBlobShareStorage:
    """Encrypted private object storage for production ShareVault files."""

    def __init__(
        self,
        token: str,
        cipher: VaultCipher,
        client_factory: Callable[..., BlobClient] = BlobClient,
    ) -> None:
        self._token = token
        self._cipher = cipher
        self._client_factory = client_factory

    def save(self, storage_key: str, content: bytes) -> str:
        pathname = f"sharevault/{storage_key}.vault"
        encrypted = self._cipher.encrypt_bytes(content)
        with self._client_factory(token=self._token) as client:
            result = client.put(
                pathname,
                encrypted,
                access="private",
                content_type="application/octet-stream",
                add_random_suffix=False,
                overwrite=False,
                multipart=len(encrypted) > 5 * 1024 * 1024,
            )
        return result.pathname

    def read(self, pathname: str) -> bytes:
        with self._client_factory(token=self._token) as client:
            result = client.get(pathname, access="private", use_cache=False)
        if result is None or result.status_code != 200:
            raise FileNotFoundError(pathname)
        return self._cipher.decrypt_bytes(result.content)

    def delete(self, pathname: str) -> None:
        with self._client_factory(token=self._token) as client:
            client.delete(pathname)
