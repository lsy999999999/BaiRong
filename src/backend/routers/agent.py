from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import os
import json
import time

from backend.models.agent import AgentChatRequest, AgentChatResponse, AgentChatHistoryResponse, UpdateAgentProfileRequest, UpdateAgentProfileResponse
from backend.utils.model_management import load_model_if_needed
from backend.routers.simulation import SIMULATION_REGISTRY
from pydantic import BaseModel

# 全局变量
AGENT_CHAT_HISTORY = {}

router = APIRouter(
    tags=["agent"],
    prefix="/agent"
)

@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(request: AgentChatRequest):
    """与代理聊天"""
    env_name = request.env_name
    agent_id = request.agent_id
    message = request.message
    chat_id = f"chat_{env_name}_{agent_id}"
    
    # 检查环境是否存在于 SIMULATION_REGISTRY
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在或未初始化")
    
    # 查找代理
    agent = None
    env_agents_data = SIMULATION_REGISTRY[env_name].get("agents", {})
    for agent_type in env_agents_data:
        if agent_id in env_agents_data[agent_type]:
            agent = env_agents_data[agent_type][agent_id]
            break
    
    # 检查代理是否存在
    if agent is None:
        raise HTTPException(status_code=404, detail=f"在环境 '{env_name}' 中未找到代理 '{agent_id}'")
    
    # 创建或获取聊天历史
    if chat_id not in AGENT_CHAT_HISTORY:
        AGENT_CHAT_HISTORY[chat_id] = []
    
    # 将用户消息添加到历史
    user_timestamp = time.time()
    user_timestamp= time.localtime(user_timestamp)
    user_timestamp= time.strftime("%Y-%m-%d %H:%M:%S", user_timestamp)
    AGENT_CHAT_HISTORY[chat_id].append({
        "role": "user",
        "content": message,
        "timestamp": user_timestamp
    })
    
    agent_response = await agent.interact(message, AGENT_CHAT_HISTORY[chat_id])
    
    # 将代理响应添加到历史
    response_timestamp = time.time()
    response_timestamp= time.localtime(response_timestamp)
    response_timestamp= time.strftime("%Y-%m-%d %H:%M:%S", response_timestamp)
    AGENT_CHAT_HISTORY[chat_id].append({
        "role": "assistant",
        "content": agent_response['message'],
        "timestamp": response_timestamp
    })
    
    return AgentChatResponse(
        env_name=env_name,
        agent_id=agent_id,
        message=agent_response['message'],
        timestamp=response_timestamp, # Return the timestamp of the assistant's response
        history=AGENT_CHAT_HISTORY[chat_id] # Return full updated history
    )

@router.get("/history/{env_name}/{agent_id}", response_model=AgentChatHistoryResponse)
async def get_agent_chat_history(env_name: str, agent_id: str):
    """获取与代理的聊天历史"""
    chat_id = f"chat_{env_name}_{agent_id}"
    
    # 检查环境是否存在于 SIMULATION_REGISTRY
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在或未初始化")
    
    # 检查代理是否存在
    agent_exists = False
    env_agents_data = SIMULATION_REGISTRY[env_name].get("agents", {})
    for agent_type in env_agents_data:
        if agent_id in env_agents_data[agent_type]:
            agent_exists = True
            break
    
    if not agent_exists:
        raise HTTPException(status_code=404, detail=f"在环境 '{env_name}' 中未找到代理 '{agent_id}'")
    
    # 检查是否有聊天历史
    if chat_id not in AGENT_CHAT_HISTORY:
        return AgentChatHistoryResponse(
            env_name=env_name,
            agent_id=agent_id,
            history=[]
        )
    
    return AgentChatHistoryResponse(
        env_name=env_name,
        agent_id=agent_id,
        history=AGENT_CHAT_HISTORY[chat_id]
    )

@router.post("/update_profile", response_model=UpdateAgentProfileResponse)
async def update_agent_profile(request: UpdateAgentProfileRequest):
    """更新代理的个人资料"""
    env_name = request.env_name
    agent_id = request.agent_id
    profile_data = request.profile_data
    
    # 检查环境是否存在于 SIMULATION_REGISTRY
    if env_name not in SIMULATION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在或未初始化")
    
    # 查找代理
    agent = None
    agent_type = None
    env_agents_data = SIMULATION_REGISTRY[env_name].get("agents", {})
    for at in env_agents_data:
        if agent_id in env_agents_data[at]:
            agent = env_agents_data[at][agent_id]
            agent_type = at
            break
    
    # 检查代理是否存在
    if agent is None:
        raise HTTPException(status_code=404, detail=f"在环境 '{env_name}' 中未找到代理 '{agent_id}'")
    
    # 获取模拟环境
    sim_env = SIMULATION_REGISTRY[env_name].get("sim_env")
    if sim_env is None:
        raise HTTPException(status_code=500, detail=f"无法获取环境 '{env_name}' 的模拟环境")
    
    # 更新代理的个人资料
    updated_fields = []
    try:
        # 对每个提供的资料字段进行更新
        for key, value in profile_data.items():
            # 在代理的 profile 字段中更新数据
            # 使用 update_agent_data 方法进行安全更新
            success = await agent.update_data(key, value)
            
            if success:
                updated_fields.append(key)
            
        if not updated_fields:
            return UpdateAgentProfileResponse(
                success=False,
                message=f"未能更新代理 '{agent_id}' 的任何资料字段",
                agent_id=agent_id,
                updated_fields=[]
            )
        
        return UpdateAgentProfileResponse(
            success=True,
            message=f"成功更新代理 '{agent_id}' 的资料",
            agent_id=agent_id,
            updated_fields=updated_fields
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"更新代理资料时出错: {str(e)}"
        )