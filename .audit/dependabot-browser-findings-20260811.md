# Dependabot browser findings — 11 Aug 2026

Source: https://github.com/samertts/gula-platform/security/dependabot

GitHub page showed **133 open** and **50 closed** Dependabot alerts for dependency files checked for commit `bd57c6b`. The visible first page exposed the following critical/high findings:

| Alert | Severity | Ecosystem | Manifest |
|---|---|---|---|
| Vite arbitrary file read via Dev Server WebSocket | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| Vitest UI server arbitrary file read and execute | Critical | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| lodash / lodash-es code injection via `_.template` imports | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| Vite `server.fs.deny` bypass with queries | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| Rollup 4 arbitrary file write via path traversal | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| Axios DoS via `__proto__` in mergeConfig | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| pnpm lifecycle scripts execution bypass | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| fast-xml-parser entity encoding bypass / regex injection | Critical | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| Axios full MITM via proxy prototype pollution gadget | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| pnpm transitive alias path traversal | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| form-data CRLF injection | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| pnpm project env lockfile can execute lockfile-selected bytes | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| node-tar hardlink/symlink/path traversal issues | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| Axios Proxy-Authorization leak across HTTP→HTTPS redirect | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| @trpc/server prototype pollution | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| nanoid non-secure generator negative-size loop | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |
| pnpm command injection via environment substitution | High | npm | `apps/gula-web-suite/pnpm-lock.yaml` |

The repository page also showed **2,052 code scanning findings** and a `Security and quality` count of 2.2k. The page was authenticated and showed package/manifest details, but alert export through `gh api` remained unavailable due integration permission (`HTTP 403`). The visible manifest `apps/gula-web-suite/pnpm-lock.yaml` is not present in the current local checkout inventory and requires reconciliation with the remote default branch or a fresh fetch of the missing path before patching.

Do not close alerts based only on local audits that omit this manifest. First obtain the exact remote dependency file or confirm its removal/branch scope, then update the affected direct packages and regenerate the lockfile with the repository's package manager.
