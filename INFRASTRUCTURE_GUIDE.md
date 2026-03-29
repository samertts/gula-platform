# GULA Platform - Infrastructure & Deployment Guide

## 🏗️ Infrastructure Architecture

### Production Environment Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet / CDN                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Balancer  │
                    │   (Nginx/HAProxy)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼───┐            ┌───▼───┐            ┌──▼───┐
    │ App 1 │            │ App 2 │            │ App 3│
    │(Node) │            │(Node) │            │(Node)│
    └───┬───┘            └───┬───┘            └──┬───┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼─────────┐   ┌─────▼──────┐   ┌────────▼──┐
    │  MySQL      │   │   Redis    │   │ S3/Storage│
    │  Primary    │   │   Cache    │   │           │
    └─────────────┘   └────────────┘   └───────────┘
        │
    ┌───▼─────────┐
    │  MySQL      │
    │  Replica    │
    └─────────────┘
```

### High Availability Setup

**Multi-Region Deployment:**

```
Region 1 (Primary)          Region 2 (Backup)
┌──────────────────┐        ┌──────────────────┐
│  Load Balancer   │        │  Load Balancer   │
│  ┌────────────┐  │        │  ┌────────────┐  │
│  │ App Servers│  │        │  │ App Servers│  │
│  └────────────┘  │        │  └────────────┘  │
│  ┌────────────┐  │        │  ┌────────────┐  │
│  │ MySQL      │  │◄──────►│  │ MySQL      │  │
│  │ Primary    │  │        │  │ Replica    │  │
│  └────────────┘  │        │  └────────────┘  │
│  ┌────────────┐  │        │  ┌────────────┐  │
│  │ Redis      │  │        │  │ Redis      │  │
│  │ Primary    │  │◄──────►│  │ Replica    │  │
│  └────────────┘  │        │  └────────────┘  │
└──────────────────┘        └──────────────────┘
```

---

## 🖥️ Server Requirements

### Development Server
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Storage:** 50 GB SSD
- **Bandwidth:** 10 Mbps
- **OS:** Ubuntu 22.04 LTS

### Production Server (Single)
- **CPU:** 8 cores
- **RAM:** 32 GB
- **Storage:** 500 GB SSD
- **Bandwidth:** 100 Mbps
- **OS:** Ubuntu 22.04 LTS

### Production Cluster (3 nodes)
- **Per Node CPU:** 16 cores
- **Per Node RAM:** 64 GB
- **Per Node Storage:** 1 TB SSD
- **Total Bandwidth:** 1 Gbps
- **Load Balancer:** Dedicated hardware or cloud LB

---

## 📋 Installation Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  curl \
  wget \
  git \
  build-essential \
  python3 \
  nodejs \
  npm \
  mysql-server \
  redis-server \
  nginx \
  certbot \
  python3-certbot-nginx

# Install Node.js 22 (LTS)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Install pnpm
npm install -g pnpm

# Verify installations
node --version
pnpm --version
mysql --version
redis-cli --version
```

### 2. Database Setup

```bash
# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Create database and user
sudo mysql -u root << EOF
CREATE DATABASE gula_platform;
CREATE USER 'gula_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON gula_platform.* TO 'gula_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis
redis-cli ping
```

### 3. Application Setup

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/samertts/gula-platform.git
cd gula-platform

# Set permissions
sudo chown -R $USER:$USER /opt/gula-platform

# Install dependencies
pnpm install

# Setup environment
cp .env.example .env
# Edit .env with production values
nano .env

# Run migrations
pnpm run db:migrate

# Seed data
pnpm run db:seed

# Build application
pnpm run build

# Verify build
ls -la dist/
```

### 4. Nginx Configuration

```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/gula-platform > /dev/null << EOF
upstream gula_backend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
    server 127.0.0.1:3002;
    keepalive 32;
}

server {
    listen 80;
    server_name gula-platform.com www.gula-platform.com;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name gula-platform.com www.gula-platform.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/gula-platform.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gula-platform.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1000;
    
    # Proxy settings
    location / {
        proxy_pass http://gula_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/gula-platform /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 5. SSL Certificate Setup

```bash
# Install SSL certificate with Certbot
sudo certbot certonly --nginx -d gula-platform.com -d www.gula-platform.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

### 6. Process Management (PM2)

```bash
# Install PM2
sudo npm install -g pm2

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'gula-platform-1',
      script: 'dist/index.js',
      instances: 1,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    },
    {
      name: 'gula-platform-2',
      script: 'dist/index.js',
      instances: 1,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3001
      }
    },
    {
      name: 'gula-platform-3',
      script: 'dist/index.js',
      instances: 1,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3002
      }
    }
  ]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js

# Setup auto-restart on reboot
pm2 startup
pm2 save

# Monitor
pm2 monit
```

---

## 🔐 Security Configuration

### Firewall Setup

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MySQL (internal only)
sudo ufw allow from 127.0.0.1 to any port 3306

# Allow Redis (internal only)
sudo ufw allow from 127.0.0.1 to any port 6379

# Verify rules
sudo ufw status
```

### Database Security

```bash
# Secure MySQL
sudo mysql_secure_installation

# Create backup user
sudo mysql -u root << EOF
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'backup_password';
GRANT SELECT, LOCK TABLES ON gula_platform.* TO 'backup_user'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### Application Security

```bash
# Set environment variables
export NODE_ENV=production
export JWT_SECRET=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)

# Verify security headers
curl -I https://gula-platform.com

# Check SSL rating
# Visit: https://www.ssllabs.com/ssltest/
```

---

## 📊 Monitoring & Logging

### Prometheus Setup

```bash
# Install Prometheus
sudo apt install -y prometheus

# Configure Prometheus
sudo tee /etc/prometheus/prometheus.yml > /dev/null << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gula-platform'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Start Prometheus
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

### Grafana Setup

```bash
# Install Grafana
sudo apt install -y grafana-server

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access at http://localhost:3000
# Default credentials: admin/admin
```

### Log Aggregation

```bash
# Install ELK Stack or use cloud solution
# Option 1: Self-hosted ELK
sudo apt install -y elasticsearch kibana logstash

# Option 2: Cloud solutions
# - Datadog
# - New Relic
# - Splunk
# - CloudWatch (AWS)
```

---

## 💾 Backup & Recovery

### Automated Backups

```bash
# Create backup script
cat > /opt/gula-platform/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/backups/gula-platform"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u gula_user -p$DB_PASSWORD gula_platform | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /opt/gula-platform

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/ s3://gula-backups/ --recursive

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

# Make executable
chmod +x /opt/gula-platform/backup.sh

# Schedule with cron (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/gula-platform/backup.sh") | crontab -
```

### Recovery Procedure

```bash
# Restore database
gunzip < /backups/gula-platform/db_20260329_020000.sql.gz | mysql -u gula_user -p$DB_PASSWORD gula_platform

# Restore application
cd /opt
tar -xzf /backups/gula-platform/app_20260329_020000.tar.gz

# Restart application
pm2 restart all
```

---

## 🚀 Deployment Checklist

- [ ] Server provisioned and configured
- [ ] Database initialized and secured
- [ ] Application built and tested
- [ ] Nginx configured with SSL
- [ ] PM2 process manager running
- [ ] Firewall configured
- [ ] Monitoring tools installed
- [ ] Backup system configured
- [ ] DNS records updated
- [ ] SSL certificate installed
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Disaster recovery tested
- [ ] Documentation updated
- [ ] Team trained

---

## 📞 Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check logs
pm2 logs gula-platform-1

# Check port availability
netstat -tlnp | grep 3000

# Check Node version
node --version
```

**Database connection error:**
```bash
# Test MySQL connection
mysql -u gula_user -p -h localhost gula_platform

# Check MySQL service
sudo systemctl status mysql
```

**SSL certificate issues:**
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal

# Check Nginx SSL
sudo nginx -t
```

---

**Last Updated:** March 29, 2026
**Version:** 1.0.0
