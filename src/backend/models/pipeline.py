from typing import Dict, Any, Optional, List
from pydantic import BaseModel, field_validator

class PipelineRequest(BaseModel):
    env_name: str
    model_name: Optional[str] = None
    category: Optional[str] = "chat"

class AgentTypesResponse(BaseModel):
    agent_types: Dict[str, str]
    env_name: str
    portrait: Optional[Dict[str, int]] = None

class UpdateAgentTypesRequest(BaseModel):
    env_name: str
    agent_types: Dict[str, str]
    portrait: Optional[Dict[str, int]] = None

class WorkflowResponse(BaseModel):
    actions: Dict[str, Any]
    events: Dict[str, Any]
    system_data_model: Dict[str, Any]
    env_name: str
    success: int = 1  # 0=Failed, 1=Success, 2=In Progress
    message: str = "Workflow generated successfully"

class CodeGenerationStatus(BaseModel):
    phase: int  # 0=complete, 1=generating code, 2=validating and fixing code
    content: str
    all_content: str
class CodeUpdateRequest(BaseModel):
    env_name: str
    actions: Dict[str, Any] = {}  # Match the format of get_code response
    events: Dict[str, Any] = {}   # Match the format of get_code response

class ProfileSchemaRequest(BaseModel):
    env_name: str
    agent_schemas: Dict[str, Dict[str, Any]]  # Map of agent_type to profile_schema

class ProfileSchemaResponse(BaseModel):
    env_name: str
    agent_schemas: Dict[str, Dict[str, Any]]  # Map of agent_type to profile_schema
    profile_counts: Dict[str, int] = {}  # Map of agent_type to profile count
    message: str

class ProfileGenerationRequest(BaseModel):
    env_name: str
    agent_types: Dict[str, int]  # Map of agent_type to count
    model_name: Optional[str] = None
    category: Optional[str] = "chat"

class ProfileGenerationResponse(BaseModel):
    env_name: str
    message: str
    profile_path: str
    relationship_path: str
    env_data_path: str 