# IntelliQR REST API v1

IntelliQR exposes a local, versioned API at `http://127.0.0.1:8000/api/v1`. Its machine-readable contract is available at `/openapi.json`; interactive Swagger and ReDoc documentation are available at `/docs` and `/redoc`.

## Authentication

Register or log in with JSON at `/auth/register` or `/auth/login`. Send the returned access token on protected calls:

```http
Authorization: Bearer <access_token>
```

Access tokens are short-lived. The refresh token is rotated in an HttpOnly cookie, so browser and native HTTP clients must retain cookies and call `POST /auth/refresh`. A successful password change or logout revokes refresh sessions. Do not persist access tokens in browser local storage.

## Resource map

| Resource | Important operations |
| --- | --- |
| Authentication | register, login, refresh, logout, current user |
| QR generation | create, search/list, read, update, delete, PNG/SVG/PDF download |
| QR scanning | multipart image decode, direct content analysis, history, deletion |
| Analytics | overview filtered by period and optional QR ID |
| ShareVault | encrypted file upload, policy update, access grant, download, history |
| BulkForge | CSV/XLSX job creation, progress, ZIP download, deletion |
| Administration | platform overview, user search, role/status updates, audit history |
| Notifications | inbox, unread state, preferences, optional localhost SMTP delivery |

Use `GET /api/v1/meta` for a runtime capability and limit summary.

## Generate a QR

```http
POST /api/v1/qr/generations
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "type": "url",
  "label": "Portfolio",
  "url": "https://example.com",
  "design": {
    "foreground_color": "#111827",
    "background_color": "#FFFFFF",
    "error_correction": "H"
  }
}
```

The `type` discriminator also accepts `text`, `email`, `phone`, `wifi`, `contact`, and `location`. The OpenAPI schemas document the fields for each type.

## Decode or analyze

Upload a PNG, JPEG, or WebP image as multipart field `file` to `POST /qr/scans/decode`. Clients that already decoded a QR can send `{"content":"...","source":"upload"}` to `POST /qr/scans/analyze` for SmartClassifier and SafeScan processing.

## Pagination and errors

Collection endpoints accept `limit` (1–100) and `offset` (0 or greater), and return `items`, `total`, `limit`, `offset`, and `has_more`. QR listing additionally supports search, type, status, and favourite filters.

Errors use one envelope:

```json
{"error":{"code":"validation_error","message":"Request validation failed","request_id":"..."}}
```

Every response includes `X-Request-ID`, `X-API-Version`, and `X-Content-Type-Options`. Supply `X-Request-ID` yourself when correlating client and server logs.

## Local administrator bootstrap

Set `INTELLIQR_ADMIN_EMAILS=["admin@example.com"]` in the ignored backend `.env`, restart the API, and sign in with that account. A matching existing account is promoted at its next successful login. Admin endpoints under `/admin` enforce the current database role on every request; changing another account's access invalidates its JWT version and revokes all refresh sessions.

## Local notification delivery

Notification resources are under `/notifications`. In-app alerts work without additional software. Email delivery is opt-in and is accepted only when `INTELLIQR_SMTP_HOST` is `127.0.0.1` or `localhost`; configure a local SMTP capture server rather than an external provider. Notification failures are isolated from the business event that generated them.

## UTF-8 and locale

Generated QR responses declare `encoding: "UTF-8"`; Unicode text is preserved through generation and image decoding. Registration optionally accepts `locale` and authenticated clients can persist `en`, `hi`, or `gu` with `PATCH /users/me/locale`. Locale affects interface presentation only and never rewrites QR content.
