# API versioning

**PROGRAM-EXT-001, Phase 7.** Normative.

GULA has mobile clients it does not control and a national platform it cannot
ask to redeploy. An API change is therefore a change to something someone else
depends on, at a time they choose.

## 1. Rules

1. **Every public route carries an explicit version** in its path:
   `/api/v1/...`. No implicit "latest".
2. **Request, response and error contracts are declared**, as Pydantic models,
   not dictionaries. A dict response has no contract and cannot be reviewed.
3. **The authorization contract is declared** — which permission, evaluated in
   which scope. Server-side, per request.
4. **Idempotency where a repeat is possible.** Any endpoint that creates or
   mutates clinical or financial state accepts `Idempotency-Key` and returns
   the same result for the same key. See the blood-bank work (Phase 14B) for
   the pattern and its proofs.
5. **Audit semantics are declared** — what is written, and whether it is written
   before or after the decision. The clinical gateway audits *before* it allows
   and *before* it denies; that ordering is the property that makes the trail
   trustworthy, and it is not an implementation detail.
6. **Deprecation is a lifecycle, not an announcement** — see §3.

## 2. Compatible vs breaking

**Compatible** (same version): adding an optional request field; adding a
response field; widening an accepted enum on input; relaxing a constraint.

**Breaking** (new version): removing or renaming any response field; narrowing
a type (`float` → `int`); changing the meaning of an existing field; making an
optional request field required; changing status codes or error shapes;
narrowing an accepted enum on input.

Two that look compatible and are not:

* Changing a quantity from `int` to `float` is breaking in one direction and
  silently lossy in the other. PR #258 moved seven pharmacy response models to
  `float` precisely because the columns are `DOUBLE PRECISION` and an integer
  truncates half a tablet.
* Removing a field that is always `null` is still breaking for a client that
  reads it — even though no information is lost.

## 3. Deprecation lifecycle

1. **Announce** — mark the route deprecated in OpenAPI, set
   `deprecation.since_version`, name the `replacement`.
2. **Overlap** — old and new run together. This is not optional; it is the
   entire mechanism by which clients migrate.
3. **Warn** — return `Deprecation` and `Sunset` headers.
4. **Remove** — only at the declared `removal_version`, and only once the
   metrics show no traffic.

A capability at maturity `deprecated` without a populated `deprecation` block
fails `validate_descriptor`. That is the enforcement.

## 4. What must never change silently

* An identifier that is a string stays a string. Internal integer keys never
  appear on a public surface — a rule already broken once and recorded:
  `GET /inventory/stock-levels` takes `warehouse_id`/`store_id` as `str` and
  compares them against `Integer` columns, so a non-numeric value surfaces as a
  500 rather than a 422. Recorded, unreachable today, not yet fixed.
* An error contract. Clients branch on it.
* The meaning of a status code. 403 must mean "you may not", not "we broke" —
  NR-048 is what happens when it means both.

## 5. Existing APIs

Nothing in this document changes an existing route. It states the rules new
routes are written to and existing routes are migrated toward. No endpoint was
renamed, versioned or removed by PROGRAM-EXT-001.
