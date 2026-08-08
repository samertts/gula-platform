GULA - AnyDoc Integration Policy

Source:
https://github.com/firecrawl/anydoc

Purpose:
Document ingestion and conversion for AI/RAG/Agent workflows.

Status:
EXTERNAL FOUNDATION

Architecture

Upload
-> File Validation
-> Security/Malware Scan
-> Resource Limits
-> AnyDoc
-> Normalized Document / Markdown
-> Metadata + Provenance
-> Chunking
-> Indexing / RAG
-> Agent

Rules

1. AnyDoc is NOT part of GULA Core Domain.
2. AnyDoc must run behind the GULA document-ingestion boundary.
3. Uploaded files are untrusted input.
4. MIME type and file signature must be validated.
5. File size and decompression/resource limits must be enforced.
6. Encrypted/password-protected documents must be rejected or routed
   through a controlled, audited manual review path.
7. Extracted text must carry provenance (source file, checksum, timestamps).
8. Output must never contain secrets, PHI, or clinical data in plaintext
   outside GULA-authorized stores.
9. All ingestion events must be recorded in the immutable audit log.
10. GULA Constitution, security, and privacy policies take precedence
    over AnyDoc behavior.
