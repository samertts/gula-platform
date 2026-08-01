# Mutation Coverage Report — PROGRAM-03 v2.0

Frontend mutation operations (POST/PUT/PATCH) wired to real backend endpoints, per page.

| Page | Mutation | Endpoint | Method |
|---|---|---|---|
| OrdersPage | create order | `/orders` | POST |
| OrdersPage | validate order | `/orders/{id}/validate` | POST |
| OrdersPage | cancel order | `/orders/{id}/cancel` | POST |
| OrdersPage | clinical analysis | `/orders/{id}/intelligence` | GET (action) |
| PatientsPage | create patient | `/patients` | POST |
| PatientsPage | update patient | `/patients/{id}` | PUT |
| SamplesPage | register sample | `/samples` | POST |
| SamplesPage | transition status | `/samples/{barcode}` | PATCH |
| ResultsPage | verify result | `/test-results/{id}/verify` | POST |
| QCPage | submit QC entry | `/qc` | POST |
| ProfilePage | change password | `/auth/change-password` | POST |
| IdentityPage | link patient (NID) | `/identity/link` | POST |
| LoginPage | login | `/login` | POST |
| LoginPage | MFA challenge | `/mfa-verify` | POST |

## Coverage

- **9/9 production workflow pages** have ≥1 real mutation.
- **14 mutations** wired (was 0 mutation-capable pages at PROGRAM-03 v1.0).
- **100% of API groups** in `endpoints.ts` used by at least one page.

## Mutation Hygiene

- All mutations use react-query `useMutation` + `queryClient.invalidateQueries` (no stale UI after server change).
- All error surfaces use `getErrorMessage(err, fallback)`.
- Optimistic updates avoided in favor of server truth (backend is source of truth).
