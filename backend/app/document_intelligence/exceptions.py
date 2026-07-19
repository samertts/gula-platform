from __future__ import annotations


class DocumentIntelligenceError(Exception):
    pass


class DocumentNotFoundError(DocumentIntelligenceError):
    pass


class IngestionError(DocumentIntelligenceError):
    pass


class UnsupportedFormatError(IngestionError):
    pass


class OcrProviderError(DocumentIntelligenceError):
    pass


class OcrEngineError(OcrProviderError):
    pass


class ProviderNotAvailableError(OcrProviderError):
    pass


class ClassificationError(DocumentIntelligenceError):
    pass


class EntityExtractionError(DocumentIntelligenceError):
    pass


class FhirMappingError(DocumentIntelligenceError):
    pass


class KnowledgeExtractionError(DocumentIntelligenceError):
    pass


class SearchError(DocumentIntelligenceError):
    pass


class IndexingError(DocumentIntelligenceError):
    pass


class InferenceError(DocumentIntelligenceError):
    pass


class VersioningError(DocumentIntelligenceError):
    pass
