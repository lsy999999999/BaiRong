"""
Experimental Results Section Generator for creating the experimental results part of a research report.
"""

from .report_section_base import ReportSectionBase


class ExperimentalResultsSection(ReportSectionBase):
    """
    Experimental Results Section Generator for creating the experimental results part of a research report.
    
    This class is responsible for generating the experimental results section of a report, presenting 
    simulation results and providing detailed analysis of the data.
    """
    
    def __init__(self, model_config: str = None):
        """
        Initialize the experimental results section generator.
        
        Args:
            model_config (str, optional): The model configuration name to use.
                If None, the default model will be used.
        """
        super().__init__(model_config)
        self.section_name = "Experimental Results"
        self.section_filename = "experimental_results.tex"
    
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
        Get additional instructions specific to the experimental results section.
        
        Returns:
            str: Additional instructions for the experimental results section.
        """
        return """
\n\nFor the Experimental Results section, please focus on:
1. Presenting the key findings from the simulation in a logical order
2. Explicitly listing out and analyzing each significant insight from the analysis results
3. Providing detailed explanations of patterns, trends, and relationships in the data
4. Referencing and describing the provided figures/visualizations
5. Connecting results to the metrics defined in the setup
6. Highlighting any unexpected or significant outcomes

The Experimental Results should be data-driven, thorough, and objective. Extract all important insights from the analysis results, and expand on each one with detailed analysis supported by data. Organize the information in a scientific and systematic way.

IMPORTANT: This section should NOT simply repeat the abstract or a general overview. Instead:
- Identify and explicitly list each significant finding from the analysis
- For each finding, provide detailed analysis of what the data shows and its significance
- Support each finding with specific data points, metrics, or visualizations
- Explore relationships between different findings to build a comprehensive picture

When referencing figures:
- Refer to figures using the proper LaTeX cross-referencing syntax (\\ref{fig:filename})
- Provide thorough captions that explain what the figure shows
- Analyze what each visualization reveals about the simulation outcomes
- Connect the visualizations to the specific findings being discussed

This section should present facts with detailed analysis (but save broader interpretations for the Conclusion section). Focus on what the data shows and its direct implications rather than broader significance.

FORMATTING GUIDELINES:
- Use proper LaTeX syntax, NOT Markdown
- For key findings, consider using \\subsection{Finding Title} to structure your content
- When emphasizing important metrics or results, use \\textbf{important value} for bold text
- Use \\begin{itemize}..\\end{itemize} for bulleted lists of findings or patterns
- Create proper tables using \\begin{table}..\\end{table} environment if needed

Example of properly including a figure:
```latex
\\begin{figure}[htbp]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{filename}
    \\caption{Description of what the figure shows, including relevant metrics and patterns.}
    \\label{fig:descriptive-label}
\\end{figure}
```

Replace "filename" with the actual filename from the Available Figures list, and use a descriptive label.
""" 