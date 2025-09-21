#!/usr/bin/env python3
"""
Main entry point for the experimental design workflow.

This module provides a command line interface for running the
experimental design workflow, which generates a detailed simulation
specification from a vague research topic.
"""

import os
import sys
import argparse
import json
import re
import random
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) # Assuming this script is in src/researcher/

from onesim.models import get_model_manager,get_model
from loguru import logger

# Import agents - adjust path as needed if agents are in a different location relative to this script
from researcher.env_design import InspirationAgent 
from researcher.env_design import EvaluatorAgent   
from researcher.env_design import DetailerAgent    
from researcher.env_design import AssessorAgent    



class Coordinator:
    """
    Coordinator for the experimental design workflow.
    
    The coordinator manages the workflow between the three main agents
    (InspirationAgent, EvaluatorAgent, and DetailerAgent) to generate
    a detailed simulation specification from a vague research topic.
    """
    
    def __init__(
        self,
        scene_name: Optional[str] = None,
        model_name: Optional[str] = None,
        save_intermediate: bool = True
    ):
        """
        Initialize the coordinator.
        
        Args:
            scene_name (str, optional): The name of the scene to create.
            model_name (str, optional): The model configuration name to use.
            save_intermediate (bool, optional): Whether to save intermediate outputs.
        """
        self.scene_name = scene_name
        self.model_name = model_name
        self.save_intermediate = save_intermediate
        
        # Initialize agents
        self.inspiration_agent = InspirationAgent(model_name)
        self.evaluator_agent = EvaluatorAgent(model_name)
        self.detailer_agent = DetailerAgent(model_name)
        self.assessor_agent = AssessorAgent(model_name)
    
    def setup_environment(self, scene_name: str) -> str:
        """
        Set up environment directory structure relative to the 'src/envs' directory.
        
        Args:
            scene_name (str): The name of the scene.
            
        Returns:
            str: The path to the created environment root under 'src/envs/'.
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        env_base_path = project_root / "src" / "envs"
        
        env_path = env_base_path / scene_name
        research_path = env_path / "research" / "env_design"
        
        # Create directories
        env_path.mkdir(parents=True, exist_ok=True)
        research_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize package
        init_file = env_path / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w') as f:
                f.write("")
                
        return str(env_path)
    
    def run(self, research_topic: str) -> Dict[str, Any]:
        """
        Run the experimental design workflow.
        
        Args:
            research_topic (str): The vague research topic to start with.
            
        Returns:
            Dict[str, Any]: The final detailed simulation specification.
        """
        logger.info(f"{'='*80}")
        logger.info(f"Starting experimental design process for topic: {research_topic}")
        logger.info(f"{'='*80}")
        
        # Determine project root and base path for envs
        project_root = Path(__file__).resolve().parent.parent.parent
        envs_base_path = project_root / "src" / "envs"

        temp_dir_name = f"temp_outputs_{random.randint(100000, 999999)}"
        # Create a temporary directory for intermediate outputs within the project structure (e.g., in a .tmp folder or similar)
        # For simplicity here, placing it where it was, but ideally in a gitignored .tmp folder at project root.
        temp_dir = envs_base_path / temp_dir_name 
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Generate research questions and scenarios
        logger.info("\n[Step 1/3] Generating potential research questions and scenarios...")
        inspiration_input = {"research_topic": research_topic}
        inspiration_output = self.inspiration_agent.process(inspiration_input)
        inspiration_output["original_topic"] = research_topic  # Ensure original topic is passed along
        
        if self.save_intermediate:
            self._save_json(
                inspiration_output,
                str(temp_dir / "inspiration_output.json")
            )
            logger.info(f"✓ Saved inspiration output to temporary location.")
        
        questions = inspiration_output.get("research_questions", [])
        logger.info(f"\nGenerated {len(questions)} potential research questions:")
        for q in questions:
            logger.info(f"  - Q{q.get('id', '')}: {q.get('question', '')}")
        
        logger.info("\n[Step 2/3] Evaluating and selecting the most promising scenario...")
        evaluator_output = self.evaluator_agent.process(inspiration_output)
        
        if self.save_intermediate:
            self._save_json(
                evaluator_output,
                str(temp_dir / "evaluator_output.json")
            )
            logger.info(f"✓ Saved evaluator output to temporary location.")
        
        selected_scenario = evaluator_output.get("selected_scenario_details", {})
        selected_id = selected_scenario.get("id", "")
        selected_question = selected_scenario.get("question", "")
        
        logger.info(f"\nSelected research question (ID: {selected_id}):")
        logger.info(f"  {selected_question}")
        logger.info(f"\nSelection rationale:")
        logger.info(f"  {evaluator_output.get('selected_scenario', {}).get('rationale', '')[:200]}...")
        
        evaluator_output["original_topic"] = research_topic
        
        logger.info("\n[Step 3/3] Elaborating the selected scenario into an ODD protocol...")
        detailer_output = self.detailer_agent.process(evaluator_output)
        
        generated_scene_name = detailer_output.get("scene_name", "")
        if not generated_scene_name:
            generated_scene_name = self.detailer_agent.get_scene_info().get("scene_name", "")
            
        if self.scene_name:
            logger.info(f"Using provided scene name: {self.scene_name}")
        elif generated_scene_name:
            self.scene_name = generated_scene_name
            logger.info(f"Using generated scene name from DetailerAgent: {self.scene_name}")
        else:
            self.scene_name = re.sub(r'[^a-zA-Z0-9]', '_', research_topic.lower())
            self.scene_name = re.sub(r'_+', '_', self.scene_name)
            self.scene_name = self.scene_name.strip('_')[:50]
            if not self.scene_name:
                self.scene_name = "research_simulation"
            logger.info(f"Using fallback scene name: {self.scene_name}")
        
        env_path_str = self.setup_environment(self.scene_name) # Returns root of env: src/envs/scene_name
        env_path = Path(env_path_str)
        research_path = env_path / "research" / "env_design" # This is src/envs/scene_name/research/env_design
        
        specification = detailer_output.get("detailed_specification", "")
        if specification:
            specification_path = research_path / "detailed_specification.md"
            with open(specification_path, 'w', encoding='utf-8') as f:
                f.write(specification)
            logger.info(f"✓ Saved detailed specification to {specification_path.relative_to(project_root)}")
        
        if self.save_intermediate:
            if (temp_dir / "inspiration_output.json").exists():
                with open(temp_dir / "inspiration_output.json", 'r') as f:
                    data = json.load(f)
                self._save_json(data, str(research_path / "inspiration_output.json"))
                logger.info(f"✓ Copied inspiration output to { (research_path / 'inspiration_output.json').relative_to(project_root) }")
            
            if (temp_dir / "evaluator_output.json").exists():
                with open(temp_dir / "evaluator_output.json", 'r') as f:
                    data = json.load(f)
                self._save_json(data, str(research_path / "evaluator_output.json"))
                logger.info(f"✓ Copied evaluator output to { (research_path / 'evaluator_output.json').relative_to(project_root) }")
        
        odd_protocol_path = research_path / "odd_protocol.json"
        self._save_json(
            detailer_output.get("odd_protocol", {}),
            str(odd_protocol_path)
        )
        logger.info(f"✓ Saved ODD protocol to {odd_protocol_path.relative_to(project_root)}")
        
        self.detailer_agent.save_scene_info(str(env_path)) # Expects string path to src/envs/scene_name
        logger.info(f"✓ Saved scene_info.json to {(env_path / 'scene_info.json').relative_to(project_root)}")
        
        final_output = {
            "original_topic": research_topic,
            "selected_research_question": selected_question,
            "scene_name": self.scene_name,
            "domain": detailer_output.get("domain", "")
        }
        
        final_summary_path = research_path / "final_output_summary.json"
        self._save_json(
            final_output,
            str(final_summary_path)
        )
        
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Experimental design process completed successfully!")
        logger.info(f"{'='*80}")
        logger.info(f"\nEnvironment created at:")
        logger.info(f"  {(env_path).relative_to(project_root.parent)}") # Show relative to project root's parent for brevity
        
        return detailer_output
    
    def assess(self, scene_name: str) -> Dict[str, Any]:
        """
        Assess the quality of the ODD protocol conversion based on four metrics.
        
        Args:
            scene_name (str): The name of the scene to assess.
            
        Returns:
            Dict[str, Any]: The assessment results.
        """
        logger.info(f"{'='*80}")
        logger.info(f"Starting assessment process for scene: {scene_name}")
        logger.info(f"{'='*80}")
        
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / "src" / "envs" / scene_name
        research_path = env_path / "research" / "env_design"
        
        if not env_path.exists():
            logger.error(f"Scene '{scene_name}' does not exist at path: {env_path}")
            return {"error": f"Scene '{scene_name}' does not exist"}
        
        odd_protocol_path = research_path / "odd_protocol.json"
        summary_path = research_path / "final_output_summary.json"
        
        if not odd_protocol_path.exists():
            logger.error(f"ODD protocol not found at: {odd_protocol_path}")
            return {"error": "ODD protocol not found"}
        
        with open(odd_protocol_path, 'r', encoding='utf-8') as f:
            odd_protocol = json.load(f)
        
        original_topic = ""
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                original_topic = summary.get("original_topic", "")
        
        assessment_input = {
            "original_topic": original_topic,
            "odd_protocol": odd_protocol,
            "scene_name": scene_name
        }
        
        logger.info("\nAssessing conversion quality based on four metrics...")
        assessment_output = self.assessor_agent.process(assessment_input)
        
        assessment_results_path = research_path / "assessment_results.json"
        self._save_json(assessment_output, str(assessment_results_path))
        logger.info(f"✓ Saved assessment results to {assessment_results_path.relative_to(project_root)}")
        
        logger.info("\nAssessment Results:")
        logger.info(f"Relevance:   {assessment_output.get('relevance', {}).get('score', 0)}/5 - {assessment_output.get('relevance', {}).get('summary', '')}")
        logger.info(f"Fidelity:    {assessment_output.get('fidelity', {}).get('score', 0)}/5 - {assessment_output.get('fidelity', {}).get('summary', '')}")
        logger.info(f"Feasibility: {assessment_output.get('feasibility', {}).get('score', 0)}/5 - {assessment_output.get('feasibility', {}).get('summary', '')}")
        logger.info(f"Significance: {assessment_output.get('significance', {}).get('score', 0)}/5 - {assessment_output.get('significance', {}).get('summary', '')}")
        logger.info(f"\nOverall Score: {assessment_output.get('overall_score', 0)}/20")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Assessment process completed successfully!")
        logger.info(f"{'='*80}")
        
        return assessment_output
    
    def _save_json(self, data: Dict[str, Any], file_path: str) -> None:
        """
        Save data to a JSON file.
        
        Args:
            data (Dict[str, Any]): The data to save.
            file_path (str): The path to save the data to.
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a detailed simulation specification from a vague research topic."
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        help="The vague research topic to start with."
    )
    
    parser.add_argument(
        "--scene_name",
        type=str,
        default=None,
        help="Name for the environment scene directory."
    )
    
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help="Model configuration name (config_name from JSON) to use."
    )
    
    parser.add_argument(
        "--model_config",
        type=str,
        default="config/model_config.json", # Default relative to project root
        help="Path to the model configuration JSON file (relative to project root)."
    )
    
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save intermediate outputs."
    )
    
    parser.add_argument(
        "--assess",
        action="store_true",
        help="Run assessment on an existing scene."
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for the experimental design workflow.
    """
    args = parse_args()
    
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        model_config_abs_path = project_root / args.model_config

        if not model_config_abs_path.exists():
            logger.error(f"Model configuration file not found at: {model_config_abs_path}")
            logger.error(f"Please ensure the path specified by --model_config is correct or the default '{args.model_config}' exists relative to the project root.")
            return 1
            
        model_manager = get_model_manager()
        model_manager.load_model_configs(str(model_config_abs_path))
        logger.info(f"Loaded model configurations from: {model_config_abs_path}")
        
        coordinator = Coordinator(
            scene_name=args.scene_name,
            model_name=args.model_name,
            save_intermediate=args.save
        )
        
        if args.assess and not args.topic: # If only assess is true
             if not args.scene_name:
                logger.error("Scene name is required for assessment mode when no topic is provided.")
                parser.print_help()
                return 1
             coordinator.assess(args.scene_name)
             return 0

        if not args.topic:
            logger.error("Research topic (--topic) is required to run the design workflow.")
            parser.print_help()
            return 1
            
        result = coordinator.run(args.topic)
        
        if args.assess: # If assess is true along with a topic (assess after run)
            # coordinator.scene_name would have been set during the run
            if coordinator.scene_name:
                 coordinator.assess(coordinator.scene_name)
            else:
                logger.warning("Could not run assessment as scene_name was not determined during the run.")
        
        return 0
    except Exception as e:
        logger.error(f"\nAn error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main()) # Ensure exit code is propagated