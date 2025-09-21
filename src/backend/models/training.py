from typing import Dict, Any, Optional, List
from pydantic import BaseModel, field_validator

class FeedbackExportRequest(BaseModel):
    env_name: Optional[str] = None
    session_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
    
    @field_validator('session_id', 'env_name')
    @classmethod
    def validate_has_one(cls, v, info):
        # Ensure at least one of session_id or env_name is provided
        if not v and not info.data.get('session_id') and not info.data.get('env_name'):
            raise ValueError('Either session_id or env_name must be provided')
        return v

class FeedbackExportResponse(BaseModel):
    success: bool
    message: str
    data: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int

class TrainingRequest(BaseModel):
    model_name: str
    dataset_path: str
    tuning_mode: str = "sft"  # "sft" or "ppo"
    experiment_name: Optional[str] = None
    
    @field_validator('tuning_mode')
    @classmethod
    def validate_tuning_mode(cls, v):
        if v not in ["sft", "ppo"]:
            raise ValueError('tuning_mode must be either "sft" or "ppo"')
        return v

class TrainingResponse(BaseModel):
    success: bool
    message: str
    tracking_uri: str
    experiment_name: str
    experiment_url: str
    run_id: Optional[str] = None 