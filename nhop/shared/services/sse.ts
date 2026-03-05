

/*
====================================================
NHOP SSE CONNECTOR — FINAL EDITION
Backend → EventBus → UI Kernel Bridge
====================================================

Purpose:
Realtime communication layer between backend events
and frontend modules without polling.

Features:
- Auto reconnect (native EventSource)
- Safe JSON parsing
- Event batching (performance safe)
- Dynamic origin support
- Memory-safe buffering
====================================================
*/

type EventBus = {
  publish: (event: string, payload: any) => void;
};

export function connectSSE(eventBus: EventBus) {

  console.log("[SSE] Connecting...");

  const url = `${window.location.origin}/api/sse`;

  const source = new EventSource(url);

  /* ---------------------------------------------
     INTERNAL BUFFER (prevents UI overload)
  --------------------------------------------- */

  let buffer: any[] = [];

  /* ---------------------------------------------
     CONNECTION STATE
  --------------------------------------------- */

  source.onopen = () => {
    console.log("[SSE] Connected");
  };

  /* ---------------------------------------------
     RECEIVE EVENTS
  --------------------------------------------- */

  source.onmessage = (event: MessageEvent) => {

    try {

      const data = JSON.parse(event.data);

      // push to buffer instead of immediate UI dispatch
      buffer.push(data);

    } catch (err) {
      console.error("[SSE] JSON parse error", err);
    }
  };

  /* ---------------------------------------------
     BATCH DISPATCH LOOP
     (prevents excessive renders)
  --------------------------------------------- */

  const dispatcher = setInterval(() => {

    if (buffer.length === 0) return;

    const batch = buffer.splice(0, 20);

    for (const msg of batch) {

      if (!msg?.type) continue;

      eventBus.publish(
        `server:${msg.type}`,
        msg.payload
      );
    }

  }, 100);

  /* ---------------------------------------------
     ERROR HANDLING
  --------------------------------------------- */

  source.onerror = () => {
    console.warn("[SSE] Disconnected — retrying automatically");
  };

  /* ---------------------------------------------
     CLEANUP (important for SPA navigation)
  --------------------------------------------- */

  return () => {
    console.log("[SSE] Closing connection");
    clearInterval(dispatcher);
    source.close();
  };
}
