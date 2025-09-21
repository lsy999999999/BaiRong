from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import os
import json
import threading
import time
import random
from loguru import logger
import asyncio
import uuid
from pydantic import BaseModel, Field
import shutil

from backend.models.base import EnvRequest
from backend.models.pipeline import (
    PipelineRequest, AgentTypesResponse, UpdateAgentTypesRequest, 
    WorkflowResponse, CodeGenerationStatus, CodeUpdateRequest,
    ProfileSchemaRequest, ProfileSchemaResponse, 
    ProfileGenerationRequest, ProfileGenerationResponse
)
from backend.utils.file_ops import setup_environment, create_directory, init_package, save_scene_info
from backend.utils.model_management import load_model_if_needed
from onesim.agent import ProfileAgent, WorkflowAgent, CodeAgent, MetricAgent, ODDAgent

# Global state storage
PIPELINE_STATES = {}
CODE_GENERATION_THREAD = None
CODE_GENERATION_STATUS = {"phase": 0, "content": ""}
WORKFLOW_GENERATION_STATUSES = {}  # Track workflow generation status by env_name (0=Failed, 1=Success, 2=In Progress)

# Define request model for update_workflow
class UpdateWorkflowRequest(BaseModel):
    env_name: str
    actions: Dict[str, Any]
    events: Dict[str, Any]

# Define response model for tips
class TipsResponse(BaseModel):
    tips: List[str]

router = APIRouter(
    tags=["pipeline"],
    prefix="/pipeline"
)

@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_pipeline_endpoint(request: PipelineRequest):
    """
    API endpoint to initialize Pipeline
    
    Parameters:
        request: PipelineRequest object containing environment name and description
    
    Returns:
        Dictionary containing initialization results
    """
    try:
        # Validate request parameters
        if not request.env_name:
            raise HTTPException(status_code=400, detail="Environment name cannot be empty")
        
        # Call initialization function
        result = await initialize_pipeline(request)
        logger.info(f"Pipeline initialization successful: {request.env_name}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Pipeline initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Pipeline initialization failed: {str(e)}"
        )

async def initialize_pipeline(request: PipelineRequest):
    """Initialize Pipeline"""
    env_name = request.env_name
   
    # Create environment directory
    env_path = setup_environment(env_name)
    
    # Load model
    model = await load_model_if_needed(request.model_name, request.category)
    
    # Initialize specialized agents
    profile_agent = ProfileAgent(model_config_name=model.config_name)
    workflow_agent = WorkflowAgent(model_config_name=model.config_name)
    code_agent = CodeAgent(model_config_name=model.config_name)
    metric_agent = MetricAgent(model_config_name=model.config_name)
    
    # Initialize Pipeline state
    initialize_pipeline_state(env_name, env_path, model)
    
    # Update agents in Pipeline state
    PIPELINE_STATES[env_name]["profile_agent"] = profile_agent
    PIPELINE_STATES[env_name]["workflow_agent"] = workflow_agent
    PIPELINE_STATES[env_name]["code_agent"] = code_agent
    PIPELINE_STATES[env_name]["metric_agent"] = metric_agent
    
    # Load scene information (if available) and store in pipeline state
    scene_info_path = os.path.join(env_path, "scene_info.json")
    if os.path.exists(scene_info_path):
        try:
            with open(scene_info_path, 'r', encoding='utf-8') as f:
                scene_info = json.load(f)
                
            # Store scene_info in pipeline state
            PIPELINE_STATES[env_name]["scene_info"] = scene_info
                
            # Extract description from scene_info if needed
            PIPELINE_STATES[env_name]["description"] = ODDAgent.odd_to_markdown(scene_info)

            PIPELINE_STATES[env_name]["agent_types"]=scene_info.get('agent_types', {})
            PIPELINE_STATES[env_name]["metrics"]=scene_info.get('metrics', {})
            PIPELINE_STATES[env_name]["portrait"]=scene_info.get('portrait', {})

        except Exception as e:
            logger.error(f"Error loading scene_info.json: {e}")
    if os.path.exists(os.path.join(env_path,"actions.json")):
        with open(os.path.join(env_path,"actions.json"),"r",encoding="utf-8") as f:
            actions = json.load(f)
            PIPELINE_STATES[env_name]["actions"] = actions
    if os.path.exists(os.path.join(env_path,"events.json")):
        with open(os.path.join(env_path,"events.json"),"r",encoding="utf-8") as f:
            events = json.load(f)
            PIPELINE_STATES[env_name]["events"] = events
    if os.path.exists(os.path.join(env_path,"env_data.json")):
        with open(os.path.join(env_path,"env_data.json"),"r",encoding="utf-8") as f:
            env_data = json.load(f)
            PIPELINE_STATES[env_name]["env_data"] = env_data
    if os.path.exists(os.path.join(env_path,"system_data_model.json")):
        with open(os.path.join(env_path,"system_data_model.json"),"r",encoding="utf-8") as f:
            system_data_model = json.load(f)
            PIPELINE_STATES[env_name]["system_data_model"] = system_data_model
    
    return {
        "env_name": env_name,
        "env_path": env_path,
        "message": f"Pipeline initialization successful: {env_name}"
    }

def initialize_pipeline_state(env_name: str, env_path: str, model) -> None:
    """Initialize Pipeline state"""
    PIPELINE_STATES[env_name] = {
        "env_name": env_name,
        "env_path": env_path,
        "model": model,
        "profile_agent": None,  # Will be set in initialize_pipeline
        "workflow_agent": None,  # Will be set in initialize_pipeline
        "code_agent": None,      # Will be set in initialize_pipeline
        "metric_agent": None,    # Will be set in initialize_pipeline
        "description": "",
        "agent_types": {},
        "portrait": {},
        "actions": {},
        "events": {},
        "system_data_model": {},
        "env_data": {},
        "metrics": {},
        "scene_info": {},
        "index": 0,
        "code_generation": {
            "phase": 0,  # 0=Completed, 1=Generating code, 2=Check & fix code, -1=Error
            "content": "",  # Current phase-related content
            "generated_code": {},  # Generated code dictionary
            "event_code": "",  # Event code
            "issues": {},  # Issues found during check
            "fix_iteration": 0,  # Fix iteration count
            "progress": 0.0,  # Progress percentage
            "all_content": ""  # All content
        }
    }
    WORKFLOW_GENERATION_STATUSES[env_name] = -1

def generate_default_portrait(agent_types):
    """Generate default portrait data for agent_types"""
    portrait = {}
    total_agents = 100
    
    # Simply distribute evenly by type count
    agent_count = len(agent_types)
    if agent_count == 0:
        return {}
    
    base_count = total_agents // agent_count
    remainder = total_agents % agent_count
    
    for i, agent_type in enumerate(agent_types.keys()):
        # Assign remaining amount to the last type
        count = base_count + (1 if i < remainder else 0)
        portrait[agent_type] = count
    
    return portrait

@router.post("/generate_agent_types", response_model=AgentTypesResponse)
async def generate_agent_types_endpoint(data: EnvRequest):
    """Generate agent types"""
    env_name = data.env_name

    # Check if environment name exists
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")

    pipeline_state = PIPELINE_STATES[env_name]
    if not pipeline_state["profile_agent"] or not pipeline_state["description"]:
        # Try to load description if missing
        if not pipeline_state.get("description"):
            scene_info = pipeline_state.get("scene_info", {})
            if scene_info:
                pipeline_state["description"] = ODDAgent.odd_to_markdown(scene_info)
        if not pipeline_state["profile_agent"] or not pipeline_state.get("description"):
            raise HTTPException(status_code=400, detail="Pipeline not properly initialized or description information is missing")

    # Check if agent_types already exist, if so return directly
    if pipeline_state.get("agent_types") and pipeline_state.get("portrait"):
        return AgentTypesResponse(
            agent_types=pipeline_state["agent_types"], 
            env_name=env_name, 
            portrait=pipeline_state["portrait"]
        )

    # Check if agent types already exist in file
    env_path = pipeline_state["env_path"]
    scene_info_path = os.path.join(env_path, "scene_info.json")
    if os.path.exists(scene_info_path):
        try:
            with open(scene_info_path, 'r', encoding='utf-8') as f:
                scene_info = json.load(f)
                if "agent_types" in scene_info and "portrait" in scene_info:
                    # Update state in memory
                    pipeline_state["agent_types"] = scene_info["agent_types"]
                    pipeline_state["portrait"] = scene_info["portrait"]
                    pipeline_state["scene_info"] = scene_info
                    logger.info(f"Loaded agent types from file: {env_name}")
                    return AgentTypesResponse(
                        agent_types=scene_info["agent_types"], 
                        env_name=env_name, 
                        portrait=scene_info["portrait"]
                    )
        except Exception as e:
            logger.error(f"Error loading scene_info.json: {e}")

    # If not in memory or file, generate new agent types
    agent_types = pipeline_state["profile_agent"].generate_agent_types(pipeline_state["description"])
    # Generate portrait assignments
    portrait_assignments = pipeline_state["profile_agent"].assign_agent_portraits(agent_types)
    # Store agent types and portrait data
    pipeline_state["agent_types"] = agent_types
    pipeline_state["portrait"] = portrait_assignments

    # Save agent types to scene_info.json
    scene_info = {}

    if os.path.exists(scene_info_path):
        try:
            with open(scene_info_path, 'r', encoding='utf-8') as f:
                scene_info = json.load(f)
        except Exception as e:
            logger.error(f"Error loading scene_info.json: {e}")

    # Update scene_info with agent types and portrait
    scene_info["agent_types"] = agent_types
    scene_info["portrait"] = portrait_assignments
    PIPELINE_STATES[env_name]["scene_info"] = scene_info

    # Save updated scene_info
    with open(scene_info_path, 'w', encoding='utf-8') as f:
        json.dump(scene_info, f, ensure_ascii=False, indent=4)

    return AgentTypesResponse(
        agent_types=agent_types, 
        env_name=env_name, 
        portrait=portrait_assignments
    )

@router.post("/update_agent_types", response_model=AgentTypesResponse)
def update_agent_types_endpoint(data: UpdateAgentTypesRequest):
    """Update agent types with user modifications"""
    env_name = data.env_name
    if not env_name or env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found or pipeline not initialized")

    pipeline_state = PIPELINE_STATES[env_name]

    # Update agent types with user modifications
    pipeline_state["agent_types"] = data.agent_types

    # Update portrait assignments if provided, otherwise regenerate them
    portrait_assignments = data.portrait
    if not portrait_assignments and pipeline_state.get("profile_agent"):
        try:
            portrait_assignments = pipeline_state["profile_agent"].assign_agent_portraits(data.agent_types)
        except Exception as e:
            logger.warning(f"Failed to regenerate portrait assignments: {e}. Proceeding without portrait.")
            portrait_assignments = generate_default_portrait(list(data.agent_types.keys()))


    pipeline_state["portrait"] = portrait_assignments

    # Save agent types to scene_info.json
    env_path = pipeline_state["env_path"]
    scene_info_path = os.path.join(env_path, "scene_info.json")
    scene_info = {}

    if os.path.exists(scene_info_path):
        try:
            with open(scene_info_path, 'r', encoding='utf-8') as f:
                scene_info = json.load(f)
        except Exception as e:
            logger.error(f"Error loading scene_info.json: {e}")
            # Continue even if loading fails, try to overwrite

    # Update scene_info with modified agent types and portrait
    scene_info["agent_types"] = data.agent_types
    scene_info["portrait"] = portrait_assignments
    PIPELINE_STATES[env_name]["scene_info"] = scene_info
    PIPELINE_STATES[env_name]["agent_types"] = data.agent_types
    PIPELINE_STATES[env_name]["portrait"] = portrait_assignments
    # Save updated scene_info
    try:
        with open(scene_info_path, 'w', encoding='utf-8') as f:
            json.dump(scene_info, f, ensure_ascii=False, indent=4)
        logger.info(f"Agent types updated and saved for {env_name}")
        
        # --- Cache Clearing Logic ---
        logger.info(f"Clearing downstream cache (Workflow, Code, Profiles) for {env_name} due to agent type update.")
        
        # Reset in-memory state to initial values instead of deleting keys
        pipeline_state["actions"] = {}
        pipeline_state["events"] = {}
        pipeline_state["system_data_model"] = {}
        pipeline_state["env_data"] = {}
        pipeline_state["code_generation"] = {
            "phase": 0,
            "content": "",
            "generated_code": {},
            "event_code": "",
            "issues": {},
            "fix_iteration": 0,
            "progress": 0.0,
            "all_content": ""
        }
        pipeline_state["profiles"] = {}  # If profiles is a known key
        
        logger.debug(f"Reset downstream pipeline state for {env_name}")

        # Clear persisted files/directories
        actions_path = os.path.join(env_path, "actions.json")
        events_path = os.path.join(env_path, "events.json")
        code_dir = os.path.join(env_path, "code")
        profile_dir = os.path.join(env_path, "profile") # Clear generated schemas as well
        system_data_model_path = os.path.join(env_path, "system_data_model.json")
        env_data_path= os.path.join(env_path, "env_data.json")

        files_to_delete = [actions_path, events_path, system_data_model_path,env_data_path]
        dirs_to_delete = [code_dir, profile_dir]

        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Deleted cached file: {file_path}")
                except OSError as e:
                    logger.error(f"Error deleting cached file {file_path}: {e}")

        for dir_path in dirs_to_delete:
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    logger.debug(f"Deleted cached directory: {dir_path}")
                except OSError as e:
                    logger.error(f"Error deleting cached directory {dir_path}: {e}")
        # --- End Cache Clearing Logic ---

    except Exception as e:
        logger.error(f"Failed to save updated scene_info.json for {env_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save scene info: {str(e)}")

    return AgentTypesResponse(agent_types=data.agent_types, env_name=env_name, portrait=portrait_assignments)

def run_workflow_generation(env_name: str):
    """Background task to generate workflow."""
    pipeline_state = PIPELINE_STATES.get(env_name)
    if not pipeline_state:
        logger.error(f"Pipeline state for {env_name} not found in background task.")
        WORKFLOW_GENERATION_STATUSES[env_name] = 0  # Failed
        return

    env_path = pipeline_state["env_path"]
    actions_path = os.path.join(env_path, "actions.json")
    events_path = os.path.join(env_path, "events.json")
    system_data_model_path = os.path.join(env_path, "system_data_model.json")

    try:
        # Use agent type keys for workflow generation
        agent_type_keys = list(pipeline_state["agent_types"].keys())
        
        logger.info(f"Starting workflow generation for {env_name} in background.")
        actions, events, system_data_model, G = pipeline_state["workflow_agent"].generate_workflow(
            pipeline_state["description"], agent_type_keys
        )
        
        # Check if the generated workflow is valid (contains at least some actions and events)
        if not actions or not events:
            logger.error(f"Generated workflow invalid for {env_name}: actions={bool(actions)}, events={bool(events)}")
            WORKFLOW_GENERATION_STATUSES[env_name] = 0 # Failed
            # Store a failure message or details? For now, just status 0.
            return

        # Add empty "code" field to each action
        for agent_type, agent_actions in actions.items():
            for action in agent_actions:
                action["code"] = ""
        
        # Ensure events dictionary keys are strings and add empty code field
        string_key_events = {}
        for key, event in events.items():
            string_key_events[str(key)] = event
            string_key_events[str(key)]["code"] = ""
        
        events = string_key_events
        
        # Store workflow in pipeline state
        pipeline_state["actions"] = actions
        pipeline_state["events"] = events
        pipeline_state["system_data_model"] = system_data_model
        
        # Save actions, events, and workflow to the environment directory
        with open(actions_path, 'w', encoding='utf-8') as f:
            json.dump(actions, f, ensure_ascii=False, indent=4)
        with open(events_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
        with open(system_data_model_path, 'w', encoding='utf-8') as f:
            json.dump(system_data_model, f, ensure_ascii=False, indent=4)
        
        # Generate workflow visualization
        try:
            workflow_agent = pipeline_state["workflow_agent"]
            if hasattr(workflow_agent, "visualize_workflow") and callable(workflow_agent.visualize_workflow):
                workflow_agent.visualize_workflow(G, env_path)
            elif hasattr(workflow_agent, "visualize_interactive_graph") and callable(workflow_agent.visualize_interactive_graph):
                visualization_path = os.path.join(env_path, "workflow.html")
                workflow_agent.visualize_interactive_graph(G, visualization_path)
                logger.info(f"Created interactive workflow visualization: {visualization_path}")
        except Exception as e:
            logger.error(f"Error creating workflow visualization for {env_name}: {e}")
        
        WORKFLOW_GENERATION_STATUSES[env_name] = 1 # Success
        logger.info(f"Workflow generation successful for {env_name}.")

    except Exception as e:
        logger.error(f"Error during workflow generation for {env_name}: {str(e)}")
        WORKFLOW_GENERATION_STATUSES[env_name] = 0 # Failed
        # Optionally store error details in pipeline_state if needed
        # pipeline_state["workflow_error"] = str(e)

@router.post("/generate_workflow", response_model=WorkflowResponse)
async def generate_workflow_endpoint(data: EnvRequest):
    """
    Generates or retrieves the status of workflow generation (actions and events).
    Status: 0=Failed, 1=Success, 2=In Progress
    """
    env_name = data.env_name
    
    # Check if environment name exists
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")
    
    pipeline_state = PIPELINE_STATES[env_name]
    env_path = pipeline_state["env_path"]
    actions_path = os.path.join(env_path, "actions.json")
    events_path = os.path.join(env_path, "events.json")
    system_data_model_path = os.path.join(env_path, "system_data_model.json")

    # Get current generation status
    current_status = WORKFLOW_GENERATION_STATUSES.get(env_name, -1) # -1 means not started

    # --- Handle different statuses ---

    # 2: In Progress
    if current_status == 2:
        logger.info(f"Workflow generation already in progress for {env_name}.")
        return WorkflowResponse(
            actions={}, events={}, system_data_model={}, env_name=env_name,
            success=2, message="Workflow generation is in progress. Please wait."
        )

    # 1: Success
    if current_status == 1:
        # Check memory first
        if pipeline_state.get("actions") and pipeline_state.get("events") and pipeline_state.get("system_data_model"):
            logger.info(f"Workflow already exists in memory for {env_name}, returning.")
            return WorkflowResponse(
                actions=pipeline_state["actions"],
                events=pipeline_state["events"],
                system_data_model=pipeline_state["system_data_model"],
                env_name=env_name,
                success=1,
                message="Workflow generation previously completed."
            )
        # If not in memory, check files (should exist if status is 1, but double-check)
        elif os.path.exists(actions_path) and os.path.exists(events_path) and os.path.exists(system_data_model_path):
            try:
                with open(actions_path, 'r', encoding='utf-8') as f: actions = json.load(f)
                with open(events_path, 'r', encoding='utf-8') as f: events = json.load(f)
                with open(system_data_model_path, 'r', encoding='utf-8') as f: system_data_model = json.load(f)
                
                # Update memory state
                pipeline_state["actions"] = actions
                pipeline_state["events"] = events
                pipeline_state["system_data_model"] = system_data_model
                
                logger.info(f"Loaded workflow from file for {env_name}.")
                return WorkflowResponse(
                    actions=actions, events=events, system_data_model=system_data_model,
                    env_name=env_name, success=1, message="Workflow loaded from file."
                )
            except Exception as e:
                logger.error(f"Error loading workflow files for {env_name} despite status 1: {str(e)}")
                # Fall through to re-generate if loading fails? Or return error?
                # Let's reset status and attempt generation again.
                WORKFLOW_GENERATION_STATUSES[env_name] = -1 # Reset status
                # Fall through to the generation logic below
        else:
             # Data missing despite status 1 - reset and regenerate
             logger.warning(f"Workflow data missing for {env_name} despite success status (1). Resetting.")
             WORKFLOW_GENERATION_STATUSES[env_name] = -1 # Reset status
             # Fall through

    # 0: Failed
    if current_status == 0:
        logger.info(f"Previous workflow generation failed for {env_name}.")
        # Optionally include more failure details from pipeline_state if stored
        return WorkflowResponse(
            actions={}, events={}, system_data_model={}, env_name=env_name,
            success=0, message="Previous workflow generation attempt failed. Please review logs or description."
        )

    # --- Start Generation (Status -1 or reset from 1/0) ---

    # Check prerequisites
    if not pipeline_state.get("workflow_agent") or not pipeline_state.get("agent_types"):
        # Allow retrying generation even if previous attempt failed
        if current_status == 0:
             logger.warning(f"Attempting to regenerate workflow for {env_name} after previous failure, but prerequisites missing.")
        raise HTTPException(status_code=400, detail="Workflow agent or agent types missing. Ensure previous steps completed.")

    # Check if files already exist (e.g., from a previous run before restart)
    # This check is moved here - if files exist but status wasn't 1, load them and set status to 1.
    if os.path.exists(actions_path) and os.path.exists(events_path) and os.path.exists(system_data_model_path):
        try:
            with open(actions_path, 'r', encoding='utf-8') as f: 
                actions = json.load(f)
            with open(events_path, 'r', encoding='utf-8') as f: 
                events = json.load(f)
            with open(system_data_model_path, 'r', encoding='utf-8') as f: 
                system_data_model = json.load(f)

            # Validate loaded data looks reasonable
            if actions and events: # Basic check
                 # Update memory state
                 pipeline_state["actions"] = actions
                 pipeline_state["events"] = events
                 pipeline_state["system_data_model"] = system_data_model
                 WORKFLOW_GENERATION_STATUSES[env_name] = 1 # Set status to success

                 logger.info(f"Found existing workflow files for {env_name}, loading and setting status to success.")
                 return WorkflowResponse(
                     actions=actions, events=events, system_data_model=system_data_model,
                     env_name=env_name, success=1, message="Workflow loaded from existing files."
                 )
            else:
                 logger.warning(f"Existing workflow files for {env_name} seem invalid. Proceeding with generation.")
                 # Potentially delete invalid files?
                 # os.remove(actions_path) ... etc.

        except Exception as e:
            logger.error(f"Error loading existing workflow files for {env_name}: {str(e)}. Proceeding with generation.")
            # Fall through to generate

    # Start generation in a background thread
    logger.info(f"Initiating background workflow generation for {env_name}.")
    WORKFLOW_GENERATION_STATUSES[env_name] = 2 # Set status to In Progress
    
    thread = threading.Thread(target=run_workflow_generation, args=(env_name,))
    thread.daemon = True # Allows main program to exit even if thread is running
    thread.start()
    
    return WorkflowResponse(
        actions={}, events={}, system_data_model={}, env_name=env_name,
        success=2, message="Workflow generation started in background."
    )

@router.post("/update_workflow", response_model=Dict[str, str])
async def update_workflow_endpoint(data: UpdateWorkflowRequest):
    """Update workflow (actions and events)"""
    env_name = data.env_name

    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")

    pipeline_state = PIPELINE_STATES[env_name]
    env_path = pipeline_state["env_path"]

    # 更新内存状态
    pipeline_state["actions"] = data.actions
    pipeline_state["events"] = data.events

    # 定义文件路径
    actions_path = os.path.join(env_path, "actions.json")
    events_path = os.path.join(env_path, "events.json")

    try:
        # 保存更新后的动作到文件
        with open(actions_path, 'w', encoding='utf-8') as f:
            json.dump(data.actions, f, ensure_ascii=False, indent=4)
        
        # 保存更新后的事件到文件
        with open(events_path, 'w', encoding='utf-8') as f:
            json.dump(data.events, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Workflow successfully updated: {env_name}")
        
        # --- Cache Clearing Logic ---
        logger.info(f"Clearing downstream cache (Code, Profiles) for {env_name} due to workflow update.")

        # Reset in-memory state to initial values instead of deleting keys
        pipeline_state["code_generation"] = {
            "phase": 0,
            "content": "",
            "generated_code": {},
            "event_code": "",
            "issues": {},
            "fix_iteration": 0,
            "progress": 0.0,
            "all_content": ""
        }
        pipeline_state["profiles"] = {}  # If profiles is a known key
        pipeline_state["system_data_model"] = {}
        pipeline_state["env_data"] = {}
        
        logger.debug(f"Reset downstream pipeline state for {env_name}")

        # Clear persisted files/directories
        code_dir = os.path.join(env_path, "code")
        system_data_model_path = os.path.join(env_path, "system_data_model.json")
        env_data_path= os.path.join(env_path, "env_data.json")

        files_to_delete = [system_data_model_path,env_data_path]
        dirs_to_delete = [code_dir]

        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Deleted cached file: {file_path}")
                except OSError as e:
                    logger.error(f"Error deleting cached file {file_path}: {e}")
        
        for dir_path in dirs_to_delete:
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    logger.debug(f"Deleted cached directory: {dir_path}")
                except OSError as e:
                    logger.error(f"Error deleting cached directory {dir_path}: {e}")
        # --- End Cache Clearing Logic ---

        return {"message": f"Workflow successfully updated: {env_name}"}
        
    except Exception as e:
        logger.error(f"Error updating workflow: {str(e)}")
        # Optionally revert in-memory changes or handle partial saves
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")

@router.post("/generate_code", response_model=Dict[str, str])
def generate_code_endpoint(data: EnvRequest):
    """Start code generation process"""
    env_name = data.env_name

    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")

    pipeline_state = PIPELINE_STATES[env_name]
    if not pipeline_state["code_agent"] or not pipeline_state["actions"] or not pipeline_state["events"]:
        raise HTTPException(status_code=400, detail="Must generate workflow first")

    # 获取代码生成状态
    code_gen_state = pipeline_state.get("code_generation", {})

    # 检查是否已经在运行代码生成
    current_phase = code_gen_state.get("phase", 0)
    if current_phase > 0 and current_phase < 4:
        return {
            "message": f"Code generation is in progress (phase {current_phase})",
            "env_name": env_name
        }

    # 检查代码是否已生成完成
    env_path = pipeline_state["env_path"]
    code_structure_path = os.path.join(env_path, "code", "code_structure.json")
    if os.path.exists(code_structure_path) and current_phase == 0:
        # 检查代码结构文件是否存在且不在生成过程中
        try:
            with open(code_structure_path, 'r', encoding='utf-8') as f:
                code_structure = json.load(f)

            # 检查是否包含必要的结构
            if ("agents" in code_structure and "events" in code_structure and 
                code_structure["agents"] and code_structure["events"]):
                pipeline_state["code_generation"]={
                    "phase": 0,
                    "content": "Code Generation Complete!\n",
                    "generated_code": code_structure['agents'],
                    "event_code": code_structure["events"],
                    "issues": {},
                    "fix_iteration": 0,
                    "progress": 1,
                    "all_content": ""
                }
                return {
                    "message": "Code generation complete. Use /pipeline/get_code to get the generated code",
                    "env_name": env_name
                }
        except Exception as e:
            logger.error(f"Error checking existing code structure: {str(e)}")

    # 重置代码生成状态
    pipeline_state["code_generation"] = {
        "phase": 1,
        "content": "Starting code generation...\n",
        "generated_code": {},
        "event_code": "",
        "issues": {},
        "fix_iteration": 0,
        "progress": 0.0,
        "all_content": ""
    }

    # 在后台线程中启动代码生成过程
    def run_code_generation():
        try:
            # 获取必要的参数
            env_path = pipeline_state["env_path"]
            code_path = os.path.join(env_path, "code")
            create_directory(code_path)
            init_package(code_path)

            # 确保有描述、动作和事件
            if pipeline_state.get("description") is None:
                with open(
                    os.path.join(env_path, "scene_info.json"), "r", encoding='utf-8'
                ) as f:
                    scene_info = json.load(f)
                description = ODDAgent.odd_to_markdown(scene_info.get("odd_protocol", {}))
                with open(
                    os.path.join(env_path, "actions.json"), "r", encoding='utf-8'
                ) as f:
                    actions = json.load(f)
                with open(
                    os.path.join(env_path, "events.json"), "r", encoding='utf-8'
                ) as f:
                    events = json.load(f)
            else:
                description = pipeline_state.get("description")
                actions = pipeline_state.get("actions")
                events = pipeline_state.get("events")

            # 启动分阶段代码生成过程
            pipeline_state["code_agent"].generate_code_phased(
                description, actions, events, 
                code_path, pipeline_state["code_generation"]
            )
        except Exception as e:
            # 更新状态以反映错误
            pipeline_state["code_generation"]["phase"] = -1
            pipeline_state["code_generation"]["content"] = f"\nCode generation error: {str(e)}. Please return to the previous step and regenerate."
            logger.error(f"Code generation error: {str(e)}")

    # 启动代码生成后台线程
    code_thread = threading.Thread(target=run_code_generation)
    code_thread.daemon = True
    code_thread.start()

    # 检查指标是否已生成
    metrics_file_path = os.path.join(env_path, "code", "metrics")
    metrics_exist = os.path.exists(metrics_file_path) and os.path.isdir(metrics_file_path) and len(os.listdir(metrics_file_path)) > 0

    # 如果指标尚未生成，则启动指标生成
    if not metrics_exist:
        # 启动指标生成后台线程
        def run_metric_generation():
            try:
                # 获取必要的参数
                env_path = pipeline_state["env_path"]
                metric_agent = pipeline_state["metric_agent"]
                agent_types = list(pipeline_state["actions"].keys())  # 从actions中获取agent类型
                system_data_model = pipeline_state["system_data_model"]

                # 生成指标列表
                metrics = metric_agent.generate_metrics(
                    pipeline_state["description"], 
                    agent_types, 
                    system_data_model
                )

                if not metrics:
                    logger.warning("Failed to generate any metrics")
                    return

                logger.info(f"Successfully generated {len(metrics)} monitoring metrics")

                # 生成指标计算代码
                code_path = os.path.join(env_path, "code", "metrics")
                create_directory(code_path)
                metric_agent.generate_metrics_module(metrics, code_path, system_data_model)

                # 更新scene_info.json中的配置
                scene_info_path = os.path.join(env_path, "scene_info.json")
                if os.path.exists(scene_info_path):
                    with open(scene_info_path, 'r', encoding='utf-8') as f:
                        scene_info = json.load(f)

                    # 格式化指标数据用于存储
                    formatted_metrics = metric_agent.format_metrics_for_export(metrics)

                    # 更新scene_info.json
                    scene_info["metrics"] = formatted_metrics

                    # 保存更新后的scene_info.json
                    with open(scene_info_path, 'w', encoding='utf-8') as f:
                        json.dump(scene_info, f, ensure_ascii=False, indent=2)

                    logger.info(f"Metrics configuration saved to scene_info.json")

            except Exception as e:
                logger.error(f"Metrics generation error: {str(e)}")

        # 启动指标生成后台线程
        metric_thread = threading.Thread(target=run_metric_generation)
        metric_thread.daemon = True
        metric_thread.start()
    else:
        logger.info(f"Metrics already exist, skipping generation: {env_name}")

    return {
        "message": "Code and metrics generation started. Use /pipeline/code_generation_status to check status",
        "env_name": env_name
    }

@router.get("/code_generation_status", response_model=CodeGenerationStatus)
def get_code_generation_status(env_name: str):
    """Get current status of code generation"""
    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")
    
    pipeline_state = PIPELINE_STATES[env_name]
    
    # 确保code_generation存在
    if "code_generation" not in pipeline_state:
        pipeline_state["code_generation"] = {
            "phase": 0,
            "content": "Code generation status not initialized",
            "all_content": ""
        }
    
    # 获取当前状态
    code_gen_state = pipeline_state["code_generation"]
    
    # 保存当前内容用于返回
    current_content = code_gen_state.get("content", "")
    
    # 更新all_content，添加当前content
    code_gen_state["all_content"] += current_content
    
    # 清空content以实现消息队列效果
    code_gen_state["content"] = ""
    
    return CodeGenerationStatus(
        phase=code_gen_state.get("phase", 0),
        content=current_content,  # Return content before clearing
        all_content=code_gen_state["all_content"]
    )

@router.get("/get_code", response_model=Dict[str, Any])
async def get_code_endpoint(env_name: str):
    """Get generated action and event code, including mapping between actions/events and their code"""
    
    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")
    
    pipeline_state = PIPELINE_STATES[env_name]
    env_path = pipeline_state["env_path"]
    
    # 检查代码结构是否存在
    code_structure_path = os.path.join(env_path, "code", "code_structure.json")
    if not os.path.exists(code_structure_path):
        raise HTTPException(status_code=404, detail="Code not yet generated")
    
    # 加载代码结构
    try:
        with open(code_structure_path, 'r', encoding='utf-8') as f:
            code_structure = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load code structure: {str(e)}")
    
    # 从状态中获取actions和events
    actions = pipeline_state.get("actions", {})
    events = pipeline_state.get("events", {})
    
    # 为actions添加代码
    for agent_type, agent_data in code_structure.get("agents", {}).items():
        for action_id, handler_data in agent_data.get("handlers", {}).items():
            if agent_type in actions:
                for action in actions[agent_type]:
                    if str(action.get("id")) == action_id:
                        action["code"] = handler_data.get("code", "")
    
    # 为events添加代码
    for event_id, event_data in code_structure.get("events", {}).get("definitions", {}).items():
        if event_id in events:
            events[event_id]["code"] = event_data.get("code", "")
    
    return {"actions": actions, "events": events}

@router.post("/update_code", response_model=Dict[str, str])
def update_code_endpoint(data: CodeUpdateRequest):
    """Update code"""
    env_name = data.env_name
    
    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")
    
    # 获取Pipeline状态
    pipeline_state = PIPELINE_STATES[env_name]
    
    env_path = pipeline_state["env_path"]
    code_path = os.path.join(env_path, "code")
    
    # 加载现有的代码结构
    code_structure_path = os.path.join(code_path, "code_structure.json")
    if not os.path.exists(code_structure_path):
        raise HTTPException(status_code=404, detail="Code not yet generated")
    
    try:
        with open(code_structure_path, 'r', encoding='utf-8') as f:
            code_structure = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load code structure: {str(e)}")
    
    # 跟踪哪些代理和事件被修改
    modified_agents = set()
    modified_events = False
    
    # 更新动作代码
    for agent_type, agent_actions in data.actions.items():
        if agent_type in code_structure["agents"]:
            # 遍历这个代理类型的所有动作
            for action in agent_actions:
                action_id = str(action.get("id"))
                action_code = action.get("code", "")
                if action_id in code_structure["agents"][agent_type]["handlers"]:
                    # 检查代码是否实际更改
                    old_code = code_structure["agents"][agent_type]["handlers"][action_id]["code"]
                    if old_code != action_code:
                        code_structure["agents"][agent_type]["handlers"][action_id]["code"] = action_code
                        modified_agents.add(agent_type)
    
    # 更新事件代码
    for event_id, event_data in data.events.items():
        if event_id in code_structure["events"]["definitions"]:
            # 检查代码是否实际更改
            event_code = event_data.get("code", "")
            old_code = code_structure["events"]["definitions"][event_id]["code"]
            if old_code != event_code:
                code_structure["events"]["definitions"][event_id]["code"] = event_code
                modified_events = True
    
    # 只有在有更改时才保存更新的代码结构
    if modified_agents or modified_events:
        try:
            with open(code_structure_path, 'w', encoding='utf-8') as f:
                json.dump(code_structure, f, indent=2)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save code structure: {str(e)}")
    
    agents_updated = []
    
    # 只更新修改过的代理文件
    for agent_type in modified_agents:
        agent_data = code_structure["agents"][agent_type]
        agent_code = f"{agent_data['imports']}\n\n"
        agent_code += f"class {agent_type}(GeneralAgent):\n"
        agent_code += "    def __init__(self,\n"
        agent_code += "                 sys_prompt: str | None = None,\n"
        agent_code += "                 model_config_name: str = None,\n"
        agent_code += "                 event_bus_queue: asyncio.Queue = None,\n"
        agent_code += "                 profile: AgentProfile=None,\n"
        agent_code += "                 memory: MemoryStrategy=None,\n"
        agent_code += "                 planning: PlanningBase=None,\n"
        agent_code += "                 relationship_manager: RelationshipManager=None) -> None:\n"
        agent_code += "        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)\n"
        
        # 添加事件注册
        # 从初始化中提取事件注册逻辑
        for handler_id, handler_data in agent_data.get("handlers", {}).items():
            handler_metadata = handler_data.get("metadata", {})
            handler_name = handler_metadata.get("name", "")
            
            # 查找针对此动作的事件
            for event_id, event_data in code_structure["events"]["definitions"].items():
                event_metadata = event_data.get("metadata", {})
                if (event_metadata.get("to_agent_type") == agent_type and 
                    event_metadata.get("to_action_name") == handler_name):
                    event_name = event_metadata.get("event_name")
                    agent_code += f"        self.register_event(\"{event_name}\", \"{handler_name}\")\n"
        
        # 添加处理程序代码，确保适当的缩进
        for handler_id, handler_data in agent_data["handlers"].items():
            handler_code = handler_data["code"]
            # 确保只有第一行（async def行）有适当的缩进（4个空格）
            if handler_code.startswith("async def "):
                # 将处理程序代码分成行
                lines = handler_code.split("\n")
                # 只给第一行添加缩进
                lines[0] = "    " + lines[0]
                # 将行重新连接在一起
                handler_code = "\n".join(lines)
            agent_code += "\n" + handler_code + "\n"
        
        # 保存代理文件
        agent_file_path = os.path.join(code_path, f"{agent_type}.py")
        with open(agent_file_path, 'w', encoding='utf-8') as f:
            f.write(agent_code)
        agents_updated.append(agent_type)
    
    # 只有在事件被修改时才更新事件文件
    if modified_events:
        event_code = code_structure["events"]["imports"] + "\n\n"
        for event_id, event_data in code_structure["events"]["definitions"].items():
            event_code += event_data["code"] + "\n\n"
        
        event_file_path = os.path.join(code_path, "events.py")
        with open(event_file_path, 'w', encoding='utf-8') as f:
            f.write(event_code)
    
    # 同时更新状态中的actions和events以反映代码更改
    actions = pipeline_state.get("actions", {})
    events = pipeline_state.get("events", {})
    
    # 更新状态中的动作代码
    for agent_type, agent_actions in data.actions.items():
        if agent_type in actions:
            for action in agent_actions:
                action_id = str(action.get("id"))
                action_code = action.get("code", "")
                for state_action in actions[agent_type]:
                    if str(state_action.get("id")) == action_id:
                        state_action["code"] = action_code
    
    # 更新状态中的事件代码
    for event_id, event_data in data.events.items():
        if event_id in events:
            events[event_id]["code"] = event_data.get("code", "")
    
    return {
        "message": "Code updated successfully",
        "updated_agents": ", ".join(agents_updated),
        "events_updated": "Yes" if modified_events else "No"
    }

@router.get("/profile_schemas", response_model=Dict[str, Dict[str, Any]])
def get_profile_schemas(env_name: str):
    """Get agent profile schemas"""
    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")

    # 获取环境路径
    env_path = PIPELINE_STATES[env_name]["env_path"]

    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"Environment '{env_name}' does not exist")

    # 画像模式目录
    schema_dir = os.path.join(env_path, "profile", "schema")
    create_directory(schema_dir)

    # 加载场景信息以获取代理类型
    if "scene_info" not in PIPELINE_STATES[env_name]:
        scene_info_path = os.path.join(env_path, "scene_info.json")
        if not os.path.exists(scene_info_path):
            raise HTTPException(status_code=404, detail=f"Scene information file for environment '{env_name}' does not exist")

        try:
            with open(scene_info_path, 'r', encoding='utf-8') as f:
                scene_info = json.load(f)
        except Exception as e:
            logger.error(f"Error loading scene_info.json: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load scene information file: {str(e)}")
    else:
        scene_info = PIPELINE_STATES[env_name]["scene_info"]

    agent_types = PIPELINE_STATES[env_name].get("agent_types", {})

    # 如果没有定义代理类型，返回空字典
    if not agent_types:
        return {}

    # 为每个代理类型加载模式
    schemas = {}
    profile_counts = {}

    system_data_model = PIPELINE_STATES[env_name].get("system_data_model", {})
    if not system_data_model and os.path.exists(os.path.join(env_path, "system_data_model.json")):
        with open(os.path.join(env_path, "system_data_model.json"), 'r', encoding='utf-8') as f:
            system_data_model = json.load(f)
    agent_data_model = system_data_model.get("agents", {})

    for agent_type in agent_types:
        schema_path = os.path.join(schema_dir, f"{agent_type}.json")
        if os.path.exists(schema_path):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schemas[agent_type] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading schema for {agent_type}: {e}")
                schemas[agent_type] = {}

            profile_path = os.path.join(env_path, "profile", "data", f"{agent_type}.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profiles = json.load(f)
                    profile_counts[agent_type] = len(profiles)
                except Exception as e:
                    logger.error(f"Error loading profiles for {agent_type}: {e}")
                    profile_counts[agent_type] = 0
            else:
                profile_counts[agent_type] = 0
        else:
            if agent_type in agent_data_model:
                profile_agent = PIPELINE_STATES[env_name]["profile_agent"]
                schema = profile_agent.generate_profile_schema(PIPELINE_STATES[env_name]["description"], agent_type, agent_data_model[agent_type])
                with open(schema_path, "w", encoding='utf-8') as f:
                    json.dump(schema, f, ensure_ascii=False, indent=4)
                schemas[agent_type] = schema
                profile_counts[agent_type] = 0
            else:
                logger.warning(f"Agent type {agent_type} not found in agent_data_model")
                profile_agent = PIPELINE_STATES[env_name]["profile_agent"]
                schema = profile_agent.generate_profile_schema(PIPELINE_STATES[env_name]["description"], agent_type, {})
                with open(schema_path, "w", encoding='utf-8') as f:
                    json.dump(schema, f, ensure_ascii=False, indent=4)
                schemas[agent_type] = schema
                profile_counts[agent_type] = 0

    return {"schemas": schemas, "profile_counts": profile_counts}

@router.post("/profile_schema", response_model=ProfileSchemaResponse)
def save_profile_schema(data: ProfileSchemaRequest):
    """Save agent profile schema"""
    env_name = data.env_name
    
    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")
    
    # 获取环境路径
    env_path = PIPELINE_STATES[env_name]["env_path"]
    
    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"Environment '{env_name}' does not exist")
    
    # 画像模式目录
    schema_dir = os.path.join(env_path, "profile", "schema")
    create_directory(schema_dir)
    
    # 配置文件目录
    profile_data_dir = os.path.join(env_path, "profile", "data")
    create_directory(profile_data_dir)
    
    # 加载现有scene_info
    scene_info_path = os.path.join(env_path, "scene_info.json")
    try:
        with open(scene_info_path, 'r', encoding='utf-8') as f:
            scene_info = json.load(f)
    except Exception as e:
        logger.error(f"Error loading scene_info.json: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load scene information file: {str(e)}")
    
    if "agent_types" not in scene_info:
        scene_info["agent_types"] = {}
    
    # 跟踪成功保存的模式和配置数量
    saved_schemas = {}
    profile_counts = {}
    errors = []
    schemas_changed = []
    
    # 为每个代理类型保存模式
    for agent_type, profile_schema in data.agent_schemas.items():
        try:
            schema_path = os.path.join(schema_dir, f"{agent_type}.json")
            schema_changed = False
            
            # 检查现有的模式是否存在，如果存在，比较是否发生变化
            if os.path.exists(schema_path):
                try:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        existing_schema = json.load(f)
                    
                    # 比较现有模式和新模式是否不同
                    existing_schema_str = json.dumps(existing_schema, sort_keys=True)
                    new_schema_str = json.dumps(profile_schema, sort_keys=True)
                    schema_changed = existing_schema_str != new_schema_str
                    
                    if schema_changed:
                        logger.info(f"Agent {agent_type} schema has been modified, will clear existing profiles")
                        schemas_changed.append(agent_type)
                except Exception as e:
                    logger.error(f"Error comparing schema for {agent_type}: {e}")
                    # 如果无法比较，假设模式已更改
                    schema_changed = True
                    schemas_changed.append(agent_type)
            
            # 保存模式
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(profile_schema, f, ensure_ascii=False, indent=2)
            
            # 使用代理类型更新scene_info
            if agent_type not in scene_info["agent_types"]:
                scene_info["agent_types"][agent_type] = f"{agent_type}"
            
            saved_schemas[agent_type] = profile_schema
            
            # 如果模式已更改，清除现有的profile数据
            if schema_changed:
                profile_path = os.path.join(profile_data_dir, f"{agent_type}.json")
                if os.path.exists(profile_path):
                    try:
                        # 删除配置文件
                        os.remove(profile_path)
                        logger.info(f"Deleted old configuration file for {agent_type}")
                        profile_counts[agent_type] = 0
                    except Exception as e:
                        logger.error(f"Error deleting configuration file for {agent_type}: {e}")
                        errors.append(f"Failed to delete configuration file for {agent_type}: {str(e)}")
            else:
                # 如果模式未更改，计算现有配置数量
                profile_path = os.path.join(profile_data_dir, f"{agent_type}.json")
                if os.path.exists(profile_path):
                    try:
                        with open(profile_path, 'r', encoding='utf-8') as f:
                            profiles = json.load(f)
                        profile_counts[agent_type] = len(profiles)
                    except Exception as e:
                        logger.error(f"Error loading configuration file for {agent_type}: {e}")
                        profile_counts[agent_type] = 0
                else:
                    profile_counts[agent_type] = 0
            
        except Exception as e:
            errors.append(f"Failed to save configuration for {agent_type}: {str(e)}")
    
    # 如果添加了任何代理类型，保存更新后的scene_info
    if any(agent_type not in scene_info["agent_types"] for agent_type in data.agent_schemas.keys()):
        try:
            with open(scene_info_path, 'w', encoding='utf-8') as f:
                json.dump(scene_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            errors.append(f"Failed to update scene information: {str(e)}")
    
    # 如果有模式发生变化，关系数据也可能需要重新生成
    if schemas_changed:
        # 尝试删除关系文件
        relationship_path = os.path.join(profile_data_dir, "Relationship.csv")
        if os.path.exists(relationship_path):
            try:
                os.remove(relationship_path)
                logger.info("Deleted relationship data file, will regenerate")
            except Exception as e:
                logger.error(f"Error deleting relationship data file: {e}")
    
    if errors:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to save some configurations: {'; '.join(errors)}"
        )
    
    # 添加有关哪些模式已更改的消息
    message = f"Successfully saved {len(saved_schemas)} agent type configurations"
    if schemas_changed:
        message += f" and {len(schemas_changed)} configurations were modified and cleared existing profiles: {', '.join(schemas_changed)}"
    
    return ProfileSchemaResponse(
        env_name=env_name,
        agent_schemas=saved_schemas,
        profile_counts=profile_counts,
        message=message
    )

@router.post("/generate_profiles", response_model=ProfileGenerationResponse)
async def generate_profiles(data: ProfileGenerationRequest):
    """Generate agent profile data"""
    env_name = data.env_name

    # 检查环境名称是否存在
    if env_name not in PIPELINE_STATES:
        raise HTTPException(status_code=404, detail="Environment not found, please call /initialize endpoint first")

    # 获取环境路径
    env_path = PIPELINE_STATES[env_name]["env_path"]

    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail=f"Environment '{env_name}' does not exist")

    # 检查画像是否已生成
    profile_data_dir = os.path.join(env_path, "profile", "data")
    relationship_csv_path = os.path.join(profile_data_dir, "Relationship.csv")
    env_data_path = os.path.join(env_path, "env_data.json")

    # 创建必要的目录
    create_directory(profile_data_dir)

    # 检查每个代理类型是否需要生成新的画像
    profiles_to_generate = {}
    existing_max_id = 0

    # 扫描已有的画像文件，统计每个类型已有的画像数量和最大ID
    existing_profiles = {}
    for agent_type in data.agent_types.keys():
        profile_file = os.path.join(profile_data_dir, f"{agent_type}.json")
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    existing_profiles[agent_type] = profiles

                    # 获取最大ID
                    for profile in profiles:
                        if 'id' in profile:
                            profile_id = profile['id']
                            if isinstance(profile_id, str) and profile_id.isdigit():
                                existing_max_id = max(existing_max_id, int(profile_id))
                            elif isinstance(profile_id, int):
                                existing_max_id = max(existing_max_id, profile_id)

                    # 检查是否需要生成更多画像
                    if len(profiles) < data.agent_types[agent_type]:
                        profiles_to_generate[agent_type] = data.agent_types[agent_type] - len(profiles)
                        logger.info(f"Agent type {agent_type} has {len(profiles)} profiles, need to generate {profiles_to_generate[agent_type]} more")
                    else:
                        logger.info(f"Agent type {agent_type} has {len(profiles)} profiles, meet the requirement, no need to generate")
            except Exception as e:
                logger.error(f"Error reading {agent_type} profile file: {e}")
                # 如果读取失败，生成完整数量的画像
                profiles_to_generate[agent_type] = data.agent_types[agent_type]
        else:
            # 文件不存在，需要生成完整数量的画像
            profiles_to_generate[agent_type] = data.agent_types[agent_type]
            logger.info(f"Agent type {agent_type} does not exist profile file, need to generate {profiles_to_generate[agent_type]} profiles")

    # 如果不需要生成任何新画像并且其他文件都存在，直接返回
    if not profiles_to_generate and os.path.exists(relationship_csv_path) and os.path.exists(env_data_path):
        # 收集已生成的代理ID
        all_agent_ids = {}
        for agent_type, profiles in existing_profiles.items():
            agent_ids = [profile.get('agent_profile_id', profile.get('id')) for profile in profiles]
            all_agent_ids[agent_type] = [id for id in agent_ids if id]  # 过滤掉None值

        # 更新pipeline状态
        PIPELINE_STATES[env_name]["profiles_generated"] = True
        PIPELINE_STATES[env_name]["agent_types"] = list(data.agent_types.keys())
        PIPELINE_STATES[env_name]["all_agent_ids"] = all_agent_ids

        logger.info(f"All profile quantities are sufficient, no generation needed: {env_name}")
        return ProfileGenerationResponse(
            env_name=env_name,
            message="All profile quantities are sufficient, no generation needed",
            profile_path=profile_data_dir,
            relationship_path=relationship_csv_path,
            env_data_path=env_data_path
        )

    # 如果需要生成新画像，加载模型
    model = await load_model_if_needed(data.model_name, data.category)

    # 从PIPELINE_STATES获取场景信息和描述（如果可用），否则从文件加载
    description = ""
    scene_info = {}

    # 检查PIPELINE_STATES中是否有scene_info
    if "scene_info" in PIPELINE_STATES[env_name]:
        scene_info = PIPELINE_STATES[env_name]["scene_info"]
        description = PIPELINE_STATES[env_name].get("description", "")

    # 如果从PIPELINE_STATES中没有scene_info，从文件加载
    if not scene_info:
        scene_info_path = os.path.join(env_path, "scene_info.json")
        if os.path.exists(scene_info_path):
            try:
                with open(scene_info_path, 'r', encoding='utf-8') as f:
                    scene_info = json.load(f)
                    # 存储在pipeline states中供以后使用
                    PIPELINE_STATES[env_name]["scene_info"] = scene_info
            except Exception as e:
                logger.error(f"Error loading scene_info.json: {e}")

    # 如果有scene_info，提取描述
    if not description and scene_info:
        description = ODDAgent.odd_to_markdown(scene_info)

    all_agent_ids = {}
    index = existing_max_id + 1  # 从当前最大ID加1开始

    # 步骤1：为每个需要生成的代理类型生成画像
    from onesim.profile import AgentSchema
    for agent_type, count in profiles_to_generate.items():
        # 加载模式
        schema_path = os.path.join(env_path, "profile", "schema", f"{agent_type}.json")
        if not os.path.exists(schema_path):
            logger.warning(f"未找到代理类型 {agent_type} 的模式。跳过。")
            continue

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)

            schema = AgentSchema(schema_data)

            # 生成画像
            output_path = os.path.join(profile_data_dir, f"{agent_type}.json")

            # 使用agent_factory中的方法
            from onesim.simulator import AgentFactory
            # 如果已有画像，我们只生成额外需要的数量
            profiles = AgentFactory.generate_profiles(
                agent_type=agent_type,
                schema=schema,
                model=model,
                num_profiles=count,
                output_path=output_path,
                index=index
            )

            # 更新索引和收集ID
            generated_ids = [profile.get_agent_profile_id() for profile in profiles]
            if agent_type in all_agent_ids:
                all_agent_ids[agent_type].extend(generated_ids)
            else:
                all_agent_ids[agent_type] = generated_ids

            # 更新索引为最新生成的最大ID加1
            if generated_ids:
                latest_id = max([int(id) if isinstance(id, str) and id.isdigit() else id for id in generated_ids if id])
                index = max(index, latest_id + 1)

            logger.info(f"Generated {len(profiles)} new profiles for agent type {agent_type}")

        except Exception as e:
            logger.error(f"Error generating profiles for agent type {agent_type}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate profiles for agent type {agent_type}: {str(e)}")

    # 加载所有代理类型的所有画像ID（包括现有和新生成的）
    for agent_type in data.agent_types.keys():
        if agent_type not in all_agent_ids:
            all_agent_ids[agent_type] = []

        profile_file = os.path.join(profile_data_dir, f"{agent_type}.json")
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    agent_ids = [profile.get('agent_profile_id', profile.get('id')) for profile in profiles]
                    all_agent_ids[agent_type] = [id for id in agent_ids if id]  # 过滤掉None值
            except Exception as e:
                logger.error(f"Error loading profiles for agent type {agent_type}: {e}")

    # 步骤2：生成关系模式
    from onesim.agent import ProfileAgent
    profile_agent = ProfileAgent(model_config_name=model.config_name)

    agent_types = list(data.agent_types.keys())
    profile_data_path = os.path.join(env_path, "profile", "schema")
    create_directory(profile_data_path)

    # 从pipeline状态或文件加载动作和事件
    actions = {}
    events = {}

    # 如果可用，从pipeline状态获取
    actions = PIPELINE_STATES[env_name].get("actions", {})
    events = PIPELINE_STATES[env_name].get("events", {})

    # 如果在pipeline状态中未找到，尝试从文件加载
    if not actions:
        actions_path = os.path.join(env_path, "actions.json")
        if os.path.exists(actions_path):
            with open(actions_path, 'r', encoding='utf-8') as f:
                actions = json.load(f)

    if not events:
        events_path = os.path.join(env_path, "events.json")
        if os.path.exists(events_path):
            with open(events_path, 'r', encoding='utf-8') as f:
                events = json.load(f)

    # 生成关系模式
    try:
        schema = profile_agent.generate_relationship_schema(agent_types, actions, events)
        with open(
            os.path.join(profile_data_path, f"Relationship.json"), "w", encoding='utf-8'
        ) as f:
            json.dump(schema, f, ensure_ascii=False, indent=4)
        logger.info("Generated relationship schema")
    except Exception as e:
        logger.error(f"Error generating relationship schema: {e}")
        # 即使关系模式生成失败也继续

    # 步骤3：生成关系
    relationship_config = {
        "min_relationships_per_agent": 1,
        "max_relationships_per_agent": 3
    }

    relationships_list = []

    # 基于模式生成关系
    try:
        with open(
            os.path.join(profile_data_path, f"Relationship.json"), "r", encoding='utf-8'
        ) as f:
            relationship_schema = json.load(f)

        for relationship in relationship_schema:
            source_type = relationship["source_agent"]
            target_type = relationship["target_agent"]
            # relationship_type = relationship["relationship_type"]
            direction = relationship["direction"]

            source_ids = all_agent_ids.get(source_type, [])
            target_ids = all_agent_ids.get(target_type, [])

            # 确保有代理可以连接
            if not source_ids or not target_ids:
                continue

            for source_id in source_ids:
                # 确定每个代理要生成的关系数量
                min_rel = relationship_config["min_relationships_per_agent"]
                max_rel = relationship_config["max_relationships_per_agent"]
                num_relationships = random.randint(min_rel, max_rel)
                num_relationships = min(num_relationships, len(target_ids))

                selected_target_ids = random.sample(target_ids, num_relationships)

                for target_id in selected_target_ids:
                    relationships_list.append({
                        "source_id": source_id,
                        "target_id": target_id,
                        #"relationship_type": relationship_type,
                        "direction": direction
                    })

        # 将关系列表转换为DataFrame并保存到CSV文件
        import pandas as pd
        relationships_df = pd.DataFrame(relationships_list)
        relationships_df.to_csv(relationship_csv_path, index=False)
        logger.info(f"Relationships has been saved to csv file {relationship_csv_path}")
    except Exception as e:
        logger.error(f"Error generating relationships: {e}")
        # 即使关系生成失败也继续

    # 步骤4：生成环境数据
    try:
        # 从pipeline状态获取系统数据模型
        system_data_model = PIPELINE_STATES[env_name].get("system_data_model", {})
        env_data_model = system_data_model.get('environment', {})

        # 如果在pipeline状态中未找到，尝试从文件加载
        if not env_data_model:
            system_data_model_path = os.path.join(env_path, "system_data_model.json")
            if os.path.exists(system_data_model_path):
                with open(system_data_model_path, 'r', encoding='utf-8') as f:
                    system_data_model = json.load(f)
                    env_data_model = system_data_model.get('environment', {})

        # 生成环境数据
        if env_data_model:
            env_data = profile_agent.generate_env_data(env_data_model, description)
            with open(env_data_path, "w", encoding='utf-8') as f:
                json.dump(env_data, f, ensure_ascii=False, indent=4)
            logger.info("Generated environment data")
        else:
            logger.warning("Environment data model not found. Skipping environment data generation.")
    except Exception as e:
        logger.error(f"Error generating environment data: {e}")
        # 即使环境数据生成失败也继续

    # 更新pipeline状态
    # 标记已生成画像
    PIPELINE_STATES[env_name]["profiles_generated"] = True
    PIPELINE_STATES[env_name]["agent_types"] = agent_types
    PIPELINE_STATES[env_name]["all_agent_ids"] = all_agent_ids

    return ProfileGenerationResponse(
        env_name=env_name,
        message="Successfully generated agent profiles, relationships, and environment data",
        profile_path=profile_data_dir,
        relationship_path=relationship_csv_path,
        env_data_path=env_data_path
    )

@router.get("/tips", response_model=TipsResponse)
async def get_tips():
    """
    Returns a list of helpful tips about the simulation system
    that can be shown to users while they're waiting for operations to complete.
    """
    all_tips = [
        "Agent profiles can be customized to create more diverse simulations. Try modifying personality traits to see how they affect behavior.",
        "When generating code, carefully check the action handlers for logical errors before running simulations.",
        "You can modify event code to add custom behaviors that occur when specific events are triggered.",
        "Each agent type can have different actions and handle different events, making the simulation more complex and realistic.",
        "Consider the relationships between agents when designing workflows - these connections impact how agents interact.",
        "If agent generation is taking too long, try reducing the number of agents or simplifying their profiles.",
        "For more complex simulations, ensure your agent types cover different functional roles in the system.",
        "Workflow visualizations can help you understand how agents interact with each other through events.",
        "Generated code sometimes needs minor adjustments for specific behaviors - don't hesitate to edit it.",
        "Setting appropriate minimum and maximum relationships per agent helps create a more realistic social network.",
        "Metrics can be used to track important aspects of your simulation, like resource distribution or communication frequency.",
        "Actions that cause events to be emitted will trigger behavior in other agents, creating a chain of interactions.",
        "The system data model defines what information is tracked in your simulation - consider what data is important for your scenario.",
        "More detailed agent type descriptions tend to result in more nuanced and realistic agent behaviors.",
        "Environment data represents the shared world state that all agents can potentially access or modify.",
        "A complex simulation might require multiple iterations of code generation and testing to fine-tune behavior.",
        "When updating agent types, all downstream artifacts including workflows and code are automatically cleared to prevent inconsistencies.",
        "Agents can be programmed to have memory of past interactions, which can influence their future decisions.",
        "The profile schema determines what attributes agents can have - carefully design this to capture important character traits.",
        "Large language models generate the agent behaviors based on your descriptions - more detailed prompts lead to better results.",
        "Each agent has a unique ID that can be used to track its behavior throughout the simulation.",
        "You can regenerate workflows if the current one doesn't match your expectations for agent interactions.",
        "The relationship graph determines which agents know or interact with each other regularly.",
        "Be patient during code generation for complex simulations - the AI needs time to create detailed behaviors.",
        "Consider adding error handling in critical action handlers to make your simulation more robust.",
        "You can update action and event handlers without regenerating the entire codebase.",
        "Planning capabilities allow agents to create and follow multi-step plans to achieve their goals.",
        "Metrics can help you identify unexpected patterns or behaviors in your simulation.",
        "Agent communication can be explicit (through events) or implicit (through shared environment data).",
        "If the simulation behaves unexpectedly, check the event handlers to see how information is being processed.",
        "More complex agent profiles may require more computational resources during simulation.",
        "When designing workflows, think about the causal relationships between different events and actions.",
        "Agent memory strategies determine how agents recall and prioritize past experiences.",
        "The event bus is responsible for routing events to the appropriate agents based on registrations.",
        "Profile generation uses AI to create diverse and realistic agent characteristics based on your schema.",
        "You can create specialized agent types for specific roles or functions in your simulation scenario."
    ]
    
    # Return all tips or a subset if you want to limit the response size
    return TipsResponse(tips=all_tips)
