from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator

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

# Common models
class EnvRequest(BaseModel):
    env_name: str

# Domain and scene models
class SceneInfo(BaseModel):
    name: str
    description: str
    domain: str

class DomainData(BaseModel):
    name: str
    scenes: List[SceneInfo]

class SceneNameCheck(BaseModel):
    scene_name: str

class SceneNameCheckResponse(BaseModel):
    exists: bool
    message: str

# Model selection models
class ModelSelection(BaseModel):
    model_name: str
    category: Optional[str] = "chat"  # 'chat' or 'embedding'

class ModelSelectionResponse(BaseModel):
    message: str
    category: str
    model_name: str

class ModelsRequest(BaseModel):
    category: Optional[str] = None  # 'chat' or 'embedding'

class ModelsResponse(BaseModel):
    models: Dict[str, List[str]] 