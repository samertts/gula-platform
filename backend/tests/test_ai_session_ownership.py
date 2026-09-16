"""Every AI endpoint that accepts a caller-supplied session_id must check ownership.

`app/routes/ai_platform.py` already has the right control, written for exactly
this:

    def _assert_session_owner(conversation, current_user) -> None:
        \"\"\"Prevent cross-user and cross-lab access to AI conversation history.\"\"\"
        if (conversation is None
                or conversation.user_id != current_user.id
                or conversation.lab_id != current_user.lab_id):
            raise HTTPException(status_code=404, detail="Session not found")

Three served endpoints take a session_id from the caller. Two called it.
`POST /api/ai/v2/agents/execute` did not, and `AgentRequest.session_id` is a
plain optional string on the request body.

What that reached. `AgentRuntime.run_session` treats the id as a resumable
conversation:

    conv = await memory_store.get_session(session_id)
    if conv is None:
        conv = await memory_store.create_session(...)
    await memory_store.add_message(session_id, "user", task)
    history = memory_store.get_history(session_id, max_tokens=500)
    llm_plan = await self._plan_tools(task, history)

and `ConversationMemory.get_session` runs

    SELECT id, lab_id, user_id, session_id, title, metadata
    FROM ai_conversations WHERE session_id = :sid

with no tenant constraint, then loads **every** message of that conversation
and caches it in `self._sessions`. So naming another user's session made the
endpoint read that conversation's history, put it in the planning prompt sent
to the external model (`app.gateways.google_ai.generate_chat`), and append the
caller's task and the run's summary back into it.

An identifier is not an authorization. `create_session` mints a `uuid.uuid4()`,
which is not guessable, and `_require_doctor` narrows who can call at all --
but session ids travel: they are returned by `POST /sessions`, they appear in
request bodies and logs, and `run_session`'s own fallback id for a missing one
is `f"agent-{time.time()}"`, which is not random at all.

The fix is the control the file already had, applied to the third endpoint.
These tests keep it applied, and keep the control itself honest: checking only
`lab_id` would still let one doctor resume another doctor's session inside the
same lab, which is what the `user_id` half of the comparison is for.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

ROUTES = pathlib.Path(__file__).resolve().parents[1] / "app" / "routes" / "ai_platform.py"
MEMORY = pathlib.Path(__file__).resolve().parents[1] / "app" / "ai" / "memory.py"

#: Route handlers that accept a session_id the caller chooses. Each must call
#: `_assert_session_owner` before anything reads or writes that conversation.
SESSION_TAKING_HANDLERS = ("execute_agent", "add_message", "get_session")


@pytest.fixture(scope="module")
def routes_source() -> str:
    return ROUTES.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def handlers(routes_source) -> dict[str, ast.AST]:
    tree = ast.parse(routes_source)
    return {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _calls(node) -> set[str]:
    return {
        getattr(c.func, "id", None) or getattr(c.func, "attr", None)
        for c in ast.walk(node)
        if isinstance(c, ast.Call)
    }


def test_every_endpoint_taking_a_session_id_checks_ownership(handlers) -> None:
    """The gap that was live, on the endpoint that had none of the three."""
    missing = [
        name for name in SESSION_TAKING_HANDLERS
        if name in handlers and "_assert_session_owner" not in _calls(handlers[name])
    ]
    assert missing == [], (
        f"these handlers accept a caller-supplied session_id without checking "
        f"ownership: {missing}. run_session resumes whatever conversation the id "
        "names -- reading its history into the prompt sent to the external model "
        "and appending to it. Call _assert_session_owner first, as the sibling "
        "endpoints do."
    )


def test_the_ownership_check_compares_both_user_and_lab(routes_source) -> None:
    """Tenant alone is not enough, and neither is user alone.

    Two doctors in one lab must not resume each other's sessions, and the same
    user id in two labs must not collide. The control compares both; this keeps
    it that way.
    """
    tree = ast.parse(routes_source)
    fn = next(
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "_assert_session_owner"
    )
    compared = {
        node.attr for node in ast.walk(fn) if isinstance(node, ast.Attribute)
    }
    for field in ("user_id", "lab_id"):
        assert field in compared, (
            f"_assert_session_owner no longer compares {field}. Both halves are "
            "load-bearing: lab_id alone lets one doctor resume a colleague's "
            "session, user_id alone lets the same id collide across labs."
        )


def test_the_lookup_it_guards_is_still_untenanted(routes_source) -> None:
    """Records why the route-layer check is load-bearing rather than belt-and-braces.

    `ConversationMemory.get_session` selects on `session_id` alone. As long as
    that is true, the only thing standing between a caller and another user's
    conversation is the check above. If the lookup is ever tenant-scoped itself,
    this test fails and the note in this file should be revisited -- the route
    checks stay either way, because defence in depth is the point.
    """
    tree = ast.parse(MEMORY.read_text(encoding="utf-8"))
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == "get_session"
    )
    lookups = [
        call.args[0].value
        for call in ast.walk(fn)
        if isinstance(call, ast.Call)
        and getattr(call.func, "id", "") == "text"
        and call.args
        and isinstance(call.args[0], ast.Constant)
        and "ai_conversations" in call.args[0].value
    ]
    assert len(lookups) == 1, (
        f"expected exactly one ai_conversations lookup in get_session, found "
        f"{len(lookups)}. Re-read this file's docstring before trusting it."
    )
    # Whole-statement, not a substring: appending "AND lab_id = :lab" leaves any
    # prefix match intact, which is how the first version of this assertion
    # failed to notice its own negative proof.
    assert "lab_id" not in lookups[0].split("WHERE", 1)[1], (
        "ConversationMemory.get_session now constrains the tenant itself. Good "
        "-- but this file's docstring explains the route-layer ownership checks "
        "as compensating for an untenanted lookup, and that explanation is now "
        "out of date. The route checks stay regardless: they also compare "
        "user_id, which a tenant filter does not."
    )
