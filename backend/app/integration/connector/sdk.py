from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.integration.connector.registry import ConnectorRegistry
from app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.sdk")


@dataclass
class SDKCapability:
    name: str = ""
    description: str = ""
    methods: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)


@dataclass
class SDKArtifact:
    language: str = "python"
    version: str = "1.0.0"
    code: str = ""
    capabilities: list[SDKCapability] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class ConnectorSDK:
    def __init__(self, registry: ConnectorRegistry):
        self._registry = registry
        self._artifacts: dict[str, SDKArtifact] = {}

    def generate_client(
        self, connector_id: str, language: str = "python",
    ) -> SDKArtifact:
        spec = self._registry.get(connector_id)
        if not spec:
            raise ValueError(f"Connector {connector_id} not found in registry")

        existing_key = f"{connector_id}:{language}"
        if existing_key in self._artifacts:
            return self._artifacts[existing_key]

        code = self._generate_code(spec, language)
        capabilities = self._extract_capabilities(spec)
        dependencies = self._resolve_dependencies(spec, language)

        artifact = SDKArtifact(
            language=language,
            version=spec.version,
            code=code,
            capabilities=capabilities,
            dependencies=dependencies,
        )
        self._artifacts[existing_key] = artifact
        logger.info(
            "SDK client generated for %s (%s)", spec.name, language,
        )
        return artifact

    def get_artifact(
        self, connector_id: str, language: str = "python",
    ) -> SDKArtifact | None:
        return self._artifacts.get(f"{connector_id}:{language}")

    def _generate_code(self, spec: ConnectorSpec, language: str) -> str:
        if language == "python":
            return self._generate_python(spec)
        return f"# {language} SDK for {spec.name}\n# Generation not implemented\n"

    def _generate_python(self, spec: ConnectorSpec) -> str:
        lines = [
            f'"""Auto-generated SDK for {spec.name} v{spec.version}"""',
            "",
            "from __future__ import annotations",
            "",
            "import httpx",
            "from typing import Any",
            "",
            "",
            f"class {self._to_class_name(spec.name)}:",
            f'    """SDK client for {spec.description}"""',
            "",
            f'    BASE_URL = "{spec.endpoints[0].url if spec.endpoints else ""}"',
            "",
            "    def __init__(self, api_key: str | None = None):",
            "        self._client = httpx.Client(base_url=self.BASE_URL)",
            "        self._headers: dict[str, str] = {}",
            "        if api_key:",
            '            self._headers["Authorization"] = f"Bearer {api_key}"',
            "",
            "    def request(self, method: str, path: str, **kwargs) -> dict:",
            "        response = self._client.request(",
            "            method=method, url=path, headers=self._headers, **kwargs",
            "        )",
            "        response.raise_for_status()",
            "        return response.json()",
            "",
            "    def close(self) -> None:",
            "        self._client.close()",
            "",
        ]
        return "\n".join(lines)

    def _to_class_name(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))

    def _extract_capabilities(
        self, spec: ConnectorSpec,
    ) -> list[SDKCapability]:
        caps = []
        type_map = {
            ConnectorType.REST: ["GET", "POST", "PUT", "DELETE"],
            ConnectorType.FHIR: ["read", "search", "create", "update"],
            ConnectorType.GRAPHQL: ["query", "mutation"],
            ConnectorType.WEBSOCKET: ["subscribe", "publish"],
        }
        methods = type_map.get(spec.connector_type, ["request"])
        caps.append(
            SDKCapability(
                name=f"{spec.name}_client",
                description=f"Client for {spec.name}",
                methods=methods,
            ),
        )
        return caps

    def _resolve_dependencies(
        self, spec: ConnectorSpec, language: str,
    ) -> list[str]:
        deps = []
        if language == "python":
            deps.append("httpx>=0.27.0")
            if spec.connector_type in (ConnectorType.GRAPHQL,):
                deps.append("gql>=3.5.0")
            if spec.connector_type == ConnectorType.WEBSOCKET:
                deps.append("websockets>=12.0")
        return deps

    def list_artifacts(self) -> dict[str, SDKArtifact]:
        return dict(self._artifacts)
