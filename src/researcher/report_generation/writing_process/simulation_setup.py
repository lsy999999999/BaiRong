"""
Simulation Setup Section Generator for creating the simulation setup part of a research report.
"""

from .report_section_base import ReportSectionBase


class SimulationSetupSection(ReportSectionBase):
    """
    Simulation Setup Section Generator for creating the simulation setup part of a research report.
    
    This class is responsible for generating the simulation setup section of a report, detailing the 
    configuration of the simulation environment, agents, and metrics.
    """
    
    def __init__(self, model_config: str = None):
        """
        Initialize the simulation setup section generator.
        
        Args:
            model_config (str, optional): The model configuration name to use.
                If None, the default model will be used.
        """
        super().__init__(model_config)
        self.section_name = "Simulation Setup"
        self.section_filename = "simulation_setup.tex"
    
    def load_scenario_description(self, scenario_file: str) -> str:
        """
        Load the scenario description from file.
        
        Args:
            scenario_file (str): Path to the scenario description file.
            
        Returns:
            str: Scenario description content.
        """
        with open(scenario_file, 'r', encoding='utf-8') as f:
            return f.read()
            
    def load_metrics_metadata(self, metrics_file: str) -> dict:
        """
        Load the metrics metadata from file.
        
        Args:
            metrics_file (str): Path to the metrics metadata file.
            
        Returns:
            dict: Metrics metadata.
        """
        import json
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def load_analysis_result(self, analysis_file: str) -> str:
        """
        Load the analysis result from file.
        
        Args:
            analysis_file (str): Path to the analysis result file.
            
        Returns:
            str: Analysis result content.
        """
        with open(analysis_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def save_to_file(self, content: str, file_path: str) -> None:
        """
        Save content to file.
        
        Args:
            content (str): Content to save.
            file_path (str): Path to save the content to.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _get_section_specific_instructions(self) -> str:
        """
        Get additional instructions specific to the simulation setup section.
        
        Returns:
            str: Additional instructions for the simulation setup section.
        """
        return """
\n\nFor the Simulation Setup section, please focus on:
1. Providing a detailed description of the simulation environment
2. Explaining the types and roles of agents in the simulation
3. Describing the metrics used to evaluate the simulation outcomes
4. Detailing the process flow and interaction patterns
5. Clarifying any constraints or assumptions made in the model

The Simulation Setup should be technically precise yet understandable. Include details from the ODD protocol and metrics metadata to ensure a complete description of how the simulation was configured.

Pay special attention to:
- Agent behaviors and decision mechanisms
- Environmental conditions and constraints
- Metrics definitions and calculation methods
- The temporal and spatial dimensions of the simulation

Use appropriate LaTeX environments for equations, definitions, or pseudocode if needed to explain the model's mechanics.
""" 