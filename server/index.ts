import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { createServer } from 'http';
import { z } from 'zod';
import { structuredLogger } from './utils/structuredLogger';
import { healthChecker as healthCheck } from './utils/healthCheck';

const app: Express = express();
const port = process.env.PORT || 3000;
const nodeEnv = process.env.NODE_ENV || 'development';

// ============================================================================
// MIDDLEWARE
// ============================================================================

// Security middleware
app.use(helmet());
app.use(compression());

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGINS?.split(',') || '*',
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
