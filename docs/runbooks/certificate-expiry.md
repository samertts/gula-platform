# Runbook: Certificate Expiry

**Severity:** SEV3 (warning at 30d) / SEV2 (warning at 7d) / SEV1 (expired)
**Response Time:** <2h (warning) / <15min (expired)
**Last Updated:** 2026-07-15

---

## Symptoms

- TLS errors in browser: "NET::ERR_CERT_DATE_INVALID" or "Your connection is not private"
- API clients return certificate errors
- `curl -I https://api.gula.health` returns SSL certificate error
- Monitoring alert: `TLSCertExpiry` or `CertExpiryCritical`
- Users cannot access the platform

## Quick Checks

```bash
# 1. Check certificate expiry for all domains
echo | openssl s_client -connect api.gula.health:443 -servername api.gula.health 2>/dev/null | openssl x509 -noout -enddate
echo | openssl s_client -connect app.gula.health:443 -servername app.gula.health 2>/dev/null | openssl x509 -noout -enddate

# 2. Check cert-manager status (K8s)
kubectl get certificates -n gula-platform
kubectl describe certificate gula-api-tls -n gula-platform

# 3. Check certbot status (Docker)
certbot certificates

# 4. Check CAA DNS record
dig CAA gula.health
```

## Certificate Inventory

| Domain | Provider | Expiry | Managed By | Location |
|--------|----------|--------|------------|----------|
| `api.gula.health` | Let's Encrypt | — | cert-manager/certbot | Host Nginx |
| `app.gula.health` | Cloudflare Edge | — | Cloudflare auto | Cloudflare |
| `*.gula.health` | Cloudflare Edge | — | Cloudflare auto | Cloudflare |
| Internal mTLS | Linkerd | 24h | Linkerd auto | Linkerd |

## Possible Causes & Fixes

### Cause 1: Cert-Manager Renewal Failed (K8s)

**Symptoms:** Certificate status shows "Not Ready", order failed

**Check:**
```bash
kubectl describe certificate gula-api-tls -n gula-platform
kubectl describe certificaterequest -n gula-platform | tail -20
kubectl get challenges -n gula-platform
kubectl describe order -n gula-platform
```

**Fix:**
```bash
# 1. Check if DNS is properly configured for HTTP-01 challenge
kubectl get ingress -n gula-platform

# 2. Force re-issue
kubectl delete certificaterequest -n gula-platform --all
kubectl annotate certificate gula-api-tls -n gula-platform \
  cert-manager.io/issue-temporary-certificate="true"

# 3. Manual certificate creation if auto-renewal fails
kubectl create secret tls gula-api-tls-manual \
  --cert=/path/to/cert.pem \
  --key=/path/to/key.pem \
  -n gula-platform
```

### Cause 2: Certbot Renewal Failed (Docker)

**Symptoms:** `certbot certificates` shows expiring, renewal log shows errors

**Check:**
```bash
# Check renewal log
cat /var/log/letsencrypt/letsencrypt.log | tail -50

# Check certbot timer
systemctl status certbot.timer
systemctl list-timers certbot.timer

# Dry run
certbot renew --dry-run
```

**Fix:**
```bash
# 1. Force renewal
certbot renew --force-renewal

# 2. If DNS issue, verify DNS records
dig +short api.gula.health
# Should resolve to server IP

# 3. If port 80 issue, ensure nginx is serving HTTP-01 challenge
# Check nginx config for:
# location /.well-known/acme-challenge/ {
#     root /var/www/html;
# }

# 4. Restart certbot timer
systemctl restart certbot.timer

# 5. Reload nginx with new cert
nginx -s reload
```

### Cause 3: ACME Rate Limited

**Symptoms:** "too many certificates already issued", "rate limit exceeded"

**Check:**
```bash
# Check ACME rate limit status
curl -s https://letsencrypt.org/rate-limits/
```

**Fix:**
```bash
# Option A: Wait for rate limit to reset (usually 1 week for duplicates)
# Option B: Request certificate for different domains
# Option C: Use staging environment for testing
certbot --staging renew

# If urgent, manually provision from another CA (e.g., ZeroSSL)
certbot --server https://acme.zerossl.com/v2/DV90 -d api.gula.health --manual
```

### Cause 4: DNS Resolution Failure

**Symptoms:** ACME challenge fails with "DNS problem: NXDOMAIN"

**Check:**
```bash
dig api.gula.health
dig -x <server-ip>
```

**Fix:**
```bash
# 1. Verify DNS records in Cloudflare dashboard
# 2. Check TTL propagation
dig api.gula.health +short
# 3. Ensure A/AAAA record points to correct IP
# 4. If Cloudflare proxy is on, ensure it's compatible with ACME
```

### Cause 5: Certificate Already Expired

**Symptoms:** Users cannot access, all certificate checks fail

**Fix:**
```bash
# Emergency: Issue temporary self-signed certificate
# (Only if you have physical access to the server)

# On the server:
openssl req -x509 -nodes -days 7 -newkey rsa:4096 \
  -keyout /etc/ssl/private/gula-temp.key \
  -out /etc/ssl/certs/gula-temp.pem \
  -subj "/CN=api.gula.health"

# Update nginx config
# ssl_certificate /etc/ssl/certs/gula-temp.pem;
# ssl_certificate_key /etc/ssl/private/gula-temp.key;
nginx -s reload

# Then fix certbot/cert-manager and issue proper certificate
certbot certonly --nginx -d api.gula.health
```

## Resolution Verification

```bash
# 1. Check new certificate expiry
echo | openssl s_client -connect api.gula.health:443 -servername api.gula.health 2>/dev/null | openssl x509 -noout -enddate

# 2. Verify the certificate chain
echo | openssl s_client -connect api.gula.health:443 -servername api.gula.health 2>/dev/null | openssl x509 -noout -issuer -subject

# 3. Test HTTPS
curl -I https://api.gula.health

# 4. Verify HSTS header
curl -sI https://api.gula.health | grep -i strict-transport-security

# 5. Check OCSP
openssl ocsp -url http://ocsp.int-x3.letsencrypt.org \
  -issuer /etc/letsencrypt/live/api.gula.health/chain.pem \
  -cert /etc/letsencrypt/live/api.gula.health/cert.pem
```

## Escalation

| Scenario | Response Time | Action |
|----------|--------------|--------|
| Warning (>30d) | Next sprint | Create ticket for renewal |
| Warning (<30d) | <24h | Investigate auto-renewal issue |
| Warning (<7d) | <2h | Manual renewal, escalate if fails |
| Expired | <15min | Emergency cert, declare SEV1 |

## Prevention

- [ ] Monitor cert expiry with alert at 30d, 14d, 7d, 1d
- [ ] Configure auto-renewal with proper monitoring
- [ ] Test renewal process monthly (dry-run)
- [ ] Keep cert-manager/certbot updated
- [ ] Document DNS provider API access
- [ ] Have backup CA configured (ZeroSSL as fallback)
- [ ] Monitor Let's Encrypt rate limits
- [ ] Use staging environment for testing renewals
