from typing import Dict, Any, Optional
from pydantic import BaseModel

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
    """Response for ODD conversation messages"""
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