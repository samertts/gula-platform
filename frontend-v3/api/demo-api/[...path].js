const DEMO_COOKIE = "gula_demo_session";
const SESSION_MAX_AGE = 15 * 60;
const DEMO_PERSONAS = {
  doctor: { role: "doctor", name: "طبيب تجريبي", email: "demo.doctor@gula-demo.invalid", description: "استعراض المرضى والطلبات والنتائج الاصطناعية للقراءة." },
  technician: { role: "technician", name: "فني مختبر تجريبي", email: "demo.technician@gula-demo.invalid", description: "استعراض سير العمل المختبري والعينات والنتائج الاصطناعية." },
  lab_admin: { role: "lab_admin", name: "مدير مختبر تجريبي", email: "demo.lab-admin@gula-demo.invalid", description: "استعراض لوحة المختبر والموظفين والتقارير دون عمليات كتابة." },
  citizen: { role: "citizen", name: "مواطن تجريبي", email: "demo.citizen@gula-demo.invalid", description: "استعراض مساحة المواطن ببيانات اصطناعية معزولة." },
};

function syntheticUser(personaId) {
  const persona = DEMO_PERSONAS[personaId] || DEMO_PERSONAS.doctor;
  return {
    id: `demo-${personaId in DEMO_PERSONAS ? personaId : "doctor"}`,
    name: persona.name,
    email: persona.email,
    role: persona.role,
    lab_id: "demo-tenant",
    lab_name: "GULA Synthetic Demo",
    is_verified: true,
  };
}

function cookiesFrom(request) {
  return Object.fromEntries(
    (request.headers.cookie || "")
      .split(";")
      .map((part) => part.trim().split("="))
      .filter(([key]) => key)
      .map(([key, ...value]) => [key, decodeURIComponent(value.join("="))]),
  );
}

function isDemoSession(request) {
  return cookiesFrom(request)[DEMO_COOKIE]?.startsWith("demo-") === true;
}

function send(response, status, body, extraHeaders = {}) {
  response.statusCode = status;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.setHeader("Cache-Control", "no-store");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("X-GULA-Demo", "synthetic-only");
  Object.entries(extraHeaders).forEach(([name, value]) => response.setHeader(name, value));
  response.end(JSON.stringify(body));
}

function requireDemoSession(request, response) {
  if (isDemoSession(request)) return true;
  send(response, 401, {
    detail: {
      code: "DEMO_SESSION_REQUIRED",
      message: "Start an isolated demo session first.",
      message_ar: "ابدأ جلسة عرض تجريبي معزولة أولاً.",
    },
  });
  return false;
}

export default function handler(request, response) {
  const pathname = new URL(request.url || "/", "http://vercel.local").pathname;
  const path = pathname.replace(/^\/api\/demo-api\/?/, "").replace(/\/$/, "");

  if (request.method === "OPTIONS") {
    response.statusCode = 204;
    response.setHeader("Access-Control-Allow-Origin", "same-origin");
    response.setHeader("Access-Control-Allow-Credentials", "true");
    response.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    response.setHeader("Access-Control-Allow-Headers", "Content-Type");
    return response.end();
  }

  if (request.method === "POST" && path === "demo/access") {
    const requestedPersona = new URL(request.url || "/", "http://vercel.local").searchParams.get("persona") || "doctor";
    const personaId = Object.prototype.hasOwnProperty.call(DEMO_PERSONAS, requestedPersona) ? requestedPersona : "doctor";
    const cookie = `demo-${personaId}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    return send(response, 200, {
      demo_mode: true,
      demo_persona: personaId,
      message: "Synthetic demo session started",
      message_ar: "تم بدء جلسة العرض التجريبي بالبيانات الاصطناعية",
      user: syntheticUser(personaId),
    }, {
      "Set-Cookie": `${DEMO_COOKIE}=${encodeURIComponent(cookie)}; Max-Age=${SESSION_MAX_AGE}; Path=/; HttpOnly; Secure; SameSite=Strict`,
    });
  }

  if (request.method === "GET" && path === "session") {
    if (!requireDemoSession(request, response)) return;
    const cookiePersona = Object.keys(DEMO_PERSONAS).find((personaId) => cookiesFrom(request)[DEMO_COOKIE]?.startsWith(`demo-${personaId}-`)) || "doctor";
    return send(response, 200, { demo_mode: true, demo_persona: cookiePersona, user: syntheticUser(cookiePersona) });
  }

  if (request.method === "POST" && path === "logout") {
    return send(response, 200, { demo_mode: false, message: "Demo session ended" }, {
      "Set-Cookie": `${DEMO_COOKIE}=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Strict`,
    });
  }

  if (request.method === "GET" && path === "dashboard") {
    if (!requireDemoSession(request, response)) return;
    return send(response, 200, {
      demo_mode: true,
      total_patients: 15,
      today_orders: 8,
      today_results: 12,
      critical_alerts: 2,
      synthetic_notice: "All values are generated for demonstration and training only.",
      synthetic_notice_ar: "جميع القيم مولدة للعرض والتدريب فقط.",
    });
  }

  return send(response, 404, { detail: "Demo route not found" });
}
