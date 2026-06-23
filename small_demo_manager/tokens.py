"""
Design tokens for Small Demo Manager.
Central source of truth for all visual design values.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ColorTokens:
    accent_button: str = "#1565C0"
    accent_light: str = "#64B5F6"
    accent_hover: str = "#0D47A1"

    surface_bg: str = "#1E1E1E"
    surface_card: str = "#2A2A2A"
    surface_elevated: str = "#333333"

    text_primary: str = "#E0E0E0"
    text_secondary: str = "#9E9E9E"
    text_on_accent: str = "#FFFFFF"

    border: str = "#666666"
    border_focus: str = "#64B5F6"

    success: str = "#4CAF50"
    warning: str = "#FF9800"
    error: str = "#EF5350"
    info: str = "#42A5F5"

    indicator_bg: str = "#3A3A3A"
    selection_bg: str = "rgba(21, 101, 192, 0.15)"


@dataclass
class LightColorTokens:
    accent_button: str = "#1565C0"
    accent_light: str = "#42A5F5"
    accent_hover: str = "#0D47A1"

    surface_bg: str = "#FAFAFA"
    surface_card: str = "#F5F5F5"
    surface_elevated: str = "#FFFFFF"

    text_primary: str = "#212121"
    text_secondary: str = "#616161"
    text_on_accent: str = "#FFFFFF"

    border: str = "#757575"
    border_focus: str = "#1565C0"

    success: str = "#388E3C"
    warning: str = "#F57C00"
    error: str = "#D32F2F"
    info: str = "#1976D2"

    indicator_bg: str = "#FFFFFF"
    selection_bg: str = "rgba(21, 101, 192, 0.12)"


@dataclass
class TypographyTokens:
    font_family: str = "Segoe UI, -apple-system, sans-serif"
    font_mono: str = "Consolas, Courier New, monospace"

    size_xs: str = "11px"
    size_sm: str = "12px"
    size_base: str = "13px"
    size_lg: str = "15px"
    size_xl: str = "18px"
    size_2xl: str = "22px"

    weight_normal: str = "400"
    weight_semibold: str = "600"
    weight_bold: str = "700"


@dataclass
class SpacingTokens:
    xs: str = "4px"
    sm: str = "8px"
    md: str = "12px"
    lg: str = "16px"
    xl: str = "20px"
    xxl: str = "24px"

    section: str = "32px"


@dataclass
class BorderTokens:
    radius_sm: str = "3px"
    radius_md: str = "6px"
    radius_lg: str = "8px"
    radius_xl: str = "12px"

    width_default: str = "1px"
    width_focus: str = "2px"


@dataclass
class DesignTokens:
    colors: ColorTokens = field(default_factory=ColorTokens)
    light_colors: LightColorTokens = field(default_factory=LightColorTokens)
    typography: TypographyTokens = field(default_factory=TypographyTokens)
    spacing: SpacingTokens = field(default_factory=SpacingTokens)
    borders: BorderTokens = field(default_factory=BorderTokens)


TOKENS = DesignTokens()
