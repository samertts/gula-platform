import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/i18n";
import "@/styles/index.css";
import { App } from "@/App";

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Offline support is progressive enhancement — failure is non-fatal.
    });
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
