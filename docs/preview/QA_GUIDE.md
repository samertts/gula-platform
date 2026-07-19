# GULA Preview Environment — QA Guide

## Automated Checks

All QA checks run automatically via GitHub Actions on every PR:

### Build Validation
- TypeScript compilation (`tsc --noEmit`)
- Vite production build
- Bundle size tracking

### Security Scan
- Production secret detection
- `.env` file verification
- Hardcoded URL/credential scanning

## Manual QA Checklist

### 1. Basic Functionality
- [ ] All pages load without errors
- [ ] Navigation works correctly
- [ ] RTL mode displays correctly
- [ ] LTR mode displays correctly
- [ ] Dark mode renders properly
- [ ] Light mode renders properly

### 2. Authentication
- [ ] Demo login works
- [ ] Role switching works
- [ ] Each role shows correct UI
- [ ] Logout works
- [ ] Session persists on refresh

### 3. Mock Data
- [ ] Patient list loads
- [ ] Laboratory list loads
- [ ] Lab results display
- [ ] Document list shows
- [ ] Analytics render charts

### 4. Feature Flags
- [ ] AI can be disabled/enabled
- [ ] OCR can be disabled/enabled
- [ ] FHIR can be disabled/enabled
- [ ] Notifications can be disabled/enabled
- [ ] Feature flags persist on refresh

### 5. AI Features
- [ ] AI chat/assistant responds
- [ ] AI analysis returns results
- [ ] OCR demo processes (synthetic)

### 6. Responsive Design
- [ ] Desktop (1920x1080) renders correctly
- [ ] Laptop (1366x768) renders correctly
- [ ] Tablet (768x1024) renders correctly
- [ ] Mobile (375x812) renders correctly

### 7. Accessibility
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Screen reader compatibility
- [ ] Color contrast meets WCAG AA

## Performance Benchmarks

| Metric | Target | Method |
|--------|--------|--------|
| Lighthouse Performance | >90 | `lighthouse-ci` |
| Lighthouse Accessibility | >95 | `lighthouse-ci` |
| Lighthouse Best Practices | >95 | `lighthouse-ci` |
| Lighthouse SEO | >95 | `lighthouse-ci` |
| First Contentful Paint | <2s | Browser DevTools |
| Time to Interactive | <3s | Browser DevTools |
| Bundle Size | <500KB | Vite build report |

## Testing Scripts

```bash
# Run type check
cd frontend-v2 && npx tsc --noEmit

# Run tests (if configured)
cd frontend-v2 && npm test

# Build for production check
cd frontend-v2 && npm run build

# Preview build
cd frontend-v2 && npx vite preview
```

## Arabic RTL Testing

- [ ] Text direction: right-to-left
- [ ] Alignment: right-aligned text
- [ ] Navigation: right-aligned sidebar
- [ ] Forms: right-aligned labels
- [ ] Numbers: left-to-right within RTL
- [ ] Mixed content: correct bi-directional rendering
