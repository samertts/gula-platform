"""GULA Design System — canonical UI tokens and component definitions.

This module defines the unified design language used across all GULA
frontend applications (frontend-v2, client, frontend).  It provides
design tokens, component blueprints, and accessibility guidelines.
"""

from .components import (
    ButtonSpec,
    CardSpec,
    DialogSpec,
    FormSpec,
    IconSpec,
    InputSpec,
    TableSpec,
)
from .rtl import RTLStyles
from .tokens import (
    BorderRadius,
    Breakpoints,
    Colors,
    Shadows,
    Spacing,
    Typography,
    ZIndex,
    design_tokens,
)

__all__ = [
    "BorderRadius",
    "Breakpoints",
    "ButtonSpec",
    "CardSpec",
    "Colors",
    "DialogSpec",
    "FormSpec",
    "IconSpec",
    "InputSpec",
    "RTLStyles",
    "Shadows",
    "Spacing",
    "TableSpec",
    "Typography",
    "ZIndex",
    "design_tokens",
]
