from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.citizen_platform.enums import TelemedicineStatus

logger = logging.getLogger("gula.citizen.telemedicine")


@dataclass
class TelemedicineSession:
    id: str = ""
    citizen_id: str = ""
    practitioner_id: str = ""
    practitioner_name: str = ""
    scheduled_at: str = ""
    started_at: str = ""
    ended_at: str = ""
    status: TelemedicineStatus = TelemedicineStatus.SCHEDULED
    meeting_url: str = ""
    consultation_notes: str = ""
    prescription: str = ""
    follow_up_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    id: str = ""
    session_id: str = ""
    sender_id: str = ""
    sender_type: str = ""
    content: str = ""
    sent_at: str = ""
    read_at: str = ""
    attachments: list[str] = field(default_factory=list)


class TelemedicineService:
    def __init__(self) -> None:
        self._sessions: dict[str, list[TelemedicineSession]] = {}

    def schedule_session(
        self,
        citizen_id: str,
        practitioner_id: str,
        practitioner_name: str = "",
        scheduled_at: str = "",
        meeting_url: str = "",
    ) -> TelemedicineSession:
        session = TelemedicineSession(
            id=str(uuid.uuid4()),
            citizen_id=citizen_id,
            practitioner_id=practitioner_id,
            practitioner_name=practitioner_name,
            scheduled_at=scheduled_at,
            status=TelemedicineStatus.SCHEDULED,
            meeting_url=meeting_url,
        )
        if citizen_id not in self._sessions:
            self._sessions[citizen_id] = []
        self._sessions[citizen_id].append(session)
        return session

    def start_session(self, session_id: str) -> bool:
        for sessions in self._sessions.values():
            for s in sessions:
                if s.id == session_id and s.status == TelemedicineStatus.SCHEDULED:
                    s.status = TelemedicineStatus.IN_PROGRESS
                    s.started_at = datetime.now(UTC).isoformat()
                    return True
        return False

    def complete_session(
        self,
        session_id: str,
        consultation_notes: str = "",
        prescription: str = "",
        follow_up_required: bool = False,
    ) -> bool:
        for sessions in self._sessions.values():
            for s in sessions:
                if s.id == session_id and s.status == TelemedicineStatus.IN_PROGRESS:
                    s.status = TelemedicineStatus.COMPLETED
                    s.ended_at = datetime.now(UTC).isoformat()
                    s.consultation_notes = consultation_notes
                    s.prescription = prescription
                    s.follow_up_required = follow_up_required
                    return True
        return False

    def cancel_session(self, session_id: str) -> bool:
        for sessions in self._sessions.values():
            for s in sessions:
                if s.id == session_id and s.status in (
                    TelemedicineStatus.SCHEDULED,
                    TelemedicineStatus.IN_PROGRESS,
                ):
                    s.status = TelemedicineStatus.CANCELLED
                    return True
        return False

    def get_sessions(
        self,
        citizen_id: str,
        status: TelemedicineStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TelemedicineSession]:
        sessions = self._sessions.get(citizen_id, [])
        if status:
            sessions = [s for s in sessions if s.status == status]
        sessions.sort(key=lambda s: s.scheduled_at, reverse=True)
        return sessions[skip : skip + limit]

    def get_session_by_id(self, session_id: str) -> TelemedicineSession | None:
        for sessions in self._sessions.values():
            for s in sessions:
                if s.id == session_id:
                    return s
        return None


class SecureMessaging:
    def __init__(self) -> None:
        self._messages: dict[str, list[Message]] = {}

    def send_message(
        self,
        session_id: str,
        sender_id: str,
        sender_type: str,
        content: str,
        attachments: list[str] | None = None,
    ) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            sender_id=sender_id,
            sender_type=sender_type,
            content=content,
            sent_at=datetime.now(UTC).isoformat(),
            attachments=attachments or [],
        )
        if session_id not in self._messages:
            self._messages[session_id] = []
        self._messages[session_id].append(msg)
        return msg

    def get_messages(self, session_id: str) -> list[Message]:
        return self._messages.get(session_id, [])

    def mark_as_read(self, message_id: str) -> bool:
        for messages in self._messages.values():
            for m in messages:
                if m.id == message_id:
                    m.read_at = datetime.now(UTC).isoformat()
                    return True
        return False

    def get_unread_count(self, session_id: str, user_id: str) -> int:
        messages = self._messages.get(session_id, [])
        return sum(1 for m in messages if m.sender_id != user_id and not m.read_at)


class FollowUpService:
    def __init__(self) -> None:
        self._follow_ups: dict[str, list[dict[str, Any]]] = {}

    def create_follow_up(
        self,
        session_id: str,
        citizen_id: str,
        practitioner_id: str,
        scheduled_at: str,
        notes: str = "",
    ) -> dict[str, Any]:
        follow_up = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "citizen_id": citizen_id,
            "practitioner_id": practitioner_id,
            "scheduled_at": scheduled_at,
            "status": "pending",
            "notes": notes,
            "created_at": datetime.now(UTC).isoformat(),
        }
        if citizen_id not in self._follow_ups:
            self._follow_ups[citizen_id] = []
        self._follow_ups[citizen_id].append(follow_up)
        return follow_up

    def complete_follow_up(self, follow_up_id: str, citizen_id: str) -> bool:
        follow_ups = self._follow_ups.get(citizen_id, [])
        for f in follow_ups:
            if f["id"] == follow_up_id:
                f["status"] = "completed"
                return True
        return False

    def get_pending_follow_ups(self, citizen_id: str) -> list[dict[str, Any]]:
        return [f for f in self._follow_ups.get(citizen_id, []) if f["status"] == "pending"]

    def get_follow_up_history(self, citizen_id: str) -> list[dict[str, Any]]:
        follow_ups = self._follow_ups.get(citizen_id, [])
        follow_ups.sort(key=lambda f: f["scheduled_at"], reverse=True)
        return follow_ups
