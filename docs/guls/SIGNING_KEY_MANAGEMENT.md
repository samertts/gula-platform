# GULS Signing Key Management

## Scope

This procedure covers generation, protection, distribution, rotation, and revocation of the Ed25519 key pair used to sign and verify language-pack manifests. Private keys are never committed to the repository, embedded in a pack, or placed in a client artifact. This document records procedure only; it does not authorize production deployment.

## Key roles

| Key | Format | Location | Purpose |
|---|---|---|---|
| Private signing key | PEM, Ed25519 | Protected signing environment / HSM-backed secret store | Sign manifest bytes |
| Public verification key | Raw 32-byte Ed25519 key | Secret manager or read-only file mounted to application instances | Verify pack signatures |

Manifest signatures cover every field except `signature` itself, including catalog hashes, publisher, signer key ID, and approval status. The verification key is configured through `GULS_PACK_PUBLIC_KEY_PATH` or `GULS_PACK_PUBLIC_KEY_B64`. If neither is set, verification fails closed; a malformed value produces a stable error rather than breaking application startup.

## Generation

1. Generate the key pair inside the protected signing environment:

   ```bash
   openssl genpkey -algorithm ed25519 -out gula-guls-ed25519.pem
   openssl pkey -in gula-guls-ed25519.pem -pubout -out gula-guls-ed25519.pub.pem
   ```

2. Derive the raw 32-byte public key for application configuration:

   ```bash
   openssl pkey -pubin -in gula-guls-ed25519.pub.pem -outform DER | tail -c 32 | base64 -w 0
   ```

3. Record a unique `signer_key_id` (for example `gula-release-2026-01`) alongside the key. The pack manifest stores this identifier; it is not a secret.
4. Store the private key only in the approved secret manager or HSM. Grant access solely to the release signing role. Do not copy it to developer machines, CI workspaces, language-pack source directories, or the distribution root.
5. Store the public key in the secret manager used by application deployments. Inject it at runtime; do not commit it to the repository.

## Protection

- Encrypt private keys at rest using the secret manager's encryption; never store an unprotected PEM in a shared filesystem.
- Restrict read access to the signing role. Log every signing operation with language ID, pack version, signer key ID, operator identity, and timestamp.
- Use separate keys per environment (development, staging, production). Never reuse a development key for production packs.
- Sign only after registry and clinical approval checks pass. `tools/guls_sign_pack.py` defaults to `synthetic_test_only`; `--approval-status approved` must be an explicit, reviewed action.
- `GULS_ALLOW_SYNTHETIC_PACKS` must be `0` in production. Synthetic test keys must not be present in the production trust configuration.

## Signing a pack

```bash
GULS_SIGNING_KEY_PATH=/secure/path/gula-guls-ed25519.pem \
python tools/guls_sign_pack.py \
  --language en --version 1.0.0 \
  --source packs/en --output dist/en-1.0.0.zip \
  --key-id gula-release-2026-01 \
  --approval-status approved
```

The tool validates pack paths, computes SHA-256 hashes for each file and the aggregate content hash, then signs the manifest. Private key bytes never enter the output archive.

## Rotation

1. Generate a new key pair using the generation steps above with a new `signer_key_id`.
2. Add the new public key to the deployment trust configuration. The application trusts one configured key at a time; for overlap, deploy the new key to a staging environment first, re-sign and verify a test pack there, then roll the new public key to production during a controlled change window.
3. Re-sign all packs that must remain available with the new key and publish them under new versions.
4. Verify that every distributed pack reports the new `signer_key_id` and that verification succeeds.
5. Only after all clients and instances have migrated, revoke the old key in the secret manager and remove it from trust configuration.
6. Record the rotation in the release log with old/new key IDs, operator, timestamp, and affected pack versions.

Because the application trusts a single configured public key, rotation is a coordinated cutover, not a dual-key trust period within one instance. Plan a short maintenance window or versioned rollout to avoid rejecting packs signed with the previous key.

## Revocation

If a private key is suspected compromised:

1. Remove the corresponding public key from deployment configuration immediately; verification then fails closed for its packs.
2. Generate and deploy a replacement key using the rotation steps.
3. Re-sign and republish all required packs under new versions with the replacement key.
4. Review signing logs for unauthorized artifacts and invalidate any distributed packs signed with the compromised key.
5. Document the incident and the corrective actions. Do not alter the registry to mask the incident.

## Evidence boundaries

No production key was generated, accessed, or rotated by this program. Testing used ephemeral in-memory Ed25519 keys created by `Ed25519PrivateKey.generate()` in the test suite. No private key material appears in the repository or any generated artifact.
