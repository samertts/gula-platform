import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const pageUrl = process.argv[2];
if (!pageUrl) throw new Error("Usage: node scripts/audit-login-keyboard.mjs <url>");

const debugPort = 9229;
const chrome = spawn("chromium", [
  "--headless",
  "--no-sandbox",
  "--disable-gpu",
  `--remote-debugging-port=${debugPort}`,
  "--window-size=1280,720",
  pageUrl,
], { stdio: "ignore" });

function request(path) {
  return fetch(`http://127.0.0.1:${debugPort}${path}`).then((response) => response.json());
}

async function waitForTarget() {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const targets = await request("/json/list");
      const target = targets.find((item) => item.type === "page");
      if (target?.webSocketDebuggerUrl) return target;
    } catch {
      // Chromium is still starting.
    }
    await delay(150);
  }
  throw new Error("Chrome debugging target was not available");
}

const target = await waitForTarget();
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let sequence = 0;
const pending = new Map();
socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    message.error ? reject(new Error(message.error.message)) : resolve(message.result);
  }
});

function cdp(method, params = {}) {
  const id = ++sequence;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

try {
  await delay(1000);
  await cdp("Runtime.evaluate", { expression: "document.body.focus()" });
  const focused = [];
  for (let index = 0; index < 8; index += 1) {
    await cdp("Input.dispatchKeyEvent", { type: "keyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9 });
    await cdp("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9 });
    const response = await cdp("Runtime.evaluate", {
      expression: `(() => { const el = document.activeElement; const style = getComputedStyle(el); return { tag: el.tagName.toLowerCase(), id: el.id || null, type: el.getAttribute('type'), label: el.getAttribute('aria-label') || document.querySelector('label[for="' + el.id + '"]')?.textContent?.trim() || el.textContent?.trim().slice(0, 50) || null, focusVisible: el.matches(':focus-visible'), hasFocusStyle: style.outlineStyle !== 'none' || style.boxShadow !== 'none' }; })()`,
      returnByValue: true,
    });
    focused.push(response.result.value);
  }
  console.log(JSON.stringify({ url: pageUrl, focusOrder: focused }, null, 2));
} finally {
  socket.close();
  chrome.kill("SIGTERM");
}
