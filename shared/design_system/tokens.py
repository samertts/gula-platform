from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Colors:
    primary: str = "#1B5E20"
    primary_light: str = "#4C8C4A"
    primary_dark: str = "#003300"
    secondary: str = "#0277BD"
    secondary_light: str = "#58A5F0"
    secondary_dark: str = "#004C8C"
    accent: str = "#FF6F00"
    accent_light: str = "#FFA040"
    error: str = "#D32F2F"
    warning: str = "#F57C00"
    success: str = "#388E3C"
    info: str = "#1976D2"
    background: str = "#FAFAFA"
    surface: str = "#FFFFFF"
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_disabled: str = "#BDBDBD"
    border: str = "#E0E0E0"
    divider: str = "#EEEEEE"


@dataclass(frozen=True)
class Typography:
    font_family_arabic: str = '"Noto Sans Arabic", "Cairo", sans-serif'
    font_family_latin: str = '"Inter", "Roboto", sans-serif'
    h1_size: str = "2.25rem"
    h1_weight: str = "700"
    h2_size: str = "1.875rem"
    h2_weight: str = "600"
    h3_size: str = "1.5rem"
    h3_weight: str = "600"
    body_size: str = "1rem"
    body_weight: str = "400"
    small_size: str = "0.875rem"
    caption_size: str = "0.75rem"
    line_height: str = "1.6"


@dataclass(frozen=True)
class Spacing:
    xs: str = "0.25rem"
    sm: str = "0.5rem"
    md: str = "1rem"
    lg: str = "1.5rem"
    xl: str = "2rem"
    xxl: str = "3rem"


@dataclass(frozen=True)
class BorderRadius:
    sm: str = "4px"
    md: str = "8px"
    lg: str = "12px"
    xl: str = "16px"
    full: str = "50%"


@dataclass(frozen=True)
class Shadows:
    sm: str = "0 1px 3px rgba(0,0,0,0.12)"
    md: str = "0 4px 6px rgba(0,0,0,0.15)"
    lg: str = "0 10px 25px rgba(0,0,0,0.15)"


@dataclass(frozen=True)
class Breakpoints:
    xs: str = "480px"
    sm: str = "768px"
    md: str = "1024px"
    lg: str = "1280px"
    xl: str = "1440px"


@dataclass(frozen=True)
class ZIndex:
    dropdown: int = 100
    sticky: int = 200
    modal_backdrop: int = 300
    modal: int = 400
    toast: int = 500
    tooltip: int = 600


@dataclass(frozen=True)
class DesignTokens:
    colors: Colors = field(default_factory=Colors)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    border_radius: BorderRadius = field(default_factory=BorderRadius)
    shadows: Shadows = field(default_factory=Shadows)
    breakpoints: Breakpoints = field(default_factory=Breakpoints)
    z_index: ZIndex = field(default_factory=ZIndex)


design_tokens = DesignTokens()
