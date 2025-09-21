"""
文件和目录操作工具函数
"""
import os
import json
from glob import glob
from typing import Dict, List, Any
from loguru import logger

def create_directory(path: str):
    """创建目录（如果不存在）"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"创建目录: {path}")

def get_scene_info_files():
    """Get all scene info files"""
    scene_files = []
    for domain in os.listdir("./scenes"):
        domain_path = os.path.join("./scenes", domain)
        if os.path.isdir(domain_path):
            for file in os.listdir(domain_path):
                if file.endswith(".json"):
                    scene_files.append(os.path.join(domain_path, file))
    return scene_files

def load_scene_info(file_path):
    """Load scene info from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading scene info from {file_path}: {str(e)}")
        return None

def init_package(path: str):
    """在包目录中创建__init__.py"""
    init_file = os.path.join(path, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
        logger.info(f"创建包初始化文件: {init_file}")

def setup_environment(env_name: str):
    """Set up environment directory structure"""
    base_path = os.path.join(os.getcwd(),"src", "envs", env_name)
    create_directory(base_path)
    
    # Create code directory
    code_path = os.path.join(base_path, "code")
    create_directory(code_path)
    init_package(code_path)
    
    # Set up agents directory
    agents_path = os.path.join(base_path, "agents")
    create_directory(agents_path)
    
    # Set up data directory
    data_path = os.path.join(base_path, "data")
    create_directory(data_path)
    
    return base_path

def save_json(path: str, data: Dict[str, Any], indent: int = 4):
    """保存JSON数据到文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.info(f"保存JSON文件: {path}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败 {path}: {str(e)}")
        return False

def load_json(path: str) -> Dict[str, Any]:
    """从文件加载JSON数据"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"加载JSON文件: {path}")
        return data
    except Exception as e:
        logger.error(f"加载JSON文件失败 {path}: {str(e)}")
        return {}

def save_scene_info(env_path: str, scene_info: dict, agent_types_with_descriptions: dict = None):
    """Save scene info to environment"""
    metadata_path = os.path.join(env_path, "metadata.json")

    # Add agent types to scene info if provided
    if agent_types_with_descriptions:
        scene_info["agent_types"] = agent_types_with_descriptions

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(scene_info, f, indent=2)

    return metadata_path 
