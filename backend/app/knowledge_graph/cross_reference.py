from __future__ import annotations

import logging
from typing import Any

from .adr import adr_manager
from .catalog import api_catalog
from .data_dictionary import data_dictionary
from .event_catalog import event_catalog
from .fhir_catalog import fhir_catalog
from .service_catalog import service_catalog

logger = logging.getLogger("gula.knowledge_graph.cross_reference")

_ENTITY_TYPE_MAP = {
    "api": {"catalog": "api_catalog", "label": "API Endpoint", "list_fn": lambda: api_catalog.get_all_endpoints()},
    "service": {"catalog": "service_catalog", "label": "Service", "list_fn": lambda: service_catalog._services},
    "capability": {"catalog": "service_catalog", "label": "Capability", "list_fn": lambda: service_catalog._capabilities},
    "entity": {"catalog": "data_dictionary", "label": "Data Entity", "list_fn": lambda: data_dictionary.get_all_entities()},
    "event": {"catalog": "event_catalog", "label": "Event", "list_fn": lambda: event_catalog._events},
    "fhir": {"catalog": "fhir_catalog", "label": "FHIR Resource", "list_fn": lambda: fhir_catalog._resources},
    "adr": {"catalog": "adr_manager", "label": "ADR", "list_fn": lambda: adr_manager._adrs},
}


class CrossReferenceEngine:
    def __init__(self):
        self._links: list[dict[str, Any]] = []

    def build_links(self) -> list[dict]:
        links = []

        # API → Service
        for ep in api_catalog.get_all_endpoints():
            path_parts = ep.path.strip("/").split("/")
            if path_parts:
                for svc_name, _svc_entry in service_catalog._services.items():
                    if svc_name.lower() in path_parts[0].lower():
                        links.append({
                            "source_type": "api",
                            "source_id": f"{ep.method}:{ep.path}",
                            "target_type": "service",
                            "target_id": svc_name,
                            "relationship": "IMPLEMENTS",
                        })

        # API → Data Entity
        for ep in api_catalog.get_all_endpoints():
            for ent in data_dictionary.get_all_entities():
                if ent.table_name.lower() in ep.path.lower() or ent.name.lower() in ep.path.lower():
                    links.append({
                        "source_type": "api",
                        "source_id": f"{ep.method}:{ep.path}",
                        "target_type": "entity",
                        "target_id": ent.table_name,
                        "relationship": "ACCESSES",
                    })

        # FHIR → Data Entity
        for fhir_name, _fhir_entry in fhir_catalog._resources.items():
            for ent in data_dictionary.get_all_entities():
                if ent.fhir_resource == fhir_name or ent.table_name.lower() == fhir_name.lower():
                    links.append({
                        "source_type": "fhir",
                        "source_id": fhir_name,
                        "target_type": "entity",
                        "target_id": ent.table_name,
                        "relationship": "MAPS_TO",
                    })

        # Event → Service
        for evt_name in event_catalog._events:
            for svc_name in service_catalog._services:
                if svc_name.lower() in evt_name.lower() or evt_name.lower() in svc_name.lower():
                    links.append({
                        "source_type": "event",
                        "source_id": evt_name,
                        "target_type": "service",
                        "target_id": svc_name,
                        "relationship": "PUBLISHED_BY",
                    })

        # ADR → Domain topics
        for adr_record in adr_manager._adrs.values():
            domain_lower = adr_record.domain.lower()
            for svc_name in service_catalog._services:
                if domain_lower in svc_name.lower() or svc_name.lower() in domain_lower:
                    links.append({
                        "source_type": "adr",
                        "source_id": adr_record.adr_id,
                        "target_type": "service",
                        "target_id": svc_name,
                        "relationship": "DECIDES",
                    })
            for evt_name in event_catalog._events:
                if domain_lower in evt_name.lower():
                    links.append({
                        "source_type": "adr",
                        "source_id": adr_record.adr_id,
                        "target_type": "event",
                        "target_id": evt_name,
                        "relationship": "DECIDES",
                    })

        self._links = links
        logger.info("Built %d cross-references between catalogs", len(links))
        return links

    def find_related(self, entity_type: str, entity_id: str) -> dict:
        related: dict[str, list[dict]] = {}
        if not self._links:
            self.build_links()
        for link in self._links:
            if link["source_type"] == entity_type and link["source_id"] == entity_id:
                ttype = link["target_type"]
                related.setdefault(ttype, []).append({
                    "id": link["target_id"],
                    "relationship": link["relationship"],
                })
            elif link["target_type"] == entity_type and link["target_id"] == entity_id:
                ttype = link["source_type"]
                related.setdefault(ttype, []).append({
                    "id": link["source_id"],
                    "relationship": link["relationship"],
                })
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "related": related,
            "total_relations": sum(len(v) for v in related.values()),
        }

    def get_impact_analysis(self, entity_type: str, entity_id: str) -> dict:
        related = self.find_related(entity_type, entity_id)
        direct = related["related"]
        transitive: dict[str, list[dict]] = {}
        for ttype, items in direct.items():
            for item in items:
                deeper = self.find_related(ttype, item["id"])
                for dttype, ditems in deeper.get("related", {}).items():
                    if dttype == entity_type:
                        continue
                    transitive.setdefault(dttype, []).extend(ditems)
        return {
            "target": {"type": entity_type, "id": entity_id},
            "direct_impact": direct,
            "transitive_impact": transitive,
            "total_direct": sum(len(v) for v in direct.values()),
            "total_transitive": sum(len(v) for v in transitive.values()),
            "risk_level": "high" if len(direct) > 10 else ("medium" if len(direct) > 5 else "low"),
        }

    def get_coverage_gaps(self) -> dict:
        gaps: dict[str, list[dict]] = {
            "apis_without_tests": [],
            "entities_without_fhir": [],
            "events_without_documentation": [],
            "services_without_capabilities": [],
            "apis_without_entity_access": [],
        }

        for ep in api_catalog.get_all_endpoints():
            linked = False
            for link in self._links:
                if link["source_type"] == "api" and link["source_id"] == f"{ep.method}:{ep.path}":
                    linked = True
                    break
            if not linked:
                gaps["apis_without_entity_access"].append(f"{ep.method} {ep.path}")

        for ent in data_dictionary.get_all_entities():
            if not ent.fhir_resource:
                gaps["entities_without_fhir"].append(ent.table_name)

        for evt_name, evt_entry in event_catalog._events.items():
            if not evt_entry.description and not evt_entry.summary:
                gaps["events_without_documentation"].append(evt_name)

        for svc_name in service_catalog._services:
            found = False
            for cap_name, _cap_entry in service_catalog._capabilities.items():
                if svc_name.lower() in cap_name.lower():
                    found = True
                    break
            if not found:
                gaps["services_without_capabilities"].append(svc_name)

        return {
            "gaps": gaps,
            "total_gaps": sum(len(v) for v in gaps.values()),
            "summary": {
                "total_apis": api_catalog.count(),
                "apis_missing_entity_link": len(gaps["apis_without_entity_access"]),
                "entities_missing_fhir": len(gaps["entities_without_fhir"]),
                "events_missing_docs": len(gaps["events_without_documentation"]),
                "services_missing_capabilities": len(gaps["services_without_capabilities"]),
            },
        }

    def build_knowledge_graph(self) -> dict:
        if not self._links:
            self.build_links()
        nodes: list[dict] = []
        edges: list[dict] = []
        seen_nodes: set[tuple[str, str]] = set()

        for ep in api_catalog.get_all_endpoints():
            nid = f"api:{ep.method}:{ep.path}"
            if (nid, "api") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "api",
                    "label": f"{ep.method.upper()} {ep.path}",
                    "group": "API",
                    "metadata": {"tags": ep.tags, "module": ep.module},
                })
                seen_nodes.add((nid, "api"))

        for svc_name in service_catalog._services:
            nid = f"service:{svc_name}"
            if (nid, "service") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "service",
                    "label": svc_name,
                    "group": "Service",
                })
                seen_nodes.add((nid, "service"))

        for cap_name in service_catalog._capabilities:
            nid = f"capability:{cap_name}"
            if (nid, "capability") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "capability",
                    "label": cap_name,
                    "group": "Capability",
                })
                seen_nodes.add((nid, "capability"))

        for ent in data_dictionary.get_all_entities():
            nid = f"entity:{ent.table_name}"
            if (nid, "entity") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "entity",
                    "label": ent.name,
                    "group": "Data Entity",
                })
                seen_nodes.add((nid, "entity"))

        for fhir_name in fhir_catalog._resources:
            nid = f"fhir:{fhir_name}"
            if (nid, "fhir") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "fhir",
                    "label": fhir_name,
                    "group": "FHIR",
                })
                seen_nodes.add((nid, "fhir"))

        for evt_name in event_catalog._events:
            nid = f"event:{evt_name}"
            if (nid, "event") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "event",
                    "label": evt_name,
                    "group": "Event",
                })
                seen_nodes.add((nid, "event"))

        for adr_record in adr_manager._adrs.values():
            nid = f"adr:{adr_record.adr_id}"
            if (nid, "adr") not in seen_nodes:
                nodes.append({
                    "id": nid,
                    "type": "adr",
                    "label": f"{adr_record.adr_id}: {adr_record.title[:60]}",
                    "group": "ADR",
                    "metadata": {"status": adr_record.status, "domain": adr_record.domain},
                })
                seen_nodes.add((nid, "adr"))

        for link in self._links:
            src_id = f"{link['source_type']}:{link['source_id']}"
            tgt_id = f"{link['target_type']}:{link['target_id']}"
            if src_id in [n["id"] for n in nodes] and tgt_id in [n["id"] for n in nodes]:
                edges.append({
                    "source": src_id,
                    "target": tgt_id,
                    "relationship": link["relationship"],
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "by_type": {
                    t: sum(1 for n in nodes if n["type"] == t)
                    for t in {n["type"] for n in nodes}
                },
            },
        }

    def get_summary(self) -> dict:
        return {
            "total_links": len(self._links),
            "catalogs": {
                "apis": api_catalog.count(),
                "services": len(service_catalog._services),
                "capabilities": len(service_catalog._capabilities),
                "data_entities": len(data_dictionary._entities),
                "fhir_resources": len(fhir_catalog._resources),
                "events": len(event_catalog._events),
                "adrs": len(adr_manager._adrs),
            },
        }


cross_reference = CrossReferenceEngine()
