from __future__ import annotations

import re
from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class AccessibilityEvaluator(DimensionEvaluator):
    WCAG_LEVELS = ["A", "AA", "AAA"]

    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        frontend_target = self._find_frontend(target)
        if not frontend_target:
            self._add_evidence(
                "frontend_found",
                value=False,
                passed=False,
                source="Path scan",
            )
            return self._result(0.0)

        rtl_support = self._check_rtl_support(frontend_target)
        self._add_evidence(
            "rtl_support",
            value=rtl_support,
            source="Frontend files",
            passed=rtl_support,
        )
        if not rtl_support:
            self._add_remediation(
                "Add RTL (right-to-left) CSS support for Arabic UI",
                severity="high",
                effort="6h",
            )

        aria_labels = self._check_aria_labels(frontend_target)
        self._add_evidence(
            "aria_labels_count",
            value=aria_labels,
            source="Frontend files",
            passed=aria_labels > 5,
        )
        if aria_labels <= 5:
            self._add_remediation(
                "Add ARIA labels to interactive elements for screen reader support",
                severity="medium",
                effort="4h",
            )

        alt_texts = self._check_alt_texts(frontend_target)
        self._add_evidence(
            "alt_texts_count",
            value=alt_texts,
            source="Frontend files",
            passed=alt_texts > 0,
        )
        if not alt_texts:
            self._add_remediation(
                "Add alt text to all images for accessibility",
                severity="medium",
                effort="2h",
            )

        contrast_ratio = self._check_color_contrast(frontend_target)
        self._add_evidence(
            "high_contrast_support",
            value=contrast_ratio,
            source="Frontend files",
            passed=contrast_ratio,
        )
        if not contrast_ratio:
            self._add_remediation(
                "Ensure color contrast meets WCAG 2.1 AA minimum ratio (4.5:1)",
                severity="medium",
                effort="3h",
            )

        dark_mode = self._check_dark_mode(frontend_target)
        self._add_evidence(
            "dark_mode_support",
            value=dark_mode,
            source="Frontend files",
            passed=dark_mode,
        )
        if not dark_mode:
            self._add_remediation(
                "Add dark mode support via CSS custom properties",
                severity="low",
                effort="3h",
            )

        keyboard_nav = self._check_keyboard_navigation(frontend_target)
        self._add_evidence(
            "keyboard_navigation",
            value=keyboard_nav,
            source="Frontend files",
            passed=keyboard_nav,
        )
        if not keyboard_nav:
            self._add_remediation(
                "Ensure all interactive elements are keyboard-accessible",
                severity="medium",
                effort="4h",
            )

        focus_indicators = self._check_focus_indicators(frontend_target)
        self._add_evidence(
            "focus_indicators",
            value=focus_indicators,
            source="Frontend files",
            passed=focus_indicators,
        )
        if not focus_indicators:
            self._add_remediation(
                "Add visible focus indicators for keyboard navigation (WCAG 2.4.7)",
                severity="low",
                effort="2h",
            )

        screen_reader = self._check_screen_reader_support(frontend_target)
        self._add_evidence(
            "screen_reader_support",
            value=screen_reader,
            source="Frontend files",
            passed=screen_reader,
        )
        if not screen_reader:
            self._add_remediation(
                "Use semantic HTML elements and aria-live regions for screen reader announcements",
                severity="medium",
                effort="3h",
            )

        score = 1.0
        checks = [
            (rtl_support, 0.2),
            (aria_labels > 5, 0.1),
            (alt_texts > 0, 0.1),
            (contrast_ratio, 0.1),
            (dark_mode, 0.1),
            (keyboard_nav, 0.1),
            (focus_indicators, 0.05),
            (screen_reader, 0.1),
        ]
        for passed, penalty in checks:
            if not passed:
                score -= penalty

        return self._result(score)

    def _find_frontend(self, target: Path) -> Path | None:
        candidates = [
            target / "frontend-v2" / "src",
            target / "frontend" / "src",
            target.parent / "frontend-v2" / "src",
            target.parent / "frontend" / "src",
        ]
        for c in candidates:
            if c.exists():
                return c
        if (target / "src").exists():
            return target / "src"
        if (target / "app" / "templates").exists():
            return target / "app" / "templates"
        return None

    def _check_rtl_support(self, target: Path) -> bool:
        for pattern in ["*.css", "*.scss", "*.less"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if (
                        "direction: rtl" in content
                        or 'dir="rtl"' in content
                        or "rtl" in content.lower()
                    ):
                        return True
                except Exception:
                    continue
        for pattern in ["*.tsx", "*.jsx", "*.vue"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if 'dir="rtl"' in content or "direction: 'rtl'" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_aria_labels(self, target: Path) -> int:
        count = 0
        for pattern in ["*.tsx", "*.jsx", "*.vue", "*.html"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    count += len(re.findall(r"aria-label[=]", content))
                    count += len(re.findall(r"aria-labelledby[=]", content))
                except Exception:
                    continue
        return count

    def _check_alt_texts(self, target: Path) -> int:
        count = 0
        for pattern in ["*.tsx", "*.jsx", "*.vue", "*.html"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    count += len(re.findall(r'alt=[\'"]', content))
                except Exception:
                    continue
        return count

    def _check_color_contrast(self, target: Path) -> bool:
        for pattern in ["*.css", "*.scss", "*.less"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if "--contrast" in content or "--color" in content or "contrast" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_dark_mode(self, target: Path) -> bool:
        for pattern in ["*.css", "*.scss", "*.less"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if (
                        "prefers-color-scheme: dark" in content
                        or "@media (prefers-color-scheme: dark)" in content
                    ):
                        return True
                except Exception:
                    continue
        for f in target.rglob("*.tsx"):
            try:
                content = f.read_text()
                if "dark" in content.lower() and (
                    "theme" in content.lower() or "mode" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_keyboard_navigation(self, target: Path) -> bool:
        for pattern in ["*.tsx", "*.jsx", "*.vue", "*.html"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if (
                        "onKeyDown" in content
                        or "onkeydown" in content
                        or "tabIndex" in content
                        or "tabindex" in content
                    ):
                        return True
                except Exception:
                    continue
        return False

    def _check_focus_indicators(self, target: Path) -> bool:
        for pattern in ["*.css", "*.scss", "*.less"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if ":focus" in content or "focus-" in content or "focus:" in content:
                        return True
                except Exception:
                    continue
        return False

    def _check_screen_reader_support(self, target: Path) -> bool:
        for pattern in ["*.tsx", "*.jsx", "*.vue", "*.html"]:
            for f in target.rglob(pattern):
                try:
                    content = f.read_text()
                    if (
                        "sr-only" in content
                        or "screen-reader" in content
                        or "aria-live" in content
                        or "role=" in content
                    ):
                        return True
                except Exception:
                    continue
        return False
