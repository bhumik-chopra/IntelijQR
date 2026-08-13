# IntelliQR Feature Implementation and Working Guide

This document explains how each IntelliQR feature is implemented, which technologies it uses, and how data moves through the application.

## 1. Overall application architecture

IntelliQR is divided into four main layers:

1. **React frontend** — displays pages, collects user input, and calls the backend API.
2. **FastAPI backend** — validates requests, authenticates users, and applies business rules.
3. **MongoDB database** — stores users, QR records, sessions, scans, jobs, shares, and notifications.
4. **Local file storage** — stores generated QR images, batch ZIP files, and encrypted shared files.

The normal request flow is:

```text
User action
   ↓
React page or component
   ↓
Feature API module
   ↓
Shared API client
   ↓
FastAPI endpoint
   ↓
Application service
   ↓
Repository / infrastructure component
   ↓
MongoDB or local file storage
```

The frontend API base URL defaults to:

```text
http://127.0.0.1:8000/api/v1
```

It can be changed with `VITE_API_BASE_URL` in `frontend/.env`.

---

## 2. Registration, login, and authentication

### Technologies used

- React Context for global authentication state
- FastAPI dependency injection
- JWT access and refresh tokens using PyJWT
- Bcrypt password hashing through `pwdlib`
- MongoDB for users and refresh sessions
- HttpOnly cookies for refresh tokens

### Important files

```text
frontend/src/features/auth/context/AuthContext.tsx
frontend/src/features/auth/api/authApi.ts
frontend/src/features/auth/hooks/useAuth.ts
frontend/src/components/ProtectedRoute.tsx
frontend/src/pages/LoginPage.tsx
frontend/src/pages/RegisterPage.tsx

backend/app/api/v1/endpoints/auth.py
backend/app/api/dependencies.py
backend/app/services/auth_service.py
backend/app/core/security.py
backend/app/repositories/user_repository.py
backend/app/repositories/session_repository.py
```

### How it works

1. The user submits the registration or login form.
2. `authApi.ts` sends the credentials to `/api/v1/auth/register` or `/api/v1/auth/login`.
3. FastAPI validates the JSON body with a Pydantic schema.
4. `AuthService` creates or finds the user and checks the bcrypt password hash.
5. The backend creates a short-lived JWT access token and a refresh session.
6. The access token is returned in JSON and kept only in frontend memory.
7. The refresh token is stored in an HttpOnly cookie, so frontend JavaScript cannot read it.
8. `ProtectedRoute` prevents unauthenticated users from opening protected pages.

When an API request returns `401`, the shared API client calls `/auth/refresh`, receives a new access token, and retries the original request once. Logout, password changes, account disablement, and important role changes revoke sessions.

---

## 3. QR Generator and BrandCraft

### Technologies used

- React and TypeScript form state
- Browser `qrcode` package for the live preview
- Python `qrcode` and Pillow for server rendering
- SVG generation and PDF output
- Pydantic discriminated schemas for different QR types
- MongoDB for generation metadata
- Local storage for generated files

### Important files

```text
frontend/src/pages/QrGeneratorPage.tsx
frontend/src/features/qr-generator/components/BrandCraftControls.tsx
frontend/src/features/qr-generator/components/BrandedQrPreview.tsx
frontend/src/features/qr-generator/api/qrGeneratorApi.ts
frontend/src/features/qr-generator/hooks/useQrGenerations.ts

backend/app/api/v1/endpoints/qr_generations.py
backend/app/services/qr/generator_service.py
backend/app/services/qr/payload_builder.py
backend/app/infrastructure/qr/renderer.py
backend/app/infrastructure/storage/local_qr_storage.py
backend/app/repositories/qr_generation_repository.py
```

### How it works

1. The user selects a payload type: URL, text, email, phone, Wi-Fi, contact, or location.
2. The page collects the content and BrandCraft design settings.
3. `BrandedQrPreview` creates an immediate browser preview.
4. The frontend sends the typed request to `/api/v1/qr/generations`.
5. `QrPayloadBuilder` converts the form values into a standard QR payload, such as a URL, `mailto:`, Wi-Fi string, or vCard.
6. For URL QR codes, the backend creates a stable `/r/{slug}` dynamic link.
7. `QrRenderer` generates matching PNG, SVG, and PDF files.
8. `LocalQrStorage` saves the files under `data/generated`.
9. `QrGenerationRepository` stores the owner, payload metadata, design, status, limits, slug, and file information in MongoDB.

The owner can later search, filter, favourite, edit, pause, activate, expire, limit, download, or delete a QR record. Because URL QR codes contain a stable redirect slug, their final destination can change without printing the QR code again.

---

## 4. Dynamic QR redirects

### Technologies used

- FastAPI redirect responses
- MongoDB atomic counters
- Stable random slugs
- Privacy-safe analytics events

### Important files

```text
backend/app/api/v1/endpoints/qr_redirects.py
backend/app/services/qr/generator_service.py
backend/app/repositories/qr_generation_repository.py
backend/app/repositories/analytics_repository.py
backend/app/services/analytics/scan_context.py
```

### How it works

1. A scanner opens the URL encoded in the QR, for example `/r/example-slug`.
2. The backend finds the QR generation by its slug.
3. It checks whether the QR is active, expired, over its scan limit, or protected.
4. For an allowed public scan, the counter is updated atomically so simultaneous scans cannot incorrectly exceed a limit.
5. A privacy-safe scan event is created for analytics.
6. FastAPI returns an HTTP redirect to the current destination.

Protected destinations first send the visitor to the SecureVault access page.

---

## 5. SafeScan QR Scanner

### Technologies used

- Browser file upload and webcam frame capture
- Multipart form uploads
- OpenCV and pyzbar for QR decoding
- Custom SmartClassifier
- Local URL risk heuristics
- MongoDB scan history

### Important files

```text
frontend/src/pages/QrScannerPage.tsx
frontend/src/features/qr-scanner/api/qrScannerApi.ts
frontend/src/features/qr-scanner/hooks/useQrScanner.ts

backend/app/api/v1/endpoints/qr_scans.py
backend/app/infrastructure/qr/decoder.py
backend/app/services/qr/scanner_service.py
backend/app/services/qr/classifier.py
backend/app/services/qr/safe_scan.py
backend/app/repositories/qr_scan_repository.py
```

### How it works

1. The user uploads a PNG, JPEG, or WebP image, or captures a webcam frame.
2. The frontend sends the image as multipart form data to `/qr/scans/decode`.
3. The backend verifies the file type and maximum 10 MB size.
4. OpenCV and pyzbar attempt to decode one or multiple QR codes.
5. `SmartClassifier` identifies the content as a URL, email, phone number, Wi-Fi configuration, contact, location, or plain text.
6. For URLs, `SafeScanService` examines suspicious patterns using transparent local heuristics.
7. The decoded content, classification, and analysis are stored in the owner's history.
8. The uploaded image itself is not retained.

SafeScan is a risk indicator, not a replacement for antivirus or a remote malware reputation service.

---

## 6. Smart QR Analytics

### Technologies used

- MongoDB aggregation queries
- React charts and breakdown components
- Privacy-safe visitor hashing
- User-agent classification

### Important files

```text
frontend/src/pages/AnalyticsPage.tsx
frontend/src/features/analytics/api/analyticsApi.ts
frontend/src/features/analytics/hooks/useAnalytics.ts
frontend/src/features/analytics/components/ScanTrendChart.tsx
frontend/src/features/analytics/components/BreakdownList.tsx

backend/app/api/v1/endpoints/analytics.py
backend/app/services/analytics/analytics_service.py
backend/app/services/analytics/scan_context.py
backend/app/repositories/analytics_repository.py
backend/app/models/qr_scan_event.py
```

### How it works

1. Every successful dynamic redirect creates a scan event.
2. `ScanContextService` classifies device, browser, operating system, and locality information.
3. A keyed one-way hash estimates unique visitors without retaining the raw IP address.
4. The analytics endpoint applies a date period and optional QR filter.
5. MongoDB aggregations calculate total scans, estimated unique visitors, trends, breakdowns, top QR codes, and recent events.
6. The React page presents this real data as charts, totals, and ranked lists.

Private addresses are labelled local. Public city/country values remain unknown unless a local GeoIP database is added; the project does not call a cloud geolocation service.

---

## 7. SecureVault protected destinations

### Technologies used

- AES-256-GCM encryption through `cryptography`
- Bcrypt for access passwords
- Short-lived purpose-bound JWT grants
- React public authorization page

### Important files

```text
frontend/src/pages/VaultAccessPage.tsx
frontend/src/features/secure-vault/api/vaultApi.ts

backend/app/api/v1/endpoints/vault.py
backend/app/services/qr/vault_access_service.py
backend/app/core/vault.py
backend/app/core/security.py
backend/app/repositories/qr_generation_repository.py
```

### How it works

SecureVault supports these policies:

- **Public** — no extra check.
- **Password** — visitor enters the configured shared password.
- **Member** — visitor must be signed in.
- **Private** — signed-in visitor's email must be on the allowlist.

For protected QR codes, the destination is encrypted in MongoDB using AES-256-GCM and a unique nonce. After the visitor passes the access check, the backend issues a short-lived JWT grant bound to that QR slug. The redirect endpoint validates the grant, decrypts the destination, records the allowed scan, and redirects without exposing the stored destination in the public policy response.

---

## 8. BulkForge

### Technologies used

- CSV parsing
- `openpyxl` for XLSX files
- FastAPI background tasks
- ZIP archive creation
- MongoDB job progress records

### Important files

```text
frontend/src/pages/BulkForgePage.tsx
frontend/src/features/bulk-forge/api/bulkForgeApi.ts
frontend/src/features/bulk-forge/hooks/useBulkJobs.ts

backend/app/api/v1/endpoints/bulk.py
backend/app/services/bulk/bulk_service.py
backend/app/infrastructure/bulk/parser.py
backend/app/infrastructure/bulk/zip_storage.py
backend/app/repositories/bulk_job_repository.py
backend/app/models/bulk_job.py
```

### How it works

1. The user downloads a template or prepares a CSV/XLSX file.
2. The file and requested PNG/SVG/PDF output format are uploaded.
3. `BulkImportParser` validates the file, maximum 5 MB size, and maximum 250 rows.
4. A MongoDB job record is created with queued status.
5. Background processing sends every valid row through the normal QR generation service.
6. Row failures are recorded without necessarily stopping the entire job.
7. Successful output files are added to a ZIP archive under `data/bulk`.
8. The frontend polls the job endpoint and displays progress, successes, failures, and errors.
9. Only the job owner can download or delete the archive.

Possible final states are completed, partial, or failed.

---

## 9. ShareVault encrypted file sharing

### Technologies used

- Multipart uploads
- File signature validation
- AES-256-GCM encryption
- Local encrypted file storage
- Bcrypt access passwords
- Short-lived JWT download grants
- QR generation service

### Important files

```text
frontend/src/pages/ShareVaultPage.tsx
frontend/src/pages/SharedFileAccessPage.tsx
frontend/src/features/share-vault/api/shareVaultApi.ts
frontend/src/features/share-vault/hooks/useShares.ts

backend/app/api/v1/endpoints/shares.py
backend/app/services/share/share_service.py
backend/app/infrastructure/storage/encrypted_share_storage.py
backend/app/repositories/share_file_repository.py
backend/app/repositories/share_download_repository.py
backend/app/models/share_file.py
```

### How it works

1. The owner uploads an approved file of up to 25 MB and selects an access policy.
2. The backend checks the filename, declared type, size, and file signature.
3. The file is encrypted with AES-256-GCM and saved under `data/shares`.
4. MongoDB stores metadata and policy information, not the plaintext file.
5. The normal QR generator creates a QR pointing to `/share/{slug}`.
6. A recipient opens the public page and completes any password, member, or allowlist requirement.
7. The backend creates a short-lived grant for that specific file.
8. The download endpoint revalidates the grant and authenticated identity when required.
9. The encrypted file is decrypted in memory and streamed to the recipient.
10. An atomic download counter and privacy-safe download event are recorded.

Expiry, pause state, and download limits are checked before authorization. Deleting a share removes its encrypted file, associated QR record, and download events.

---

## 10. Personal Dashboard

### Technologies used

- MongoDB aggregation
- React summary cards and activity lists
- Feature API hook

### Important files

```text
frontend/src/pages/DashboardPage.tsx
frontend/src/features/personal-dashboard/api/dashboardApi.ts
frontend/src/features/personal-dashboard/hooks/useDashboardSummary.ts

backend/app/api/v1/endpoints/dashboard.py
backend/app/services/dashboard_service.py
backend/app/repositories/dashboard_repository.py
```

### How it works

The dashboard makes one request to `/dashboard/summary`. The backend aggregates the current user's QR generations, favourites, dynamic scans, scanner history, ShareVault files, BulkForge jobs, exports, downloads, and recent activity. The response is owner-scoped, so one user cannot see another user's dashboard data.

---

## 11. Notifications and optional local email

### Technologies used

- MongoDB notification records
- React polling and unread badge
- Python SMTP client
- Local SMTP capture server such as Mailpit

### Important files

```text
frontend/src/pages/NotificationsPage.tsx
frontend/src/features/notifications/api/notificationApi.ts
frontend/src/features/notifications/hooks/useNotifications.ts

backend/app/api/v1/endpoints/notifications.py
backend/app/services/notification_service.py
backend/app/infrastructure/notifications/local_smtp.py
backend/app/repositories/notification_repository.py
backend/app/models/notification.py
```

### How it works

Business services create notifications for important events such as risky scans, scan-limit activity, BulkForge results, and ShareVault downloads. The navbar periodically requests the unread count. Users can filter the inbox, mark one or all messages as read, delete messages, and configure category preferences.

Email is disabled by default. If enabled, the backend only accepts `127.0.0.1` or `localhost` as the SMTP host. This permits local email testing without sending private development notifications to an external provider. Email failure is logged but does not undo the business operation.

---

## 12. Profile, settings, theme, and language

### Technologies used

- React Context for locale
- Shared TypeScript translation dictionaries
- Local browser theme preference
- MongoDB user profile fields

### Important files

```text
frontend/src/pages/ProfilePage.tsx
frontend/src/hooks/useTheme.ts
frontend/src/features/i18n/translations.ts
frontend/src/features/i18n/context/LocaleContext.tsx
frontend/src/features/i18n/hooks/useLocale.ts
frontend/src/features/i18n/components/LanguageSelector.tsx

backend/app/api/v1/endpoints/users.py
backend/app/services/profile_service.py
backend/app/repositories/user_repository.py
```

### How it works

The profile page allows the user to update a display name, choose English/Hindi/Gujarati, select a local appearance preference, or rotate the password. Locale is stored on the user record and is restored with the session. The theme is a local presentation preference.

Password rotation verifies the current password, stores a new hash, increments the account token version, deletes refresh sessions, and clears the refresh cookie. The user must then sign in again on every device.

---

## 13. Administration and role-based access control

### Technologies used

- Backend role dependencies
- MongoDB user and audit queries
- React protected route with required role
- JWT token-version invalidation

### Important files

```text
frontend/src/pages/AdminPage.tsx
frontend/src/features/admin/api/adminApi.ts
frontend/src/features/admin/hooks/useAdminDashboard.ts
frontend/src/components/ProtectedRoute.tsx

backend/app/api/v1/endpoints/admin.py
backend/app/services/admin_service.py
backend/app/repositories/admin_repository.py
backend/app/api/dependencies.py
```

### How it works

Administrator emails are configured in `INTELLIQR_ADMIN_EMAILS`. A matching account is promoted during registration or its next login. The frontend hides and protects the admin route, while the backend independently verifies the current database role on every admin request.

Administrators can view platform totals, search and paginate accounts, enable or disable users, change roles, and review recent audit activity. Status or role changes invalidate the affected user's access tokens and refresh sessions. The service prevents administrators from changing their own access and prevents removal of the final active administrator.

---

## 14. Internationalization and Unicode QR content

### Technologies used

- Local TypeScript translation dictionaries
- React locale provider
- UTF-8 throughout frontend, API, database, and QR renderer

### How it works

The `LocaleProvider` exposes the selected language and translation function to React components. The account locale is persisted through `/users/me/locale`. Interface translation does not modify QR payload content.

The QR generation pipeline preserves UTF-8 strings. Tests cover content in Hindi, Gujarati, Arabic, and Japanese, while English and other valid Unicode text remain supported.

---

## 15. Error handling, logging, and API documentation

### Technologies used

- FastAPI middleware and exception handlers
- Pydantic validation
- Request IDs
- OpenAPI, Swagger UI, and ReDoc

### Important files

```text
backend/app/main.py
backend/app/core/exceptions.py
backend/app/core/logging.py
backend/app/schemas/
backend/API.md
```

### How it works

Every request receives an `X-Request-ID`, either supplied by the client or generated by the backend. The middleware logs the method, path, status, request ID, and duration. Responses include API-version and content-type-protection headers.

Errors use a consistent envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "request_id": "..."
  }
}
```

Interactive API documentation is available while the backend is running:

```text
Swagger UI: http://127.0.0.1:8000/docs
ReDoc:      http://127.0.0.1:8000/redoc
OpenAPI:    http://127.0.0.1:8000/openapi.json
```

---

## 16. Testing strategy

### Backend

Pytest covers health checks, schemas, authentication/security, QR generation, scanning, analytics, SecureVault, BulkForge, ShareVault, notifications, dashboard/profile, administration, and the REST API contract.

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

### Frontend

Vitest covers feature API wrappers, authentication behavior, QR generation/scanning, analytics, BulkForge, ShareVault, notifications, dashboard, administration, and internationalization.

```powershell
cd frontend
npm test
npm run typecheck
npm run build
```

This separation verifies both backend business behavior and the frontend's contract with the REST API.

---

## 17. Starting the complete project

Start MongoDB first. Then open two PowerShell terminals.

### Backend terminal

```powershell
cd C:\codes\react\IntelijQR\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Frontend terminal

```powershell
cd C:\codes\react\IntelijQR\frontend
npm run dev
```

Open `http://127.0.0.1:5173` in the browser.

