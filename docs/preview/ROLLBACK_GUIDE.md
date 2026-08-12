# GULA Preview Environment — Rollback Guide

## When to Rollback

Rollback is required when:
- Build fails validation checks
- Feature breaks core functionality
- Security vulnerability detected
- Incorrect configuration deployed
- UI rendering breaks in production browsers

## Rollback Methods

### Method 1: GitHub Actions (Recommended)

1. Navigate to GitHub → Actions → Rollback
2. Click "Run workflow"
3. Select environment:
   - `preview` — Rollback preview deployment
   - `production` — Rollback production deployment
4. Optionally specify a deployment ID
5. Click "Run workflow"

### Method 2: Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com)
2. Select the GULA project
3. Click "Deployments" tab
4. Find the deployment to rollback to
5. Click "..." → "Promote to Production" (or "Promote to Preview")

### Method 3: Vercel CLI

```bash
# List recent deployments
vercel list

# Rollback to specific deployment
vercel rollback <deployment-id>

# Rollback to previous production deployment
vercel rollback
```

## Automatic Rollback Triggers

The CI pipeline triggers automatic build validation. If any check fails:

1. **Build failure** → Deployment is cancelled
2. **TypeScript errors** → Blocked from deploying
3. **Security scan positive** → Blocked with notification

## Recovery Steps

### If Preview is Broken:
```bash
# 1. Identify the last working deployment
vercel list

# 2. Rollback to it
vercel rollback dep_abc123

# 3. Verify fix
curl https://preview.gula-platform.org/api/health
```

### If Environment Variables are Corrupted:
1. Go to Vercel → Project Settings → Environment Variables
2. Restore from `.env.example` template
3. Redeploy

### If Build Cache is Corrupted:
1. Vercel → Project Settings → Build Cache
2. Click "Clear Build Cache"
3. Trigger new deployment

## Post-Rollback Verification

- [ ] All pages load (dashboard, patients, labs, etc.)
- [ ] Authentication works
- [ ] Mock data renders
- [ ] No console errors
- [ ] RTL works correctly
- [ ] Dark mode renders

## Preventing Future Rollbacks

1. Always test on preview before merging to main
2. Review CI build output before deployment
3. Use feature flags for risky changes
4. Run QA checklist before production promotion
