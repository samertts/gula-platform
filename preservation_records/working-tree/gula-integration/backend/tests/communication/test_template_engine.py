"""Unit tests: Template Engine (multi-language, versioning, variables,
HTML/Markdown escaping, renderer registry)."""

from __future__ import annotations

import pytest

from shared.communication.model import ContentFormat
from shared.communication.templates import (
    HtmlRenderer,
    MarkdownV2Renderer,
    PlainRenderer,
    Template,
    TemplateEngine,
)


class TestRenderers:
    def test_plain_substitutes_variables(self):
        out = PlainRenderer().render("Hello {name}", {"name": "Ali"}, strict=False)
        assert out == "Hello Ali"

    def test_plain_keeps_missing_variable_loose_mode(self):
        out = PlainRenderer().render("Hi {name}", {}, strict=False)
        assert out == "Hi {name}"

    def test_strict_mode_raises_on_missing(self):
        with pytest.raises(KeyError):
            PlainRenderer().render("Hi {name}", {}, strict=True)

    def test_html_escapes_variables(self):
        out = HtmlRenderer().render("<b>{name}</b>", {"name": "<script>x</script>"}, strict=False)
        assert "<script>" not in out
        assert "&lt;script&gt;" in out
        assert "<b>" in out  # template markup preserved

    def test_markdown_escapes_reserved_chars(self):
        out = MarkdownV2Renderer().render("{name}*", {"name": "a*b"}, strict=False)
        assert "a\\*b" in out

    def test_custom_renderer_registered(self):
        engine = TemplateEngine()
        engine.register_renderer(ContentFormat.PLAIN, PlainRenderer())
        engine.register(
            Template(id="t", bodies={ContentFormat.PLAIN: "{x}"}),
        )
        assert engine.render("t", {"x": "y"}).body == "y"


class TestVersioning:
    def test_versioned_lookup_picks_newest(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", version="1", locale="", bodies={ContentFormat.PLAIN: "v1"}))
        engine.register(Template(id="t", version="2", locale="", bodies={ContentFormat.PLAIN: "v2"}))
        rendered = engine.render("t")
        assert rendered.body == "v2"
        assert rendered.template_version == "2"

    def test_explicit_version_pinned(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", version="1", locale="", bodies={ContentFormat.PLAIN: "v1"}))
        engine.register(Template(id="t", version="2", locale="", bodies={ContentFormat.PLAIN: "v2"}))
        assert engine.render("t", version="1").body == "v1"

    def test_version_of(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", version="3", bodies={ContentFormat.PLAIN: "x"}))
        assert engine.version_of("t") == "3"


class TestLocales:
    def test_exact_locale_wins(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", locale="ar", bodies={ContentFormat.PLAIN: "مرحبا"}))
        engine.register(Template(id="t", locale="en", bodies={ContentFormat.PLAIN: "hello"}))
        assert engine.render("t", locale="ar").body == "مرحبا"

    def test_falls_back_to_neutral(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", locale="", bodies={ContentFormat.PLAIN: "neutral"}))
        rendered = engine.render("t", locale="ar")
        assert rendered.body == "neutral"
        assert rendered.locale == ""


class TestFormats:
    def test_body_format_fallback(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", bodies={ContentFormat.HTML: "<b>{n}</b>"}))
        html = engine.render("t", {"n": "x"}, format=ContentFormat.HTML)
        assert html.body == "<b>x</b>"
        plain = engine.render("t", {"n": "x"}, format=ContentFormat.PLAIN)
        assert plain.body == "<b>x</b>"  # falls back to the HTML body

    def test_render_unknown_template_raises(self):
        engine = TemplateEngine()
        with pytest.raises(KeyError):
            engine.render("nope")

    def test_duplicate_template_rejected(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", version="1", locale="", bodies={ContentFormat.PLAIN: "a"}))
        with pytest.raises(ValueError):
            engine.register(Template(id="t", version="1", locale="", bodies={ContentFormat.PLAIN: "b"}))

    def test_subject_substituted(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", subject="Hi {name}", bodies={ContentFormat.PLAIN: "body"}))
        rendered = engine.render("t", {"name": "Sam"})
        assert rendered.subject == "Hi Sam"

    def test_list_templates(self):
        engine = TemplateEngine()
        engine.register(Template(id="t", version="1", bodies={ContentFormat.PLAIN: "a"}))
        engine.register(Template(id="u", version="1", bodies={ContentFormat.PLAIN: "b"}))
        assert {t["id"] for t in engine.list_templates()} == {"t", "u"}
