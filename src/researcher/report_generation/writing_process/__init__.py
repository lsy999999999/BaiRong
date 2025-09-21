"""
Research Report Generation Module

This module provides components for generating each section of a research report, including:
- Research Objectives
- Simulation Setup
- Experimental Results
- Conclusion

"""

from .report_section_base import ReportSectionBase
from .research_objectives import ResearchObjectivesSection
from .simulation_setup import SimulationSetupSection
from .experimental_results import ExperimentalResultsSection
from .conclusion import ConclusionSection
from .latex_compiler import LatexCompiler

__all__ = [
    'ReportSectionBase',
    'ResearchObjectivesSection',
    'SimulationSetupSection',
    'ExperimentalResultsSection',
    'ConclusionSection',
    'LatexCompiler',
] 