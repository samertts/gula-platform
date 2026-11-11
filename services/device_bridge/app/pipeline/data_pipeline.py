from __future__ import annotations

import logging
import os

from app.adapters.registry import AdapterRegistry
from app.core.retry_queue import RetryQueue
from app.edge.agent import EdgeAgentBuffer
from app.integration.gula_client import GulaClient
from app.pipeline.normalizer import NormalizedResult, Normalizer
from app.pipeline.parser_engine import (
    ASTMBuffer,
    ASTMMessageBuilder,
    ASTMParser,
    ParsedResult,
    ParserEngine,
    validate_checksum,
)
from app.pipeline.patient_matching import PatientMatcher
from app.pipeline.smart_router import SmartRoutingEngine
from app.pipeline.test_mapping import TestMappingEngine
from app.storage.result_repository import LogRepository, ResultRepository

logger = logging.getLogger("lablink.pipeline")

# IA-052. Three unbounded growth paths, all reachable from the authenticated
# POST /ingest, in a container docker-compose caps at mem_limit: 256m.
#
# An ASTM E1381 frame is at most 247 bytes including its overhead; a long
# message is sent as several frames, not one enormous one. So a partial frame
# that has grown past tens of kilobytes is not a partial frame any more -- it is
# a stream that will never produce one, from a truncated serial read, a
# malfunctioning instrument, or an authenticated client that never sends an ETX.
# Measured before the cap: 200 chunks of 8 KiB retained 1,638,600 bytes and
# wrote zero log rows.
#
# Both defaults are generous by two orders of magnitude against the protocol's
# own frame size, and both are overridable so an operator is never stuck.
_MAX_PENDING_BYTES = max(1, int(os.getenv("LABLINK_MAX_PENDING_BYTES", "65536")))

# One ASTMDeviceSession is held per device_id, and device_id is caller-supplied
# with only min_length=1. Measured: 1,000 invented ids held 1,000 sessions, each
# with its own buffer. A bridge serves one lab's instruments, so this bound sits
# far above any real device count; the least recently used session is evicted.
_MAX_SESSIONS = max(1, int(os.getenv("LABLINK_MAX_SESSIONS", "256")))


class ASTMDeviceSession:
    def __init__(self) -> None:
        self.buffer = ASTMBuffer()
        self.builder = ASTMMessageBuilder()


class DataPipeline:
    def __init__(
        self,
        *,
        parser: ASTMParser | ParserEngine,
        normalizer: Normalizer,
        gula_client: GulaClient | None = None,
        mapping_engine: TestMappingEngine | None = None,
        retry_queue: RetryQueue | None = None,
        adapter_registry: AdapterRegistry | None = None,
        patient_matcher: PatientMatcher | None = None,
        router: SmartRoutingEngine | None = None,
        edge_buffer: EdgeAgentBuffer | None = None,
        result_repo: ResultRepository | None = None,
        log_repo: LogRepository | None = None,
    ) -> None:
        self.parser = parser
        self.normalizer = normalizer
        self.gula_client = gula_client or GulaClient(base_url="http://gula.local", lab_id="LAB001")
        self.mapping_engine = mapping_engine or TestMappingEngine()
        self.retry_queue = retry_queue or RetryQueue()
        self.adapter_registry = adapter_registry or AdapterRegistry()
        self.patient_matcher = patient_matcher or PatientMatcher()
        self.router = router or SmartRoutingEngine()
        self.edge_buffer = edge_buffer or EdgeAgentBuffer()
        self.result_repo = result_repo or ResultRepository()
        self.log_repo = log_repo or LogRepository()
        self.sessions: dict[str, ASTMDeviceSession] = {}

    async def process_chunk(
        self,
        chunk: bytes | str,
        device_id: str,
        fallback_patient_id: str | None = None,
        patient_id: str | None = None,
        vendor: str | None = None,
        barcode: str | None = None,
    ) -> list[NormalizedResult]:
        if isinstance(chunk, str):
            return self._process_legacy_chunk(chunk=chunk, patient_id=patient_id, device_id=device_id)

        resolved_patient_id = fallback_patient_id or patient_id or "UNKNOWN"
        session = self._acquire_session(device_id)
        session.buffer.append(chunk)
        adapter = self.adapter_registry.resolve(vendor)

        normalized_results: list[NormalizedResult] = []
        # (reason, detail, source_text). A local list, not an attribute: two
        # concurrent process_chunk calls share this pipeline instance, and a
        # shared counter read after an await could belong to the other request.
        rejections: list[tuple[str, str, str]] = []

        discarded_oversize = False
        if session.buffer.pending_bytes > _MAX_PENDING_BYTES:
            # Recorded, never silently dropped: this is the one place the service
            # deliberately throws bytes away, so it says so. IA-039's invariant
            # holds -- a loss leaves a record.
            discarded = session.buffer.discard_pending()
            logger.warning(
                "Discarded an over-long partial ASTM frame",
                extra={"device_id": device_id, "discarded_bytes": discarded},
            )
            rejections.append(
                (
                    "partial_frame_too_large",
                    f"{discarded} bytes retained without a complete frame "
                    f"(limit {_MAX_PENDING_BYTES}); the buffer was cleared",
                    "",
                ),
            )
            discarded_oversize = True

        frames = session.buffer.extract_frames()
        # `and not discarded_oversize`: the discard above empties the buffer, so
        # without this the same loss is reported twice -- once truthfully as
        # partial_frame_too_large and once as unframed_chunk, which would be the
        # wrong reason for it. One loss, one record.
        if not frames and session.buffer.pending_bytes == 0 and not discarded_oversize:
            # No frame was assembled and nothing was kept for continuation, so the
            # assembler found no STX and dropped the bytes. An analyzer speaking
            # the wrong protocol at this port lands here, and used to do so without
            # leaving a single trace.
            rejections.append(
                (
                    "unframed_chunk",
                    "no ASTM frame start byte; bytes discarded",
                    chunk.decode("ascii", errors="replace"),
                ),
            )

        for payload, received_checksum in frames:
            frame_text = payload.decode("ascii", errors="replace")
            try:
                validate_checksum(payload, received_checksum)
                records = self.parser.parse_frame(payload)
                message_rows = session.builder.process_records(records)
                message_rows = adapter.transform_rows(message_rows)
            except Exception as exc:
                # Was logged as "Invalid ASTM frame" whatever the cause, and
                # recorded nowhere. The exception type is the operator's only clue
                # to whether the analyzer, the mapping or the adapter is at fault.
                logger.exception(
                    "ASTM frame rejected",
                    extra={"device_id": device_id, "reason": type(exc).__name__},
                )
                rejections.append((f"frame_{type(exc).__name__}", str(exc), frame_text))
                continue

            for index, row in enumerate(message_rows):
                missing = [field for field in ("test_code", "value") if not row.get(field)]
                if missing:
                    # Previously a bare `continue`: a result the analyzer sent left
                    # no trace, and the chunk was still recorded as processed.
                    rejections.append(
                        (
                            "row_missing_" + "_and_".join(missing),
                            f"row {index}: test_code={row.get('test_code', '')!r} unit={row.get('unit', '')!r}",
                            frame_text,
                        ),
                    )
                    continue
                try:
                    canonical = self.mapping_engine.canonical_code(row["test_code"])
                    row_patient_id = self.patient_matcher.resolve_patient_id(
                        row_patient_id=row["patient_id"],
                        fallback_patient_id=resolved_patient_id,
                        barcode=barcode,
                    )
                    parsed = ParsedResult(
                        test_code=canonical,
                        value=float(row["value"]),
                        unit=row["unit"],
                        # IA-050: carried through verbatim. `.get` rather than
                        # `[...]` because a vendor adapter may rebuild the row
                        # dict, and a missing key must not turn a usable result
                        # into a rejection.
                        reference_range=row.get("reference_range", ""),
                        abnormal_flags=row.get("abnormal_flags", ""),
                        result_status=row.get("result_status", ""),
                        completed_at=row.get("completed_at", ""),
                    )
                    normalized = self.normalizer.transform(
                        parsed,
                        patient_id=row_patient_id,
                        device_id=device_id,
                        nature_of_abnormality=row.get("nature_of_abnormality", ""),
                    )
                except Exception as exc:
                    # Per row, not per frame: one unparseable value used to abandon
                    # every row after it in the same frame.
                    logger.exception(
                        "ASTM result row rejected",
                        extra={"device_id": device_id, "reason": type(exc).__name__},
                    )
                    rejections.append(
                        (f"row_{type(exc).__name__}", f"row {index}: {exc}", frame_text),
                    )
                    continue
                normalized_results.append(normalized)

        for reason, detail, source_text in rejections:
            self.log_repo.save(
                {
                    "device_id": device_id,
                    "raw_data": source_text,
                    "status": "rejected",
                    "error_message": f"{reason}: {detail}",
                }
            )

        if not normalized_results:
            return normalized_results

        self.result_repo.save_results(normalized_results)
        self.log_repo.save(
            {
                "device_id": device_id,
                "raw_data": chunk.decode("ascii", errors="ignore"),
                "status": "processed" if not rejections else "partially_processed",
                "error_message": "" if not rejections else f"{len(rejections)} rejected",
            }
        )

        decision = self.router.decide(device_id=device_id, results=normalized_results)

        if decision.target in {"gula", "both"}:
            response = await self.gula_client.send_results(normalized_results)
            if response.get("status") == "failed":
                # The retry queue and the edge buffer already carried this, but
                # neither is readable through the API, so a bridge that has never
                # once delivered a result looked identical to one that always does.
                self.log_repo.save(
                    {
                        "device_id": device_id,
                        "raw_data": chunk.decode("ascii", errors="ignore"),
                        "status": "forward_failed",
                        "error_message": str(response.get("error", "send_failed")),
                    }
                )
                self.retry_queue.enqueue(
                    {
                        "device_id": device_id,
                        "results": [r.test_code for r in normalized_results],
                        "reason": response.get("error", "send_failed"),
                    }
                )
                self.edge_buffer.enqueue(
                    {
                        "device_id": device_id,
                        "results": [r.test_code for r in normalized_results],
                    }
                )

        if decision.target in {"offline", "both"}:
            self.edge_buffer.enqueue(
                {
                    "device_id": device_id,
                    "results": [r.test_code for r in normalized_results],
                }
            )

        return normalized_results

    def _acquire_session(self, device_id: str) -> ASTMDeviceSession:
        """Return this device's session, holding at most _MAX_SESSIONS of them.

        IA-052: device_id is caller-supplied, so an unbounded dict of sessions,
        each with its own frame buffer, is reachable from the authenticated
        endpoint. Eviction is least-recently-used, and a session evicted while
        holding a partial frame has those bytes discarded -- so it is logged
        rather than done quietly.
        """
        session = self.sessions.get(device_id)
        if session is not None:
            # Re-insert so dict order is least-recently-used order.
            self.sessions[device_id] = self.sessions.pop(device_id)
            return session

        while len(self.sessions) >= _MAX_SESSIONS:
            evicted_id, evicted = next(iter(self.sessions.items()))
            del self.sessions[evicted_id]
            logger.warning(
                "Evicted a device session to stay within the session limit",
                extra={
                    "device_id": evicted_id,
                    "limit": _MAX_SESSIONS,
                    "discarded_bytes": evicted.buffer.pending_bytes,
                },
            )

        session = ASTMDeviceSession()
        self.sessions[device_id] = session
        return session

    def _process_legacy_chunk(self, *, chunk: str, patient_id: str | None, device_id: str) -> list[NormalizedResult]:
        if not isinstance(self.parser, ParserEngine):
            raise TypeError("Legacy string chunk flow requires ParserEngine")

        normalized_results: list[NormalizedResult] = []
        for parsed in self.parser.feed(chunk):
            normalized = self.normalizer.transform(
                parsed,
                patient_id=patient_id or "UNKNOWN",
                device_id=device_id,
            )
            normalized_results.append(normalized)

        if normalized_results:
            self.result_repo.save_results(normalized_results)
            self.log_repo.save(
                {
                    "device_id": device_id,
                    "raw_data": chunk,
                    "status": "processed",
                }
            )

        return normalized_results
