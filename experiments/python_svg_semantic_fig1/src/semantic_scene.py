from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Role = Literal["visual_anchor", "data_visualization", "process_flow", "annotation", "mechanism"]
Authority = Literal["ground_truth", "guidance_only", "known_defects"]
Severity = Literal["BLOCKER", "MAJOR", "MINOR"]


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class Label:
    text: str
    x: float
    y: float
    size: float = 14.0
    tone: str = "ink"
    weight: str = "normal"


@dataclass(frozen=True)
class SemanticObject:
    id: str
    role: Role
    panel_id: str
    summary: str
    must_depict: tuple[str, ...]
    must_avoid: tuple[str, ...] = ()
    labels: tuple[Label, ...] = ()
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Panel:
    id: str
    bounds: Rect
    title: str
    label: str
    role: str
    source_region: Rect | None = None


@dataclass(frozen=True)
class SemanticAssertion:
    id: str
    on: str
    statement: str
    severity: Severity


@dataclass(frozen=True)
class Reference:
    source: str
    authority: Authority
    width: int
    height: int


@dataclass(frozen=True)
class Scene:
    id: str
    width: int
    height: int
    reference: Reference
    panels: tuple[Panel, ...]
    objects: tuple[SemanticObject, ...]
    assertions: tuple[SemanticAssertion, ...]

    def object_by_id(self, object_id: str) -> SemanticObject:
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        raise KeyError(object_id)

    def panel_by_id(self, panel_id: str) -> Panel:
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        raise KeyError(panel_id)
