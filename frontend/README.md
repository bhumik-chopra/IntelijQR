# IntelliQR frontend

React, TypeScript, Vite, and Tailwind frontend for the local IntelliQR platform.

Implemented flows include public landing/authentication, protected routing, session restoration, the premium QR Generator, BrandCraft customization, and the QR management Dashboard. URL QR codes use stable dynamic links and can be searched, filtered, favourited, edited, paused, activated, limited, expired, downloaded, and deleted. BrandCraft provides a matching live SVG preview for persisted gradients, patterns, frames, correction levels, sizing, margins, and validated logos.

Access tokens remain in memory. The refresh token remains in an HttpOnly backend cookie and is never exposed to JavaScript.

The protected SafeScan scanner supports drag-and-drop images, webcam frame capture, automatic content classification, local URL risk scoring, and user-owned scan history. Uploaded image files are analyzed locally by the backend and are not retained.

The protected analytics dashboard reports real dynamic-redirect events with period and QR filters, interactive scan trends, unique visitors, device/browser/OS/location breakdowns, top performers, and recent activity. It does not seed placeholder analytics data.

SecureVault controls in the URL generator support public, password, signed-in-member, and private-allowlist policies. Protected scans open the public `/access/:slug` authorization screen before a short-lived grant forwards the visitor to the encrypted destination.

The protected BulkForge page accepts CSV/XLSX imports, provides a CSV template, selects PNG/SVG/PDF output formats, polls persisted job progress, reports row failures, and downloads completed local ZIP archives.

The protected ShareVault owner page encrypts and shares approved local files, creates downloadable QR codes, controls access/expiry/download limits, and displays download history. Recipients use the public `/share/:slug` authorization page; authenticated/private transfers revalidate the signed-in account during the file download.

The personal Dashboard now uses a cross-feature summary for real QR, favourite, scan, share, bulk, and export statistics plus recent activity and download history. Profile & Settings supports display-name editing, local theme preference, and password rotation with an enforced all-device sign-out.

Configured administrators receive a role-gated `/admin` control center with real platform statistics, searchable and paginated account management, enable/disable and role controls, and recent audit activity. Regular members cannot see its navigation or enter the route.

The protected `/notifications` center displays persisted security, QR, ShareVault, and BulkForge events with an unread navbar badge, filtering, read/delete controls, deep links, and account-level delivery preferences. Optional email stays local through a configured localhost SMTP capture server.

The local internationalization layer provides English, हिन्दी, and ગુજરાતી without external translation services. Language selection is available on public/authentication pages, the authenticated navbar, and Profile & Settings. The selected account locale survives session restoration, and core landing, authentication, navigation, dashboard, and generator workflows use the shared translation dictionaries.

## Validation

```powershell
npm install
npm run build
npm test
```
