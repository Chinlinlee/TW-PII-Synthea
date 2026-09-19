"""
Scenario and LLM Context Synthesis Package for Taiwan PII Synthetic Engine.
"""

from pii_synthea.scenarios.domains import (
    DomainCategory,
    ScenarioDefinition,
    ScenarioRegistry,
    TextLengthCategory,
)
from pii_synthea.scenarios.generator import ScenarioSynthesizer
from pii_synthea.scenarios.prompts import PromptBuilder
from pii_synthea.scenarios.tag_parser import TagToSpanParser
from pii_synthea.scenarios.templates import SeedTemplate, SeedTemplateLibrary

__all__ = [
    # Domains & Categories
    "DomainCategory",
    "TextLengthCategory",
    "ScenarioDefinition",
    "ScenarioRegistry",
    # Tag-to-Span Parser
    "TagToSpanParser",
    # Prompts
    "PromptBuilder",
    # Templates
    "SeedTemplate",
    "SeedTemplateLibrary",
    # Pipeline Synthesizer
    "ScenarioSynthesizer",
]
