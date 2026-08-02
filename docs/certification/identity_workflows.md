# Identity Workflows — PROGRAM-05

## Citizen registration → operational

```
register (person+identity+account)  →  pending_verification
phone/email OTP                     →  verified contact
identity verification (authority)   →  identity_verified
activation (approval)               →  active  [permissions activate]
suspension                          →  suspended [login blocked]
restore                             →  active [login allowed again]
deactivate                          →  deactivated [terminal, audit preserved]
```

## Professional registration → privileges

```
register professional  →  profession_pending (no professional permissions)
license issued + verified → professional permissions activate automatically
license expired/suspended → permissions revoked immediately (Appendix-B)
```

## Session lifecycle (Rule 8/9)

```
login → session created (policy_id, mfa_used, device)
limit exceeded → OLDEST session terminated + notification + audit
logout / remote logout / policy termination → session_terminated (audited)
```

## Verification authorities (Rule 4-7)

Each authority approves only within its scope; every decision audited.
