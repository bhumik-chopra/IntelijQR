# IntelliQR API

FastAPI backend foundation for IntelliQR.

## Local setup

From the `backend` directory on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

API documentation is available at `http://127.0.0.1:8000/docs`.

The checked-in `.env.example` uses a local MongoDB instance. The real `.env` is ignored by Git. Set `MONGODB_REQUIRED_ON_STARTUP=true` when startup should fail if MongoDB is unavailable. In the default development mode the API starts, logs a database warning, and reports `503` from `/api/v1/health/ready` until MongoDB is available.

## Tests

```powershell
python -m pytest
```

With local MongoDB running, exercise registration, protected access, refresh-token rotation, logout, and revocation against a disposable database:

```powershell
python -m scripts.smoke_test
```
