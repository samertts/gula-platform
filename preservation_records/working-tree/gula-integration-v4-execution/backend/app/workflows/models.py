from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.identity.base import IdentityBaseEntity


class WorkflowDefinition(IdentityBaseEntity):
    __tablename__ = "niam_wf_definitions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    def_id = Column(String(100), unique=True, nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(String(30), nullable=False, index=True)
    version = Column(String(20), default="1.0", nullable=False)
    status = Column(String(20), default="draft", nullable=False, index=True)

    steps = Column(JSON, nullable=False)
    timeout_hours = Column(Integer, nullable=True)
    escalation_step = Column(String(100), nullable=True)
    retry_policy = Column(JSON, nullable=True)
    notification_triggers = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)


class WorkflowInstance(IdentityBaseEntity):
    __tablename__ = "niam_wf_instances"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    instance_id = Column(String(100), unique=True, nullable=False, index=True)

    def_id = Column(
        String(100),
        ForeignKey("niam_wf_definitions.def_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    trigger_type = Column(String(50), nullable=False)
    trigger_id = Column(String(100), nullable=False, index=True)
    initiator_id = Column(String(100), nullable=False)

    status = Column(String(30), default="pending", nullable=False, index=True)
    current_step = Column(String(100), nullable=True)
    state = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)
    assigned_to = Column(String(100), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    last_action_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)


class WorkflowApproval(IdentityBaseEntity):
    __tablename__ = "niam_wf_approvals"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    approval_id = Column(String(100), unique=True, nullable=False, index=True)

    instance_id = Column(
        String(100),
        ForeignKey("niam_wf_instances.instance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_name = Column(String(100), nullable=False)
    approver_id = Column(String(100), nullable=False, index=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    comments = Column(Text, nullable=True)

    assigned_at = Column(DateTime(timezone=True), nullable=True)
    action_at = Column(DateTime(timezone=True), nullable=True)
    delegated_to = Column(String(100), nullable=True)
    escalation_reason = Column(Text, nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)


class WorkflowNotification(IdentityBaseEntity):
    __tablename__ = "niam_wf_notifications"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    notification_id = Column(String(100), unique=True, nullable=False, index=True)

    instance_id = Column(
        String(100),
        ForeignKey("niam_wf_instances.instance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_id = Column(String(100), nullable=False, index=True)
    notification_type = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=True)
    template_id = Column(String(100), nullable=True)

    subject = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)
