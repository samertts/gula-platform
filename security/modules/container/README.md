# GSF-005: Container Security Module

Analyzes Docker, Docker Compose, and containerized service security configurations.

## Components

### DockerSecurityManager
- Dockerfile best practices checking (DL3000-series rules)
- Privilege escalation detection
- Capability auditing
- User namespace validation
- Secret scanning in Dockerfiles/build args

### ComposeSecurityManager
- Network isolation validation
- Volume mount security (read-only enforcement)
- Environment variable secrets detection
- Port exposure analysis (0.0.0.0 bindings)
- Restart policy validation

### RedisSecurityManager
- requirepass, rename-command, protected-mode validation
- ACL configuration checks
- TLS enforcement
- Eviction policy security review

### RabbitMQSecurityManager
- Default credential detection
- VHost isolation and permission auditing
- Authentication mechanism validation (SCRAM vs PLAIN)
- Shovel/federation TLS checks

### PostgreSQLSecurityManager
- pg_hba.conf authentication method analysis
- SSL/TLS configuration validation
- pgaudit and logging configuration
- Password policy enforcement
- Row-level security validation

### NginxSecurityManager
- Server tokens hiding
- TLS protocols and ciphers validation
- HSTS, rate limiting, access control
- Security headers (CSP, X-Frame-Options, etc.)
