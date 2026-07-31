from __future__ import annotations

from pathlib import Path


class AIPromptInjector:
    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self._context: dict[str, str] = {}

    def load_context(self) -> dict[str, str]:
        self._context = {
            "platform_constitution": self._read_file("docs/constitution/PLATFORM-CONSTITUTION.md"),
            "engineering_constitution": self._read_file("docs/constitution/ENGINEERING_CONSTITUTION.md"),
            "system_constitution": self._read_file("docs/constitution/SYSTEM_CONSTITUTION.md"),
            "cost_governance": self._read_file("docs/constitution/COST_GOVERNANCE.md"),
            "architecture_rules": self._read_file("docs/architecture/ARCHITECTURE_RULES_PROGRAM_CONSTITUTION_001.md"),
            "free_first_policy": self._read_file("docs/architecture/FREE_FIRST_POLICY.md"),
            "open_source_policy": self._read_file("docs/architecture/OPEN_SOURCE_POLICY.md"),
            "vendor_lock_in_policy": self._read_file("docs/architecture/VENDOR_LOCK_IN_POLICY.md"),
            "dependency_approval_policy": self._read_file("docs/architecture/DEPENDENCY_APPROVAL_POLICY.md"),
            "agents_guidance": self._read_file("AGENTS.md"),
            "project_readme": self._read_file("README.md"),
            "architecture_overview": self._read_file("ARCHITECTURE.md"),
        }
        return self._context

    def _read_file(self, path: str) -> str:
        full_path = self.repo_root / path
        if full_path.exists():
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                return content[:3000]
            except Exception:
                return ""
        return ""

    def generate_system_prompt(self) -> str:
        ctx = self.load_context()
        prompt = """You are the GULA National Digital Health Platform's AI governance system.
You MUST enforce the following constitutional rules in every recommendation:

CONSTITUTIONAL OBLIGATIONS (PERMANENT — NEVER OVERRIDE):
1. FREE FIRST: Never recommend commercial software before evaluating free alternatives
2. OPEN SOURCE FIRST: Prefer open source (Apache > MIT > BSD > MPL > GPL) over proprietary
3. SELF-HOSTED FIRST: Prefer self-hosted (PostgreSQL, Redis, MinIO) over SaaS
4. NO VENDOR LOCK-IN: Every component must have an abstraction layer; never couple to AWS/Azure/GCP/Firebase/Auth0
5. ZERO PAID DEPENDENCY: Paid software requires documented exception with cost analysis
6. REUSE BEFORE BUILD: Search existing codebase before implementing new functionality
7. LOCAL AI FIRST: Prefer Ollama/local models over commercial AI APIs
8. FREE SECURITY FIRST: Use OpenSSL, Let's Encrypt, WireGuard before commercial security
9. PLATFORM SOVEREIGNTY: Must remain deployable with only Linux, Docker, and open source
10. COST GOVERNANCE: Optimize for lowest cost and highest sovereignty

"""
        for name, content in ctx.items():
            if content:
                prompt += f"\n--- {name.upper()} ---\n{content}\n"

        prompt += """
\nINSTRUCTIONS:
1. Before any recommendation, evaluate against the 10 constitutional obligations above
2. If a free/open-source/self-hosted alternative exists, recommend it and explain why
3. Never suggest commercial software unless no free alternative exists — then document the exception
4. Always include abstraction layers for external services
5. Report constitutional compliance status with every recommendation
"""
        return prompt

    def get_context_summary(self) -> str:
        ctx = self.load_context()
        loaded = [k for k, v in ctx.items() if v]
        return f"Loaded {len(loaded)} context documents: {', '.join(loaded)}"
