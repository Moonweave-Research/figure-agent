from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Palette:
    ink: str = "#171717"
    muted: str = "#69707a"
    rule: str = "#d9dde4"
    panel_fill: str = "#fcfdff"
    panel_hero_fill: str = "#fff7f6"
    panel_tint: str = "#f4f7fb"
    sulfur_yellow: str = "#e0c884"
    sulfur_amber: str = "#b89060"
    sulfur_brown: str = "#7a5a30"
    shallow_blue: str = "#3a78c5"
    shallow_blue_light: str = "#dde8f5"
    deep_red: str = "#9d3838"
    deep_red_mid: str = "#b85050"
    deep_red_light: str = "#ead7d7"
    violet: str = "#6f42c1"
    violet_light: str = "#eadfff"
    metal: str = "#818b99"
    white: str = "#ffffff"


@dataclass(frozen=True)
class Typography:
    family: str = "Helvetica, Arial, sans-serif"
    title_size: float = 22.0
    hero_title_size: float = 16.0
    support_title_size: float = 13.5
    subtitle_size: float = 13.5
    label_size: float = 15.0
    section_label_size: float = 13.0
    plot_label_size: float = 10.5
    annotation_size: float = 11.0
    callout_size: float = 13.0
    small_size: float = 12.0


@dataclass(frozen=True)
class FigureStyle:
    palette: Palette = field(default_factory=Palette)
    typography: Typography = field(default_factory=Typography)
    panel_radius: float = 8.0
    panel_stroke_width: float = 1.0
    hero_stroke_width: float = 1.25
    schematic_stroke_width: float = 1.15
    accent_stroke_width: float = 1.65
    plot_stroke_width: float = 1.9


DEFAULT_STYLE = FigureStyle()
