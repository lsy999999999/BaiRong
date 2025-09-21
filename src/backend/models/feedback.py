from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class RateDecisionDataRequest(BaseModel):
    """对决策数据进行评分的请求模型"""
    env_name: str
    selected_data: List[Dict[str, Any]]
    model_name: str = "gpt-4o-mini"

class RefineDecisionDataRequest(BaseModel):
    """优化决策数据的请求模型"""
    env_name: str
    selected_data: List[Dict[str, Any]]
    model_name: str = "gpt-4o-mini"

class UpdateDecisionDataRequest(BaseModel):
    """更新决策数据的请求模型"""
    env_name: str
    updated_data: List[Dict[str, Any]]

class SaveDecisionDataRequest(BaseModel):
    """保存决策数据的请求模型"""
    env_name: str

class SaveResponse(BaseModel):
    """保存决策数据的响应模型"""
    success: bool
    file_path: str

class FeedbackResponse(BaseModel):
    """反馈接口的通用响应模型"""
    success: bool
    message: str
    data: List[Dict[str, Any]] = [] 