from typing import Dict, Any
import asyncio
import uuid
import os
import time
import datetime
from loguru import logger


def normalize_for_hashing(profile_data: Dict[str, Any]) -> tuple:
    """Normalize profile data to be hashable (convert lists to tuples)."""
    normalized_data = {}
    for key, value in profile_data.items():
        if isinstance(value, list):
            normalized_data[key] = tuple(value)  # Convert list to tuple
        elif isinstance(value, dict):
            normalized_data[key] = tuple(sorted(value.items()))  # Convert dict to tuple of sorted items
        else:
            normalized_data[key] = value
    return tuple(sorted(normalized_data.items()))  # Sort it


def convert_sql_data(obj):
    if isinstance(obj, dict):
        return {k: convert_sql_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_sql_data(item) for item in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        return obj


def call_llm_sync(model,prompt):
    """
    Synchronous wrapper for calling the LLM model.
    
    Args:
        prompt: The input prompt for the model
        
    Returns:
        The model's response
        
    Raises:
        Exception: If model call fails
    """
    try:
        # Run async call in event loop
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(model(prompt))
        return response
    except Exception as e:
        # Re-raise exception with additional context
        raise Exception(f"Error calling LLM model: {str(e)}")


def gen_id():
    """Generate a random id that should
    avoid collisions"""
    return str(uuid.uuid4())


def create_directory(path: str):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def setup_logging(env_name: str):
    """Set up logging with a stable filename based on environment name.
    Logs will be rotated when they reach 500MB and compressed."""
    # Get the project root directory (3 levels up from this file)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
    
    env_path = os.path.join(project_root,"src", "envs", env_name)
    log_dir = os.path.join(env_path, "log", "run")
    create_directory(log_dir)
    log_file = os.path.join(log_dir, f"{env_name}.log")
    logger.add(log_file, rotation="500 MB", compression="zip", level="INFO")
    return log_file
