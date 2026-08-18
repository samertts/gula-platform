import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/i18n";
import "@/styles/index.css";
import { App } from "@/App";
import { registerSW } from 'virtual:pwa-register';

// Register Service Worker for PWA
if ('serviceWorker' in navigator && !import.meta.env.DEV) {
  registerSW({
    onNeedRefresh() {
      if (confirm('يتوفر تحديث جديد للمنصة. هل تريد التحديث الآن؟')) {
        window.location.reload();
      }
    },
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
