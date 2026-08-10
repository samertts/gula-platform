from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.identity.models.audit import AuditAction
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.organizations.hierarchy import (
    ORG_HIERARCHY_LAYERS,
    OrganizationHierarchyError,
    OrganizationHierarchyService,
    ancestor_ids,
    descendant_ids,
    effective_scope_ids,
    layer_index,
    layer_name_for,
    would_create_cycle,
)


def org(
    node_id: str, org_type: str = "health_center", parent: str | None = None
) -> NIAMOrganization:
    return NIAMOrganization(
        id=node_id,
        org_id=f"org-{node_id}",
        name_en=f"Org {node_id}",
        name_ar=f"مؤسسة {node_id}",
        org_type=org_type,
        parent_org_id=parent,
    )


class TestLayerClassification:
    def test_layers_ordered_national_to_unit(self):
        assert [layer.name for layer in ORG_HIERARCHY_LAYERS] == [
            "national",
            "directorate",
            "institution",
            "department",
            "unit",
        ]

    def test_classification_first_match_wins(self):
        assert layer_name_for("ministry") == "national"
        assert layer_name_for("directorate") == "directorate"
        assert layer_name_for("government_hospital") == "institution"
        assert layer_name_for("government_laboratory") == "institution"
        assert layer_name_for("pharmacy") == "institution"

    def test_unknown_type_is_unclassified(self):
        assert layer_name_for("vendor") == "unclassified"
        assert layer_name_for(None) == "unclassified"
        assert layer_name_for("") == "unclassified"

    def test_layer_index_deterministic(self):
        assert layer_index("national") < layer_index("directorate")
        assert layer_index("directorate") < layer_index("institution")
        assert layer_index("institution") < layer_index("department")
        assert layer_index("department") < layer_index("unit")
        assert layer_index("unknown") == len(ORG_HIERARCHY_LAYERS)


class TestAncestorChain:
    def test_root_first_chain(self):
        parent_map = {"a": None, "b": "a", "c": "b", "d": "c"}
        assert ancestor_ids(parent_map, "d") == ["a", "b", "c"]
        assert ancestor_ids(parent_map, "b") == ["a"]
        assert ancestor_ids(parent_map, "a") == []

    def test_missing_node_raises(self):
        with pytest.raises(OrganizationHierarchyError, match="node_not_found"):
            ancestor_ids({"a": None}, "zz")

    def test_cycle_raises(self):
        parent_map = {"a": "b", "b": "a"}
        with pytest.raises(OrganizationHierarchyError, match="cycle_detected"):
            ancestor_ids(parent_map, "a")

    def test_dangling_parent_raises(self):
        with pytest.raises(OrganizationHierarchyError, match="dangling_parent"):
            ancestor_ids({"a": "zz", "zz": "yy"}, "a")


class TestDescendants:
    def test_flat_children(self):
        children_map = {"a": ["b", "c"], "b": [], "c": []}
        assert descendant_ids(children_map, "a") == ["b", "c"]

    def test_multilevel_bfs_order(self):
        children_map = {"a": ["b", "c"], "b": ["d", "e"], "c": ["f"], "d": [], "e": [], "f": []}
        assert descendant_ids(children_map, "a") == ["b", "c", "d", "e", "f"]

    def test_excludes_start_and_cycles_guard(self):
        children_map = {"a": ["b", "a"], "b": ["a"]}
        assert descendant_ids(children_map, "a") == ["b"]

    def test_leaf_has_no_descendants(self):
        assert descendant_ids({}, "a") == []

    def test_deterministic_when_sorted(self):
        children_map = {"a": ["c", "b"]}
        assert descendant_ids(children_map, "a") == ["c", "b"]


class TestEffectiveScope:
    def test_scope_includes_self_and_descendants_sorted(self):
        scope = effective_scope_ids("b", ["d", "c"])
        assert scope == ["b", "c", "d"]

    def test_scope_of_leaf(self):
        assert effective_scope_ids("a", []) == ["a"]


class TestCycleCheck:
    def test_no_cycle_for_unrelated_parent(self):
        parent_map = {"a": None, "b": "c", "c": None}
        assert would_create_cycle(parent_map, "a", "b") is False

    def test_cycle_detected_when_parent_is_descendant(self):
        parent_map = {"a": None, "b": "a", "c": "b"}
        assert would_create_cycle(parent_map, "a", "b") is True
        assert would_create_cycle(parent_map, "b", "c") is True

    def test_cycle_detected_on_self(self):
        parent_map = {"a": None}
        assert would_create_cycle(parent_map, "a", "a") is True

    def test_dangling_parent_not_cycle(self):
        assert would_create_cycle({"a": None}, "a", "zz") is False


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


def _scalar(node):
    return MagicMock(scalar_one_or_none=lambda: node)


def _scalars(nodes):
    result = MagicMock()
    result.scalars.return_value = MagicMock(all=lambda: nodes)
    return result


class TestHierarchyService:
    async def test_get_ancestors_root_first(self, mock_session):
        orgs = {
            "a": org("a", "ministry"),
            "b": org("b", "directorate", "a"),
            "c": org("c", "health_center", "b"),
        }
        mock_session.execute = AsyncMock(
            side_effect=[_scalar(orgs["c"]), _scalar(orgs["b"]), _scalar(orgs["a"])]
        )
        service = OrganizationHierarchyService(mock_session)
        chain = await service.get_ancestors("c")
        assert [node.id for node in chain] == ["a", "b"]

    async def test_get_path_includes_node_with_layer(self, mock_session):
        orgs = {
            "a": org("a", "ministry"),
            "b": org("b", "directorate", "a"),
        }
        # require(b), get_ancestors -> require(b), walk -> require(a)
        mock_session.execute = AsyncMock(
            side_effect=[_scalar(orgs["b"]), _scalar(orgs["b"]), _scalar(orgs["a"])]
        )
        service = OrganizationHierarchyService(mock_session)
        path = await service.get_path("b")
        assert [(node.id, node.layer) for node in path] == [
            ("a", "national"),
            ("b", "directorate"),
        ]

    async def test_get_descendants_deterministic(self, mock_session):
        orgs = {
            "a": org("a", "ministry"),
            "b": org("b", "directorate", "a"),
            "c": org("c", "directorate", "a"),
            "d": org("d", "health_center", "b"),
            "e": org("e", "health_center", "b"),
        }
        # require(a), level(a) -> [b, c], level(b,c) -> [d, e], level(d,e) -> []
        mock_session.execute = AsyncMock(
            side_effect=[
                _scalar(orgs["a"]),
                _scalars([orgs["b"], orgs["c"]]),
                _scalars([orgs["d"], orgs["e"]]),
                _scalars([]),
            ]
        )
        service = OrganizationHierarchyService(mock_session)
        descendants = await service.get_descendants("a")
        assert [node.id for node in descendants] == ["b", "c", "d", "e"]

    async def test_get_effective_scope_sorted(self, mock_session):
        orgs = {
            "a": org("a", "ministry"),
            "b": org("b", "directorate", "a"),
            "c": org("c", "health_center", "b"),
        }
        # require(a), require(a) [in get_descendants], level(a) -> [b], level(b) -> [c], level(c) -> []
        mock_session.execute = AsyncMock(
            side_effect=[
                _scalar(orgs["a"]),
                _scalar(orgs["a"]),
                _scalars([orgs["b"]]),
                _scalars([orgs["c"]]),
                _scalars([]),
            ]
        )
        service = OrganizationHierarchyService(mock_session)
        assert await service.get_effective_scope("a") == ["a", "b", "c"]

    async def test_set_parent_success_audits(self, mock_session):
        orgs = {
            "a": org("a", "ministry"),
            "b": org("b", "directorate"),
        }
        # require(b), require(a), ancestors(b)->require(b), walk->require(a), ancestors(a)->require(a)
        mock_session.execute = AsyncMock(
            side_effect=[
                _scalar(orgs["b"]),
                _scalar(orgs["a"]),
                _scalar(orgs["b"]),
                _scalar(orgs["a"]),
                _scalar(orgs["a"]),
            ]
        )
        audit = MagicMock()
        audit.record = AsyncMock()
        service = OrganizationHierarchyService(mock_session, audit=audit)
        updated = await service.set_parent("b", "a", actor_id="actor-1", reason="merge")
        assert updated.parent_org_id == "a"
        audit.record.assert_awaited_once()
        call = audit.record.await_args
        assert call.args[0] is AuditAction.organization_hierarchy_changed
        assert call.kwargs["actor_id"] == "actor-1"
        assert call.kwargs["target_id"] == "b"
        assert call.kwargs["changes"]["parent_org_id"] == {"from": None, "to": "a"}

    async def test_set_parent_self_parent_rejected(self, mock_session):
        org_a = org("a", "ministry")
        mock_session.execute = AsyncMock(side_effect=[_scalar(org_a), _scalar(org_a)])
        service = OrganizationHierarchyService(mock_session)
        with pytest.raises(OrganizationHierarchyError, match="self_parent"):
            await service.set_parent("a", "a")

    async def test_set_parent_cycle_rejected(self, mock_session):
        orgs = {
            "a": org("a", "ministry"),
            "b": org("b", "directorate", "a"),
        }
        # require(a), require(b), ancestors(a)->require(a), ancestors(b)->require(b), walk->require(a)
        mock_session.execute = AsyncMock(
            side_effect=[
                _scalar(orgs["a"]),
                _scalar(orgs["b"]),
                _scalar(orgs["a"]),
                _scalar(orgs["b"]),
                _scalar(orgs["a"]),
            ]
        )
        service = OrganizationHierarchyService(mock_session)
        with pytest.raises(OrganizationHierarchyError, match="cycle_detected"):
            await service.set_parent("a", "b")

    async def test_set_parent_missing_parent_rejected(self, mock_session):
        org_a = org("a", "ministry")
        mock_session.execute = AsyncMock(side_effect=[_scalar(org_a), _scalar(None)])
        service = OrganizationHierarchyService(mock_session)
        with pytest.raises(OrganizationHierarchyError, match="organization_not_found"):
            await service.set_parent("a", "missing")

    async def test_detach_audits_and_clears_parent(self, mock_session):
        org_c = org("c", "health_center", "b")
        mock_session.execute = AsyncMock(side_effect=[_scalar(org_c)])
        audit = MagicMock()
        audit.record = AsyncMock()
        service = OrganizationHierarchyService(mock_session, audit=audit)
        detached = await service.detach("c", actor_id="actor-1", reason="restructure")
        assert detached.parent_org_id is None
        audit.record.assert_awaited_once()
        call = audit.record.await_args
        assert call.kwargs["changes"]["parent_org_id"] == {"from": "b", "to": None}

    async def test_detach_root_is_noop(self, mock_session):
        org_a = org("a", "ministry")
        mock_session.execute = AsyncMock(side_effect=[_scalar(org_a)])
        audit = MagicMock()
        audit.record = AsyncMock()
        service = OrganizationHierarchyService(mock_session, audit=audit)
        result = await service.detach("a", actor_id="actor-1")
        assert result.parent_org_id is None
        audit.record.assert_not_awaited()

    async def test_validate_layer_ordering_warns_upside_down(self, mock_session):
        orgs = {
            "a": org("a", "health_center"),
            "b": org("b", "ministry", "a"),
        }
        # require(b), walk -> require(a)
        mock_session.execute = AsyncMock(side_effect=[_scalar(orgs["b"]), _scalar(orgs["a"])])
        service = OrganizationHierarchyService(mock_session)
        warnings = await service.validate_layer_ordering("b")
        assert len(warnings) == 1
        assert "national" in warnings[0]

    async def test_validate_layer_ordering_clean_for_nested_facility(self, mock_session):
        orgs = {
            "a": org("a", "directorate"),
            "b": org("b", "health_center", "a"),
        }
        mock_session.execute = AsyncMock(side_effect=[_scalar(orgs["b"]), _scalar(orgs["a"])])
        service = OrganizationHierarchyService(mock_session)
        assert await service.validate_layer_ordering("b") == []
