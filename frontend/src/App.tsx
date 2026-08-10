import React from "react";
import { Home, QrCode } from "lucide-react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { DashboardLayout } from "./components/layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Badge, Button, Card } from "./components/ui";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

const DashboardPage = React.lazy(() => import("./pages/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const QrGeneratorPage = React.lazy(() => import("./pages/QrGeneratorPage").then((module) => ({ default: module.QrGeneratorPage })));
const QrScannerPage = React.lazy(() => import("./pages/QrScannerPage").then((module) => ({ default: module.QrScannerPage })));
const AnalyticsPage = React.lazy(() => import("./pages/AnalyticsPage").then((module) => ({ default: module.AnalyticsPage })));
const VaultAccessPage = React.lazy(() => import("./pages/VaultAccessPage").then((module) => ({ default: module.VaultAccessPage })));
const BulkForgePage = React.lazy(() => import("./pages/BulkForgePage").then((module) => ({ default: module.BulkForgePage })));
const ShareVaultPage = React.lazy(() => import("./pages/ShareVaultPage").then((module) => ({ default: module.ShareVaultPage })));
const SharedFileAccessPage = React.lazy(() => import("./pages/SharedFileAccessPage").then((module) => ({ default: module.SharedFileAccessPage })));
const ProfilePage = React.lazy(() => import("./pages/ProfilePage").then((module) => ({ default: module.ProfilePage })));
const AdminPage = React.lazy(() => import("./pages/AdminPage").then((module) => ({ default: module.AdminPage })));
const NotificationsPage = React.lazy(() => import("./pages/NotificationsPage").then((module) => ({ default: module.NotificationsPage })));

const NotFoundRoute: React.FC = () => (
  <main className="flex min-h-screen items-center justify-center bg-[#08080F] px-6 text-center">
    <Card className="w-full max-w-md" glow>
      <Badge variant="purple">404</Badge>
      <div className="mx-auto mt-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-500/10">
        <QrCode className="h-7 w-7 text-violet-400" />
      </div>
      <h1 className="mt-5 text-2xl font-bold text-white">Page not found</h1>
      <p className="mt-2 text-sm text-slate-500">
        The page you requested does not exist in IntelliQR.
      </p>
      <Link to="/" className="mt-6 inline-block">
        <Button icon={<Home className="h-4 w-4" />}>Back to landing</Button>
      </Link>
    </Card>
  </main>
);

const App: React.FC = () => (
  <BrowserRouter>
    <React.Suspense fallback={<main className="flex min-h-screen items-center justify-center bg-[#08080F]"><span className="h-8 w-8 animate-spin rounded-full border-2 border-violet-400 border-t-transparent" /></main>}>
      <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/access/:slug" element={<VaultAccessPage />} />
      <Route path="/share/:slug" element={<SharedFileAccessPage />} />

      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/generator" element={<QrGeneratorPage />} />
        <Route path="/scanner" element={<QrScannerPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/bulk" element={<BulkForgePage />} />
        <Route path="/share-vault" element={<ShareVaultPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/admin" element={<ProtectedRoute requiredRole="admin"><AdminPage /></ProtectedRoute>} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/qr-codes" element={<Navigate to="/generator" replace />} />
      </Route>

      <Route path="*" element={<NotFoundRoute />} />
      </Routes>
    </React.Suspense>
  </BrowserRouter>
);

export default App;
