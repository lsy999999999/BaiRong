from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class AgentInfo(BaseModel):
    id: str
    type: str
    profile: Dict[str, Any]
    
class InitializeAgentsRequest(BaseModel):
    env_name: str
    model_name: Optional[str] = None
    category: Optional[str] = "chat"

class InitializeAgentsResponse(BaseModel):
    success: bool
    message: str
    agent_count: int
    agents: List[AgentInfo]

class GetAgentsRequest(BaseModel):
    env_name: str
    agent_type: Optional[str] = None



class GetAgentsResponse(BaseModel):
    agents: List[AgentInfo]
    count: int

class StartSimulationRequest(BaseModel):
    env_name: str

class StartSimulationResponse(BaseModel):
    success: bool
    message: str
    simulation_id: str

class StopSimulationRequest(BaseModel):
    env_name: str

class StopSimulationResponse(BaseModel):
    success: bool
    message: str

class PauseSimulationRequest(BaseModel):
    env_name: str

class PauseSimulationResponse(BaseModel):
    success: bool
    message: str
    is_paused: bool

class ResumeSimulationRequest(BaseModel):
    env_name: str

class ResumeSimulationResponse(BaseModel):
    success: bool
    message: str
    is_running: bool

class GetDecisionDataRequest(BaseModel):
    env_name: str

class GetDecisionDataResponse(BaseModel):
    success: bool
    message: str
    data: List[Dict[str, Any]]

class GetEventsResponse(BaseModel):
    success: bool
    message: str
    events: List[Dict[str, Any]]