"""
领域路由模块
提供获取可用领域和场景的功能
"""
import os
import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from loguru import logger
from glob import glob
from onesim.agent import ODDAgent

from backend.models.base import DOMAIN_LIST, SceneNameCheck, SceneNameCheckResponse
from backend.utils.file_ops import get_scene_info_files, load_scene_info

router = APIRouter(
    prefix="",
    tags=["domains"],
)

# 常量
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

def get_scene_info_files():
    """在src/envs中查找所有scene_info.json文件"""
    scene_files = []
    
    # 检查envs
    env_path=os.path.join("src","envs")
    env_dirs = glob(os.path.join(env_path,"*"))
    for env_dir in env_dirs:
        scene_file = os.path.join(env_dir, "scene_info.json")
        if os.path.exists(scene_file):
            scene_files.append(scene_file)
    
    return scene_files

def load_scene_info(file_path):
    """从JSON文件加载场景信息"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 提取所需字段
            data['name'] = file_path.split(os.sep)[-2]
            data['description'] = ODDAgent.odd_to_markdown(data['odd_protocol']) if 'odd_protocol' in data else ""
            return data
    except Exception as e:
        logger.error(f"加载 {file_path} 出错: {e}")
        return None

@router.get("/domains", response_model=List[str])
def get_domains():
    """获取所有领域列表"""
    return DOMAIN_LIST

@router.get("/scenes", response_model=Dict[str, List[Dict[str, str]]])
def get_scenes_by_domain():
    """获取按领域分组的场景"""
    scene_files = get_scene_info_files()
    
    # 初始化领域字典
    domains = {domain: [] for domain in DOMAIN_LIST}
    
    # 加载并分类场景信息
    for file_path in scene_files:
        scene_data = load_scene_info(file_path)
        if scene_data and 'domain' in scene_data:
            domain = scene_data["domain"]
            # 添加到现有领域或在预定义列表中不存在时创建新领域
            if domain in domains:
                name = scene_data.get("scene_name", scene_data.get("name", ""))
                if name != os.path.dirname(file_path).split(os.sep)[-1]:
                    name = os.path.dirname(file_path).split(os.sep)[-1]
                domains[domain].append({
                    "name": name,
                    "description": scene_data.get("description", ""),
                    "path": os.path.dirname(file_path)
                })
    
    # 过滤掉空领域
    return {k: v for k, v in domains.items() if v}

@router.get("/scenes/{domain}", response_model=List[Dict[str, str]])
def get_scenes_for_domain(domain: str):
    """获取特定领域的场景"""
    all_scenes = get_scenes_by_domain()
    
    if domain not in all_scenes:
        raise HTTPException(status_code=404, detail=f"未找到领域 '{domain}'")
    
    return all_scenes[domain]

@router.get("/scene/{scene_name}")
def get_scene_details(scene_name: str):
    """获取特定场景的详细信息"""
    full_path = os.path.join("src","envs", scene_name, "scene_info.json")
    scene_details = {}
    try:
        with open(full_path, "r", encoding='utf-8') as f:
            scene_details = json.load(f)

        with open(
            os.path.join("src", "envs", scene_name, "actions.json"),
            "r",
            encoding='utf-8',
        ) as f:
            actions = json.load(f)

        with open(
            os.path.join("src", "envs", scene_name, "events.json"),
            "r",
            encoding='utf-8',
        ) as f:
            events = json.load(f)

        with open(
            os.path.join("src", "envs", scene_name, "code", "code_structure.json"),
            "r",
            encoding='utf-8',
        ) as f:
            code_structure = json.load(f)
            for agent_type, agent_data in code_structure.get("agents", {}).items():
                for action_id, handler_data in agent_data.get("handlers", {}).items():
                    if agent_type in actions:
                        for action in actions[agent_type]:
                            if str(action.get("id")) == action_id:
                                action["code"] = handler_data.get("code", "")

            # 添加代码到事件
            for event_id, event_data in code_structure.get("events", {}).get("definitions", {}).items():
                if event_id in events:
                    events[event_id]["code"] = event_data.get("code", "")

        scene_details["actions"] = actions
        scene_details["events"] = events
        if 'odd_protocol' in scene_details:
            scene_details['description'] = scene_details['odd_protocol'].get('overview', {}).get('system_goal', '')
            scene_details['odd_protocol'] = ODDAgent.odd_to_markdown(scene_details)
        return scene_details

    except FileNotFoundError:
        return {}
        # raise HTTPException(status_code=404, detail=f"在 {full_path} 未找到场景信息")

    except Exception as e:
        return {}
        # raise HTTPException(status_code=500, detail=f"加载场景信息出错: {str(e)}")

@router.post("/check_scene_name", response_model=SceneNameCheckResponse)
def check_scene_name(data: SceneNameCheck):
    """Check if a scene name already exists"""
    scene_name = data.scene_name
    scene_files = get_scene_info_files()
    
    for file_path in scene_files:
        scene_data = load_scene_info(file_path)
        if scene_data and scene_data.get("name") == scene_name:
            return SceneNameCheckResponse(
                exists=True,
                message=f"Scene with name '{scene_name}' already exists"
            )
    
    return SceneNameCheckResponse(
        exists=False,
        message=f"Scene name '{scene_name}' is available"
    ) 
