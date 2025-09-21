"""
Report section base class, providing shared functionality for various report sections.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from onesim.models import SystemMessage, UserMessage
from onesim.agent.base import AgentBase


class ReportSectionBase(AgentBase):
    """
    Report section base class, providing shared functionality for generating different parts of research reports.
    
    This class handles LaTeX content generation, file loading, and other common functions,
    that can be inherited by specific report section classes.
    """
    
    def __init__(self, model_config_name: str = None):
        """
        Initialize the report section base class.
        
        Args:
            model_config_name (str, optional): The model configuration name to use.
                If None, the default model will be used.
        """
        super().__init__(model_config_name=model_config_name)
        self.section_name = "Base Section"  # Subclasses should override this attribute
        self.section_filename = "base_section.tex"  # Subclasses should override this attribute
    
    def load_report_outline(self, outline_file: str) -> str:
        """
        Load the report outline file.
        
        Args:
            outline_file (str): Path to the report outline file.
            
        Returns:
            str: Report outline content.
        """
        with open(outline_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_review_feedback(self, review_file: str) -> Dict[str, Any]:
        """
        Load the review feedback file.
        
        Args:
            review_file (str): Path to the review feedback file.
            
        Returns:
            Dict[str, Any]: Review feedback content.
        """
        with open(review_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_section_outline(self, report_outline: str, section_title: str) -> str:
        """
        Extract the outline for a specific section from the complete report outline.
        
        Args:
            report_outline (str): Complete report outline.
            section_title (str): Title of the section to extract.
            
        Returns:
            str: Extracted section outline content.
        """
        lines = report_outline.split('\n')
        section_content = []
        in_section = False
        next_section_pattern = "##"  # Assume subsections are marked with ##
        
        for line in lines:
            # Detect section start
            if line.strip().startswith("## ") and section_title.lower() in line.lower():
                in_section = True
                section_content.append(line)
                continue
            
            # Detect section end (next section at same level starts)
            if in_section and line.strip().startswith("## "):
                break
            
            # Collect section content
            if in_section:
                section_content.append(line)
        
        return '\n'.join(section_content)
    
    def extract_section_review(self, review_results: Dict[str, Any], section_name: str) -> Dict[str, Any]:
        """
        Extract review feedback for a specific section from complete review results.
        
        Args:
            review_results (Dict[str, Any]): Complete review feedback.
            section_name (str): Name of the section to extract.
            
        Returns:
            Dict[str, Any]: Extracted section review feedback.
        """
        section_reviews = review_results.get("section_reviews", {})
        
        # Try to match English section name
        if section_name in section_reviews:
            return section_reviews[section_name]
            
        # Try to match Chinese section name
        section_name_mapping = {
            "Research Objectives": "研究目标",
            "Simulation Setup": "模拟设置",
            "Experimental Results": "实验结果",
            "Conclusion": "结论"
        }
        
        chinese_name = section_name_mapping.get(section_name)
        if chinese_name and chinese_name in section_reviews:
            return section_reviews[chinese_name]
        
        # If no matching section is found, return empty dictionary
        return {}
    
    def generate_section_content(
        self,
        scenario_file: str,
        metrics_file: str,
        analysis_file: str,
        outline_file: str,
        image_files: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        review_file: Optional[str] = None
    ) -> str:
        """
        Generate content for a report section.
        
        Args:
            scenario_file (str): Path to the scenario description file.
            metrics_file (str): Path to the metrics metadata file.
            analysis_file (str): Path to the data analysis results file.
            outline_file (str): Path to the report outline file.
            image_files (List[str], optional): List of paths to image files.
            output_file (str, optional): Path to output file.
            review_file (str, optional): Path to review feedback file.
            
        Returns:
            str: Generated section content (in LaTeX format).
        """
        # Load data
        scenario_description = self.load_scenario_description(scenario_file)
        metrics_metadata = self.load_metrics_metadata(metrics_file)
        analysis_result = self.load_analysis_result(analysis_file)
        report_outline = self.load_report_outline(outline_file)
        
        # Extract outline for current section
        section_outline = self.extract_section_outline(report_outline, self.section_name)
        
        # Load review feedback (if provided)
        review_results = None
        section_review = None
        if review_file:
            review_results = self.load_review_feedback(review_file)
            section_review = self.extract_section_review(review_results, self.section_name)
        
        # Construct prompt text
        prompt_text = self._construct_prompt_text(
            scenario_description,
            metrics_metadata,
            analysis_result,
            section_outline,
            image_files or [],
            review_results,
            section_review
        )
        
        # Call the language model
        response = self.model(self.model.format(
            SystemMessage(content=self._construct_system_prompt(review_results is not None)),
            UserMessage(content=prompt_text)
        ))
        
        latex_content = response.text
        
        # If output file path is provided, save the result
        if output_file:
            self.save_to_file(latex_content, output_file)
        
        return latex_content
    
    def _construct_system_prompt(self, is_revision: bool = False) -> str:
        """
        Construct the system prompt.
        
        Args:
            is_revision (bool): Whether this is a revision version.
            
        Returns:
            str: System prompt content.
        """
        base_prompt = f"""You are an expert scientific writer specializing in multi-agent social simulations.
Your task is to write the {self.section_name} section of a research report based on simulation analysis results.

You should write high-quality LaTeX content for this section that is:
1. Scientifically accurate and based only on the provided information
2. Well-structured and academically rigorous
3. Free of LaTeX compilation errors
4. Using proper academic language and scientific writing style

IMPORTANT:
- Produce ONLY the LaTeX content for the {self.section_name} section, without any section command (like \\section{{{self.section_name}}})
- Only include content that is directly supported by the data provided
- For any figures mentioned, use proper LaTeX figure environment with appropriate captions and references
- Use standard LaTeX commands and packages only
- Do not include any preamble or document environment - just the content for this section
- Use proper LaTeX formatting:
  * For bold text, use \\textbf{{text}} instead of Markdown syntax like **text**
  * For subsections, use \\subsection{{title}} 
  * For italics, use \\textit{{text}}
  * For lists, use proper LaTeX environments like itemize and enumerate
  * For mathematical expressions, use $ and $$ delimiters or \\begin{{equation}} environment
"""
        
        if is_revision:
            revision_prompt = """
You are now working on a REVISED VERSION based on reviewer feedback.
Please carefully address ALL the reviewer comments and suggestions to improve this section.
Make sure to:
1. Fix any issues identified by the reviewer
2. Strengthen weak points mentioned in the review
3. Improve clarity, structure, and scientific rigor as suggested
4. Maintain consistency with the rest of the document

Your goal is to produce a significantly improved version that addresses all reviewer concerns.
"""
            return base_prompt + revision_prompt
        
        return base_prompt
    
    def _construct_prompt_text(
        self,
        scenario_description: str,
        metrics_metadata: List[Dict[str, Any]],
        analysis_result: str,
        section_outline: str,
        image_files: List[str],
        review_results: Optional[Dict[str, Any]] = None,
        section_review: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construct the user prompt text.
        
        Args:
            scenario_description (str): Scenario description.
            metrics_metadata (List[Dict[str, Any]]): Metrics metadata.
            analysis_result (str): Data analysis results.
            section_outline (str): Section outline.
            image_files (List[str]): List of paths to image files.
            review_results (Dict[str, Any], optional): Complete review feedback.
            section_review (Dict[str, Any], optional): Review feedback for the current section.
            
        Returns:
            str: User prompt text content.
        """
        # Format metrics metadata
        metrics_info = json.dumps(metrics_metadata, indent=2)
        
        # Prepare basic text content
        text_content = f"""# Writing the {self.section_name} Section

## Simulation Scenario (ODD Protocol)
```
{scenario_description}
```

## Metrics Metadata
```json
{metrics_info}
```

## Analysis Results and Insights
```
{analysis_result}
```

## Section Outline
```
{section_outline}
```

Based on the above information, please write the complete {self.section_name} section of the research report in LaTeX format.
Follow the provided outline for content and structure.

IMPORTANT GUIDELINES:
1. Do NOT simply repeat the abstract or overview in this section - create rich, distinct content specific to this section
2. Focus on the unique aspects that should be covered in the {self.section_name} section
3. For Experimental Results section, make sure to explicitly list and analyze the key insights from the analysis
4. Each section should be distinct and complementary to other sections, not redundant
5. Maintain academic rigor and scientific writing style throughout
6. Use correct LaTeX syntax and formatting:
   - For bold text: use \\textbf{{text}} NOT Markdown syntax like **text**
   - For subsections: use \\subsection{{Title}}
   - For lists: use proper LaTeX environments like itemize and enumerate
   - For emphasis: use \\textit{{text}} for italics
   - For mathematical content: use proper LaTeX math mode
"""
        
        # Add review feedback (if available)
        if review_results and section_review:
            review_content = """
## Reviewer Feedback to Address

### Overall Assessment
"""
            # Add overall evaluation
            overall = review_results.get("overall_assessment", {})
            review_content += f"Summary: {overall.get('summary', 'No summary provided')}\n\n"
            
            strengths = overall.get("strengths", [])
            if strengths:
                review_content += "Strengths:\n"
                for strength in strengths:
                    review_content += f"- {strength}\n"
                review_content += "\n"
            
            weaknesses = overall.get("weaknesses", [])
            if weaknesses:
                review_content += "Weaknesses:\n"
                for weakness in weaknesses:
                    review_content += f"- {weakness}\n"
                review_content += "\n"
            
            # Add specific feedback for the current section
            review_content += f"\n### Specific Feedback for {self.section_name}\n"
            assessment = section_review.get("assessment", "No specific assessment provided.")
            review_content += f"Assessment: {assessment}\n\n"
            
            suggestions = section_review.get("suggestions", [])
            if suggestions:
                review_content += "Suggestions to implement:\n"
                for suggestion in suggestions:
                    review_content += f"- {suggestion}\n"
                review_content += "\n"
            
            # Add format issues (if any)
            format_issues = review_results.get("latex_format_issues", [])
            if format_issues:
                review_content += "\n### LaTeX Format Issues to Fix\n"
                for issue in format_issues:
                    review_content += f"- {issue}\n"
                review_content += "\n"
            
            # Reminder about using proper LaTeX formatting
            review_content += """
REMINDER: When implementing these suggestions in your LaTeX content:
- Use \\textbf{text} for bold text, NOT Markdown format
- Use \\subsection{title} for subsections
- Use proper LaTeX formatting throughout
"""
            
            # Add review feedback to prompt text
            text_content += review_content
        
        # Add image file information (if any)
        if image_files:
            image_info = "\n\n## Available Figures:\n"
            for img_path in image_files:
                # img_filename = os.path.basename(img_path)
                image_info += f"- {img_path}\n"
            text_content += image_info
            
            text_content += "\nYou can reference these figures in your LaTeX content using standard figure environment."
        
        # Append section-specific instructions
        text_content += self._get_section_specific_instructions()
        
        return text_content
    
    def _get_section_specific_instructions(self) -> str:
        """
        Get additional instructions specific to a particular section.
        
        This method should be overridden by subclasses to provide guidance specific to their section.
        
        Returns:
            str: Additional section-specific instructions.
        """
        return "\n\nPlease write high-quality LaTeX content for this section, following academic standards." 
    
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