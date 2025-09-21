"""
ODD Protocol Router
Handles ODD protocol generation, dialogue and scene confirmation
"""
import os
import json
import re
import uuid
import shutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional
from loguru import logger
import time
import httpx

from onesim.agent import ODDAgent
from backend.utils.model_management import load_model_if_needed
from backend.utils.file_ops import create_directory, init_package
from backend.models.pipeline import PipelineRequest

router = APIRouter(
    prefix="/odd",
    tags=["odd"],
)

# Session storage
CONVERSATIONS = {}

# Model definitions
class UserMessage(BaseModel):
    session_id: str
    message: str

class InitialPrompt(BaseModel):
    prompt: str
    model_name: Optional[str] = None
    category: Optional[str] = "chat"

class SceneConfirmation(BaseModel):
    session_id: str
    scene_name: str

class ODDResponse(BaseModel):
    """Response for ODD session messages"""
    session_id: str
    domain: str
    message: str
    odd_protocol: Dict[str, Any]
    is_complete: bool
    scene_name: Optional[str] = None

class SceneConfirmationResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    scene_name: Optional[str] = None

class SceneNameCheck(BaseModel):
    scene_name: str

class SceneNameCheckResponse(BaseModel):
    exists: bool
    message: str

class HistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, Any]]
    scene_name: Optional[str] = None

class ProtocolResponse(BaseModel):
    session_id: str
    odd_protocol: Dict[str, Any]
    scene_name: Optional[str] = None
# Constants
DOMAIN_LIST = [
    "Economics",
    "Sociology",
    "Politics",
    "Psychology",
    "Organization", 
    "Demographics",
    "Law",
    "Communication"
]

# Set up environment directory structure
def setup_environment(env_name: str):
    """Set up environment directory structure"""
    base_path = os.path.abspath(os.getcwd())
    env_path = os.path.join(base_path, "src", "envs", env_name)
    create_directory(env_path)
    init_package(env_path)
    return env_path

async def get_odd_agent(session_id: str, model_name: Optional[str] = None, category: str = "chat"):
    """
    Get or create an ODD agent for the session
    
    Parameters:
        session_id: Unique session identifier
        model_name: Optional specific model name
        category: Model category ('chat' or 'embedding')
    
    Returns:
        Session data dictionary containing the ODD agent
    """
    # Check if this session already exists
    if session_id in CONVERSATIONS:
        return CONVERSATIONS[session_id]
    
    # Initialize model
    model = await load_model_if_needed(model_name, category)
    
    # Create new ODD agent
    odd_agent = ODDAgent(model_config_name=model.config_name)
    
    # Store session data
    CONVERSATIONS[session_id] = {
        "odd_agent": odd_agent,
        "history": [],
        "domain": None,
        "scene_name": None,
        "odd_protocol": None,
        "is_complete": False,
        "pipeline_initialized": False,
        "scene_created": False
    }
    return CONVERSATIONS[session_id]

@router.get("/domains", response_model=List[str])
def get_domains():
    """Get list of all domains"""
    return DOMAIN_LIST

@router.post("/start", response_model=ODDResponse)
async def start_odd_conversation(prompt: InitialPrompt):
    """Start a new ODD conversation with an initial prompt"""
    session_id = str(uuid.uuid4())
    
    # Initialize session with provided model parameters
    session_data = await get_odd_agent(
        session_id, 
        model_name=prompt.model_name,
        category=prompt.category
    )
    odd_agent = session_data["odd_agent"]
    
    # Process initial prompt
    response = odd_agent.process_user_input(prompt.prompt)
    
    # Update session data with new history format
    session_data["history"].append({
        "sender": "user", 
        "content": prompt.prompt, 
        "timestamp": int(time.time())
    })
   
    
    session_data["domain"] = response["domain"]
    session_data["scene_name"] = response["scene_name"]
    session_data["odd_protocol"] = response["odd_protocol"]
    session_data["is_complete"] = response["is_complete"]
    session_data["session_id"] = session_id
    if response["is_complete"]:
        message = "The ODD protocol is shown on the right. Is there any additional information that needs to be added?"
    else:
        message = response["clarification_question"]

    session_data["history"].append({
        "sender": "system", 
        "content": message, 
        "timestamp": int(time.time())
    })
    return ODDResponse(
        session_id=session_id,
        domain=response["domain"],
        message=message,
        odd_protocol=response["odd_protocol"],
        is_complete=response["is_complete"],
        scene_name=response["scene_name"]
    )

@router.post("/chat", response_model=ODDResponse)
async def process_odd_message(message: UserMessage):
    """Process messages in the ODD conversation"""
    if message.session_id not in CONVERSATIONS:
        raise HTTPException(status_code=404, detail=f"Session {message.session_id} not found")
    
    session_data = CONVERSATIONS[message.session_id]
    odd_agent = session_data["odd_agent"]
    
    # Process user input
    response = odd_agent.process_user_input(message.message)
    
    # Update session data with new history format
    session_data["history"].append({
        "sender": "user", 
        "content": message.message, 
        "timestamp": int(time.time())
    })
   
    
    session_data["domain"] = response["domain"]
    session_data["scene_name"] = response["scene_name"]
    # Only store the odd_protocol part from scene_info
    session_data["odd_protocol"] = response["odd_protocol"]
    session_data["is_complete"] = response["is_complete"]
    
    if not response["is_complete"]:
        reply = response["clarification_question"]
    else:
        reply = "The ODD protocol is shown on the right. Is there any additional information that needs to be added?"
        
    session_data["history"].append({
        "sender": "system", 
        "content": reply, 
        "timestamp": int(time.time())
    })
    return ODDResponse(
        session_id=message.session_id,
        domain=response["domain"],
        message=reply,
        odd_protocol=response["odd_protocol"],
        is_complete=response["is_complete"],
        scene_name=response["scene_name"]
    )

@router.post("/confirm_scene", response_model=SceneConfirmationResponse)
async def confirm_scene(confirmation: SceneConfirmation):
    """Confirm scene creation with the provided scene name, clearing existing directory if present."""
    if confirmation.session_id not in CONVERSATIONS:
        raise HTTPException(status_code=404, detail=f"Session {confirmation.session_id} not found")
    
    session_data = CONVERSATIONS[confirmation.session_id]
    odd_agent = session_data["odd_agent"]
    scene_name = confirmation.scene_name
    
    # Verify if this scene has already been created IN THIS SESSION
    # Note: This does not prevent overwriting an existing directory from a different session
    # if session_data.get("scene_created", False):
    #     return SceneConfirmationResponse(
    #         success=False,
    #         message=f"Scene for session {confirmation.session_id} has already been created ({session_data.get('env_name')}). Confirming again will overwrite.",
    #         session_id=confirmation.session_id,
    #         scene_name=session_data.get('env_name')
    #     )
    # Removing the above check to allow overwriting / re-initialization easily.
        
    # Validate scene name
    if not re.match(r'^[a-zA-Z0-9_-]+$', scene_name):
        return SceneConfirmationResponse(
            success=False,
            message="Invalid scene name. Use only letters, numbers, underscores, and hyphens.",
            session_id=confirmation.session_id,
            scene_name=None
        )
    
    # Check if target directory exists and clear if it does
    base_path = os.path.abspath(os.getcwd())
    env_path = os.path.join(base_path, "src", "envs", scene_name)
    message_suffix = ""
    if os.path.exists(env_path):
        try:
            shutil.rmtree(env_path)
            logger.info(f"Cleared existing directory: {env_path}")
            message_suffix = " (existing directory cleared)"
        except OSError as e:
            logger.error(f"Error clearing existing directory {env_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to clear existing scene directory: {str(e)}")

    # Create environment directory structure (recreates after clearing or creates if new)
    try:
        setup_environment(scene_name)
    except Exception as e:
        logger.error(f"Error setting up environment directory {env_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create scene directory: {str(e)}")
    
    # Update scene name in scene_info with the confirmed name
    odd_agent.scene_info["scene_name"] = scene_name
    
    # Save using the agent's method
    try:
        odd_agent.save_scene_info(env_path)
    except Exception as e:
        logger.error(f"Error saving scene info to {env_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save scene information: {str(e)}")

    # Mark this session as having created/confirmed a scene
    session_data["scene_created"] = True
    session_data["env_name"] = scene_name
    
    return SceneConfirmationResponse(
        success=True,
        message=f"Scene '{scene_name}' created successfully{message_suffix}",
        scene_name=scene_name,
        session_id=confirmation.session_id
    )

@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_odd_history(session_id: str, env_name: Optional[str] = None):
    """Get the conversation history for an ODD session. Creates a new session if session_id is 'None'."""
    # env_name is ignored for history retrieval for now.
    # If session_id is 'None', always create a new session.
    if session_id == "None":
        new_session_id = str(uuid.uuid4())
        await get_odd_agent(new_session_id) # Initialize session
        logger.info(f"Created new session {new_session_id} for history request (env_name ignored).")
        return HistoryResponse(
            session_id=new_session_id, 
            history=[{
                "sender": "system",
                "content": "ODD protocol is shown on the right. Is there any additional information that needs to be added?",
                "timestamp": int(time.time())
            }],
            scene_name=env_name
        )

    if session_id not in CONVERSATIONS:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session_data = CONVERSATIONS[session_id]
    return HistoryResponse(session_id=session_id, history=session_data["history"], scene_name=session_data["scene_name"])

@router.get("/protocol/{session_id}", response_model=ProtocolResponse)
async def get_odd_protocol(session_id: str, env_name: Optional[str] = None):
    """
    Get the ODD protocol.
    - If session_id is 'None' and env_name is provided: Reads protocol directly from env_name/scene_info.json without creating a session.
    - If session_id is 'None' and env_name is not provided: Creates a new session and returns its initial empty protocol.
    - If session_id is provided: Retrieves the protocol from the existing session data.
    """
    if session_id == "None":
        if env_name=="":
            env_name = None
        if env_name:
            # Attempt to load directly from env_name/scene_info.json
            base_path = os.path.abspath(os.getcwd())
            scene_info_path = os.path.join(base_path, "src", "envs", env_name, "scene_info.json")
            
            if not os.path.exists(scene_info_path):
                logger.warning(f"scene_info.json not found at {scene_info_path}")
                raise HTTPException(status_code=404, detail=f"Protocol source for environment '{env_name}' not found.")

            try:
                with open(scene_info_path, 'r', encoding='utf-8') as f:
                    loaded_scene_info = json.load(f)
                
                odd_protocol = loaded_scene_info.get("odd_protocol", {})
                logger.info(f"Read ODD protocol directly from '{scene_info_path}' for env_name '{env_name}'.")
                # Return the loaded protocol; session_id in response is the env_name
                session_id = str(uuid.uuid4())
                session_data = await get_odd_agent(session_id)
                session_data["odd_protocol"] = odd_protocol
                session_data["scene_name"] = env_name
                CONVERSATIONS[session_id] = session_data
                return ProtocolResponse(
                    session_id=session_id, 
                    odd_protocol=odd_protocol,
                    scene_name=env_name
                )
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {scene_info_path}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to parse protocol file for environment '{env_name}'.")
            except Exception as e:
                logger.error(f"Error reading protocol file {scene_info_path}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to read protocol file for environment '{env_name}'.")
        else:
            # session_id is 'None' but no env_name provided - create new session
            new_session_id = str(uuid.uuid4())
            session_data = await get_odd_agent(new_session_id) # Initialize session
            odd_agent = session_data["odd_agent"]
            logger.info(f"Created new session {new_session_id} for protocol request (no env_name).")
            # Return initial empty protocol from the new agent
            return ProtocolResponse(
                session_id=new_session_id,
                odd_protocol=odd_agent.scene_info.get("odd_protocol", {}),
                scene_name=env_name
            )

    # If session_id is provided (and not 'None')
    if session_id not in CONVERSATIONS:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    session_data = CONVERSATIONS[session_id]
    odd_agent = session_data["odd_agent"]
    
    # Return existing session's protocol data
    return ProtocolResponse(
        session_id=session_id,
        odd_protocol=odd_agent.scene_info.get("odd_protocol", {}),
        scene_name=session_data["scene_name"]
    )

@router.post("/check_scene_name", response_model=SceneNameCheckResponse)
def check_scene_name(data: SceneNameCheck):
    """
    Check if the scene name already exists.
    
    Parameters:
        data: SceneNameCheck containing:
            - scene_name: The scene name to check
    
    Returns:
        SceneNameCheckResponse with exists (boolean) and message fields
    """
    # Validate scene name (no special characters except underscores and hyphens)
    if not re.match(r'^[a-zA-Z0-9_-]+$', data.scene_name):
        return SceneNameCheckResponse(
            exists=False,
            message="Invalid scene name. Use only letters, numbers, underscores, and hyphens."
        )
    
    # Check if scene directory already exists
    base_path = os.path.abspath(os.getcwd())
    scene_path = os.path.join(base_path, "src", "envs", data.scene_name)
    
    if os.path.exists(scene_path):
        return SceneNameCheckResponse(
            exists=True,
            message=f"Scene '{data.scene_name}' already exists"
        )
    
    return SceneNameCheckResponse(
        exists=False,
        message=f"Scene name '{data.scene_name}' is available"
    )

@router.get("/examples", response_model=List[str])
def get_scenario_examples():
    """Get a list of example descriptions for social simulation scenarios to inspire users"""
    examples = [
        "In a simplified job market, multiple applicants search for suitable positions based on their education and experience, while companies post job openings with varying salaries and requirements. Applicants adjust their application strategies based on available jobs, and employers may revise salaries or criteria based on the applicant pool. This simulation explores how supply and demand dynamics shape employment outcomes and market efficiency.",
        "This model simulates a local election where residents choose between two candidates. Each resident's voting decision is influenced by personal preferences, neighborhood opinions, and the candidates' policy positions. Candidates may also adjust their messaging strategies in response to public feedback. The simulation examines how information flow, social influence, and strategic communication impact election results.",
        "A small group of individuals each faces a judgment task, with prior responses from others visible. Although individuals have an initial opinion, they may change their decision under perceived social pressure to conform with the group majority. This simulation explores the psychological mechanisms of conformity and how group consensus can override personal judgment.",
        "Individuals in a social network each hold a binary opinion (e.g., support or oppose an issue) and are influenced by the opinions of their neighbors. Over time, individuals update their stance based on the proportion of agreement in their social circle. This simulation models how local influence patterns can lead to widespread consensus, persistent division, or opinion polarization."
    ]
    return examples 