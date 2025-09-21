import os
import re
import zipfile
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Optional, Any
from pydantic import BaseModel

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

ENVS_DIR = "src/envs"


class GeneratedFilesResponse(BaseModel):
    files: Dict[str, Any]


class RunsCountResponse(BaseModel):
    env_name: str
    runs_count: int
    runs: list[str]


def _build_structured_file_tree(path: str) -> Any:
    """
    Recursively builds a tree structure for a directory.
    - De-duplicates files based on the latest timestamp in the filename.
    - Returns a list of files for leaf directories.
    - Returns a dictionary for directories with subdirectories.
    """
    try:
        entries = os.listdir(path)
    except FileNotFoundError:
        return None

    subdirs = [d for d in entries if os.path.isdir(os.path.join(path, d))]
    files_in_dir = [f for f in entries if os.path.isfile(os.path.join(path, f))]

    # De-duplicate files in the current directory based on timestamps
    latest_files_map = {}
    filename_pattern = re.compile(r"^(.*?)_(\d{8}_\d{6})\.(.*)$")

    for f in files_in_dir:
        match = filename_pattern.match(f)
        if match:
            base_name, timestamp, extension = match.groups()
            group_key = (base_name, extension)

            if group_key not in latest_files_map or timestamp > latest_files_map[group_key][1]:
                latest_files_map[group_key] = (os.path.join(path, f), timestamp)
        else:
            # No timestamp, just add it. Key by filename to avoid collisions.
            latest_files_map[(f, None)] = (os.path.join(path, f), "")

    deduped_files = sorted([p for p, t in latest_files_map.values()])

    if not subdirs:
        # It's a leaf directory, return the list of files.
        return deduped_files if deduped_files else None
    else:
        # It's a directory with subdirectories, return a dict.
        result = {}
        for d in subdirs:
            subtree = _build_structured_file_tree(os.path.join(path, d))
            if subtree:  # Don't add empty entries
                result[d] = subtree

        if deduped_files:
            # Add files at the current level to the dictionary
            result["files"] = deduped_files
        return result if result else None


def get_generated_files_for_env(env_name: str) -> Dict[str, Any]:
    """
    Gets structured, de-duplicated generated files for a given environment.
    Separates dataset, metrics, and profile files.
    """
    env_path = os.path.join(ENVS_DIR, env_name)
    if not os.path.isdir(env_path):
        return {}

    result: Dict[str, Any] = {}

    # 1. Handle 'datasets'
    datasets_path = os.path.join(env_path, "datasets")
    if os.path.isdir(datasets_path):
        datasets_tree = _build_structured_file_tree(datasets_path)
        if datasets_tree:
            result["datasets"] = datasets_tree

    # 2. Handle 'metrics_plots' and extract 'profile' data from within its steps
    metrics_plots_path = os.path.join(env_path, "metrics_plots")
    profiles_data: Dict[str, Any] = {}
    metrics_data: Dict[str, Any] = {}

    if os.path.isdir(metrics_plots_path):
        # Iterate through step directories (e.g., 'step_1', 'step_2')
        for step_dir_name in os.listdir(metrics_plots_path):
            step_dir_path = os.path.join(metrics_plots_path, step_dir_name)
            if not os.path.isdir(step_dir_path):
                continue

            step_metrics_content = {}
            # Iterate contents of step dir (e.g., 'profiles', 'scene_metrics')
            for content_name in os.listdir(step_dir_path):
                content_path = os.path.join(step_dir_path, content_name)
                if not os.path.isdir(content_path):
                    continue

                if content_name == "profiles":
                    # Extract profile data and store it separately
                    profile_files = _build_structured_file_tree(content_path)
                    if profile_files:
                        profiles_data[step_dir_name] = profile_files
                else:
                    # Treat as regular metric data
                    metric_subtree = _build_structured_file_tree(content_path)
                    if metric_subtree:
                        step_metrics_content[content_name] = metric_subtree
            
            if step_metrics_content:
                metrics_data[step_dir_name] = step_metrics_content

    if metrics_data:
        result["metrics"] = metrics_data
    if profiles_data:
        result["profile"] = profiles_data

    return result


@router.get("/generated_files", response_model=GeneratedFilesResponse)
async def get_generated_files(env_name: Optional[str] = None):
    """
    Returns the relative paths of generated files for one or all scenarios.

    - De-duplicates files to return only the latest version based on timestamp in filename.
    - Provides a structured, hierarchical view under `datasets`, `metrics_plots`, and `profile` keys.
    - Profile data is extracted from `metrics_plots/step_*/profiles` directories.
    """
    if env_name:
        if not os.path.isdir(os.path.join(ENVS_DIR, env_name)):
            raise HTTPException(
                status_code=404, detail=f"Environment '{env_name}' not found."
            )

        files = get_generated_files_for_env(env_name)
        return GeneratedFilesResponse(files={env_name: files})
    else:
        all_files = {}
        if not os.path.isdir(ENVS_DIR):
            raise HTTPException(
                status_code=404, detail=f"Envs directory '{ENVS_DIR}' not found."
            )

        for scenario in os.listdir(ENVS_DIR):
            scenario_path = os.path.join(ENVS_DIR, scenario)
            if os.path.isdir(scenario_path):
                files = get_generated_files_for_env(scenario)
                if files:
                    all_files[scenario] = files
        return GeneratedFilesResponse(files=all_files)


@router.get("/runs", response_model=RunsCountResponse)
async def get_runs(env_name: str):
    """
    Returns the count and list of run folders for a given environment.
    """
    env_path = os.path.join(ENVS_DIR, env_name)
    if not os.path.isdir(env_path):
        raise HTTPException(
            status_code=404, detail=f"Environment '{env_name}' not found."
        )

    runs_path = os.path.join(env_path, "runs")
    if not os.path.isdir(runs_path):
        return RunsCountResponse(env_name=env_name, runs_count=0, runs=[])

    try:
        entries = os.listdir(runs_path)
        run_folders = [d for d in entries if os.path.isdir(os.path.join(runs_path, d))]
        run_folders.sort()  # Sort for consistent ordering

        return RunsCountResponse(
            env_name=env_name, runs_count=len(run_folders), runs=run_folders
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading runs directory: {str(e)}"
        )


@router.get("/runs/download")
async def get_runs_file(env_name: str, run_name: str):
    """
    Downloads a specific run folder as a zip file.
    """
    env_path = os.path.join(ENVS_DIR, env_name)
    if not os.path.isdir(env_path):
        raise HTTPException(
            status_code=404, detail=f"Environment '{env_name}' not found."
        )

    run_path = os.path.join(env_path, "runs", run_name)
    if not os.path.isdir(run_path):
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_name}' not found in environment '{env_name}'.",
        )

    try:
        # Create a temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()

        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(run_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate relative path from run_path
                    arcname = os.path.relpath(file_path, run_path)
                    zipf.write(file_path, arcname)

        # Return the zip file as a download
        return FileResponse(
            path=temp_zip.name,
            filename=f"{env_name}_{run_name}.zip",
            media_type='application/zip',
            background=None,  # File will be deleted after response
        )

    except Exception as e:
        # Clean up temp file if error occurs
        if os.path.exists(temp_zip.name):
            os.unlink(temp_zip.name)
        raise HTTPException(
            status_code=500, detail=f"Error creating zip file: {str(e)}"
        )
