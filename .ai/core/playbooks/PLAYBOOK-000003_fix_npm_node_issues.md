---
id: PLAYBOOK-000003
type: playbook
title: "Fix npm/Node.js Issues"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [npm, node, nvm, javascript, frontend]
related_skills: [SKILL-000001]
related_runbooks: []
estimated_duration: "10 minutes"
---

# PLAYBOOK-000003: Fix npm/Node.js Issues

## Objective
Resolve common npm and Node.js issues in the development environment.

## Prerequisites
- [ ] NVM installed (`~/.nvm/nvm.sh`)
- [ ] Node.js available via NVM

## Scope
- **In scope:** npm errors, node version issues, package conflicts
- **Out of scope:** Node.js installation, NVM installation

## Procedure

### Phase 1: Diagnose (2 min)
```bash
nvm current                  # Check active node version
node --version               # Verify node
npm --version                # Verify npm
npm config get prefix        # Should point to NVM path
which node                   # Should be NVM path
```

### Phase 2: Common Fixes (8 min)

**Fix 1: Wrong node version**
```bash
nvm install 24               # Install correct version
nvm use 24                   # Switch to it
nvm alias default 24         # Set as default
```

**Fix 2: npm permission errors**
```bash
# Fix npm global directory permissions
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
# Add to .bashrc: export PATH="$HOME/.npm-global/bin:$PATH"
```

**Fix 3: Corrupted node_modules**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Fix 4: npm cache issues**
```bash
npm cache clean --force
npm install
```

**Fix 5: Version conflicts in package.json**
```bash
# Check engines field
cat package.json | grep -A3 "engines"
# Use nvm to match required version
```

**Fix 6: pnpm lockfile out of sync**
```bash
rm pnpm-lock.yaml
pnpm install
```

## Verification
```bash
node --version && npm --version
cd frontend-v3 && npm run build  # Should succeed
```

## Rollback
```bash
# Restore from backup if needed
cp -r node_modules.bak node_modules
```

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial creation |
