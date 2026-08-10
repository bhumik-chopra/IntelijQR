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
The versioned consumer contract and endpoint map are documented in [API.md](API.md). Runtime discovery is available at `GET /api/v1/meta`.

The checked-in `.env.example` uses a local MongoDB instance. The real `.env` is ignored by Git. Set `INTELLIQR_MONGODB_REQUIRED_ON_STARTUP=true` when startup should fail if MongoDB is unavailable. In development mode the readiness endpoint reports `503` until MongoDB is available.

## Dynamic QR links

URL QR codes encode a stable `/r/{slug}` link. Configure `INTELLIQR_REDIRECT_BASE_URL` with the backend address scanners can reach. For phone testing on the same network, use the computer's LAN IP instead of `127.0.0.1`.

Authenticated QR management supports generation, listing/search/filtering, detail, update, deletion, favourites, pause/activate, expiry, scan limits, and PNG/SVG/PDF downloads. Redirect scans are counted atomically before forwarding to the current destination.

BrandCraft design settings are stored with each generation. The local renderer supports solid or gradient colors, square/rounded/dot modules, square/rounded frames, frame text, selectable correction levels, output sizes, quiet-zone margins, and validated PNG/JPEG logos. PNG, SVG, and PDF are rendered from the same persisted contract.

## QR scanning

Authenticated scanning accepts PNG, JPEG, and WebP images up to 10 MB from file upload or webcam capture. OpenCV decodes one or multiple QR codes, SmartClassifier identifies structured content, and SafeScan performs transparent local URL heuristics. Only decoded content and analysis metadata are stored in `qr_scans`; uploaded images are not retained. SafeScan is a risk aid, not a guarantee that a URL is malware-free.

## Analytics

Successful dynamic redirects create local `qr_scan_events` records for totals, unique-visitor estimates, time trends, devices, browsers, operating systems, top QR codes, and recent activity. Visitor identity is stored only as a keyed one-way hash; raw IP addresses and full user-agent strings are not retained. Private addresses are labelled Local. Public country/city values remain Unknown until an optional local GeoIP database is introduced; no cloud geolocation service is called.

## SecureVault

Dynamic URL QR codes can be public, password-protected, member-only, or restricted to an email allowlist. Protected destinations are encrypted at rest with AES-256-GCM and a unique nonce; shared passwords use bcrypt hashes. Successful authorization issues a short-lived JWT grant bound to one QR slug. Redirect responses disable referrer propagation and caching so grant tokens are not forwarded to destination sites. Set a dedicated `INTELLIQR_VAULT_ENCRYPTION_KEY` outside development and retain it safely—changing it makes existing protected destinations unreadable.

## BulkForge

Authenticated users can import up to 250 QR rows from a UTF-8 CSV or XLSX file (maximum 5 MB). Rows use the same validation and generation service as individual QR codes, while persisted `bulk_jobs` records expose queued/processing/completed/partial/failed progress and bounded row errors. Successful PNG/SVG/PDF outputs are packaged in an owner-only local ZIP. Generated QR records remain in normal QR history if the job archive is deleted.

## ShareVault

Authenticated owners can upload approved PDF, image, video, text, CSV, and modern document formats up to 25 MB. Files are signature-checked, encrypted locally with AES-256-GCM, and paired with a normal user-owned QR code. Recipient policies support public, password, signed-in, and email-allowlist access plus expiry, pause, and atomic download limits. Purpose-bound JWT grants authorize one in-memory decryption/download, while privacy-safe download events record device/browser/OS/locality metadata. Share deletion removes the encrypted file, its QR generation, and its download events.

## Personal dashboard and profile

`/dashboard/summary` aggregates owner-scoped counts and recent activity across QR generation, dynamic scans, scanner history, BulkForge, ShareVault, and export events. QR and bulk downloads append lightweight `download_events` records without duplicating the source data. Users can update their display name and rotate their password; password rotation increments the token version, revokes every refresh session, clears the cookie, and requires a fresh login on all devices.

## Administration and RBAC

Set `INTELLIQR_ADMIN_EMAILS` to a JSON list of trusted local account emails. Matching accounts receive the admin role at registration or their next successful login. Admin APIs expose aggregate platform counts, paginated user access management, and a privacy-safe audit history. Role or status changes invalidate the target account's access tokens and revoke all refresh sessions. Administrators cannot change their own access or remove the final active administrator.

## Local notifications and email

Authenticated users receive persisted, owner-isolated notifications for risky SafeScan results, dynamic QR scan limits, ShareVault downloads, and BulkForge results. The notification center supports unread filtering, read state, deletion, and per-category preferences. Email is disabled by default and can only target a localhost SMTP listener. To test email without sending anything externally, run a local SMTP capture tool on port 1025, set `INTELLIQR_SMTP_HOST=127.0.0.1`, restart the backend, and opt in from the Notifications page. Delivery failures are logged and never block the underlying QR or file operation.

## Multilingual content and locale

QR payloads use a tested UTF-8 contract. Render-and-decode coverage includes Hindi, Gujarati, Arabic, and Japanese, while normal Unicode strings remain supported for text and structured fields. Account responses include a persisted `locale`; `PATCH /users/me/locale` accepts `en`, `hi`, or `gu`. Legacy users safely default to English.

## Tests

```powershell
python -m pytest
```

With local MongoDB running, exercise registration, protected access, refresh-token rotation, logout, and revocation against a disposable database:

```powershell
python -m scripts.smoke_test
```

Exercise all seven QR payload types, MongoDB persistence, and PNG/SVG/PDF downloads against disposable local resources:

```powershell
python -m scripts.qr_generator_smoke_test
```
