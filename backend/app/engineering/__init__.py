from __future__ import annotations

from .ci.quality_gates import QualityGates
from .generators.base import BaseGenerator
from .validation.clean_arch import CleanArchitectureValidator
from .validation.ddd import DDDValidator
from .validation.cqrs import CQRSValidator
from .validation.event_driven import EventDrivenValidator
from .validation.solid import SOLIDValidator
from .intelligence.knowledge_graph import KnowledgeGraphGenerator
from .intelligence.dependency_graph import DependencyGraphGenerator
from .intelligence.changelog import CHANGELOGAutomator, ADRAutomator, ReleaseNotesAutomator

__all__ = [
    "BaseGenerator",
    "CleanArchitectureValidator",
    "DDDValidator",
    "CQRSValidator",
    "EventDrivenValidator",
    "SOLIDValidator",
    "QualityGates",
    "KnowledgeGraphGenerator",
    "DependencyGraphGenerator",
    "CHANGELOGAutomator",
    "ADRAutomator",
    "ReleaseNotesAutomator",
]
