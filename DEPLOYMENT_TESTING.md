# GULA Platform - Deployment & Testing Guide

## Quick Start

### 1. Local Development with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps

# Stop all services
docker-compose down
```

### 2. Health Checks

```bash
# Liveness check (is the app running?)
curl http://localhost:3000/health/live

# Readiness check (is the app ready to serve traffic?)
curl http://localhost:3000/health/ready

# Full health status
curl http://localhost:3000/health
```

### 3. API Testing

#### Run full test suite
```bash
bash scripts/test-api.sh http://localhost:3000
```

#### Individual endpoint tests

**Ping test:**
```bash
curl http://localhost:3000/api/test/ping
```

**Echo test:**
```bash
curl -X POST http://localhost:3000/api/test/echo \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello GULA"}'
```

#### Create patient
```bash
curl -X POST http://localhost:3000/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "أحمد محمد",
    "email": "ahmed@example.com",
    "phone": "+964771234567",
    "nationalId": "12345678901234",
    "dateOfBirth": "1990-01-15",
    "gender": "M",
    "address": "بغداد، العراق"
  }'
```

#### Create sample
```bash
curl -X POST http://localhost:3000/api/samples \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "patient-123",
    "sampleType": "blood",
    "collectionDate": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "volume": "5ml",
    "notes": "Routine blood test"
  }'
```

#### Create result
```bash
curl -X POST http://localhost:3000/api/results \
  -H "Content-Type: application/json" \
  -d '{
    "sampleId": "sample-123",
    "testType": "blood_count",
    "values": {
      "wbc": 7.5,
      "rbc": 4.8,
      "hemoglobin": 14.2,
      "hematocrit": 42.5
    },
    "referenceRange": {
      "wbc": "4.5-11.0",
      "rbc": "4.5-5.5",
      "hemoglobin": "13.5-17.5",
      "hematocrit": "41-53"
    },
    "status": "normal"
  }'
```

#### Generate report
```bash
curl -X POST http://localhost:3000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patientId": "patient-123",
    "resultIds": ["result-123"],
    "format": "pdf"
  }'
```

---

## Load Testing

### With Apache Bench (100 concurrent users)

```bash
# Install Apache Bench (if not installed)
sudo apt-get install apache2-utils

# Run load test
bash scripts/load-test.sh http://localhost:3000 100 60
```

### Manual load test with wrk (if installed)

```bash
# Install wrk
sudo apt-get install wrk

# Run 4 threads, 100 connections for 60 seconds
wrk -t4 -c100 -d60s http://localhost:3000/health
```

### With Apache Bench - Detailed

```bash
# 1000 requests, 100 concurrent
ab -n 1000 -c 100 http://localhost:3000/health

# With output file
ab -n 1000 -c 100 -g /tmp/results.tsv http://localhost:3000/health

# POST request
ab -n 1000 -c 100 -p payload.json -T application/json http://localhost:3000/api/test/echo
```

---

## Monitoring

### Docker Compose Monitoring

```bash
# View real-time stats
docker stats

# View logs for specific service
docker-compose logs -f app

# View logs with timestamps
docker-compose logs -f --timestamps app

# View last 100 lines
docker-compose logs --tail=100 app
```

### Health Check Monitoring

```bash
# Continuous health monitoring
watch -n 5 'curl -s http://localhost:3000/health | jq'

# With timestamps
watch -n 5 'echo "=== $(date) ===" && curl -s http://localhost:3000/health | jq'
```

### Database Monitoring

```bash
# Connect to MySQL
docker-compose exec mysql mysql -u gula_user -p gula_platform

# Check connections
SHOW PROCESSLIST;

# Check database size
SELECT table_schema, ROUND(SUM(data_length+index_length)/1024/1024,2) AS size_mb 
FROM information_schema.tables 
GROUP BY table_schema;
```

### Redis Monitoring

```bash
# Connect to Redis
docker-compose exec redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d= -f2)

# Check memory
INFO memory

# Check keys
DBSIZE

# Monitor commands
MONITOR
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs app

# Check if port is in use
lsof -i :3000

# Rebuild container
docker-compose build --no-cache app
```

### Database connection issues

```bash
# Check MySQL is running
docker-compose ps mysql

# Test connection
docker-compose exec mysql mysql -u gula_user -p -e "SELECT 1"

# Check connection pool
docker-compose exec mysql mysql -u gula_user -p -e "SHOW PROCESSLIST"
```

### Redis connection issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Check memory usage
docker-compose exec redis redis-cli INFO memory
```

### Memory leaks

```bash
# Monitor memory usage
docker stats --no-stream

# Check Node.js heap
curl http://localhost:3000/health | jq '.memory'

# If memory keeps growing, check logs for errors
docker-compose logs app | grep -i error
```

---

## Performance Optimization

### Database Query Optimization

```bash
# Enable slow query log
docker-compose exec mysql mysql -u gula_user -p -e "SET GLOBAL slow_query_log = 'ON';"

# View slow queries
docker-compose exec mysql mysql -u gula_user -p -e "SELECT * FROM mysql.slow_log;"
```

### Redis Cache Optimization

```bash
# Check cache hit rate
docker-compose exec redis redis-cli INFO stats

# Monitor cache operations
docker-compose exec redis redis-cli MONITOR
```

### Connection Pool Tuning

Edit `.env`:
```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
REDIS_POOL_SIZE=10
```

---

## Production Deployment

### DigitalOcean Droplet Setup

```bash
# 1. Create droplet (Ubuntu 22.04, 2GB RAM minimum)
# 2. SSH into droplet
ssh root@your_droplet_ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Clone repository
git clone https://github.com/samertts/gula-platform.git
cd gula-platform

# 6. Setup environment
cp .env.example .env
# Edit .env with production values

# 7. Start services
docker-compose up -d

# 8. Verify health
curl http://localhost:3000/health
```

### SSL/TLS Setup

```bash
# Using Let's Encrypt with Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d gula-platform.com

# Update nginx config with certificate paths
# Restart nginx
docker-compose restart nginx
```

### Monitoring in Production

```bash
# Enable monitoring services
docker-compose --profile monitoring up -d

# Access Grafana
# http://your_server:3000 (default: admin/changeme_grafana)

# Access Prometheus
# http://your_server:9090
```

---

## Backup and Recovery

### Backup Database

```bash
# Manual backup
docker-compose exec mysql mysqldump -u gula_user -p gula_platform > backup.sql

# Automated backup (daily at 2 AM)
# Add to crontab: 0 2 * * * docker-compose exec mysql mysqldump -u gula_user -p gula_platform > /backups/db_$(date +\%Y\%m\%d).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T mysql mysql -u gula_user -p gula_platform < backup.sql
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

```bash
# Scale app service to 3 instances
docker-compose up -d --scale app=3

# Load balance with nginx (already configured)
```

### Vertical Scaling (Increase Resources)

Edit `docker-compose.yml`:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Enable SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable database backups
- [ ] Setup monitoring and alerts
- [ ] Enable audit logging
- [ ] Setup rate limiting
- [ ] Enable CORS restrictions
- [ ] Setup API authentication
- [ ] Enable database encryption

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Run health check: `curl http://localhost:3000/health`
3. Check GitHub issues: https://github.com/samertts/gula-platform/issues
4. Contact support: support@gula-platform.com
