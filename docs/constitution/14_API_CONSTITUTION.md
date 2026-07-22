# GULA API Constitution

## Design Standards

1. **RESTful resource naming:** `/api/v1/{domain}/{resource}/{id}`. Resources are nouns. Actions are HTTP methods. Collections are plural. New route groups use the `/api/v1/` prefix; existing route groups are migrated incrementally per the backward compatibility policy (Article 23).

2. **Consistent response envelope:** Every response returns `{ "data": ..., "meta": { ... } }` where meta includes request_id, pagination, and server timing. *Current codebase uses a flat `{ "items": ..., "total": ... }` pattern for list endpoints; the envelope is adopted incrementally for new route groups.*

3. **Error format:** Every error returns `{ "error": { "code": "ERROR_CODE", "message": "...", "message_ar": "...", "details": [...] } }`. *Existing routes use FastAPI `HTTPException`; migration to the canonical format is phased.*

4. **HTTP methods:**
   - `GET` — Retrieve (never mutate)
   - `POST` — Create (returns 201)
   - `PUT` — Full update (returns 200)
   - `PATCH` — Partial update (returns 200)
   - `DELETE` — Remove (returns 204)

5. **Status codes:**
   - 200 — Success
   - 201 — Created
   - 204 — No content (delete success)
   - 400 — Bad request (validation error)
   - 401 — Unauthenticated
   - 403 — Forbidden (authorization failure)
   - 404 — Not found
   - 409 — Conflict (duplicate, version mismatch)
   - 422 — Unprocessable entity (semantic validation error)
   - 429 — Too many requests
   - 500 — Internal server error (never leak details)

## Versioning

6. **URL prefix versioning:** `/api/v1/...` is current stable. `/api/v2/...` is next.

7. **Backward compatibility:** API changes must be additive for one full version cycle. Breaking changes require a new version.

8. **Deprecation:** Endpoints are marked with `Deprecation` header and documented sunset date. Minimum 6 months deprecation period.

## Documentation

9. **OpenAPI 3.0** specification is generated from code. The spec is the source of truth.

10. **Every endpoint** must have `summary`, `description`, `tags`, and response schemas in the OpenAPI spec.

11. **Request/response examples** are provided for common use cases.

## Security

12. **Authentication:** Bearer JWT token in `Authorization` header. Token obtained from `POST /api/v1/auth/login`.

13. **Authorization:** Every endpoint enforces permission checks via `require_permission()`. (See Article 05.15 — Backend Authority, Article 08.10-12 — Authorization model.)

14. **Idempotency:** Mutating POST endpoints accept `Idempotency-Key` header. Duplicate requests with same key return original response. (See Article 05.9 — Idempotency.)

15. **Rate limiting:** Enforced per user, per IP, per endpoint tier. Headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` are returned.

16. **CORS:** Restricted to configured origins. Credentials never sent cross-origin.

## Pagination

17. **Cursor-based pagination:** `GET /resource?cursor={id}&limit={n}`. Response includes `next_cursor` and `has_more`.

18. **Offset pagination:** Supported for simple lists with `?skip={n}&limit={n}`. Max limit 1000.

## Search and Filtering

19. **Search:** `?q={term}` performs full-text search across indexed fields. Results ranked by relevance.

20. **Filtering:** `?field=value` or `?field__operator=value` (e.g., `created_at__gte=2025-01-01`).

21. **Sorting:** `?sort=field` for ascending, `?sort=-field` for descending. Compound sorts with comma separation.

## Performance

22. **Response compression** via GZip for responses over 1000 bytes.

23. **Conditional requests** support ETags and If-None-Match for caching.

24. **Sparse fields:** `?fields=id,name,result` returns only requested fields.

25. **Embedded resources:** `?include=patient,order` embeds related resources to reduce round trips.
