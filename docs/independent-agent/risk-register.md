# Risk register

Risks, not defects: things that make defects likely or hard to see.

| # | Risk | Why it matters | Mitigation |
|---|---|---|---|
| R-1 | **A route's signature does not tell you its authorization.** Router-level `dependencies=[...]` are the effective guard, and FastAPI binds a dependency's `citizen_id` parameter to the *path* id. | A signature scan reported 17 correctly-guarded PHI routes as unguarded. The same error in the other direction would report a live IDOR as safe. | Measure the served OpenAPI surface plus router-level dependencies; read the dependency body. Never conclude from the decorator. |
| R-2 | **Route existence is not capability.** `/reference/*` has 4 tenant-broken handlers and serves 0 paths; `/ehr/*` serves 54 paths over tables no migration creates. | Any count of endpoints, or of "features", overstates the platform. | Count served paths, and check the tables behind them exist. |
| R-3 | **Local suite counts are corruptible by the environment.** PostgreSQL is reclaimed mid-run and the failure presents as dozens of plausible test errors. | An 18-error environment failure was nearly committed as a regression. | Assert database reachability before collection; re-check `pg_isready` after any surprising error count. |
| R-4 | **Generated code is verified by generating it, not by reading it.** A repair to the capability generator was valid in its output and a `SyntaxError` in the template; the capability tests passed because they never import the generator. | A generator can be broken while everything downstream of its last run is green. | Generate into a temp directory and compile every emitted file. |
| R-5 | **Two lanes share one finding-number space.** 80 ids exist in both registers and 66 mean *different* findings; the fork is at NR-008. | A bare `NR-nnn` above NR-015 is ambiguous in both directions, including inside open PR bodies. | Cite the branch with the number. See `docs/architecture/CROSS_LANE_FINDING_ID_COLLISIONS.md`. |
| R-6 | **A self-certifying test is worse than no test.** Ten generated capabilities asserted their own hard-coded `{"success": True}`. | A passing suite counted them. | A test must be able to fail for the reason it exists; pin the honest state. |
