from __future__ import annotations

import logging

from .adr import adr_manager
from .catalog import api_catalog
from .data_dictionary import data_dictionary
from .event_catalog import event_catalog
from .fhir_catalog import fhir_catalog
from .service_catalog import service_catalog

logger = logging.getLogger("gula.knowledge_graph.search")


class KnowledgeSearch:
    def search(self, query: str, domains: list[str] | None = None) -> dict[str, list[dict]]:
        results: dict[str, list[dict]] = {}
        if domains is None or "apis" in domains:
            api_results = self.search_apis(query)
            if api_results:
                results["apis"] = api_results
        if domains is None or "services" in domains:
            svc_results = self.search_services(query)
            if svc_results:
                results["services"] = svc_results
        if domains is None or "entities" in domains:
            ent_results = self.search_entities(query)
            if ent_results:
                results["entities"] = ent_results
        if domains is None or "events" in domains:
            evt_results = self.search_events(query)
            if evt_results:
                results["events"] = evt_results
        if domains is None or "adrs" in domains:
            adr_results = self.search_adrs(query)
            if adr_results:
                results["adrs"] = adr_results
        if domains is None or "fhir" in domains:
            fhir_results = self.search_fhir(query)
            if fhir_results:
                results["fhir"] = fhir_results
        return results

    def search_apis(self, query: str) -> list[dict]:
        results = api_catalog.search_endpoints(query)
        return [r.to_dict() for r in results]

    def search_services(self, query: str) -> list[dict]:
        results = service_catalog.search(query)
        return [r.to_dict() if hasattr(r, "to_dict") else {"name": str(r)} for r in results]

    def search_entities(self, query: str) -> list[dict]:
        results = data_dictionary.search_entities(query)
        return [r.to_dict() for r in results]

    def search_events(self, query: str) -> list[dict]:
        results = event_catalog.search(query)
        return [r.to_dict() for r in results]

    def search_adrs(self, query: str) -> list[dict]:
        results = adr_manager.search(query)
        return [r.to_dict() for r in results]

    def search_fhir(self, query: str) -> list[dict]:
        results = fhir_catalog.search(query)
        return [r.to_dict() for r in results]


knowledge_search = KnowledgeSearch()
