import React from "react";
import ReactDOM from "react-dom/client";
import { AuthProvider } from "./features/auth";
import { LocaleProvider } from "./features/i18n";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LocaleProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </LocaleProvider>
  </React.StrictMode>
);
