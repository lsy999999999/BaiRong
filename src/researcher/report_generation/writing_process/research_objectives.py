"""
Research Objectives Section Generator for creating the research objectives part of a research report.
"""

from .report_section_base import ReportSectionBase


class ResearchObjectivesSection(ReportSectionBase):
    """
    Research Objectives Section Generator for creating the research objectives part of a research report.
    
    This class is responsible for generating the research objectives section of a report, focusing on 
    the purpose, questions, and significance of the research.
    """
    
    def __init__(self, model_config: str = None):
        """
        Initialize the research objectives section generator.
        
        Args:
            model_config (str, optional): The model configuration name to use.
                If None, the default model will be used.
        """
        super().__init__(model_config)
        self.section_name = "Research Objectives"
        self.section_filename = "research_objectives.tex"
    
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
        Get additional instructions specific to the research objectives section.
        
        Returns:
            str: Additional instructions for the research objectives section.
        """
        return """
\n\nFor the Research Objectives section, please focus on:
1. Clearly stating the main research questions and goals
2. Providing context for why these objectives are important
3. Explaining the scope and boundaries of the research
4. Connecting the objectives to the simulation scenario described in the ODD protocol
5. Being concise yet comprehensive

The Research Objectives should set the stage for the entire report by providing a clear direction and purpose for the research. Make sure to connect the objectives to the specific simulation scenario and metrics being used.

Do not include methodological details or results - those will be covered in later sections. Focus only on what the research aims to achieve and why it matters.
""" 