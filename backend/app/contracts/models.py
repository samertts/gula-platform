from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .._compat import StrEnum


class ContractFormat(StrEnum):
    openapi = "openapi"
    asyncapi = "asyncapi"
    json_schema = "json_schema"
    fhir_profile = "fhir_profile"
    graphql_schema = "graphql_schema"


class ContractStatus(StrEnum):
    draft = "draft"
    stable = "stable"
    deprecated = "deprecated"


class ContractVersion(BaseModel):
    version: str = Field(..., description="Semantic version of the contract")
    description: str = Field(default="", description="Human-readable description")
    status: ContractStatus = Field(default=ContractStatus.stable)
    format: ContractFormat
    generated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    source: str = Field(default="gula-platform", description="Source system identifier")


class ContractMetadata(BaseModel):
    name: str = Field(..., description="Contract name (e.g. 'Patient API', 'Order Events')")
    version: ContractVersion
    tags: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)


class OpenAPISpec(BaseModel):
    openapi: str = Field(default="3.1.0")
    info: dict[str, Any]
    servers: list[dict[str, Any]] = Field(default_factory=list)
    paths: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)
    tags: list[dict[str, Any]] = Field(default_factory=list)


class AsyncAPISpec(BaseModel):
    asyncapi: str = Field(default="2.6.0")
    info: dict[str, Any]
    servers: dict[str, Any] = Field(default_factory=dict)
    channels: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)


class JSONSchema(BaseModel):
    schema_: str = Field(default="http://json-schema.org/draft-07/schema#", alias="$schema")
    id: str | None = Field(default=None, alias="$id")
    type: str = Field(default="object")
    title: str | None = None
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    definitions: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class FHIRProfile(BaseModel):
    resourceType: str = Field(default="StructureDefinition")
    id: str
    url: str
    version: str
    name: str
    status: str = Field(default="draft")
    description: str
    fhirVersion: str = Field(default="4.0.1")
    kind: str = Field(default="resource")
    abstract: bool = Field(default=False)
    type: str
    baseDefinition: str = Field(default="http://hl7.org/fhir/StructureDefinition/DomainResource")
    derivation: str = Field(default="constraint")
    differential: dict[str, Any] = Field(default_factory=lambda: {"element": []})


class GraphQLSchema(BaseModel):
    schema_: str = Field(default="http://graphql.org/schema/", alias="schema")
    query: str
    mutation: str | None = None
    subscription: str | None = None
    types: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ContractExport(BaseModel):
    output_dir: str = Field(default="contracts/", description="Directory to export contracts to")
    formats: list[ContractFormat] = Field(
        default_factory=lambda: list(ContractFormat),
        description="Formats to export",
    )
    include_metadata: bool = Field(default=True)
    pretty: bool = Field(default=True)
