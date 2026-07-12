"""GULA Design System — canonical UI tokens and component definitions.

This module defines the unified design language used across all GULA
frontend applications (frontend-v2, client, frontend).  It provides
design tokens, component blueprints, and accessibility guidelines.
"""

from .tokens import (
    Colors,
    Typography,
    Spacing,
    BorderRadius,
    Shadows,
    Breakpoints,
    ZIndex,
    design_tokens,
)
from .components import (
    ButtonSpec,
    CardSpec,
    DialogSpec,
    FormSpec,
    InputSpec,
    TableSpec,
    IconSpec,
)
from .rtl import RTLStyles

__all__ = [
    "Colors",
    "Typography",
    "Spacing",
    "BorderRadius",
    "Shadows",
    "Breakpoints",
    "ZIndex",
    "design_tokens",
    "ButtonSpec",
    "CardSpec",
    "DialogSpec",
    "FormSpec",
    "InputSpec",
    "TableSpec",
    "IconSpec",
    "RTLStyles",
]
