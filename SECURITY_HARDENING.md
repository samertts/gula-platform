# GULA Platform - Security Hardening Guide

## 🔒 Comprehensive Security Implementation

This guide provides production-grade security hardening for GULA Platform.

---

## 1. Security Headers Configuration

### 1.1 Nginx Security Headers

```nginx
# /etc/nginx/conf.d/security-headers.conf

# Strict Transport Security
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';" always;

# X-Frame-Options (Clickjacking Protection)
add_header X-Frame-Options "SAMEORIGIN" always;

# X-Content-Type-Options (MIME Sniffing Protection)
add_header X-Content-Type-Options "nosniff" always;

# X-XSS-Protection
add_header X-XSS-Protection "1; mode=block" always;

# Referrer-Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions-Policy
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

---

## 2. CORS Configuration

### 2.1 Strict CORS Policy

```typescript
// server/_core/cors.ts

const corsOptions = {
  origin: process.env.CORS_ORIGINS?.split(',') || ['https://gula-platform.org'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  exposedHeaders: ['X-Total-Count', 'X-Page-Number'],
  maxAge: 3600,
  preflightContinue: false,
  optionsSuccessStatus: 200,
};

app.use(cors(corsOptions));
```

---

## 3. Input Validation & Sanitization

### 3.1 Request Validation

```typescript
// server/utils/validation.ts

import { z } from 'zod';

export const patientSchema = z.object({
  nationalId: z.string().regex(/^\d{11}$/, 'Invalid national ID format'),
  firstName: z.string().min(2).max(50),
  lastName: z.string().min(2).max(50),
  email: z.string().email(),
  phone: z.string().regex(/^\+?[\d\s-()]{10,}$/, 'Invalid phone number'),
  dateOfBirth: z.date(),
});

// Usage in tRPC
createPatient: protectedProcedure
  .input(patientSchema)
  .mutation(async ({ input }) => {
    // Input is validated and type-safe
  }),
```

---

## 4. Authentication & Authorization

### 4.1 JWT Token Security

```typescript
// server/utils/jwt.ts

const jwtOptions = {
  algorithm: 'HS256',
  expiresIn: '15m', // Short-lived tokens
  issuer: 'gula-platform',
  audience: 'gula-platform-users',
};

const refreshTokenOptions = {
  expiresIn: '7d', // Longer expiry for refresh tokens
};
```

### 4.2 Role-Based Access Control

```typescript
// server/utils/rbac.ts

export const adminProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (ctx.user?.role !== 'admin') {
    throw new TRPCError({ code: 'FORBIDDEN' });
  }
  return next({ ctx });
});

export const doctorProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (!['admin', 'doctor'].includes(ctx.user?.role || '')) {
    throw new TRPCError({ code: 'FORBIDDEN' });
  }
  return next({ ctx });
});
```

---

## 5. Encryption & Data Protection

### 5.1 Data Encryption

```typescript
// server/utils/encryption.ts

import crypto from 'crypto';

export function encryptSensitiveData(data: string, key: string): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
  
  let encrypted = cipher.update(data, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  return `${iv.toString('hex')}:${encrypted}:${authTag.toString('hex')}`;
}

export function decryptSensitiveData(encrypted: string, key: string): string {
  const [iv, data, authTag] = encrypted.split(':');
  const decipher = crypto.createDecipheriv(
    'aes-256-gcm',
    Buffer.from(key, 'hex'),
    Buffer.from(iv, 'hex')
  );
  
  decipher.setAuthTag(Buffer.from(authTag, 'hex'));
  let decrypted = decipher.update(data, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}
```

---

## 6. Database Security

### 6.1 SQL Injection Prevention

```typescript
// Always use parameterized queries with Drizzle ORM

// ✅ SAFE - Using Drizzle ORM
const patient = await db.select()
  .from(patients)
  .where(eq(patients.nationalId, nationalId))
  .limit(1);

// ❌ UNSAFE - Never do this
const query = `SELECT * FROM patients WHERE national_id = '${nationalId}'`;
```

### 6.2 Database User Permissions

```sql
-- Create limited database user
CREATE USER 'gula_user'@'localhost' IDENTIFIED BY 'strong_password';

-- Grant only necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON gula_platform.* TO 'gula_user'@'localhost';

-- Revoke dangerous permissions
REVOKE ALL PRIVILEGES ON *.* FROM 'gula_user'@'localhost';
REVOKE GRANT OPTION ON *.* FROM 'gula_user'@'localhost';
```

---

## 7. API Security

### 7.1 Rate Limiting

```typescript
// Already implemented in advancedRateLimiter.ts

// Per IP: 50 requests/minute
// Per User: 100 requests/minute
// Per Endpoint: 1000 requests/minute
// Login Attempts: 5 attempts/minute
```

### 7.2 API Key Management

```typescript
// server/utils/apiKey.ts

export function generateApiKey(): string {
  return crypto.randomBytes(32).toString('hex');
}

export function hashApiKey(apiKey: string): string {
  return crypto.createHash('sha256').update(apiKey).digest('hex');
}

export async function validateApiKey(apiKey: string): Promise<boolean> {
  const hashedKey = hashApiKey(apiKey);
  const key = await db.select()
    .from(apiKeys)
    .where(eq(apiKeys.hash, hashedKey))
    .limit(1);
  
  return key.length > 0;
}
```

---

## 8. Session Security

### 8.1 Session Configuration

```typescript
// server/_core/cookies.ts

export const sessionOptions = {
  name: 'gula_session',
  secret: process.env.JWT_SECRET,
  cookie: {
    secure: true, // HTTPS only
    httpOnly: true, // No JavaScript access
    sameSite: 'strict', // CSRF protection
    maxAge: 15 * 60 * 1000, // 15 minutes
    domain: 'gula-platform.org',
    path: '/',
  },
};
```

---

## 9. File Upload Security

### 9.1 File Validation

```typescript
// server/utils/fileUpload.ts

const ALLOWED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png'];
const MAX_FILE_SIZE = 52428800; // 50MB

export async function validateFile(file: Express.Multer.File): Promise<void> {
  // Check MIME type
  if (!ALLOWED_MIME_TYPES.includes(file.mimetype)) {
    throw new Error('Invalid file type');
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    throw new Error('File too large');
  }

  // Scan for viruses (integrate with ClamAV or similar)
  await scanFileForViruses(file.path);

  // Validate file content
  await validateFileContent(file.path);
}
```

---

## 10. Logging & Monitoring

### 10.1 Security Event Logging

```typescript
// server/utils/securityLogger.ts

export async function logSecurityEvent(
  event: string,
  severity: 'low' | 'medium' | 'high' | 'critical',
  userId?: string,
  details?: Record<string, any>
): Promise<void> {
  const logEntry = {
    timestamp: new Date(),
    event,
    severity,
    userId,
    details,
    ip: getClientIp(),
    userAgent: getUserAgent(),
  };

  // Log to database
  await db.insert(securityLogs).values(logEntry);

  // Alert if critical
  if (severity === 'critical') {
    await sendSecurityAlert(logEntry);
  }
}
```

---

## 11. Dependency Security

### 11.1 Dependency Scanning

```bash
# Check for vulnerabilities
npm audit
npm audit fix

# Use npm audit in CI/CD
npm audit --audit-level=moderate
```

---

## 12. Environment Security

### 12.1 Secrets Management

```bash
# Never commit secrets
echo ".env.production" >> .gitignore
echo ".env.local" >> .gitignore

# Use environment variables
export JWT_SECRET=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -hex 16)
```

---

## 13. SSL/TLS Configuration

### 13.1 SSL Certificate

```bash
# Generate SSL certificate
certbot certonly --nginx -d gula-platform.org -d www.gula-platform.org

# Auto-renewal
certbot renew --dry-run
```

### 13.2 SSL Configuration

```nginx
# /etc/nginx/conf.d/ssl.conf

server {
    listen 443 ssl http2;
    server_name gula-platform.org www.gula-platform.org;

    ssl_certificate /etc/letsencrypt/live/gula-platform.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gula-platform.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

---

## 14. Security Checklist

- [x] Security headers configured
- [x] CORS properly restricted
- [x] Input validation implemented
- [x] Authentication & authorization enforced
- [x] Data encryption enabled
- [x] Database security hardened
- [x] API rate limiting active
- [x] Session security configured
- [x] File upload validation
- [x] Security logging enabled
- [x] Dependencies scanned
- [x] Secrets management implemented
- [x] SSL/TLS configured
- [x] Firewall rules applied
- [x] Regular security audits scheduled

---

## 15. Regular Security Maintenance

### 15.1 Weekly Tasks

```bash
# Check for security updates
npm audit

# Review security logs
grep "CRITICAL\|HIGH" /var/log/gula-security.log
```

### 15.2 Monthly Tasks

```bash
# Full security audit
npm audit fix

# Penetration testing
# Review access logs for suspicious activity
# Update security policies
```

### 15.3 Quarterly Tasks

```bash
# Full security assessment
# Update SSL certificates
# Review and update firewall rules
# Conduct security training
```

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Express.js Security](https://expressjs.com/en/advanced/best-practice-security.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
