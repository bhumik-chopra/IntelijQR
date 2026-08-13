from collections.abc import Callable

from vercel.blob import BlobClient

from app.models.qr_generation import QrFileFormat


class VercelBlobQrStorage:
    """Private durable storage for generated QR artifacts."""

    _formats: tuple[QrFileFormat, ...] = ("png", "svg", "pdf")

    def __init__(self, token: str, client_factory: Callable[..., BlobClient] = BlobClient) -> None:
        self._token = token
        self._client_factory = client_factory

    def save(self, storage_key: str, files: dict[QrFileFormat, bytes], logo: bytes | None = None) -> dict[QrFileFormat, str]:
        stored: dict[QrFileFormat, str] = {}
        uploaded: list[str] = []
        try:
            with self._client_factory(token=self._token) as client:
                for file_format, content in files.items():
                    pathname = f"{storage_key}/qr.{file_format}"
                    result = client.put(pathname, content, access="private", content_type=self._content_type(file_format),
                                        add_random_suffix=False, overwrite=False, multipart=False)
                    stored[file_format] = result.pathname
                    uploaded.append(result.pathname)
                if logo:
                    pathname = f"{storage_key}/logo.png"
                    result = client.put(pathname, logo, access="private", content_type="image/png",
                                        add_random_suffix=False, overwrite=False, multipart=False)
                    uploaded.append(result.pathname)
            return stored
        except Exception:
            if uploaded:
                with self._client_factory(token=self._token) as client:
                    client.delete(uploaded)
            raise

    def read(self, pathname: str) -> bytes:
        with self._client_factory(token=self._token) as client:
            result = client.get(pathname, access="private", use_cache=False)
        if result is None or result.status_code != 200:
            raise FileNotFoundError(pathname)
        return result.content

    def delete(self, storage_key: str) -> None:
        paths = [f"{storage_key}/qr.{file_format}" for file_format in self._formats]
        paths.append(f"{storage_key}/logo.png")
        with self._client_factory(token=self._token) as client:
            client.delete(paths)

    @staticmethod
    def _content_type(file_format: QrFileFormat) -> str:
        return {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}[file_format]
