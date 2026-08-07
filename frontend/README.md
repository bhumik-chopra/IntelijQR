# IntelliQR frontend authentication layer

This milestone intentionally contains no pages or final UI. It provides:

- a typed fetch client with credentialed requests;
- in-memory access-token storage;
- single-flight refresh-token recovery;
- register, login, logout, refresh, and current-user API functions;
- `AuthProvider` and `useAuth` for future React screens.

The refresh token remains in an `HttpOnly` backend cookie and is never exposed to JavaScript. Access tokens are not stored in `localStorage` or `sessionStorage`.

## Validation

```powershell
npm install
npm run typecheck
npm test
```
