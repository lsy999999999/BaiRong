"""
Conclusion Section Generator for creating the conclusion part of a research report.
"""

from .report_section_base import ReportSectionBase


class ConclusionSection(ReportSectionBase):
    """
    Conclusion Section Generator for creating the conclusion part of a research report.
    
    This class is responsible for generating the conclusion section of a report, summarizing key findings, 
    interpreting their meaning, and suggesting future research directions.
    """
    
    def __init__(self, model_config: str = None):
        """
        Initialize the conclusion section generator.
        
        Args:
            model_config (str, optional): The model configuration name to use.
                If None, the default model will be used.
        """
        super().__init__(model_config)
        self.section_name = "Conclusion"
        self.section_filename = "conclusion.tex"
    
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
        Get additional instructions specific to the conclusion section.
        
        Returns:
            str: Additional instructions for the conclusion section.
        """
        return """
\n\nFor the Conclusion section, please focus on:
1. Summarizing the key findings and insights from the simulation
2. Interpreting what these results mean in the context of the research objectives
3. Discussing the implications for theory and practice
4. Acknowledging limitations of the current simulation approach
5. Suggesting directions for future research or improvements

The Conclusion should tie everything together, connecting the results back to the original objectives and providing a sense of closure. Unlike the Experimental Results section, here you should interpret and explain the significance of the findings.

Structure your conclusion to include:
- A brief recap of the most important findings (without simply repeating the results)
- The broader implications of these findings
- Limitations that should be considered when interpreting the results
- Concrete suggestions for future work or model improvements

Make sure your conclusion remains grounded in the data while providing valuable insights that go beyond just describing what happened in the simulation.
""" 