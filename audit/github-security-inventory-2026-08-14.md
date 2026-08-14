# GitHub Security inventory — 2026-08-14

The GitHub Dependabot page for `samertts/gula-platform` reports **45 open alerts** and **331 closed alerts**. The dependency files were checked 10 hours ago for commit `6405bbb`.

The visible open findings include one critical Bouncy Castle advisory, multiple high-severity Netty advisories, JDOM2 XXE, jose4j compressed-JWE DoS, Apache Commons Compress memory exhaustion, and a direct Python `cryptography` advisory in `backend/requirements-lock.txt` (alert #120). The alerts are concentrated in `mobile/android/settings.gradle.kts` and the backend lockfile.

The page navigation reports **1,916 Code Scanning alerts**. GitHub API access from the sandbox returned HTTP 403 (`Resource not accessible by integration`), so the authenticated browser dashboard is the authoritative source currently available for inventory.

No alert was dismissed, closed, or modified.

The Code Scanning page reports **1,916 open alerts** and **710 closed alerts** on `main`. GitHub displays a banner: **CodeQL is reporting errors**. The first visible open findings include four critical `Partial server-side request forgery` alerts in `backend/.../integration/testing.py` at lines 427, 392, 357, and 228. Visible high findings include clear-text logging of sensitive information in `backend/.../gateways/residency_gateway.py`, `scripts/quality_gate.py`, `scripts/constitution_enforcer.py`, and `contracts/.../gula/client.py`; insecure SSL/TLS version in `.audit/check_security_headers.py`; and uncontrolled data used in path expressions across certification, contracts, and API files. No alert was modified.

After revisiting the dashboard, GitHub now reports **42 open Dependabot alerts / 334 closed** and **376 open Code Scanning alerts**. The Bouncy Castle alert #310 detail is marked **Fixed** with patched version `1.80.2`, indicating that GitHub is actively reprocessing the repository and the earlier counts were stale. The Dependabot list still labels its dependency snapshot as commit `6405bbb`, so the dashboard may lag behind `main` tip. No alert was modified.

Dependency detail checks: Netty alert #291 reports `io.netty:netty-codec-http2` patched at `4.1.132.Final` (the current forced version `4.1.118.Final` is insufficient). JDOM alert #287 reports `org.jdom:jdom2` patched at `2.0.6.1`; the repository already forces `2.0.6.1`, so that alert should clear after the dependency snapshot refreshes. The Bouncy Castle alert #310 is fixed at `1.80.2`; the repository currently forces `1.80` and should be raised to `1.80.2`.

Additional dependency detail checks: Kotlin Gradle Plugin alert #321 is patched at `2.4.20-Beta1`, while the project currently uses `2.1.20` and KSP `2.1.20-1.0.31`. Maven metadata currently exposes KSP versions only through the 2.3.x line in this environment, so an unverified Kotlin/KSP jump would risk breaking Android builds; the safer immediate mitigation is disabling Gradle build cache (`org.gradle.caching=false`) until a compatible Kotlin/KSP pair is validated. Commons Compress alert #276 is patched at `1.26.0`, which the project already forces; it should clear after dependency refresh.

CodeQL detail review: alert #2621 flags `print(_redact(output))` in `scripts/quality_gate.py`; alert #2618 flags `print(_redact(json.dumps(report, ...)))` in `scripts/constitution_enforcer.py`. Both are `py/clear-text-logging-sensitive-data` findings. The fix is to emit only allowlisted status metadata and counts rather than raw subprocess/report details, because regex redaction is not a sufficient proof for CodeQL or clinical log safety.

After pushing commit `d658088d`, the Code Scanning dashboard now shows **170 open alerts / 2,456 closed**, down from 376 open / 710 closed during the previous snapshot. The page still shows a CodeQL reporting-errors banner and lists alerts from the pre-refresh snapshot, including the files changed in the new commit; the new CodeQL runs are queued on GitHub. This indicates the alert database is actively being reprocessed, but final closure counts must wait for the queued runs to finish.

A second remediation patch also hardened `backend/core/api/main.py` by replacing the user-derived PDF filename with an OS-generated temporary filename, and removed API-key environment-name logging from `backend/app/ai_fabric/gateway.py` plus entity identifiers from `backend/app/ai/guardrails.py`. The latest local security subset passed **33/33 tests** and the modified Python files compile successfully. These changes are pending the next GitHub push and CodeQL refresh.
