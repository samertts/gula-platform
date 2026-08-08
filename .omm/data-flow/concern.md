Redis used as in-memory fallback when unavailable (lazy cache); full PG restore validated via DR drill (WAL→S3, RPO ~1 min). Offline sync conflict resolution is complex and highest-risk surface.
