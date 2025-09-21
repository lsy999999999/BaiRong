import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from onesim.models import get_model, get_model_manager, SystemMessage, UserMessage
from onesim.agent.base import AgentBase


class DataAnalysisAgent(AgentBase):
    """
    A data analysis agent that analyzes social simulation data and extracts insights.
    
    This agent takes a simulation scenario description, generated data visualizations,
    and metrics metadata to generate insights using a large language model.
    """
    
    def __init__(self, model_config_name: str = None):
        """
        Initialize the data analysis agent.
        
        Args:
            model_config_name (str, optional): The name of the model configuration to use.
                If None, the default model will be used.
        """
        sys_prompt = self._construct_system_prompt()
        super().__init__(sys_prompt=sys_prompt, model_config_name=model_config_name)
    
    def analyze(
        self,
        scenario_file: str,
        image_files: List[str],
        metrics_file: str,
        metrics_func_file: str,
        output_file: Optional[str] = None
    ) -> str:
        """
        Analyze simulation data and extract insights.
        
        Args:
            scenario_file (str): Path to the scenario description file.
            image_files (List[str]): Paths to visualization image files.
            metrics_file (str): Path to the metrics metadata file.
            metrics_func_file (str): Path to the metrics function file.
            output_file (str, optional): Path to save the analysis results. If None, results are not saved.
            
        Returns:
            str: Insights extracted from the simulation data.
        """
        # Load data
        scenario_description = self.load_scenario_description(scenario_file)
        metrics_metadata = self.load_metrics_metadata(metrics_file)
        metrics_functions = self.load_metrics_functions(metrics_func_file)
        
        # Construct the prompt text
        prompt_text = self._construct_prompt_text(
            scenario_description,
            metrics_metadata,
            metrics_functions,
            image_files
        )
        
        # Make sure we have a model
        if not hasattr(self, 'model'):
            from onesim.models import get_model
            self.model = get_model()
        
        # Call the LLM
        response = self.model(self.model.format(
            SystemMessage(content=self.sys_prompt),
            UserMessage(
                content=prompt_text,
                images=image_files
            )
        ))
        
        analysis_result = response.text
        
        # Save results to file if output_file is provided
        if output_file:
            self.save_to_file(analysis_result, output_file)
        
        return analysis_result
    
    def _construct_system_prompt(self) -> str:
        """
        Construct the system prompt for the LLM.
        
        Returns:
            str: The system prompt.
        """
        return """You are an expert data analyst specializing in multi-agent social simulations. 
Your task is to analyze data from simulation runs and provide meaningful insights.

Given:
1. A description of the simulation scenario following the ODD (Overview, Design Concepts, Details) protocol
2. Data visualizations from the simulation run
3. Metadata about the metrics being visualized
4. Function definitions for calculating those metrics

You should:
1. Understand the simulation scenario and its goals
2. Interpret the visualizations in the context of the metrics definitions
3. Identify patterns, correlations, and notable findings
4. Provide a comprehensive analysis with actionable insights

Your analysis should be thorough, data-driven, and focused on the research goals implied by the simulation scenario.
Support your insights with specific observations from the visualizations.
"""
    
    def _construct_prompt_text(
        self,
        scenario_description: str,
        metrics_metadata: List[Dict[str, Any]],
        metrics_functions: str,
        image_files: List[str]
    ) -> str:
        """
        Construct the text part of the user prompt for the LLM.
        
        Args:
            scenario_description (str): Simulation scenario description.
            metrics_metadata (List[Dict[str, Any]]): Metrics metadata.
            metrics_functions (str): Metrics function definitions.
            image_files (List[str]): Paths to visualization image files.
            
        Returns:
            str: The text content of the user prompt.
        """
        # Format metrics metadata for the prompt
        metrics_info = json.dumps(metrics_metadata, indent=2)
        
        # Prepare the text content
        text_content = f"""# Simulation Analysis Task

## Simulation Scenario (ODD Protocol)
```
{scenario_description}
```

## Metrics Metadata
```json
{metrics_info}
```

## Metrics Calculation Functions
```python
{metrics_functions}
```

Please analyze the attached visualizations in the context of the simulation scenario and metrics definitions.
Provide a comprehensive analysis with specific insights and patterns.
"""
        
        # Add image filenames for reference
        if image_files:
            text_content += "\n\n## Visualizations:\n"
            for img_path in image_files:
                img_filename = os.path.basename(img_path)
                text_content += f"- {img_filename}\n"
        
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
    
    def load_metrics_metadata(self, metrics_file: str) -> List[Dict[str, Any]]:
        """
        Load the metrics metadata from a file.
        
        Args:
            metrics_file (str): Path to the metrics metadata file.
            
        Returns:
            List[Dict[str, Any]]: The metrics metadata.
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
            return []
    
    def load_metrics_functions(self, metrics_func_file: str) -> str:
        """
        Load the metrics function definitions from a file.
        
        Args:
            metrics_func_file (str): Path to the metrics function file.
            
        Returns:
            str: The metrics function definitions.
        """
        try:
            with open(metrics_func_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading metrics functions: {e}")
            return "Error loading metrics functions."
    
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
    Main function to run the data analysis agent.
    """
    # Set up file paths
    base_dir = Path(__file__).parent
    scenario_file = base_dir / "test" / "odd_protocol.txt"
    metrics_file = base_dir / "test" / "metrics.json"
    metrics_func_file = base_dir / "test" / "metrics_func.py"
    image_files = [
        str(base_dir / "test" / "imgs" / "test_1.png"),
        str(base_dir / "test" / "imgs" / "test_2.png")
    ]
    output_file = base_dir / "test" / "analysis_result.txt"

    model_manager = get_model_manager()
    model_manager.load_model_configs("src/researcher/test/my_model_config.json")
    
    # Create and run the agent
    agent = DataAnalysisAgent("model_1")
    insights = agent.analyze(
        scenario_file=str(scenario_file),
        image_files=image_files,
        metrics_file=str(metrics_file),
        metrics_func_file=str(metrics_func_file),
        output_file=str(output_file)
    )
    
    print("Data analysis results saved to:", output_file)
    print("\nAnalysis results preview:")
    print("-" * 50)
    print(insights[:500] + "..." if len(insights) > 500 else insights)
    print("-" * 50)


if __name__ == "__main__":
    main() 