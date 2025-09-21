from typing import Dict, Any, Optional
from pydantic import BaseModel

class ConfigOptions(BaseModel):
    environment: Dict[str, Any]
    agent: Dict[str, Any]
    model: Dict[str, Any]  # Add model field for model configuration options

class ProfileCountRequest(BaseModel):
    env_name: str
    agent_type: str

class ProfileCountResponse(BaseModel):
    max_count: int
    message: str

class SaveConfigRequest(BaseModel):
    env_name: str
    config: Dict[str, Any]

class SaveConfigResponse(BaseModel):
    success: bool
    message: str 