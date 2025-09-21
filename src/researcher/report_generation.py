#!/usr/bin/env python3
"""
Research Report Generation Entry Point Script
This script can be called directly from the command line to generate reports.
Supports report review and iterative improvement functionality.
"""

import os
import argparse
from pathlib import Path
import sys
import json
import re
import glob
import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from onesim.models import get_model_manager, get_model
from loguru import logger

# Import directly from researcher.report_generation package
from researcher.report_generation.data_analysis_agent import DataAnalysisAgent
from researcher.report_generation.outline_writing_agent import OutlineWritingAgent
from researcher.report_generation.reviewer_agent import ReviewerAgent
from researcher.report_generation.writing_process.generate_full_report import main as generate_report_main


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Social Simulation Research Report Generation Tool")
    
    # Base arguments for all commands
    parser.add_argument(
        "--scene_name", 
        type=str, 
        help="Name of the scene to analyze (directory under src/envs/).",
        required=True
    )
    
    parser.add_argument(
        "--model_name", 
        type=str, 
        help="Model configuration name (config_name from JSON) to use.", 
        default=None
    )

    parser.add_argument(
        "--model_config",
        type=str,
        default=None, # Will be handled in main to try default paths
        help="Path to the model configuration JSON file (relative to project root). Defaults to config/model_config.json then src/researcher/test/my_model_config.json."
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    
    # Data analysis command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze simulation data")
    
    # Outline generation command
    outline_parser = subparsers.add_parser("outline", help="Generate report outline")
    
    # Report generation command
    report_parser = subparsers.add_parser("report", help="Generate complete research report (assumes analysis and outline are done or skipped)")
    report_parser.add_argument(
        "--report_title",
        type=str,
        help="Report title (defaults to a formatted scene name).",
        default=None
    )
    report_parser.add_argument(
        "--report_author",
        type=str,
        help="Report author.",
        default="AI Social Researcher"
    )
    report_parser.add_argument(
        "--iterations",
        type=int,
        help="Number of report iterative improvement iterations.",
        default=3
    )
    report_parser.add_argument(
        "--skip_review",
        action="store_true",
        help="Skip review and iterative improvement process.",
        default=False
    )
    # These are effectively true by default for 'report' command, but can be explicitly set if needed for clarity
    report_parser.add_argument(
        "--skip_analysis",
        action="store_true",
        help="Skip data analysis step, use existing analysis results (default for 'report' command).",
        default=True # Default for 'report' subcommand
    )
    report_parser.add_argument(
        "--skip_outline",
        action="store_true",
        help="Skip outline generation step, use existing outline file (default for 'report' command).",
        default=True # Default for 'report' subcommand
    )
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review and evaluate an existing research report (LaTeX file)")
    review_parser.add_argument(
        "--latex_file",
        type=str,
        help="Path to LaTeX report file to be reviewed (e.g., src/envs/scene_name/research/report/report_iter1.tex).",
        required=True
    )
    
    # Full process command
    full_parser = subparsers.add_parser("full", help="Execute complete analysis and report generation process")
    full_parser.add_argument(
        "--report_title",
        type=str,
        help="Report title (defaults to a formatted scene name).",
        default=None
    )
    full_parser.add_argument(
        "--report_author",
        type=str,
        help="Report author.",
        default="AI Social Researcher"
    )
    full_parser.add_argument(
        "--iterations",
        type=int,
        help="Number of report iterative improvement iterations.",
        default=3
    )
    full_parser.add_argument(
        "--skip_review",
        action="store_true",
        help="Skip review and iterative improvement process.",
        default=False
    )
    full_parser.add_argument(
        "--skip_analysis",
        action="store_true",
        help="Skip data analysis step, use existing analysis results.",
        default=False # Default for 'full' subcommand
    )
    full_parser.add_argument(
        "--skip_outline",
        action="store_true",
        help="Skip outline generation step, use existing outline file.",
        default=False # Default for 'full' subcommand
    )
    
    return parser.parse_args()


def get_project_root() -> Path:
    """Gets the project root directory (assuming this script is in src/researcher/)."""
    return Path(__file__).resolve().parent.parent.parent


def get_scene_paths(scene_name: str) -> Dict[str, Any]:
    """
    Get scene file paths based on scene name, relative to the project root.
    
    Args:
        scene_name (str): The name of the scene.
        
    Returns:
        dict: A dictionary of file paths (as Path objects) for the scene.
    """
    if not scene_name:
        raise ValueError("Scene name is required.")
    
    project_root = get_project_root()
    base_path = project_root / "src" / "envs" / scene_name
    
    if not base_path.exists() or not base_path.is_dir():
        logger.error(f"Scene directory not found or is not a directory: {base_path}")
        raise FileNotFoundError(f"Scene '{scene_name}' directory not found at {base_path}")
    
    scene_info_path = base_path / "scene_info.json"
    metrics_func_path = base_path / "code" / "metrics" / "metrics.py"
    
    research_path = base_path / "research"
    report_path = research_path / "report"
    research_path.mkdir(parents=True, exist_ok=True)
    report_path.mkdir(parents=True, exist_ok=True)
    
    analysis_file = research_path / "analysis_result.md"
    outline_file = research_path / "report_outline.md"
    
    if not scene_info_path.exists():
        logger.error(f"scene_info.json not found at {scene_info_path}")
        raise FileNotFoundError(f"scene_info.json not found for scene '{scene_name}'. Was env_design.py run?")
    
    if not metrics_func_path.exists():
        logger.warning(f"Metrics function file not found at {metrics_func_path}. Analysis may be limited.")
    
    return {
        "base_path": base_path,
        "scene_info_path": scene_info_path,
        "metrics_func_path": metrics_func_path,
        "research_path": research_path,
        "report_path": report_path,
        "analysis_file": analysis_file,
        "outline_file": outline_file,
    }


def find_latest_images(scene_name: str) -> List[str]:
    """
    Find the latest metric plot images for the scene. Paths returned are absolute.
    
    Args:
        scene_name (str): The name of the scene.
        
    Returns:
        list: A list of absolute image file paths (as strings).
    """
    project_root = get_project_root()
    base_path = project_root / "src" / "envs" / scene_name
    metrics_plots_path = base_path / "metrics_plots"
    
    if not metrics_plots_path.exists():
        logger.warning(f"No metrics_plots directory found at {metrics_plots_path}")
        return []
    
    round_folders = list(metrics_plots_path.glob("round_*"))
    if not round_folders:
        logger.warning("No round folders found in metrics_plots directory.")
        return [str(p) for p in metrics_plots_path.rglob("*.png")] # Fallback: all pngs in metrics_plots
        
    sorted_rounds = sorted(round_folders, key=lambda x: int(x.name.split("round_")[-1]) if "round_" in x.name else 0)
    latest_round_path = sorted_rounds[-1]
    
    scene_metrics_path = latest_round_path / "scene_metrics"
    if not scene_metrics_path.exists():
        logger.warning(f"No scene_metrics folder found in {latest_round_path}")
        return [str(p) for p in latest_round_path.rglob("*.png")] # Fallback: all pngs in latest_round_path
    
    latest_images = []
    metric_folders = [f for f in scene_metrics_path.iterdir() if f.is_dir()]
    
    for metric_folder_path in metric_folders:
        image_files = list(metric_folder_path.glob("*.png"))
        if image_files:
            latest_image = sorted(image_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            latest_images.append(str(latest_image.resolve()))
    
    if not latest_images:
        logger.warning(f"No PNG images found in individual metric folders within {scene_metrics_path}. Searching recursively.")
        latest_images = [str(p.resolve()) for p in scene_metrics_path.rglob("*.png")]
    
    logger.info(f"Found {len(latest_images)} image(s) for the report from {latest_round_path}.")
    return latest_images


def save_json(data, file_path: Path):
    """
    Save data to a JSON file.
    
    Args:
        data: The data to save.
        file_path (Path): The path to save the data to.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def analyze_data(args, scene_paths: Dict[str, Path]) -> str:
    """
    Execute data analysis.
    
    Args:
        args: Command line arguments.
        scene_paths: Dictionary of scene paths.
        
    Returns:
        str: Path to the analysis results file (as string).
    """
    logger.info("=" * 60)
    logger.info("Data Analysis Process")
    logger.info("=" * 60)
    
    image_files = find_latest_images(args.scene_name)
    output_file = scene_paths["analysis_file"]
    
    model_config_name = args.model_name # This should be the config_name from JSON
    analysis_agent = DataAnalysisAgent(model_config_name=model_config_name)
    
    insights = analysis_agent.analyze(
        scenario_file=str(scene_paths["scene_info_path"]),
        image_files=image_files,
        metrics_file=str(scene_paths["scene_info_path"]), # Use scene_info.json for metrics metadata
        metrics_func_file=str(scene_paths["metrics_func_path"]),
        output_file=str(output_file)
    )
    
    logger.info(f"✓ Data analysis completed, results saved to: {output_file.relative_to(get_project_root())}")
    logger.info("\nAnalysis results preview:")
    logger.info("-" * 50)
    logger.info(insights[:500] + "..." if len(insights) > 500 else insights)
    logger.info("-" * 50)
    
    return str(output_file)


def generate_outline(args, scene_paths: Dict[str, Path]) -> str:
    """
    Generate report outline.
    
    Args:
        args: Command line arguments.
        scene_paths: Dictionary of scene paths.
    
    Returns:
        str: Path to the generated outline file (as string).
    """
    logger.info("=" * 60)
    logger.info("Report Outline Generation Process")
    logger.info("=" * 60)

    analysis_file = scene_paths["analysis_file"]
    if not analysis_file.exists():
        logger.error(f"Analysis file not found at {analysis_file}")
        raise FileNotFoundError(f"Analysis file not found. Please run 'analyze' command first.")
    
    output_file = scene_paths["outline_file"]
    model_config_name = args.model_name
    report_agent = OutlineWritingAgent(model_config_name=model_config_name)
    
    report_outline = report_agent.generate_report_outline(
        scenario_file=str(scene_paths["scene_info_path"]),
        analysis_file=str(analysis_file),
        metrics_file=str(scene_paths["scene_info_path"]), # Use scene_info.json for metrics metadata
        output_file=str(output_file)
    )
    
    logger.info(f"✓ Report outline generated, saved to: {output_file.relative_to(get_project_root())}")
    logger.info("\nOutline preview:")
    logger.info("-" * 60)
    logger.info(report_outline[:500] + "..." if len(report_outline) > 500 else report_outline)
    logger.info("-" * 60)
    
    return str(output_file)


def review_report_cli(args, scene_paths: Dict[str, Path]): # Renamed to avoid conflict
    """Review and evaluate research report (CLI handler)."""
    logger.info("=" * 60)
    logger.info("Report Review Evaluation Process")
    logger.info("=" * 60)

    latex_file_path = Path(args.latex_file)
    if not latex_file_path.exists():
        logger.error(f"LaTeX file not found at {latex_file_path}")
        raise FileNotFoundError(f"LaTeX file not found at {latex_file_path}")
    
    analysis_file = scene_paths["analysis_file"]
    if not analysis_file.exists():
        logger.error(f"Analysis file not found at {analysis_file}. Review may be incomplete.")
        # Decide if to proceed or raise error. For now, proceeding with a warning.

    latex_name = latex_file_path.stem
    output_file = scene_paths["report_path"] / f"review_{latex_name}.json"
    
    with open(latex_file_path, 'r', encoding='utf-8') as f:
        latex_content = f.read()
    
    section_contents = extract_section_contents(latex_content)
    model_config_name = args.model_name
    reviewer = ReviewerAgent(model_config_name=model_config_name)
    
    review_results = reviewer.review_report(
        latex_content=latex_content,
        section_contents=section_contents,
        scenario_file=str(scene_paths["scene_info_path"]),
        metrics_file=str(scene_paths["scene_info_path"]),
        analysis_file=str(analysis_file) if analysis_file.exists() else None, # Pass None if not found
        output_file=str(output_file)
    )
    
    logger.info(f"✓ Review feedback generated, results saved to: {output_file.relative_to(get_project_root())}")
    
    logger.info("\nReview Evaluation Summary:")
    logger.info("-" * 50)
    overall = review_results.get("overall_assessment", {})
    summary = overall.get("summary", "No review summary provided.")
    scores = overall.get("scores", {})
    logger.info(f"Overall evaluation: {summary[:300] + '...' if len(summary) > 300 else summary}")
    if scores:
      logger.info("\nScores:")
      for key, score in scores.items():
          logger.info(f"  - {key}: {score}")
    
    priorities = review_results.get("improvement_priorities", [])
    if priorities:
        logger.info("\nMain improvement suggestions:")
        for i, priority in enumerate(priorities[:5], 1):
            logger.info(f"  {i}. {priority}")
    logger.info("-" * 50)


def extract_section_contents(latex_content: str) -> dict:
    """
    Extract section contents from LaTeX content.
    This is a simplified version. More robust parsing might be needed for complex documents.
    """
    section_contents = {}
    section_names = ["Research Objectives", "Simulation Setup", "Experimental Results", "Conclusion"]
    for i, name in enumerate(section_names):
        # Regex to capture content between \section{Name} and the next \section or \end{document}
        # It handles optional arguments to \section like \section*[options]{Name}
        pattern_str = f"\\section\*?(\[.*?\])?{{{re.escape(name)}}}(.*?)"
        if i < len(section_names) - 1:
            next_section_escaped = re.escape(section_names[i+1])
            pattern_str += f"(?=\\section\*?(\[.*?\])?{{{next_section_escaped}}})"
        else:
            pattern_str += "(?=\\end{document})"
        
        matches = re.search(pattern_str, latex_content, re.DOTALL | re.IGNORECASE)
        if matches:
            content = matches.group(2).strip() # Group 2 is the content
            section_contents[name] = content
    return section_contents


def generate_full_workflow(args, scene_paths: Dict[str, Path]) -> str:
    """
    Run the full report generation workflow.
    
    Args:
        args: Command line arguments.
        scene_paths: Dictionary of scene paths.
        
    Returns:
        str: Path to the final generated report PDF (as string).
    """
    logger.info("\n" + "=" * 60)
    logger.info("FULL REPORT GENERATION WORKFLOW")
    logger.info("=" * 60)
    logger.info(f"Generating report for scene: {args.scene_name}")

    # Determine report title
    if not args.report_title:
        with open(scene_paths["scene_info_path"], 'r', encoding='utf-8') as f:
            scene_info = json.load(f)
        report_title_from_info = scene_info.get("scene_name", args.scene_name).replace("_", " ").title()
        args.report_title = f"{report_title_from_info} Analysis Report"
    
    output_filename_prefix = "simulation_report"
    output_dir = scene_paths["report_path"]
    
    analysis_file_str = str(scene_paths["analysis_file"])
    outline_file_str = str(scene_paths["outline_file"])
    
    if not args.skip_analysis:
        logger.info("\n[Step 1/3] Performing data analysis...")
        analysis_file_str = analyze_data(args, scene_paths)
    else:
        logger.info("\n[Step 1/3] Skipping data analysis...")
        if not Path(analysis_file_str).exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_file_str}. Run 'analyze' or disable skip.")
        logger.info(f"✓ Using existing analysis from: {Path(analysis_file_str).relative_to(get_project_root())}")
    
    if not args.skip_outline:
        logger.info("\n[Step 2/3] Generating report outline...")
        outline_file_str = generate_outline(args, scene_paths)
    else:
        logger.info("\n[Step 2/3] Skipping outline generation...")
        if not Path(outline_file_str).exists():
            raise FileNotFoundError(f"Outline file not found: {outline_file_str}. Run 'outline' or disable skip.")
        logger.info(f"✓ Using existing outline from: {Path(outline_file_str).relative_to(get_project_root())}")
    
    logger.info("\n[Step 3/3] Generating full report (LaTeX compilation and optional review)...")
    image_files = find_latest_images(args.scene_name) # Returns absolute paths
    
    model_config_name = args.model_name
    
    cmd_params_for_generate_report = [
        "--scenario_file", str(scene_paths["scene_info_path"]),
        "--metrics_file", str(scene_paths["scene_info_path"]), # Using scene_info for metrics metadata
        "--metrics_func_file", str(scene_paths["metrics_func_path"]),
        "--analysis_file", analysis_file_str,
        "--outline_file", outline_file_str,
        "--output_dir", str(output_dir),
        "--report_title", args.report_title,
        "--report_author", args.report_author,
        "--output_filename", output_filename_prefix,
    ]
    
    if model_config_name:
        cmd_params_for_generate_report.extend(["--model_config", model_config_name])
    if args.skip_review:
        cmd_params_for_generate_report.append("--skip_review")
    if hasattr(args, 'iterations') and args.iterations is not None:
        cmd_params_for_generate_report.extend(["--iterations", str(args.iterations)])
    if image_files:
        cmd_params_for_generate_report.append("--image_files")
        cmd_params_for_generate_report.extend(image_files) # Pass absolute paths
    
    original_sys_argv = sys.argv
    sys.argv = ["generate_full_report.py"] + cmd_params_for_generate_report
    try:
        generate_report_main() # This is the main from the imported script
    finally:
        sys.argv = original_sys_argv
    
    logger.info("\nFull report workflow completed successfully!")
    logger.info("=" * 60)
    final_report_path = output_dir / f"{output_filename_prefix}_final.pdf"
    logger.info(f"Report generated at: {final_report_path.relative_to(get_project_root())}")
    
    return str(final_report_path)


def main():
    """Main entry point for report generation script."""
    args = parse_args()
    project_root = get_project_root()

    # Determine model_config_file_path
    model_config_file_to_load = None
    if args.model_config: # User specified a path
        model_config_file_to_load = project_root / args.model_config
        if not model_config_file_to_load.exists():
            logger.error(f"Specified model configuration file not found: {model_config_file_to_load}")
            return 1
    else: # Try default paths
        default_primary_path = project_root / "config" / "model_config.json"
        default_fallback_path = project_root / "src" / "researcher" / "test" / "my_model_config.json"
        if default_primary_path.exists():
            model_config_file_to_load = default_primary_path
        elif default_fallback_path.exists():
            model_config_file_to_load = default_fallback_path
            logger.warning(f"Primary model config '{default_primary_path}' not found. Using fallback: {default_fallback_path}")
        else:
            logger.error(f"Default model configuration files not found at '{default_primary_path}' or '{default_fallback_path}'. Please specify with --model_config.")
            return 1

    model_manager = get_model_manager()
    try:
        model_manager.load_model_configs(str(model_config_file_to_load))
        logger.info(f"Loaded model configurations from: {model_config_file_to_load}")
    except Exception as e:
        logger.error(f"Could not load model configurations from '{model_config_file_to_load}': {e}")
        return 1

    try:
        scene_paths = get_scene_paths(args.scene_name)

        if args.command == "analyze":
            analyze_data(args, scene_paths)
        elif args.command == "outline":
            generate_outline(args, scene_paths)
        elif args.command == "review":
            review_report_cli(args, scene_paths)
        elif args.command == "report":
            # For 'report', skip_analysis and skip_outline are True by default in parse_args
            generate_full_workflow(args, scene_paths)
        elif args.command == "full":
            # For 'full', skip_analysis and skip_outline are False by default in parse_args
            generate_full_workflow(args, scene_paths)
        else:
            # Should not happen due to `required=True` for subparsers, but as a fallback:
            logger.error(f"Invalid command: {args.command}")
            parser.print_help()
            return 1
            
    except FileNotFoundError as fnf_error:
        logger.error(f"File not found during operation: {fnf_error}")
        logger.error("Please check if the required files exist or if previous steps were completed successfully.")
        return 1
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 