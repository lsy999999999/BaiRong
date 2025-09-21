"""
Review agent module for evaluating research reports and providing improvement suggestions.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from onesim.models import get_model, SystemMessage, UserMessage
from onesim.agent.base import AgentBase


class ReviewerAgent(AgentBase):
    """
    Reviewer agent class, responsible for reviewing research reports and generating review feedback.
    
    This class reviews various parts of a report and provides feedback on insight, structure, content, 
    and utility.
    """
    
    def __init__(self, model_config_name: str = None):
        """
        Initialize the reviewer agent.
        
        Args:
            model_config_name (str, optional): The model configuration name to use.
                If None, the default model will be used.
        """
        sys_prompt = self._construct_system_prompt()
        super().__init__(sys_prompt=sys_prompt, model_config_name=model_config_name)
    
    def review_report(
        self,
        latex_content: str,
        section_contents: Dict[str, str],
        scenario_file: str,
        metrics_file: str,
        analysis_file: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review a complete research report and its various sections.
        
        Args:
            latex_content (str): Complete LaTeX report content.
            section_contents (Dict[str, str]): Dictionary of section contents in {section_name: content} format.
            scenario_file (str): Path to the scenario description file.
            metrics_file (str): Path to the metrics metadata file.
            analysis_file (str): Path to the data analysis results file.
            output_file (str, optional): Path for the review output file.
            
        Returns:
            Dict[str, Any]: Dictionary containing overall assessment and specific opinions for each section.
        """
        # Load necessary context information
        scenario_description = self.load_scenario_description(scenario_file)
        metrics_metadata = self.load_metrics_metadata(metrics_file)
        analysis_result = self.load_analysis_result(analysis_file)
        
        # Construct prompt text
        prompt_text = self._construct_review_prompt(
            latex_content,
            section_contents,
            scenario_description,
            metrics_metadata,
            analysis_result
        )
        
        # Call the LLM
        # Make sure we have a model
        if not hasattr(self, 'model'):
            from onesim.models import get_model
            self.model = get_model()
        
        response = self.model(self.model.format(
                SystemMessage(content=self.sys_prompt),
                UserMessage(content=prompt_text)
        ))
        
        # Parse review feedback
        review_results = self._parse_review_response(response.text)
        
        # Save review feedback to file (if specified)
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(review_results, f, ensure_ascii=False, indent=2)
        
        return review_results
    
    def _construct_system_prompt(self) -> str:
        """
        Construct the system prompt.
        
        Returns:
            str: System prompt content.
        """
        return """You are a rigorous academic reviewer specializing in multi-agent social simulation research reports.
Your responsibility is to comprehensively evaluate various aspects of the report, focusing on these four core criteria:

1. Insight: Evaluation of analytical depth, originality, and value, including pattern recognition, causal reasoning, explanatory depth, and multi-level analysis
2. Structure: Assessment of the report's organizational logic and clarity of expression, including coherence, hierarchical organization, content balance, and readability
3. Content: Evaluation of the quality and completeness of the presented material, including comprehensiveness, accuracy, depth, and evidence support
4. Utility: Assessment of how well the report addresses research questions and provides practical value, including alignment with needs, problem-solving, decision support, and implementation guidance

Your review should be constructive, clearly pointing out problems and providing specific improvement suggestions. 
The review should remain objective and impartial.

Please provide:
1. Overall evaluation: Assessment of the overall quality of the report
2. Section-by-section review: Specific evaluation for each section
3. Improvement suggestions: Specific, actionable modification suggestions
4. Scoring: Score the report on a scale of 1-5 (1 worst, 5 best) according to the following criteria:

Scoring guidelines:
   - Insight (1-5):
     1: Lacks analytical depth, fails to identify key patterns and relationships
     2: Provides basic analysis but limited depth, lacking original insights
     3: Demonstrates reasonable depth of analysis, identifies some important patterns
     4: Provides deep analysis, discovers non-obvious relationships and patterns
     5: Exhibits exceptional insight, offering unique perspectives and innovative explanations
     
   - Structure (1-5):
     1: Disorganized, logical breaks, difficult to understand
     2: Basic structure exists but lacks coherence and balance
     3: Clear structure with natural transitions between sections
     4: Excellent organization, clearly defined hierarchy, guides reader smoothly
     5: Refined structure, perfect balance, optimizes content presentation and understanding
     
   - Content (1-5):
     1: One-sided content with major omissions or errors
     2: Content basically covers the topic but with limited depth and accuracy
     3: Comprehensive content, good accuracy, supports main arguments
     4: Rich content, highly accurate, provides detailed evidence
     5: Exceptional content, both comprehensive and in-depth, flawless evidence support
     
   - Utility (1-5):
     1: Difficult to apply to real problems, barely addresses research questions
     2: Limited practical value, only partially addresses research questions
     3: Good practical value, directly addresses main research questions
     4: High practical value, comprehensively addresses research questions, provides valuable guidance
     5: Exceptional practical value, exceeds expectations in problem-solving, offers innovative solutions
     
   - Overall score (1-5): Comprehensive evaluation of the report
"""
    
    def _construct_review_prompt(
        self,
        latex_content: str,
        section_contents: Dict[str, str],
        scenario_description: str,
        metrics_metadata: List[Dict[str, Any]],
        analysis_result: str
    ) -> str:
        """
        Construct the review prompt text.
        
        Args:
            latex_content (str): Complete LaTeX report content.
            section_contents (Dict[str, str]): Dictionary of section contents.
            scenario_description (str): Scenario description.
            metrics_metadata (List[Dict[str, Any]]): Metrics metadata.
            analysis_result (str): Data analysis results.
            
        Returns:
            str: Review prompt text.
        """
        # Format metrics metadata
        metrics_info = json.dumps(metrics_metadata, indent=2)
        
        # Build review prompt
        prompt = """# Research Report Review Task

## Research Background
### Simulation Scenario (ODD Protocol):
```
%s
```

### Evaluation Metrics Metadata:
```json
%s
```

### Data Analysis Results:
```
%s
```

## Report Content
### Complete LaTeX Document:
```latex
%s
```

### Detailed Content for Each Section:
""" % (
            scenario_description,
            metrics_info,
            analysis_result,
            latex_content
        )
        
        # Add content for each section
        for section_name, content in section_contents.items():
            prompt += f"\n#### {section_name}\n```latex\n{content}\n```\n"
        
        prompt += """
Please conduct a comprehensive review of this research report and return the review results in JSON format with the following structure:
```json
{
  "overall_assessment": {
    "summary": "Summary of overall evaluation",
    "strengths": ["Strength 1", "Strength 2", ...],
    "weaknesses": ["Weakness 1", "Weakness 2", ...],
    "scores": {
      "insight": score,
      "structure": score,
      "content": score,
      "utility": score,
      "overall": score
    }
  },
  "section_reviews": {
    "Research Objectives": {
      "assessment": "Evaluation",
      "suggestions": ["Suggestion 1", "Suggestion 2", ...]
    },
    "Simulation Setup": {
      "assessment": "Evaluation",
      "suggestions": ["Suggestion 1", "Suggestion 2", ...]
    },
    "Experimental Results": {
      "assessment": "Evaluation",
      "suggestions": ["Suggestion 1", "Suggestion 2", ...]
    },
    "Conclusion": {
      "assessment": "Evaluation",
      "suggestions": ["Suggestion 1", "Suggestion 2", ...]
    }
  },
  "latex_format_issues": ["Issue 1", "Issue 2", ...],
  "improvement_priorities": ["Priority improvement item 1", "Priority improvement item 2", ...]
}
```

Please ensure your review is comprehensive, objective, specific, and provides actionable suggestions. The review results will be used to guide the revision of the report.
"""
        return prompt
    
    def _parse_review_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the review feedback generated by the LLM.
        
        Args:
            response_text (str): Review feedback text generated by the LLM.
            
        Returns:
            Dict[str, Any]: Parsed review feedback dictionary.
        """
        try:
            # Try to extract the JSON part
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            
            # If JSON cannot be extracted, return original text as overall assessment
            return {
                "overall_assessment": {
                    "summary": response_text,
                    "scores": {
                        "insight": 3,
                        "structure": 3,
                        "content": 3,
                        "utility": 3,
                        "overall": 3  # Default medium score
                    }
                },
                "parse_error": "Cannot parse as JSON format, returning original text"
            }
            
        except Exception as e:
            # Return error information when parsing fails
            return {
                "overall_assessment": {
                    "summary": "Review feedback parsing failed",
                    "scores": {
                        "insight": 3,
                        "structure": 3,
                        "content": 3,
                        "utility": 3,
                        "overall": 3  # Default medium score
                    }
                },
                "parse_error": str(e),
                "original_text": response_text
            } 
    
    def review_section(
        self,
        section_content: str,
        section_name: str,
        feedback_file: Optional[str] = None
    ) -> str:
        """
        Review a specific section of the report.
        
        Args:
            section_content (str): Content of the section to review.
            section_name (str): Name of the section.
            feedback_file (str, optional): Path to feedback file for reference.
            
        Returns:
            str: Review feedback for the section.
        """
        # Load feedback file if provided
        feedback = None
        if feedback_file and os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedback = f.read()
            except Exception as e:
                print(f"Warning: Could not load feedback file: {e}")
        
        # Construct prompt
        prompt = f"""# Section Review Task

## Section Information
- Section Name: {section_name}
- Section Content:
```latex
{section_content}
```

"""
        # Add feedback if available
        if feedback:
            prompt += f"""
## Reference Feedback
```
{feedback}
```
"""
        
        prompt += f"""
Please review this {section_name} section and provide specific, constructive feedback. Focus on:

1. Content completeness and accuracy
2. Logical structure and flow
3. Clarity and precision of language
4. Academic writing standards
5. Connection to the research goals

Provide your feedback in a well-structured format that highlights strengths, weaknesses, and specific suggestions for improvement.
"""
        
        # Call the model
        response = self.model(self.model.format(
            SystemMessage(content=self._construct_section_review_prompt()),
            UserMessage(content=prompt)
        ))
        
        return response.text
    
    def _construct_section_review_prompt(self) -> str:
        """
        Construct the system prompt for section review.
        
        Returns:
            str: System prompt for section review.
        """
        return """You are an expert academic reviewer specializing in reviewing sections of research reports on multi-agent social simulations.
Your task is to provide detailed, constructive feedback on a specific section of a research report.

Your review should evaluate the section on these four core criteria:
1. Insight: Evaluate analytical depth, originality, and value, including pattern recognition and causal reasoning
2. Structure: Assess the section's organizational logic and clarity of expression 
3. Content: Evaluate the quality and completeness of the presented material, including accuracy and evidence support
4. Utility: Assess how well the section addresses research questions and provides practical value

Provide a well-structured review that includes:
1. A brief summary of the section's strengths
2. Specific areas that need improvement
3. Actionable suggestions for revision
4. If applicable, examples of better wording or structure

Your feedback should be constructive, specific, and actionable, aimed at helping the author improve the section.
"""

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