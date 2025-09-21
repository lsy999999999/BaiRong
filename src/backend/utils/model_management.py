"""
模型管理工具函数
处理模型的加载、获取和配置管理
"""
import os
import json
from loguru import logger
from typing import Optional, Dict, Any, List

from onesim.models import ModelManager
import onesim
from backend.models.model_library import get_model_library

# 全局变量
MODEL = None
MODEL_CONFIG_NAME = None
MODEL_CONFIG_PATH = os.path.join(os.getcwd(), 
                                "config", "model_config.json")
DEFAULT_CONFIG = {}  # 将从load_default_config初始化

def load_default_config():
    """从配置文件加载默认配置"""
    global DEFAULT_CONFIG
    config_path = os.path.join(os.getcwd(), 
                              "config", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                DEFAULT_CONFIG = json.load(f)
                logger.info(f"从{config_path}加载默认配置")
        else:
            logger.warning(f"未找到默认配置文件: {config_path}")
            DEFAULT_CONFIG = {}
    except Exception as e:
        logger.error(f"加载默认配置出错: {str(e)}")
        DEFAULT_CONFIG = {}
    return DEFAULT_CONFIG

async def load_model_if_needed(model_name: Optional[str] = None, category: str = "chat"):
    """
    加载并初始化LLM（如果尚未加载）
    
    参数:
        model_name: 要加载的特定模型名称
        category: 模型类别（'chat'或'embedding'）
    
    返回:
        初始化的模型适配器
    """
    global MODEL
    
    logger.info(f"从{MODEL_CONFIG_PATH}加载模型{model_name}")
    # 如果未提供model_name，则从DEFAULT_CONFIG中检查
    if not model_name and "model" in DEFAULT_CONFIG:
        if category == "chat" and "chat" in DEFAULT_CONFIG["model"]:
            model_name = DEFAULT_CONFIG["model"]["chat"]
            logger.info(f"从默认配置使用聊天模型{model_name}")
        elif category == "embedding" and "embedding" in DEFAULT_CONFIG["model"]:
            model_name = DEFAULT_CONFIG["model"]["embedding"]
            logger.info(f"从默认配置使用嵌入模型{model_name}")
    
    try:
        # 如果尚未初始化，则初始化onesim
        model_manager = ModelManager.get_instance()
        if not hasattr(model_manager, 'model_configs') or not model_manager.model_configs:
            await onesim.init(model_config_path=MODEL_CONFIG_PATH)

        # 如果请求了特定模型，则使用它
        if model_name:
            MODEL = model_manager.get_model(model_name=model_name)
        else:
            # 按类别获取模型
            MODEL = model_manager.get_model(model_type=category)
        logger.info(f"加载的模型配置名称: {MODEL.config_name}")
    except Exception as e:
        logger.error(f"初始化模型失败: {str(e)}")
        raise Exception(f"初始化模型失败: {str(e)}")
    return MODEL

async def get_available_models(category: str = "chat"):
    """
    获取按类别筛选的可用模型列表
    
    参数:
        category: 模型类别（'chat'或'embedding'）
    
    返回:
        与筛选条件匹配的模型信息字典列表
    """
    try:
        model_manager = ModelManager.get_instance()
        
        # 如果需要初始化
        if not hasattr(model_manager, 'model_configs') or not model_manager.model_configs:
            await onesim.init(model_config_path=MODEL_CONFIG_PATH)
            
        # 按类别获取所有配置
        model_configs = model_manager.get_configs_by_type(category)
        
        # 按model_name将模型分组以便显示
        models_by_name = set()
        
        for config in model_configs:
            model_name = config.get("model_name")
            if not model_name:
                continue
                
            models_by_name.add(model_name)
        
        
        # 按model_name返回唯一模型
        return list(models_by_name)
    except Exception as e:
        logger.error(f"获取可用模型错误: {e}")
        return []

def _get_library_models_by_category(category: str) -> set:
    """从模型库获取模型名称"""
    model_names = set()
    try:
        model_library = get_model_library()
        
        # 对应的模型类型
        model_type = "base"  # 默认基础模型
        
        if category == "chat":
            # 获取聊天模型（包括基础和微调模型）
            chat_models = model_library.get_all_models()
            chat_models = [m for m in chat_models if m.get("model_type") in ["base", "fine_tuned"]]
            
            for model in chat_models:
                model_names.add(model.get("model_name", ""))
        
        elif category == "embedding":
            # 获取嵌入模型
            embedding_models = model_library.get_all_models(model_type="embedding")
            for model in embedding_models:
                model_names.add(model.get("model_name", ""))
    except Exception as e:
        logger.error(f"从模型库获取模型错误: {e}")
    
    return model_names

async def update_model_config_from_library(model_id: str):
    """
    从模型库更新模型配置
    
    参数:
        model_id: 模型ID
    
    返回:
        bool: 更新是否成功
    """
    try:
        model_library = get_model_library()
        model = model_library.get_model_by_id(model_id)
        
        if not model:
            logger.error(f"找不到模型ID: {model_id}")
            return False
        
        # 加载配置文件
        with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 确定模型类型
        model_type = "chat"
        if model["model_type"] == "embedding":
            model_type = "embedding"
        
        # 创建新的配置项
        new_config = {
            "provider": "vllm",  # 默认使用vllm
            "config_name": model["model_name"],
            "model_name": model["model_name"],
            "model_path": model["path"],
            "api_key": "123",
            "client_args": {
                "max_retries": 3
            }
        }
        
        # 将配置添加到相应类别
        found = False
        for i, existing_config in enumerate(config.get(model_type, [])):
            if existing_config.get("model_name") == model["model_name"]:
                config[model_type][i] = new_config
                found = True
                break
        
        if not found and model_type in config:
            config[model_type].append(new_config)
        
        # 保存更新后的配置
        with open(MODEL_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
        logger.info(f"已将模型 {model['model_name']} 添加到配置文件")
        return True
    except Exception as e:
        logger.error(f"更新模型配置失败: {e}")
        return False 
