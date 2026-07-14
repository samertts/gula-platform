from __future__ import annotations

import logging
from typing import Any

from backend.app.integration.connector.http import HttpConnector
from backend.app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.graphql")


class GraphQLConnector(HttpConnector):
    def __init__(self, spec: ConnectorSpec):
        if spec.connector_type != ConnectorType.GRAPHQL:
            raise ValueError(
                f"GraphQLConnector requires type GRAPHQL, got {spec.connector_type.name}"
            )
        super().__init__(spec)

    async def query(
        self,
        query_str: str,
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query_str}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        response = await self.request(
            method="POST",
            json_data=payload,
        )
        result = response.json()
        if "errors" in result:
            logger.warning("GraphQL query returned errors: %s", result["errors"])
        return result

    async def mutate(
        self,
        mutation_str: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.query(mutation_str, variables)
