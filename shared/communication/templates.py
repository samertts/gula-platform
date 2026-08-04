"""Template engine for the GULA Communication Platform Core.

Multi-language, versioned, renderer-pluggable content templates. Renderers
(plain / HTML / MarkdownV2 today, more later) are registered into the engine
— the engine never couples to a specific rendering library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from .model import ContentFormat

_VARIABLE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class Renderer(Protocol):
    """Renders a template body for one content format."""

    def render(self, text: str, variables: dict[str, Any], strict: bool) -> str: ...


_MISSING = object()


def _substitute(text: str, variables: dict[str, Any], strict: bool) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = variables.get(key, _MISSING)
        if value is _MISSING:
            if strict:
                raise KeyError(f"template variable not provided: {key}")
            return match.group(0)
        return str(value)

    return _VARIABLE.sub(_replace, text)


class PlainRenderer:
    """Plain text renderer: direct substitution, no escaping."""

    def render(self, text: str, variables: dict[str, Any], strict: bool) -> str:
        return _substitute(text, variables, strict)


class HtmlRenderer:
    """HTML renderer: variable values are HTML-escaped before substitution."""

    _ESCAPES = str.maketrans(
        {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;"},
    )

    def render(self, text: str, variables: dict[str, Any], strict: bool) -> str:
        escaped = {
            key: str(value).translate(self._ESCAPES) for key, value in variables.items()
        }
        return _substitute(text, escaped, strict)


class MarkdownV2Renderer:
    """MarkdownV2 renderer.

    Variable values are escaped for MarkdownV2 reserved characters so user
    data can never break formatting or inject markup.
    """

    _RESERVED = "_*[]()~`>#+-=|{}.!"

    def render(self, text: str, variables: dict[str, Any], strict: bool) -> str:
        def _escape(value: Any) -> str:
            return "".join(
                f"\\{ch}" if ch in self._RESERVED else ch for ch in str(value)
            )

        escaped = {key: _escape(value) for key, value in variables.items()}
        return _substitute(text, escaped, strict)


@dataclass(frozen=True)
class Template:
    """A versioned, locale-scoped communication template."""

    id: str
    version: str = "1"
    locale: str = ""  # BCP-47 ("ar", "en", "ar-IQ"); "" = neutral/fallback
    subject: str = ""
    bodies: dict[ContentFormat, str] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        coerced = {}
        for fmt, body in self.bodies.items():
            if isinstance(fmt, str):
                fmt = ContentFormat(fmt)
            coerced[fmt] = body
        object.__setattr__(self, "bodies", coerced)

    def body_for(self, fmt: ContentFormat) -> str:
        """Return the body for a format, falling back across formats."""
        if fmt in self.bodies:
            return self.bodies[fmt]
        for candidate in (ContentFormat.HTML, ContentFormat.MARKDOWN, ContentFormat.PLAIN):
            if candidate in self.bodies:
                return self.bodies[candidate]
        raise KeyError(f"template {self.id} has no renderable body")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "locale": self.locale,
            "subject": self.subject,
            "bodies": {fmt.value: body for fmt, body in self.bodies.items()},
        }


@dataclass(frozen=True)
class RenderedContent:
    """Finished content ready for delivery."""

    template_id: str
    template_version: str
    locale: str
    subject: str
    body: str
    format: ContentFormat

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_version": self.template_version,
            "locale": self.locale,
            "subject": self.subject,
            "body": self.body,
            "format": self.format.value,
        }


class TemplateEngine:
    """Locale-aware, versioned template registry + renderer pipeline."""

    def __init__(self, strict_variables: bool = False) -> None:
        self._templates: dict[tuple[str, str, str], Template] = {}
        self._renderers: dict[ContentFormat, Renderer] = {
            ContentFormat.PLAIN: PlainRenderer(),
            ContentFormat.HTML: HtmlRenderer(),
            ContentFormat.MARKDOWN: MarkdownV2Renderer(),
        }
        self._strict = strict_variables

    def register_renderer(self, fmt: ContentFormat, renderer: Renderer) -> None:
        """Register a renderer for a content format (future formats)."""
        self._renderers[fmt] = renderer

    def register(self, template: Template) -> Template:
        key = (template.id, template.version, template.locale)
        if key in self._templates:
            raise ValueError(f"template already registered: {template}")
        self._templates[key] = template
        return template

    def get(self, template_id: str, version: str = "", locale: str = "") -> Template | None:
        """Resolve a template with locale fallback (exact → neutral → newest)."""
        if version:
            for candidate in (locale, "",):
                tpl = self._templates.get((template_id, version, candidate))
                if tpl is not None:
                    return tpl
            return None
        candidates = [
            t
            for (tid, _v, loc), t in self._templates.items()
            if tid == template_id and loc in (locale, "")
        ]
        if not candidates:
            return None
        # Prefer the requested locale; within a locale prefer the newest version.
        exact = [t for t in candidates if t.locale == locale]
        pool = exact if exact else candidates
        ordered = sorted(pool, key=lambda t: _version_key(t.version))
        return ordered[-1] if ordered else None

    def list_templates(self) -> list[dict[str, Any]]:
        return [tpl.to_dict() for tpl in self._templates.values()]

    def render(
        self,
        template_id: str,
        variables: dict[str, Any] | None = None,
        *,
        version: str = "",
        locale: str = "",
        format: ContentFormat = ContentFormat.PLAIN,
        strict: bool | None = None,
    ) -> RenderedContent:
        """Render a template to one content format."""
        template = self.get(template_id, version=version, locale=locale)
        if template is None:
            raise KeyError(f"template not found: {template_id}")
        renderer = self._renderers[format]
        body = renderer.render(
            template.body_for(format),
            variables or {},
            self._strict if strict is None else strict,
        )
        return RenderedContent(
            template_id=template.id,
            template_version=template.version,
            locale=template.locale,
            subject=_substitute(template.subject, variables or {}, self._strict),
            body=body,
            format=format,
        )

    def version_of(self, template_id: str, locale: str = "") -> str:
        template = self.get(template_id, locale=locale)
        return template.version if template else ""


def _version_key(version: str) -> tuple[int, ...]:
    """Comparable key for dotted versions ('1.2.3' → (1, 2, 3))."""
    parts = []
    for part in str(version).replace("v", "").split("."):
        token = ""
        for ch in part:
            token += ch if ch.isdigit() else " "
        try:
            parts.append(int(token.split()[0]))
        except (IndexError, ValueError):
            parts.append(0)
    return tuple(parts)


__all__ = [
    "HtmlRenderer",
    "MarkdownV2Renderer",
    "PlainRenderer",
    "RenderedContent",
    "Renderer",
    "Template",
    "TemplateEngine",
]