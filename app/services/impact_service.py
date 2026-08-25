from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import String, cast, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.models.metamodel import (
    ArchitectureObject,
    ArchitectureRelationship,
    ObjectType,
    RelationshipType,
)
from app.repositories.object_repository import ObjectRepository


class ImpactAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class ImpactPathStep:
    relationship_id: str
    relationship_type_key: str
    label: str
    direction: str
    from_object_id: str
    to_object_id: str


@dataclass
class ImpactResult:
    object: ArchitectureObject
    depth: int
    path_object_ids: list[str]
    path_steps: list[ImpactPathStep]

    @property
    def direct(self) -> bool:
        return self.depth == 1


@dataclass
class ImpactAnalysis:
    root: ArchitectureObject
    depth: int
    results: list[ImpactResult]
    relationship_type_keys: list[str] = field(default_factory=list)
    object_type_keys: list[str] = field(default_factory=list)

    @property
    def direct_results(self) -> list[ImpactResult]:
        return [item for item in self.results if item.direct]

    @property
    def indirect_results(self) -> list[ImpactResult]:
        return [item for item in self.results if not item.direct]

    def grouped(self, *, direct: bool) -> dict[str, list[ImpactResult]]:
        source = self.direct_results if direct else self.indirect_results
        groups: dict[str, list[ImpactResult]] = {}
        for item in source:
            groups.setdefault(item.object.object_type.name, []).append(item)
        return dict(sorted(groups.items()))

    def graph_payload(self) -> dict[str, list[dict[str, object]]]:
        result_by_id = {item.object.id: item for item in self.results}
        included_ids = {self.root.id}
        for item in self.results:
            included_ids.update(item.path_object_ids)

        objects: dict[str, ArchitectureObject] = {self.root.id: self.root}
        for item in self.results:
            objects[item.object.id] = item.object
        missing_ids = included_ids.difference(objects)
        if missing_ids:
            # Path intermediates can be filtered out of the result list; they are populated by the service.
            for item in self.results:
                for obj in getattr(item, "_path_objects", []):
                    objects[obj.id] = obj

        nodes: list[dict[str, object]] = []
        for object_id in included_ids:
            obj = objects.get(object_id)
            if obj is None:
                continue
            result = result_by_id.get(object_id)
            nodes.append(
                {
                    "data": {
                        "id": obj.id,
                        "label": obj.name,
                        "type": obj.object_type.name,
                        "depth": result.depth if result else 0,
                        "root": obj.id == self.root.id,
                        "url": f"/explore/{obj.id}",
                    }
                }
            )

        edge_map: dict[str, dict[str, object]] = {}
        for item in self.results:
            for step in item.path_steps:
                edge_key = f"{step.relationship_id}:{step.from_object_id}:{step.to_object_id}"
                edge_map.setdefault(
                    edge_key,
                    {
                        "data": {
                            "id": edge_key,
                            "source": step.from_object_id,
                            "target": step.to_object_id,
                            "label": step.label,
                            "type": step.relationship_type_key,
                        }
                    },
                )
        return {"nodes": nodes, "edges": list(edge_map.values())}


class ImpactService:
    DEFAULT_DEPTH = 3
    MAX_DEPTH = 5

    def __init__(self, db: Session) -> None:
        self.db = db
        self.object_repo = ObjectRepository(db)

    def analyze(
        self,
        object_id: str,
        *,
        depth: int = DEFAULT_DEPTH,
        relationship_type_keys: list[str] | None = None,
        object_type_keys: list[str] | None = None,
    ) -> ImpactAnalysis:
        if depth < 1 or depth > self.MAX_DEPTH:
            raise ImpactAnalysisError(f"Depth must be between 1 and {self.MAX_DEPTH}")
        root = self.object_repo.get_by_id(object_id)
        if root is None:
            raise ImpactAnalysisError("Object not found")

        rel_filters = sorted({value for value in (relationship_type_keys or []) if value})
        object_filters = sorted({value for value in (object_type_keys or []) if value})

        rel = ArchitectureRelationship.__table__
        rel_type = RelationshipType.__table__

        outbound = (
            select(
                rel.c.source_object_id.label("from_id"),
                rel.c.target_object_id.label("to_id"),
                rel.c.id.label("relationship_id"),
                rel_type.c.key.label("relationship_type_key"),
                rel_type.c.name.label("edge_label"),
                literal("outbound").label("direction"),
            )
            .join(rel_type, rel_type.c.id == rel.c.relationship_type_id)
            .where(rel.c.archived_at.is_(None))
        )
        inbound = (
            select(
                rel.c.target_object_id.label("from_id"),
                rel.c.source_object_id.label("to_id"),
                rel.c.id.label("relationship_id"),
                rel_type.c.key.label("relationship_type_key"),
                rel_type.c.inverse_label.label("edge_label"),
                literal("inbound").label("direction"),
            )
            .join(rel_type, rel_type.c.id == rel.c.relationship_type_id)
            .where(rel.c.archived_at.is_(None))
        )
        if rel_filters:
            outbound = outbound.where(rel_type.c.key.in_(rel_filters))
            inbound = inbound.where(rel_type.c.key.in_(rel_filters))
        edges = union_all(outbound, inbound).subquery("impact_edges")

        anchor = select(
            literal(root.id).label("root_id"),
            literal(root.id).label("current_id"),
            literal(0).label("depth"),
            literal(f"|{root.id}|").label("object_path"),
            literal("").label("relationship_path"),
            literal("").label("label_path"),
            literal("").label("direction_path"),
        )
        paths = anchor.cte("impact_paths", recursive=True)

        next_token = literal("|") + cast(edges.c.to_id, String) + literal("|")
        dialect = self.db.bind.dialect.name if self.db.bind is not None else ""
        if dialect == "postgresql":
            unseen = func.strpos(paths.c.object_path, next_token) == 0
        else:
            unseen = func.instr(paths.c.object_path, next_token) == 0

        recursive = (
            select(
                paths.c.root_id,
                edges.c.to_id,
                (paths.c.depth + 1).label("depth"),
                (paths.c.object_path + cast(edges.c.to_id, String) + literal("|")).label("object_path"),
                (
                    paths.c.relationship_path
                    + cast(edges.c.relationship_id, String)
                    + literal("|")
                ).label("relationship_path"),
                (paths.c.label_path + cast(edges.c.edge_label, String) + literal("|")).label("label_path"),
                (paths.c.direction_path + cast(edges.c.direction, String) + literal("|")).label("direction_path"),
            )
            .join(edges, edges.c.from_id == paths.c.current_id)
            .where(paths.c.depth < depth, unseen)
        )
        paths = paths.union_all(recursive)

        rows = self.db.execute(
            select(
                paths.c.current_id,
                paths.c.depth,
                paths.c.object_path,
                paths.c.relationship_path,
                paths.c.label_path,
                paths.c.direction_path,
            ).where(paths.c.depth > 0)
        ).all()

        best_rows: dict[str, object] = {}
        for row in rows:
            current = best_rows.get(row.current_id)
            if current is None or row.depth < current.depth:
                best_rows[row.current_id] = row

        if not best_rows:
            return ImpactAnalysis(root=root, depth=depth, results=[], relationship_type_keys=rel_filters, object_type_keys=object_filters)

        objects = list(
            self.db.scalars(
                select(ArchitectureObject)
                .join(ObjectType)
                .where(
                    ArchitectureObject.id.in_(best_rows),
                    ArchitectureObject.archived_at.is_(None),
                )
            ).unique().all()
        )
        object_map = {obj.id: obj for obj in objects}
        all_path_ids: set[str] = set()
        for row in best_rows.values():
            all_path_ids.update(self._split_path(row.object_path))
        path_objects = list(
            self.db.scalars(
                select(ArchitectureObject).where(
                    ArchitectureObject.id.in_(all_path_ids),
                    ArchitectureObject.archived_at.is_(None),
                )
            ).unique().all()
        )
        path_object_map = {obj.id: obj for obj in path_objects}

        relationship_ids: set[str] = set()
        for row in best_rows.values():
            relationship_ids.update(self._split_path(row.relationship_path))
        rel_rows = list(
            self.db.scalars(
                select(ArchitectureRelationship).where(ArchitectureRelationship.id.in_(relationship_ids))
            ).unique().all()
        )
        relationship_map = {item.id: item for item in rel_rows}

        results: list[ImpactResult] = []
        for object_id, row in best_rows.items():
            obj = object_map.get(object_id)
            if obj is None:
                continue
            if object_filters and obj.object_type.key not in object_filters:
                continue
            object_path = self._split_path(row.object_path)
            rel_path = self._split_path(row.relationship_path)
            labels = self._split_path(row.label_path)
            directions = self._split_path(row.direction_path)
            steps: list[ImpactPathStep] = []
            for index, relationship_id in enumerate(rel_path):
                relationship = relationship_map.get(relationship_id)
                if relationship is None or index + 1 >= len(object_path):
                    continue
                steps.append(
                    ImpactPathStep(
                        relationship_id=relationship_id,
                        relationship_type_key=relationship.relationship_type.key,
                        label=labels[index] if index < len(labels) else relationship.relationship_type.name,
                        direction=directions[index] if index < len(directions) else "outbound",
                        from_object_id=object_path[index],
                        to_object_id=object_path[index + 1],
                    )
                )
            result = ImpactResult(object=obj, depth=row.depth, path_object_ids=object_path, path_steps=steps)
            result._path_objects = [path_object_map[item_id] for item_id in object_path if item_id in path_object_map]  # type: ignore[attr-defined]
            results.append(result)

        results.sort(key=lambda item: (item.depth, item.object.object_type.name, item.object.name.lower()))
        return ImpactAnalysis(
            root=root,
            depth=depth,
            results=results,
            relationship_type_keys=rel_filters,
            object_type_keys=object_filters,
        )

    @staticmethod
    def _split_path(value: str | None) -> list[str]:
        if not value:
            return []
        return [part for part in value.split("|") if part]
