#!/usr/bin/env python3
"""
Generate Complete Research Report Script - Connects various section generators,
produces a complete research report and compiles it to PDF.
Supports iterative improvement, enhancing report quality based on review feedback.
"""

import os
import argparse
import json
import shutil
from pathlib import Path
import tempfile
from typing import Dict, List, Optional, Tuple, Any

from .research_objectives import ResearchObjectivesSection
from .simulation_setup import SimulationSetupSection
from .experimental_results import ExperimentalResultsSection
from .conclusion import ConclusionSection
from .latex_compiler import LatexCompiler

from .. import ReviewerAgent


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate complete research report")
    
    parser.add_argument(
        "--scenario_file",
        type=str,
        help="Path to ODD protocol scenario description file",
        default=None
    )
    
    parser.add_argument(
        "--metrics_file",
        type=str,
        help="Path to metrics metadata file",
        default=None
    )
    
    parser.add_argument(
        "--metrics_func_file",
        type=str,
        help="Path to metrics calculation function file",
        default=None
    )
    
    parser.add_argument(
        "--analysis_file",
        type=str,
        help="Path to data analysis results file",
        default=None
    )
    
    parser.add_argument(
        "--outline_file",
        type=str,
        help="Path to report outline file",
        default=None
    )
    
    parser.add_argument(
        "--image_files",
        type=str,
        nargs="+",
        help="List of paths to data visualization image files",
        default=None
    )
    
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Path to output directory",
        default=None
    )
    
    parser.add_argument(
        "--report_title",
        type=str,
        help="Report title",
        default="Multi-Agent Social Simulation Analysis Report"
    )
    
    parser.add_argument(
        "--report_author",
        type=str,
        help="Report author",
        default="OneSim Social AI Researcher"
    )
    
    parser.add_argument(
        "--output_filename",
        type=str,
        help="Output filename (without extension)",
        default="simulation_report"
    )
    
    parser.add_argument(
        "--model_config",
        type=str,
        help="Model configuration name",
        default=None
    )
    
    parser.add_argument(
        "--save_intermediates",
        action="store_true",
        help="Whether to save intermediate files",
        default=False
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        help="Number of report iterative improvement iterations",
        default=3
    )
    
    parser.add_argument(
        "--skip_review",
        action="store_true",
        help="Skip review and iterative improvement process",
        default=False
    )
    
    return parser.parse_args()


def get_default_paths():
    """Get default file paths"""
    base_dir = Path(__file__).parent.parent
    
    return {
        "scenario_file": str(base_dir / "test" / "odd_protocol.txt"),
        "metrics_file": str(base_dir / "test" / "metrics.json"),
        "metrics_func_file": str(base_dir / "test" / "metrics_func.py"),
        "analysis_file": str(base_dir / "test" / "analysis_result.txt"),
        "outline_file": str(base_dir / "test" / "report_outline.txt"),
        "image_files": [
            str(base_dir / "test" / "imgs" / "test_1.png"),
            str(base_dir / "test" / "imgs" / "test_2.png")
        ],
        "output_dir": str(base_dir / "test" / "report")
    }


def generate_report_sections(
    scenario_file: str,
    metrics_file: str,
    analysis_file: str,
    outline_file: str,
    image_files: List[str],
    temp_dir: str,
    iteration: int = 0,
    review_results: Optional[Dict[str, Any]] = None,
    model_config: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate content for report sections.
    
    Args:
        scenario_file (str): Path to the scenario description file.
        metrics_file (str): Path to the metrics metadata file.
        analysis_file (str): Path to the data analysis results file.
        outline_file (str): Path to the report outline file.
        image_files (List[str]): List of paths to image files.
        temp_dir (str): Path to the temporary directory.
        iteration (int, optional): Current iteration number.
        review_results (Dict[str, Any], optional): Results from the previous review round.
        model_config (str, optional): Model configuration name.
        
    Returns:
        Dict[str, str]: Dictionary of file paths for each section.
    """
    section_files = {}
    
    # Create review prompt file (if review results exist)
    review_prompt_file = None
    if review_results:
        review_prompt_file = os.path.join(temp_dir, f"review_prompt_iter_{iteration}.json")
        with open(review_prompt_file, 'w', encoding='utf-8') as f:
            json.dump(review_results, f, ensure_ascii=False, indent=2)
    
    # Step 1: Generate Research Objectives section
    print(f"\n[Step 1/4] Generating Research Objectives section..." + (f" (Iteration {iteration})" if iteration > 0 else ""))
    research_obj_section = ResearchObjectivesSection(model_config=model_config)
    research_obj_file = os.path.join(temp_dir, f"research_objectives_iter_{iteration}.tex")
    
    research_obj_section.generate_section_content(
        scenario_file=scenario_file,
        metrics_file=metrics_file,
        analysis_file=analysis_file,
        outline_file=outline_file,
        output_file=research_obj_file,
        review_file=review_prompt_file if review_results else None
    )
    
    section_files["Research Objectives"] = research_obj_file
    print(f"✓ Research Objectives section generated")
    
    # Step 2: Generate Simulation Setup section
    print(f"\n[Step 2/4] Generating Simulation Setup section..." + (f" (Iteration {iteration})" if iteration > 0 else ""))
    setup_section = SimulationSetupSection(model_config=model_config)
    setup_file = os.path.join(temp_dir, f"simulation_setup_iter_{iteration}.tex")
    
    setup_section.generate_section_content(
        scenario_file=scenario_file,
        metrics_file=metrics_file,
        analysis_file=analysis_file,
        outline_file=outline_file,
        output_file=setup_file,
        review_file=review_prompt_file if review_results else None
    )
    
    section_files["Simulation Setup"] = setup_file
    print(f"✓ Simulation Setup section generated")
    
    # Step 3: Generate Experimental Results section
    print(f"\n[Step 3/4] Generating Experimental Results section..." + (f" (Iteration {iteration})" if iteration > 0 else ""))
    results_section = ExperimentalResultsSection(model_config=model_config)
    results_file = os.path.join(temp_dir, f"experimental_results_iter_{iteration}.tex")
    
    results_section.generate_section_content(
        scenario_file=scenario_file,
        metrics_file=metrics_file,
        analysis_file=analysis_file,
        outline_file=outline_file,
        image_files=image_files,
        output_file=results_file,
        review_file=review_prompt_file if review_results else None
    )
    
    section_files["Experimental Results"] = results_file
    print(f"✓ Experimental Results section generated")
    
    # Step 4: Generate Conclusion section
    print(f"\n[Step 4/4] Generating Conclusion section..." + (f" (Iteration {iteration})" if iteration > 0 else ""))
    conclusion_section = ConclusionSection(model_config=model_config)
    conclusion_file = os.path.join(temp_dir, f"conclusion_iter_{iteration}.tex")
    
    conclusion_section.generate_section_content(
        scenario_file=scenario_file,
        metrics_file=metrics_file,
        analysis_file=analysis_file,
        outline_file=outline_file,
        output_file=conclusion_file,
        review_file=review_prompt_file if review_results else None
    )
    
    section_files["Conclusion"] = conclusion_file
    print(f"✓ Conclusion section generated")
    
    return section_files


def get_version_dir(output_dir: str, iteration: int) -> str:
    """
    Get the version directory for the specified iteration.
    
    Args:
        output_dir (str): Base output directory.
        iteration (int): Iteration number.
        
    Returns:
        str: Path to the version directory.
    """
    version_dir = os.path.join(output_dir, f"v{iteration+1}")
    Path(version_dir).mkdir(parents=True, exist_ok=True)
    
    # Create images directory within version dir
    images_dir = os.path.join(version_dir, "images")
    Path(images_dir).mkdir(parents=True, exist_ok=True)
    
    return version_dir


def copy_images_to_version_dir(image_files: List[str], version_dir: str) -> List[str]:
    """
    Copy image files to the version directory's images folder.
    
    Args:
        image_files (List[str]): Original image file paths.
        version_dir (str): Version directory path.
        
    Returns:
        List[str]: New image file paths within the version directory.
    """
    if not image_files:
        return []
    
    images_dir = os.path.join(version_dir, "images")
    new_image_paths = []
    
    for img_path in image_files:
        if not os.path.exists(img_path):
            print(f"Warning: Image file not found: {img_path}")
            continue
        
        img_filename = os.path.basename(img_path)
        dest_path = os.path.join(images_dir, img_filename)
        
        # Copy the file
        shutil.copy2(img_path, dest_path)
        new_image_paths.append(dest_path)
    
    return new_image_paths


def compile_full_report(
    title: str,
    author: str,
    section_files: Dict[str, str],
    image_files: List[str],
    output_dir: str,
    output_filename: str,
    abstract: str,
    iteration: int = 0
) -> Tuple[str, str]:
    """
    Compile the complete research report.
    
    Args:
        title (str): Report title.
        author (str): Report author.
        section_files (Dict[str, str]): Dictionary of file paths for each section.
        image_files (List[str]): List of paths to image files.
        output_dir (str): Path to the output directory.
        output_filename (str): Output filename (without extension).
        abstract (str): Report abstract.
        iteration (int, optional): Current iteration number.
        
    Returns:
        Tuple[str, str]: (Path to the generated PDF file, complete LaTeX content)
    """
    # Get the version directory
    version_dir = get_version_dir(output_dir, iteration)
    
    # Copy images to version directory
    version_image_files = copy_images_to_version_dir(image_files, version_dir)
    
    # Compile report
    print(f"\n[Compiling] Compiling complete report to PDF..." + (f" (Iteration {iteration+1})" if iteration > 0 else ""))
    latex_compiler = LatexCompiler(output_dir=version_dir)
    
    # Modify output filename for consistency
    full_output_filename = output_filename
    
    # Get complete LaTeX content
    latex_content = latex_compiler.generate_latex_document(
        title=title,
        author=author,
        section_files=section_files,
        abstract=abstract
    )
    
    # Save complete LaTeX file
    latex_file_path = os.path.join(version_dir, f"{full_output_filename}.tex")
    with open(latex_file_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    # Compile to PDF
    pdf_path = latex_compiler.compile_report_from_content(
        title=title,
        author=author,
        latex_content=latex_content,
        image_files=version_image_files,
        output_filename=full_output_filename,
        abstract=abstract
    )
    
    print(f"✓ Report compiled to PDF: {pdf_path}")
    return pdf_path, latex_content


def review_report(
    latex_content: str,
    section_files: Dict[str, str],
    scenario_file: str,
    metrics_file: str,
    analysis_file: str,
    output_dir: str,
    iteration: int,
    model_config: Optional[str] = None
) -> Dict[str, Any]:
    """
    Review the research report.
    
    Args:
        latex_content (str): Complete LaTeX report content.
        section_files (Dict[str, str]): Dictionary of file paths for each section.
        scenario_file (str): Path to the scenario description file.
        metrics_file (str): Path to the metrics metadata file.
        analysis_file (str): Path to the data analysis results file.
        output_dir (str): Path to the output directory.
        iteration (int): Current iteration number.
        model_config (str, optional): Model configuration name.
        
    Returns:
        Dict[str, Any]: Review results.
    """
    # Get the version directory
    version_dir = get_version_dir(output_dir, iteration)
    
    print(f"\n[Review] Starting report review..." + (f" (Iteration {iteration+1})" if iteration > 0 else ""))
    
    # Read content from each section file
    section_contents = {}
    for section_name, file_path in section_files.items():
        with open(file_path, 'r', encoding='utf-8') as f:
            section_contents[section_name] = f.read()
    
    # Create reviewer agent
    reviewer = ReviewerAgent(model_config_name=model_config)
    
    # Review report
    review_output_file = os.path.join(version_dir, f"review_results.json")
    review_results = reviewer.review_report(
        latex_content=latex_content,
        section_contents=section_contents,
        scenario_file=scenario_file,
        metrics_file=metrics_file,
        analysis_file=analysis_file,
        output_file=review_output_file
    )
    
    # Also save a human-readable text version of the review
    review_text_file = os.path.join(version_dir, f"review.md")
    _save_human_readable_review(review_results, review_text_file)
    
    # Print review summary
    print("\n" + "=" * 50)
    print(f"Report Review Results (Version {iteration+1}):")
    print("-" * 50)
    
    overall = review_results.get("overall_assessment", {})
    summary = overall.get("summary", "No review summary")
    scores = overall.get("scores", {})
    
    print(f"Overall assessment: {summary[:100]}..." if len(summary) > 100 else summary)
    print("\nScores:")
    for key, score in scores.items():
        print(f"  - {key}: {score}")
    
    print("\nMain improvement suggestions:")
    priorities = review_results.get("improvement_priorities", [])
    for i, priority in enumerate(priorities[:3], 1):
        print(f"  {i}. {priority}")
    
    print("=" * 50)
    print(f"✓ Review saved to: {review_output_file} (JSON) and {review_text_file} (TXT)")
    
    return review_results


def _save_human_readable_review(review_results: Dict[str, Any], output_file: str) -> None:
    """
    Save review results in a human-readable text format.
    
    Args:
        review_results (Dict[str, Any]): Review results dictionary.
        output_file (str): Output file path.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# RESEARCH REPORT REVIEW\n\n")
        
        # Overall assessment
        overall = review_results.get("overall_assessment", {})
        f.write("## OVERALL ASSESSMENT\n\n")
        f.write(overall.get("summary", "No summary provided") + "\n\n")
        
        # Strengths
        strengths = overall.get("strengths", [])
        if strengths:
            f.write("### STRENGTHS\n\n")
            for i, strength in enumerate(strengths, 1):
                f.write(f"{i}. {strength}\n")
            f.write("\n")
        
        # Weaknesses
        weaknesses = overall.get("weaknesses", [])
        if weaknesses:
            f.write("### WEAKNESSES\n\n")
            for i, weakness in enumerate(weaknesses, 1):
                f.write(f"{i}. {weakness}\n")
            f.write("\n")
        
        # Scores
        scores = overall.get("scores", {})
        if scores:
            f.write("### SCORES\n\n")
            for key, score in scores.items():
                f.write(f"{key.capitalize()}: {score}/10\n")
            f.write("\n")
        
        # Section reviews
        section_reviews = review_results.get("section_reviews", {})
        if section_reviews:
            f.write("## SECTION REVIEWS\n\n")
            for section_name, review in section_reviews.items():
                f.write(f"### {section_name.upper()}\n\n")
                f.write(review.get("assessment", "No assessment provided") + "\n\n")
                
                suggestions = review.get("suggestions", [])
                if suggestions:
                    f.write("Suggestions:\n")
                    for i, suggestion in enumerate(suggestions, 1):
                        f.write(f"{i}. {suggestion}\n")
                    f.write("\n")
        
        # LaTeX format issues
        format_issues = review_results.get("latex_format_issues", [])
        if format_issues:
            f.write("## LATEX FORMAT ISSUES\n\n")
            for i, issue in enumerate(format_issues, 1):
                f.write(f"{i}. {issue}\n")
            f.write("\n")
        
        # Improvement priorities
        priorities = review_results.get("improvement_priorities", [])
        if priorities:
            f.write("## IMPROVEMENT PRIORITIES\n\n")
            for i, priority in enumerate(priorities, 1):
                f.write(f"{i}. {priority}\n")
            f.write("\n")


def save_intermediate_files(
    section_files: Dict[str, str],
    output_dir: str,
    iteration: int
) -> None:
    """
    Save intermediate generated files.
    
    Args:
        section_files (Dict[str, str]): Dictionary of file paths for each section.
        output_dir (str): Path to the output directory.
        iteration (int): Current iteration number.
    """
    # Get the version directory
    version_dir = get_version_dir(output_dir, iteration)
    intermediate_dir = os.path.join(version_dir, "intermediate")
    Path(intermediate_dir).mkdir(parents=True, exist_ok=True)
    
    for section_name, file_path in section_files.items():
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(intermediate_dir, file_name)
        shutil.copy2(file_path, dest_path)
    
    print(f"\n✓ Intermediate files saved to: {intermediate_dir}")


def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Get default paths
    default_paths = get_default_paths()
    
    # Use command line arguments or default values
    scenario_file = args.scenario_file or default_paths["scenario_file"]
    metrics_file = args.metrics_file or default_paths["metrics_file"]
    metrics_func_file = args.metrics_func_file or default_paths["metrics_func_file"]
    analysis_file = args.analysis_file or default_paths["analysis_file"]
    outline_file = args.outline_file or default_paths["outline_file"]
    image_files = args.image_files or default_paths["image_files"]
    output_dir = args.output_dir or default_paths["output_dir"]
    save_intermediates = args.save_intermediates
    iterations = args.iterations if not args.skip_review else 1
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print("=" * 60)
        print("Research Report Generation and Iterative Improvement Process")
        print("=" * 60)
        print(f"Planned iterations: {iterations}")
        
        # Extract abstract from report outline
        abstract = _extract_abstract_from_outline(outline_file)
        
        best_pdf_path = None
        best_score = -1
        best_iteration = 0
        review_results = None
        
        # Iterate to generate and improve report
        for iteration in range(iterations):
            print(f"\n{'='*20} Iteration {iteration + 1}/{iterations} {'='*20}")
            
            # Generate report sections
            section_files = generate_report_sections(
                scenario_file=scenario_file,
                metrics_file=metrics_file,
                analysis_file=analysis_file,
                outline_file=outline_file,
                image_files=image_files,
                temp_dir=temp_dir,
                iteration=iteration,
                review_results=review_results,
                model_config=args.model_config
            )
            
            # Save intermediate files (if needed)
            if save_intermediates:
                save_intermediate_files(section_files, output_dir, iteration)
            
            # Compile complete report
            pdf_path, latex_content = compile_full_report(
                title=args.report_title,
                author=args.report_author,
                section_files=section_files,
                image_files=image_files,
                output_dir=output_dir,
                output_filename=args.output_filename,
                abstract=abstract,
                iteration=iteration
            )
            
            # Save path from last iteration (if not reviewing)
            if args.skip_review:
                best_pdf_path = pdf_path
                break
            
            # Review report
            review_results = review_report(
                latex_content=latex_content,
                section_files=section_files,
                scenario_file=scenario_file,
                metrics_file=metrics_file,
                analysis_file=analysis_file,
                output_dir=output_dir,
                iteration=iteration,
                model_config=args.model_config
            )
            
            # Update best report information
            current_score = review_results.get("overall_assessment", {}).get("scores", {}).get("overall", 0)
            if current_score > best_score:
                best_score = current_score
                best_pdf_path = pdf_path
                best_iteration = iteration
            
            # Determine whether to continue iterating
            if current_score >= 5:  # If score is very high, break early
                break
        
        # Create copy of final version
        if best_pdf_path:
            final_pdf_path = os.path.join(output_dir, f"{args.output_filename}_final.pdf")
            shutil.copy2(best_pdf_path, final_pdf_path)
            
            if not args.skip_review:
                print(f"\n✓ Best version is iteration {best_iteration+1}, score: {best_score}/10")
                print(f"✓ Final report saved to: {final_pdf_path}")
            else:
                print(f"\n✓ Report generated: {final_pdf_path}")
        
        print("\nProcessing complete!")
        print("=" * 60)


def _extract_abstract_from_outline(outline_file: str) -> str:
    """
    Attempt to extract abstract from report outline.
    
    Args:
        outline_file (str): Path to the report outline file.
        
    Returns:
        str: Extracted abstract, or default abstract if extraction fails.
    """
    try:
        with open(outline_file, 'r', encoding='utf-8') as f:
            outline_content = f.read()
        
        # Simple search for sections marked "Abstract"
        abstract_markers = ["# Abstract", "## Abstract"]
        
        for marker in abstract_markers:
            if marker in outline_content:
                start_idx = outline_content.find(marker) + len(marker)
                end_idx = outline_content.find('#', start_idx)
                
                if end_idx > start_idx:
                    return outline_content[start_idx:end_idx].strip()
        
        # If no explicitly marked abstract is found, use the beginning part
        lines = outline_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('# ') and i > 0:
                intro_text = '\n'.join(lines[:i]).strip()
                if len(intro_text) > 100:  # Ensure there's enough content
                    return intro_text
                break
        
        # Default abstract
        return "This report presents an analysis of a multi-agent social simulation, detailing research objectives, simulation setup, experimental results, and conclusions. The simulation focuses on studying agent interactions and emergent patterns in a controlled virtual environment."
    
    except Exception as e:
        print(f"Error extracting abstract: {e}")
        return "This report presents an analysis of a multi-agent social simulation, detailing research objectives, simulation setup, experimental results, and conclusions."


if __name__ == "__main__":
    main() 