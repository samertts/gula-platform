from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ChangelogEntry:
    type: str
    message: str
    scope: str = ""
    breaking: bool = False
    sha: str = ""
    author: str = ""
    date: str = ""


@dataclass
class ReleaseNote:
    version: str
    date: str
    features: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    security: list[str] = field(default_factory=list)
    deprecations: list[str] = field(default_factory=list)


class CHANGELOGAutomator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def generate_from_git(
        self,
        since_tag: str | None = None,
        output_path: str = "CHANGELOG.md",
    ) -> list[ChangelogEntry]:
        entries = self._parse_git_log(since_tag)
        content = self._format_changelog(entries)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = path.read_text()
            header, _, body = existing.partition("\n## ")
            content = header + "\n## " + body
        path.write_text(content)
        return entries

    def generate(self, entries: list[ChangelogEntry] | None = None) -> str:
        if entries is None:
            entries = self._parse_git_log()
        return self._format_changelog(entries)

    def write(
        self,
        entries: list[ChangelogEntry] | None = None,
        output_path: str = "CHANGELOG.md",
    ) -> None:
        content = self.generate(entries)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def _parse_git_log(self, since_tag: str | None = None) -> list[ChangelogEntry]:
        entries: list[ChangelogEntry] = []
        try:
            cmd = ["git", "log", "--oneline", "--format=%H|%s|%an|%ai"]
            if since_tag:
                cmd.insert(2, f"{since_tag}..HEAD")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=30,
            )
            if result.returncode != 0:
                return entries

            for line in result.stdout.strip().split("\n"):
                if not line or "|" not in line:
                    continue
                parts = line.split("|", 3)
                sha, msg, author, date = (
                    parts[0],
                    parts[1],
                    parts[2],
                    parts[3] if len(parts) > 3 else "",
                )

                entry = self._parse_commit_message(msg)
                entry.sha = sha[:8]
                entry.author = author
                entry.date = date[:10] if date else ""
                entries.append(entry)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return entries

    def _parse_commit_message(self, msg: str) -> ChangelogEntry:
        entry = ChangelogEntry(type="other", message=msg)

        breaking = "!" in msg or "BREAKING" in msg.upper()
        entry.breaking = breaking

        conventional_match = re.match(r"^(\w+)(?:\(([^)]+)\))?!?:\s*(.*)", msg)
        if conventional_match:
            prefix, scope, desc = conventional_match.groups()
            entry.type = self._map_type(prefix)
            entry.message = desc
            entry.scope = scope or ""

        return entry

    def _map_type(self, prefix: str) -> str:
        mapping = {
            "feat": "feature",
            "fix": "fix",
            "docs": "documentation",
            "style": "style",
            "refactor": "refactor",
            "perf": "performance",
            "test": "test",
            "build": "build",
            "ci": "ci",
            "chore": "chore",
            "revert": "revert",
        }
        return mapping.get(prefix, prefix)

    def _format_changelog(self, entries: list[ChangelogEntry]) -> str:
        sections: dict[str, list[str]] = {
            "feature": [],
            "fix": [],
            "breaking": [],
            "improvement": [],
            "security": [],
            "deprecation": [],
            "other": [],
        }

        for e in entries:
            line = f"- {e.message}"
            if e.scope:
                line = f"- **{e.scope}:** {e.message}"
            if e.sha:
                line += f" ({e.sha})"

            if e.breaking:
                sections["breaking"].append(line)
            elif e.type == "feature":
                sections["feature"].append(line)
            elif e.type == "fix":
                sections["fix"].append(line)
            elif e.type in ("perf", "refactor"):
                sections["improvement"].append(line)
            elif e.type == "security":
                sections["security"].append(line)
            elif e.type == "deprecation":
                sections["deprecation"].append(line)
            else:
                sections["other"].append(line)

        now = datetime.now(UTC).strftime("%Y-%m-%d")
        lines = ["# Changelog\n", f"## [{now}]\n"]

        section_map = [
            ("breaking", "Breaking Changes"),
            ("feature", "Features"),
            ("improvement", "Improvements"),
            ("fix", "Bug Fixes"),
            ("security", "Security"),
            ("deprecation", "Deprecations"),
            ("other", "Other"),
        ]

        for key, title in section_map:
            if sections[key]:
                lines.append(f"### {title}\n")
                lines.extend(f"{item}\n" for item in sections[key])
                lines.append("\n")

        return "".join(lines)


class ADRAutomator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.changelog = CHANGELOGAutomator(project_root)

    def generate_from_git(self) -> None:
        entries = self.changelog._parse_git_log()
        adrs_dir = self.project_root / "docs" / "adrs"
        adrs_dir.mkdir(parents=True, exist_ok=True)

        decisions = [e for e in entries if e.type in ("feature", "breaking")]
        if not decisions:
            return

        content = """# Architecture Decision Log

This log lists architectural decisions for the project.

| ADR | Title | Status | Date |
|-----|-------|--------|------|
"""
        adr_files = sorted(adrs_dir.glob("*.md"))
        for af in adr_files:
            text = af.read_text()
            title_match = re.search(r"# ADR-\d+:\s*(.*)", text)
            status_match = re.search(r"\*\*Status:\*\*\s*(.*)", text)
            date_match = re.search(r"\*\*Date:\*\*\s*(.*)", text)
            title = title_match.group(1) if title_match else af.stem
            status = status_match.group(1).strip() if status_match else "Unknown"
            date = date_match.group(1).strip() if date_match else ""
            content += f"| {af.stem[:4]} | {title} | {status} | {date} |\n"

        (adrs_dir / "README.md").write_text(content)


class ReleaseNotesAutomator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def generate(self, version: str, previous_version: str | None = None) -> ReleaseNote:
        entries = CHANGELOGAutomator(self.project_root)._parse_git_log(since_tag=previous_version)

        note = ReleaseNote(
            version=version,
            date=datetime.now(UTC).strftime("%Y-%m-%d"),
        )

        for e in entries:
            line = e.message
            if e.scope:
                line = f"**{e.scope}:** {line}"

            if e.breaking:
                note.breaking_changes.append(line)
            elif e.type == "feature":
                note.features.append(line)
            elif e.type == "fix":
                note.fixes.append(line)
            elif e.type == "security":
                note.security.append(line)
            elif e.type == "deprecation":
                note.deprecations.append(line)
            else:
                note.improvements.append(line)

        return note

    def write(self, note: ReleaseNote, output_path: str = "RELEASE_NOTES.md") -> None:
        lines = [f"# Release {note.version} — {note.date}\n"]

        sections = [
            ("Breaking Changes", note.breaking_changes),
            ("Features", note.features),
            ("Improvements", note.improvements),
            ("Bug Fixes", note.fixes),
            ("Security", note.security),
            ("Deprecations", note.deprecations),
        ]

        for title, items in sections:
            if items:
                lines.append(f"## {title}\n")
                lines.extend(f"- {item}\n" for item in items)
                lines.append("\n")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(lines))
