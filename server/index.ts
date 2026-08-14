import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { createServer } from 'http';
import { createHmac, randomBytes, timingSafeEqual } from 'crypto';
import { z } from 'zod';
import type { CookieOptions } from 'express';
import { structuredLogger } from './utils/structuredLogger';
import { healthChecker as healthCheck } from './utils/healthCheck';

const app: Express = express();
const port = process.env.PORT || 3000;
const nodeEnv = process.env.NODE_ENV || 'development';
const isProduction = nodeEnv === 'production';
const demoSessionSecret = process.env.DEMO_SESSION_SECRET || 'development-only-demo-secret-change-before-production';
const demoSessionLifetimeSeconds = 20 * 60;

const configuredCorsOrigins = (process.env.CORS_ORIGINS || '')
  .split(',')
  .map((origin) => origin.trim().replace(/\/$/, ''))
  .filter(Boolean);
const allowedCorsOrigins = configuredCorsOrigins.length > 0
  ? configuredCorsOrigins
  : isProduction
    ? ['https://gula-platform.org', 'https://www.gula-platform.org']
    : ['http://localhost:3000', 'http://localhost:4173', 'http://localhost:5173'];

if (allowedCorsOrigins.includes('*')) {
  throw new Error('CORS_ORIGINS must not contain "*" when credentialed cookies are enabled.');
}
if (isProduction && (!process.env.DEMO_SESSION_SECRET || demoSessionSecret.length < 32)) {
  throw new Error('DEMO_SESSION_SECRET must be set to a random value of at least 32 characters in production.');
}
const demoAttempts = new Map<string, { count: number; resetAt: number }>();
const revokedDemoSessions = new Map<string, number>();

type DemoClaims = {
  environment: 'demo';
  sessionId: string;
  issuedAt: number;
  expiresAt: number;
};

const demoCookieOptions: CookieOptions = {
  httpOnly: true,
  sameSite: 'strict',
  secure: nodeEnv === 'production',
  maxAge: demoSessionLifetimeSeconds * 1000,
  path: '/',
};

const demoDashboard = {
  environment: 'demo' as const,
  user: {
    name: 'د. سارة',
    role: 'مشرفة المختبر — عرض توضيحي',
    facility: 'مختبر جولا التدريبي',
  },
  summary: [
    { label: 'عينات مستلمة', value: '128', note: '+8.6% مقارنة بالأسبوع السابق', trend: 'up' as const },
    { label: 'قيد المعالجة', value: '24', note: 'ضمن الزمن المستهدف', trend: 'neutral' as const },
    { label: 'بانتظار مراجعة', value: '7', note: 'تتطلب اعتماداً تدريبياً', trend: 'down' as const },
    { label: 'تقارير مكتملة', value: '96', note: '+12.4% مقارنة بالأسبوع السابق', trend: 'up' as const },
  ],
  workload: [
    { day: 'السبت', value: 44 },
    { day: 'الأحد', value: 61 },
    { day: 'الاثنين', value: 58 },
    { day: 'الثلاثاء', value: 72 },
    { day: 'الأربعاء', value: 66 },
    { day: 'الخميس', value: 81 },
    { day: 'الجمعة', value: 53 },
  ],
  queue: [
    { id: 'TRN-1048', type: 'كيمياء سريرية', status: 'جاهز للمراجعة', urgency: 'priority' as const, updated: 'منذ 8 دقائق' },
    { id: 'TRN-1047', type: 'تعداد دم كامل', status: 'قيد المعالجة', urgency: 'normal' as const, updated: 'منذ 13 دقيقة' },
    { id: 'TRN-1046', type: 'مؤشرات حيوية', status: 'تم التحقق', urgency: 'normal' as const, updated: 'منذ 21 دقيقة' },
    { id: 'TRN-1045', type: 'كيمياء سريرية', status: 'قيد المعالجة', urgency: 'normal' as const, updated: 'منذ 33 دقيقة' },
  ],
  activity: [
    { id: 'activity-1', title: 'تم التحقق من عينة تدريبية', detail: 'TRN-1046 — لا توجد بيانات حقيقية', time: 'منذ 6 دقائق', state: 'done' as const },
    { id: 'activity-2', title: 'أُحيلت نتيجة للمراجعة التدريبية', detail: 'TRN-1048 — اعتماد محاكٍ مطلوب', time: 'منذ 14 دقيقة', state: 'review' as const },
    { id: 'activity-3', title: 'أُنشئ طلب تدريبي جديد', detail: 'TRN-1049 — مسار الاستقبال', time: 'منذ 20 دقيقة', state: 'new' as const },
  ],
  safety: { verifiedSamples: 96, pendingReview: 7, auditEvents: 184 },
};

function base64url(value: string): string {
  return Buffer.from(value).toString('base64url');
}

function unbase64url(value: string): string | null {
  try {
    return Buffer.from(value, 'base64url').toString('utf8');
  } catch {
    return null;
  }
}

function signDemoPayload(payload: string): string {
  return createHmac('sha256', demoSessionSecret).update(payload).digest('base64url');
}

function createDemoToken(): string {
  const now = Date.now();
  const claims: DemoClaims = {
    environment: 'demo',
    sessionId: randomBytes(18).toString('base64url'),
    issuedAt: now,
    expiresAt: now + demoSessionLifetimeSeconds * 1000,
  };
  const encodedPayload = base64url(JSON.stringify(claims));
  return `${encodedPayload}.${signDemoPayload(encodedPayload)}`;
}

function parseCookies(header: string | undefined): Record<string, string> {
  if (!header) return {};
  return header.split(';').reduce<Record<string, string>>((cookies, pair) => {
    const separatorIndex = pair.indexOf('=');
    if (separatorIndex < 0) return cookies;
    const key = pair.slice(0, separatorIndex).trim();
    const value = pair.slice(separatorIndex + 1).trim();
    cookies[key] = value;
    return cookies;
  }, {});
}

function isDemoSessionRevoked(sessionId: string): boolean {
  const expiresAt = revokedDemoSessions.get(sessionId);
  if (!expiresAt) return false;
  if (expiresAt <= Date.now()) {
    revokedDemoSessions.delete(sessionId);
    return false;
  }
  return true;
}

function readDemoClaims(req: Request): DemoClaims | null {
  const token = parseCookies(req.headers.cookie).gula_demo;
  if (!token) return null;
  const [payload, signature] = token.split('.');
  if (!payload || !signature) return null;
  const expectedSignature = signDemoPayload(payload);
  if (signature.length !== expectedSignature.length || !timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) return null;
  const decodedPayload = unbase64url(payload);
  if (!decodedPayload) return null;
  try {
    const claims = JSON.parse(decodedPayload) as DemoClaims;
    if (claims.environment !== 'demo' || typeof claims.sessionId !== 'string' || typeof claims.expiresAt !== 'number' || claims.expiresAt <= Date.now() || isDemoSessionRevoked(claims.sessionId)) return null;
    return claims;
  } catch {
    return null;
  }
}

function setNoStoreHeaders(res: Response): void {
  res.set('Cache-Control', 'no-store, private');
  res.set('Pragma', 'no-cache');
}

function canStartDemo(requestIP: string): boolean {
  const now = Date.now();
  const current = demoAttempts.get(requestIP);
  if (!current || current.resetAt <= now) {
    demoAttempts.set(requestIP, { count: 1, resetAt: now + 60_000 });
    return true;
  }
  if (current.count >= 8) return false;
  current.count += 1;
  return true;
}

// ============================================================================
// MIDDLEWARE
// ============================================================================

// Security middleware
app.use(helmet());
app.use(compression());

// CORS configuration
app.use(cors({
  origin: allowedCorsOrigins,
  credentials: true,
  maxAge: 3600,
}));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// Request logging middleware
app.use((req: Request, res: Response, next) => {
  const startTime = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    structuredLogger.info('HTTP Request', {
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
      userAgent: req.get('user-agent'),
    });
  });
  
  next();
});

// ============================================================================
// HEALTH CHECK ENDPOINTS
// ============================================================================

// Liveness probe - is the app running?
app.get('/health/live', async (_req: Request, res: Response) => {
  res.status(200).json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  });
});

// Readiness probe - is the app ready to serve traffic?
app.get('/health/ready', async (_req: Request, res: Response) => {
  try {
    const health = await healthCheck.getFullStatus();
    
    if (health.checks.database.status !== 'ok' || health.checks.redis.status !== 'ok') {
      return res.status(503).json({
        status: 'not_ready',
        timestamp: new Date().toISOString(),
        health,
      });
    }
    
    return res.status(200).json({
      status: 'ready',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      health,
    });
  } catch (error) {
    structuredLogger.error('Health check failed', error instanceof Error ? error : undefined, { errorDetail: String(error) });
    return res.status(503).json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

// Detailed health endpoint
app.get('/health', async (_req: Request, res: Response) => {
  try {
    const health = await healthCheck.getFullStatus();
    
    const dbOk = health.checks.database.status === 'ok';
    const redisOk = health.checks.redis.status === 'ok';
    return res.status(200).json({
      status: dbOk && redisOk ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: nodeEnv,
      database: health.checks.database,
      redis: health.checks.redis,
      memory: {
        heapUsed: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`,
        heapTotal: `${Math.round(process.memoryUsage().heapTotal / 1024 / 1024)}MB`,
      },
    });
  } catch (error) {
    structuredLogger.error('Health check failed', error instanceof Error ? error : undefined, { errorDetail: String(error) });
    return res.status(503).json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

// ============================================================================
// PUBLIC STATUS & ISOLATED DEMO ENDPOINTS
// ============================================================================

// This endpoint never exposes infrastructure detail. It only backs the public UI status indicator.
app.get('/api/v1/demo/status', async (_req: Request, res: Response) => {
  setNoStoreHeaders(res);
  try {
    const health = await healthCheck.getFullStatus();
    const isHealthy = health.checks.database.status === 'ok' && health.checks.redis.status === 'ok';
    res.status(200).json({
      status: isHealthy ? 'healthy' : 'degraded',
      updatedAt: new Date().toISOString(),
      message: isHealthy ? 'الخدمات الأساسية تعمل بصورة طبيعية' : 'المنصة تعمل في وضع محدود',
    });
  } catch {
    res.status(200).json({
      status: 'unknown',
      updatedAt: new Date().toISOString(),
      message: 'يجري التحقق من حالة المنصة',
    });
  }
});

// Demo sessions are short-lived, signed, HttpOnly cookies and are intentionally isolated from clinical APIs.
app.post('/api/v1/demo/session', (req: Request, res: Response) => {
  setNoStoreHeaders(res);
  const requestIP = req.ip || 'unknown';
  if (!canStartDemo(requestIP)) {
    structuredLogger.warn('Demo session rate limit reached', { requestIP });
    return res.status(429).json({ error: 'Too many demo requests. Please wait before trying again.' });
  }

  const token = createDemoToken();
  res.cookie('gula_demo', token, demoCookieOptions);
  structuredLogger.info('Demo session created', { requestIP, environment: 'demo' });
  return res.status(201).json({ environment: 'demo', expiresInSeconds: demoSessionLifetimeSeconds });
});

app.get('/api/v1/demo/dashboard', (req: Request, res: Response) => {
  setNoStoreHeaders(res);
  const claims = readDemoClaims(req);
  if (!claims) {
    structuredLogger.warn('Rejected demo dashboard access', { requestIP: req.ip || 'unknown' });
    return res.status(401).json({ error: 'A valid demo session is required.' });
  }

  structuredLogger.info('Demo dashboard viewed', { sessionId: claims.sessionId, environment: 'demo' });
  return res.status(200).json({ ...demoDashboard, generatedAt: new Date().toISOString() });
});

app.delete('/api/v1/demo/session', (req: Request, res: Response) => {
  setNoStoreHeaders(res);
  const claims = readDemoClaims(req);
  res.clearCookie('gula_demo', demoCookieOptions);
  if (claims) {
    revokedDemoSessions.set(claims.sessionId, claims.expiresAt);
    structuredLogger.info('Demo session ended', { sessionId: claims.sessionId, environment: 'demo' });
  }
  return res.status(204).end();
});

// ============================================================================
// TEST ENDPOINTS
// ============================================================================

// Test endpoint - simple ping
app.get('/api/test/ping', (_req: Request, res: Response) => {
  res.json({
    message: 'pong',
    timestamp: new Date().toISOString(),
  });
});

// Test endpoint - echo
app.post('/api/test/echo', (req: Request, res: Response) => {
  const schema = z.object({
    message: z.string(),
  });
  
  try {
    const data = schema.parse(req.body);
    res.json({
      echo: data.message,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(400).json({
      error: 'Invalid request',
      details: error instanceof z.ZodError ? error.issues : [],
    });
  }
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({
    error: 'Not Found',
    path: req.path,
    method: req.method,
  });
});

// Global error handler
app.use((err: any, req: Request, res: Response, _next: any) => {
  structuredLogger.error('Unhandled error', err, { path: req.path, method: req.method });
  
  res.status(500).json({
    error: 'Internal Server Error',
    message: nodeEnv === 'development' ? err.message : 'An error occurred',
  });
});

// ============================================================================
// SERVER STARTUP
// ============================================================================

const server = createServer(app);

server.listen(port, () => {
  structuredLogger.info('Server started', {
    port,
    environment: nodeEnv,
    uptime: process.uptime(),
  });
  
  // Log startup info
  console.log(`
╔════════════════════════════════════════════════════════════╗
║          GULA Platform - Backend Server                    ║
╠════════════════════════════════════════════════════════════╣
║  Environment: ${nodeEnv.padEnd(45)}║
║  Port: ${String(port).padEnd(51)}║
║  Uptime: ${process.uptime().toFixed(2).padEnd(48)}║
║  Timestamp: ${new Date().toISOString().padEnd(42)}║
╚════════════════════════════════════════════════════════════╝

Health Checks:
  - Liveness:  GET /health/live
  - Readiness: GET /health/ready
  - Full:      GET /health

Test Endpoints:
  - Ping:      GET /api/test/ping
  - Echo:      POST /api/test/echo

Ready to serve requests ✓
  `);
});

// ============================================================================
// GRACEFUL SHUTDOWN
// ============================================================================

const gracefulShutdown = async () => {
  structuredLogger.info('Graceful shutdown initiated');
  
  server.close(() => {
    structuredLogger.info('Server closed');
    process.exit(0);
  });
  
  // Force shutdown after 30 seconds
  setTimeout(() => {
    structuredLogger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000);
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// ============================================================================
// UNHANDLED REJECTION HANDLING
// ============================================================================

process.on('unhandledRejection', (reason: any) => {
  const err = reason instanceof Error ? reason : new Error(String(reason));
  structuredLogger.error('Unhandled Rejection', err, { reasonDetail: String(reason) });
});

process.on('uncaughtException', (error: Error) => {
  structuredLogger.error('Uncaught Exception', error, { errorMessage: error.message, errorStack: error.stack });
  process.exit(1);
});

export default app;
