# GULA Preview Environment — Deployment Guide

## Overview

The GULA Preview Environment provides automated Vercel deployments for every branch and pull request. Each deployment is completely isolated from production and uses only synthetic data.

## Architecture

```
Git Push → GitHub Actions → Vercel Build → Preview URL
                                     ↓
                          Mock Backend (in-browser)
                          Synthetic Data Store
                          Demo Authentication
```

## Vercel Setup

### 1. Create Vercel Project

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Link project
cd frontend-v2
vercel link
```

### 2. Configure Environment Variables

In Vercel dashboard → Project Settings → Environment Variables:

**Preview Environment:**
| Variable | Value |
|----------|-------|
| `VITE_APP_ENV` | `preview` |
| `VITE_USE_MOCK` | `true` |
| `VITE_DEMO_MODE` | `true` |
| `VITE_TELEMETRY_DISABLED` | `true` |

**Production Environment (placeholder):**
| Variable | Value |
|----------|-------|
| `VITE_APP_ENV` | `production` |
| `VITE_USE_MOCK` | `false` |
| `VITE_DEMO_MODE` | `false` |

### 3. GitHub Integration

Add these secrets to GitHub repository → Settings → Secrets → Actions:

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel API token (from Account → Settings → Tokens) |
| `VERCEL_ORG_ID` | Vercel organization ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |

### 4. Custom Domain (Optional)

```bash
vercel domains add preview.gula-platform.org
```

## Automatic Deployments

### Pull Request Deployments

When a PR is opened against `main` or `develop`:
1. Build validation runs (lint → TypeScript check → build)
2. Vercel Preview deployment starts
3. Preview URL is posted as a PR comment
4. QA checks run (bundle size, secret scanning)

### Branch Deployments

Pushes to `develop` and `preview` branches trigger automatic deployments.

## Manual Deployment

```bash
# Deploy preview
vercel --env VITE_APP_ENV=preview --env VITE_USE_MOCK=true --env VITE_DEMO_MODE=true

# Promote to production alias
vercel --prod
```

## Rollback

### Via GitHub Actions
1. Go to Actions → Rollback → Run workflow
2. Select environment (`preview` or `production`)
3. Optionally specify a deployment ID

### Via Vercel CLI
```bash
# List deployments
vercel list

# Rollback to specific deployment
vercel rollback <deployment-id>
```

## Environment Isolation

| Aspect | Preview | Production |
|--------|---------|------------|
| Data | Synthetic only | Real patient data |
| Auth | Demo accounts | Firebase Auth |
| Backend | Mock (in-browser) | Production API |
| Telemetry | Disabled | Enabled |
| Secrets | None | Encrypted |
