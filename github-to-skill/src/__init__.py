"""
GitHub to Skill - Convert GitHub repositories to Claude skills.

Modules:
    detector: Project profiling and type detection
    generator: Template-based skill generation
    validator: Progressive validation
    pipeline: Complete conversion workflow
"""

from .detector import profile_project, ProjectProfile, ProjectType, BuildSystem, EntryPoint
from .generator import generate_skill, GeneratedSkill, CapabilitySpec
from .validator import validate_skill, ValidationReport, ValidationResult, ValidationLevel
from .pipeline import run_full_pipeline

__all__ = [
    "profile_project",
    "ProjectProfile",
    "ProjectType",
    "BuildSystem",
    "EntryPoint",
    "generate_skill",
    "GeneratedSkill",
    "CapabilitySpec",
    "validate_skill",
    "ValidationReport",
    "ValidationResult",
    "ValidationLevel",
    "run_full_pipeline",
]