from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Generic, Literal, TypeVar


ColumnRole = Literal["supporting", "hero"]
ReferenceAuthority = Literal["style_layout_evidence", "guidance_only"]

P = TypeVar("P")


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Point:
        return Point(self.x + self.width / 2, self.y + self.height / 2)

    def inset(self, dx: float, dy: float | None = None) -> Rect:
        inset_y = dx if dy is None else dy
        return Rect(self.x + dx, self.y + inset_y, self.width - 2 * dx, self.height - 2 * inset_y)


@dataclass(frozen=True)
class LayoutBox:
    id: str
    bounds: Rect


@dataclass(frozen=True)
class Column:
    index: int
    id: str
    title: str
    role: ColumnRole
    ratio: float
    bounds: Rect
    object_ids: tuple[str, ...]
    local_boxes: tuple[LayoutBox, ...] = ()

    def box(self, box_id: str) -> Rect:
        for box in self.local_boxes:
            if box.id == box_id:
                return box.bounds
        raise KeyError(box_id)


@dataclass(frozen=True)
class Layout:
    kind: str
    ratio: tuple[float, ...]
    columns: tuple[Column, ...]
    flow_object_id: str


@dataclass(frozen=True)
class Reference:
    source: str
    authority: ReferenceAuthority
    note: str


@dataclass(frozen=True)
class SemanticObject(Generic[P]):
    id: str
    kind: str
    column: int
    label: str
    payload: P


@dataclass(frozen=True)
class Scene:
    id: str
    width: int
    height: int
    source_files: tuple[str, ...]
    reference: Reference
    layout: Layout
    objects: tuple[SemanticObject[Any], ...]

    def object_by_id(self, object_id: str) -> SemanticObject[Any]:
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        raise KeyError(object_id)

    def object_by_kind(self, kind: str) -> SemanticObject[Any]:
        for obj in self.objects:
            if obj.kind == kind:
                return obj
        raise KeyError(kind)

    def objects_in_column(self, column_index: int) -> tuple[SemanticObject[Any], ...]:
        return tuple(obj for obj in self.objects if obj.column == column_index)

    def replace_payload(self, object_id: str, payload: object) -> Scene:
        objects = tuple(
            replace(obj, payload=payload) if obj.id == object_id else obj
            for obj in self.objects
        )
        return replace(self, objects=objects)
