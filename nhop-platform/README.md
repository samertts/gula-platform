# NHOP — National Health Oversight Platform

Companion service to the GULA lab platform. NHOP owns the **national citizen
registry** (the person-centric view of health data) whereas GULA owns the
per-lab LIMS (the lab-centric view).

## CMD-006 — Citizen Registration API

FastAPI CRUD for the citizen registry, living at `app/api/v1/citizens.py`.

| Method | Path                             | Purpose                                            |
|--------|----------------------------------|----------------------------------------------------|
| POST   | `/v1/citizens/register`          | Register a new citizen (dedup-checked, auto `health_id`) |
| GET    | `/v1/citizens/search`            | Search by name or national_id, filter by province  |
| GET    | `/v1/citizens/{health_id}`       | Read a citizen                                     |
| PUT    | `/v1/citizens/{health_id}`       | Update mutable fields (not `national_id` / `health_id`) |
| GET    | `/v1/citizens/{health_id}/summary` | Profile + last 5 tests + chronic diseases        |

Every endpoint writes to the `audit_log` table via `services.audit.log_action`.

### Duplicate detection

`services.duplicates.find_duplicates` scores candidates using a weighted
Fellegi-Sunter style combination of name Jaro-Winkler, birth date, phone
(last 10 digits), and mother name. `register_citizen` returns **409 Conflict**
when the top score exceeds `DUPLICATE_CONFLICT_THRESHOLD` (0.85).

### Health ID format

`HID-YYYY-XXXXXXXX` — year + 8-char Crockford base32 suffix (~40 bits entropy).
Collisions are checked on insertion with a 5-attempt retry.

## Running locally

```bash
cd nhop-platform
pip install fastapi uvicorn sqlalchemy pydantic
NHOP_DATABASE_URL=sqlite:///./nhop.db uvicorn app.main:app --reload --port 8100
```
