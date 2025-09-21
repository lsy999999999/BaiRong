from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class AgentChatRequest(BaseModel):
    env_name: str
    agent_id: str
    message: str

class AgentChatResponse(BaseModel):
    env_name: str
    agent_id: str
    message: str
    timestamp: str
    history: List[Dict[str, Any]] 

class AgentChatHistoryResponse(BaseModel):
    env_name: str
    agent_id: str
    history: List[Dict[str, Any]]

class UpdateAgentProfileRequest(BaseModel):
    env_name: str
    agent_id: str
    profile_data: Dict[str, Any]
    
class UpdateAgentProfileResponse(BaseModel):
    success: bool
    message: str
    agent_id: str
    updated_fields: List[str]