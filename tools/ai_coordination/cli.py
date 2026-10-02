from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

from .coordination import AgentCoordinator, AgentIdentity, CoordinationError, git_context


def _json(value: object) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _coordinator(args: argparse.Namespace) -> AgentCoordinator:
    return AgentCoordinator(args.db)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GULA multi-agent coordination layer")
    parser.add_argument("--db", default=os.getenv("GULA_COORDINATION_DB", ".gula/coordination.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register")
    register.add_argument("--agent-id", required=True)
    register.add_argument("--provider", required=True)
    register.add_argument("--model", default="unknown")
    register.add_argument("--session-id", default=str(uuid.uuid4()))

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    create = task_sub.add_parser("create")
    create.add_argument("title")
    create.add_argument("description")
    create.add_argument("--created-by", required=True)
    claim = task_sub.add_parser("claim")
    claim.add_argument("task_id")
    claim.add_argument("--agent-id", required=True)
    claim.add_argument("--lease-seconds", type=int, default=900)
    release = task_sub.add_parser("release")
    release.add_argument("task_id")
    release.add_argument("--agent-id", required=True)
    release.add_argument("--lease-id", required=True)
    release.add_argument("--status", default="done")

    intent = sub.add_parser("intent")
    intent_sub = intent.add_subparsers(dest="intent_command", required=True)
    declare = intent_sub.add_parser("declare")
    declare.add_argument("task_id")
    declare.add_argument("--agent-id", required=True)
    declare.add_argument("--operation", choices=["add", "modify", "delete", "rename", "review"], required=True)
    declare.add_argument("--base-commit", default="")
    declare.add_argument("paths", nargs="+")
    close = intent_sub.add_parser("close")
    close.add_argument("intent_id")
    close.add_argument("--agent-id", required=True)
    close.add_argument("--status", default="completed")

    message = sub.add_parser("message")
    message_sub = message.add_subparsers(dest="message_command", required=True)
    send = message_sub.add_parser("send")
    send.add_argument("--sender-id", required=True)
    send.add_argument("--recipient-id")
    send.add_argument("--kind", default="status")
    send.add_argument("body", help="JSON object")
    receive = message_sub.add_parser("receive")
    receive.add_argument("--agent-id", required=True)
    receive.add_argument("--limit", type=int, default=50)

    sub.add_parser("status")
    args = parser.parse_args(argv)
    coordinator = _coordinator(args)
    try:
        if args.command == "register":
            branch, commit = git_context()
            coordinator.register_agent(AgentIdentity(args.agent_id, args.provider, args.model, args.session_id, branch, commit))
            _json({"registered": True, "agent_id": args.agent_id, "branch": branch, "commit": commit})
        elif args.command == "task":
            if args.task_command == "create":
                _json({"task_id": coordinator.create_task(args.title, args.description, args.created_by)})
            elif args.task_command == "claim":
                _json(coordinator.claim_task(args.task_id, args.agent_id, args.lease_seconds).__dict__)
            else:
                coordinator.release_task(type("Claim", (), {"task_id": args.task_id, "agent_id": args.agent_id, "lease_id": args.lease_id})(), args.status)
                _json({"released": True, "task_id": args.task_id, "status": args.status})
        elif args.command == "intent":
            if args.intent_command == "declare":
                _, current_commit = git_context()
                declared = coordinator.declare_intent(args.task_id, args.agent_id, args.paths, args.operation, args.base_commit or current_commit)
                _json(declared.__dict__)
            else:
                coordinator.close_intent(args.intent_id, args.agent_id, args.status)
                _json({"closed": True, "intent_id": args.intent_id, "status": args.status})
        elif args.command == "message":
            if args.message_command == "send":
                body = json.loads(args.body)
                _json({"message_id": coordinator.send_message(args.sender_id, body, args.recipient_id, args.kind)})
            else:
                _json(coordinator.receive_messages(args.agent_id, args.limit))
        else:
            _json(coordinator.status())
        return 0
    except (CoordinationError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(json.dumps({"error": str(exc), "type": type(exc).__name__}, ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
