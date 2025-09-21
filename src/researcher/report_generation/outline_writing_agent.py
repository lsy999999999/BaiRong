import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from onesim.models import get_model, get_model_manager, SystemMessage, UserMessage
from onesim.agent.base import AgentBase


class OutlineWritingAgent(AgentBase):
    """
    A report outline writing agent that creates structured outlines for social simulation reports.
    
    This agent takes a simulation scenario description, analysis results, and metrics metadata
    to generate an outline for a comprehensive research report.
    """
    
    def __init__(self, model_config_name: str = None):
        """
        Initialize the outline writing agent.
        
        Args:
            model_config_name (str, optional): The name of the model configuration to use.
                If None, the default model will be used.
        """
        sys_prompt = self._construct_system_prompt()
        super().__init__(sys_prompt=sys_prompt, model_config_name=model_config_name)
    
    def generate_report_outline(
        self,
        scenario_file: str,
        analysis_file: str,
        metrics_file: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a report outline.
        
        Args:
            scenario_file (str): Path to the scenario description file.
            analysis_file (str): Path to the analysis results file.
            metrics_file (str): Path to the metrics metadata file.
            output_file (str, optional): Path to save the outline to. If None, outline is not saved.
            
        Returns:
            str: The generated report outline.
        """
        # Load data
        scenario_description = self.load_scenario_description(scenario_file)
        analysis_results = self.load_analysis_results(analysis_file)
        metrics_metadata = self.load_metrics_metadata(metrics_file)
        
        # Construct the prompt text
        prompt_text = self._construct_prompt_text(
            scenario_description,
            analysis_results,
            metrics_metadata
        )
        
        # Make sure we have a model
        if not hasattr(self, 'model'):
            from onesim.models import get_model
            self.model = get_model()
            
        # Call the LLM
        response = self.model(self.model.format(
            SystemMessage(content=self.sys_prompt),
            UserMessage(content=prompt_text)
        ))
        
        outline = response.text
        
        # Save results to file if output_file is provided
        if output_file:
            self.save_to_file(outline, output_file)
        
        return outline
    
    def _construct_system_prompt(self) -> str:
        """
        Construct the system prompt for the LLM.
        
        Returns:
            str: The system prompt.
        """
        return """You are an expert research report writer specializing in multi-agent social simulations. 
Your task is to create a detailed outline for a comprehensive research report based on simulation results.

Given:
1. A description of the simulation scenario following the ODD (Overview, Design Concepts, Details) protocol
2. Analysis results from the simulation data
3. Metadata about the metrics being measured

You should create a structured outline for a comprehensive research report that:
1. Clearly states the research objectives based on the simulation scenario
2. Describes the simulation setup and methodology
3. Presents the experimental results in a logical order
4. Provides sections for discussion and conclusion

Your outline should be detailed enough to guide the full report writing process, with clear hierarchical structure.
Include bullet points for the key content that should be included in each section.
"""
    
    def _construct_prompt_text(
        self,
        scenario_description: str,
        analysis_results: str,
        metrics_metadata: Dict[str, Any]
    ) -> str:
        """
        Construct the user prompt for the LLM.
        
        Args:
            scenario_description (str): Simulation scenario description.
            analysis_results (str): Analysis results from the data analysis agent.
            metrics_metadata (Dict[str, Any]): Metrics metadata.
            
        Returns:
            str: The text content of the user prompt.
        """
        # Format metrics metadata for the prompt
        metrics_info = json.dumps(metrics_metadata, indent=2)
        
        # Prepare the text content
        text_content = f"""# Report Outline Generation Task

## Simulation Scenario (ODD Protocol)
```
{scenario_description}
```

## Analysis Results
```
{analysis_results}
```

## Metrics Metadata
```json
{metrics_info}
```

Please create a detailed outline for a comprehensive research report on this simulation.
The outline should have a clear hierarchical structure with main sections and subsections.
Include bullet points for the key content that should be included in each section.
"""
        
        return text_content
    
    def load_scenario_description(self, scenario_file: str) -> str:
        """
        Load the scenario description from a file.
        
        Args:
            scenario_file (str): Path to the scenario description file.
            
        Returns:
            str: The scenario description.
        """
        try:
            with open(scenario_file, 'r', encoding='utf-8') as f:
                # Check if file is JSON or plain text
                if scenario_file.endswith('.json'):
                    data = json.load(f)
                    # If it's scene_info.json, extract the ODD protocol
                    if 'odd_protocol' in data:
                        return json.dumps(data['odd_protocol'], indent=2)
                    return json.dumps(data, indent=2)
                else:
                    return f.read()
        except Exception as e:
            print(f"Error loading scenario description: {e}")
            return "Error loading scenario description."
    
    def load_analysis_results(self, analysis_file: str) -> str:
        """
        Load the analysis results from a file.
        
        Args:
            analysis_file (str): Path to the analysis results file.
            
        Returns:
            str: The analysis results.
        """
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading analysis results: {e}")
            return "Error loading analysis results."
    
    def load_metrics_metadata(self, metrics_file: str) -> Dict[str, Any]:
        """
        Load the metrics metadata from a file.
        
        Args:
            metrics_file (str): Path to the metrics metadata file.
            
        Returns:
            Dict[str, Any]: The metrics metadata.
        """
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # If it's scene_info.json, extract the metrics
                if 'metrics' in data:
                    return data['metrics']
                return data
        except Exception as e:
            print(f"Error loading metrics metadata: {e}")
            return {}
    
    def save_to_file(self, content: str, file_path: str) -> None:
        """
        Save content to a file.
        
        Args:
            content (str): The content to save.
            file_path (str): The path to save the content to.
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving to file {file_path}: {e}")


def main():
    """
    Main function to run the outline writing agent.
    """
    # Set up file paths
    base_dir = Path(__file__).parent
    scenario_file = base_dir / "test" / "odd_protocol.txt"
    analysis_file = base_dir / "test" / "analysis_result.txt"
    metrics_file = base_dir / "test" / "metrics.json"
    output_file = base_dir / "test" / "report_outline.txt"

    model_manager = get_model_manager()
    model_manager.load_model_configs("src/researcher/test/my_model_config.json")
    
    # Create and run the agent
    agent = OutlineWritingAgent("model_1")
    outline = agent.generate_report_outline(
        scenario_file=str(scenario_file),
        analysis_file=str(analysis_file),
        metrics_file=str(metrics_file),
        output_file=str(output_file)
    )
    
    print("Report outline saved to:", output_file)
    print("\nOutline preview:")
    print("-" * 50)
    print(outline[:500] + "..." if len(outline) > 500 else outline)
    print("-" * 50)


if __name__ == "__main__":
    main() 