"""
配置管理路由
处理系统配置、模型配置和环境设置
"""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional
from loguru import logger
import onesim
from onesim.config import get_component_registry, get_config as get_onesim_config
from onesim.models.core.model_manager import ModelManager
from backend.models.config import ConfigOptions, ProfileCountRequest, ProfileCountResponse, SaveConfigRequest, SaveConfigResponse
from backend.models.simulation import AgentInfo
from backend.utils.model_management import load_model_if_needed, get_available_models

router = APIRouter(
    prefix="/config",
    tags=["config"],
)


class UpdateModelConfigRequest(BaseModel):
    """模型配置更新请求"""
    config: Dict[str, Any]
    
    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        """验证配置格式"""
        if not isinstance(v, dict):
            raise ValueError("配置必须是字典格式")
        
        # 检查是否有chat或embedding字段
        if 'chat' not in v and 'embedding' not in v:
            raise ValueError("配置必须包含 'chat' 或 'embedding' 字段")
        
        # 验证chat配置
        if 'chat' in v:
            if not isinstance(v['chat'], list):
                raise ValueError("'chat' 配置必须是列表格式")
            for chat_config in v['chat']:
                if not isinstance(chat_config, dict):
                    raise ValueError("每个chat配置必须是字典格式")
                required_fields = ['provider', 'config_name', 'model_name']
                for field in required_fields:
                    if field not in chat_config:
                        raise ValueError(f"chat配置缺少必需字段: {field}")
        
        # 验证embedding配置
        if 'embedding' in v:
            if not isinstance(v['embedding'], list):
                raise ValueError("'embedding' 配置必须是列表格式")
            for emb_config in v['embedding']:
                if not isinstance(emb_config, dict):
                    raise ValueError("每个embedding配置必须是字典格式")
                required_fields = ['provider', 'config_name', 'model_name']
                for field in required_fields:
                    if field not in emb_config:
                        raise ValueError(f"embedding配置缺少必需字段: {field}")
        
        return v


class UpdateModelConfigResponse(BaseModel):
    """模型配置更新响应"""
    success: bool
    message: str
    updated_models: Dict[str, List[str]] = {}


# 存储用户配置
USER_CONFIGS = {}

# 模型配置路径
MODEL_CONFIG_PATH = os.path.join(os.getcwd(), 
                                "config", "model_config.json")

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), 
                                  "config", "config.json")

def load_default_config():
    """加载默认配置"""
    try:
        if os.path.exists(DEFAULT_CONFIG_PATH):
            with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
                logger.info(f"已加载默认配置: {DEFAULT_CONFIG_PATH}")
                return default_config
        else:
            logger.warning(f"默认配置文件不存在: {DEFAULT_CONFIG_PATH}")
            return {}
    except Exception as e:
        logger.error(f"加载默认配置出错: {str(e)}")
        return {}

# 加载默认配置
DEFAULT_CONFIG = load_default_config()

def generate_default_portrait(agent_types):
    """为代理类型生成默认的头像值（1-5之间）"""
    portrait = {}
    # 根据代理类型索引使用1-5之间的不同值
    for i, agent_type in enumerate(agent_types):
        # 根据代理类型索引循环使用1-5的值
        portrait[agent_type] = (i % 5) + 1
    return portrait

@router.get("/options", response_model=ConfigOptions)
def get_config_options(env_name: str):
    """获取场景的配置选项"""
    if not env_name:
        raise HTTPException(status_code=400, detail="需要env_name查询参数")
    
    # 检查场景是否存在
    base_path = os.path.abspath(os.getcwd())
    scenes_root = os.path.join(base_path,"src", "envs")
    scene_path = os.path.join(scenes_root, env_name)
    
    if not os.path.exists(scene_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")
    
    # 动态获取可用的规划策略
    try:
        import importlib
        import inspect
        from onesim.planning import __all__ as planning_all
        from onesim.planning.base import PlanningBase
        
        # 过滤掉基类，只获取具体的规划类
        planning_options = ["None"]  # 首先添加None选项
        for class_name in planning_all:
            module = importlib.import_module("onesim.planning")
            cls = getattr(module, class_name)
            if inspect.isclass(cls) and cls is not PlanningBase and issubclass(cls, PlanningBase):
                planning_options.append(class_name)
    except Exception as e:
        logger.error(f"加载规划选项出错: {e}")
        # 回退到默认选项
        planning_options = ["None", "BDIPlanning", "COTPlanning", "TOMPlanning"]
    
    # 动态获取可用的记忆策略
    try:
        import importlib
        import inspect
        from onesim.memory.strategy import __all__ as strategy_all
        from onesim.memory.strategy.strategy import MemoryStrategy
        
        # 过滤掉基类，只获取具体的策略类
        memory_options = ["None"]  # 首先添加None选项
        for class_name in strategy_all:
            try:
                module = importlib.import_module("onesim.memory.strategy")
                cls = getattr(module, class_name)
                # 检查是否为类、不是基类本身、并且是MemoryStrategy的子类
                if inspect.isclass(cls) and cls is not MemoryStrategy and issubclass(cls, MemoryStrategy):
                    memory_options.append(class_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"检查内存策略类 {class_name} 出错: {e}")
    except Exception as e:
        logger.error(f"加载内存策略选项出错: {e}")
        # 回退到默认选项
        memory_options = ["None", "ListStrategy", "ShortLongStrategy"]
    
    # 从scene_info.json获取可用的代理类型
    scene_info_path = os.path.join(scene_path, "scene_info.json")
    agent_types = {}
    portrait = {}
    
    if os.path.exists(scene_info_path):
        try:
            with open(scene_info_path, 'r', encoding='utf-8') as f:
                scene_info = json.load(f)
                
            if "agent_types" in scene_info:
                agent_types = scene_info["agent_types"]
                
            # 从scene_info.json获取头像（如果存在）
            if "portrait" in scene_info:
                portrait = scene_info["portrait"]
            else:
                # 如果未找到，生成默认头像
                portrait = generate_default_portrait(agent_types.keys())
        except Exception as e:
            logger.error(f"加载scene_info.json出错: {e}")
    
    # 为每个代理类型创建配置文件选项
    profile_options = {}
    for agent_type in agent_types:
        # 检查默认配置文件路径
        profile_path = os.path.join(scene_path, "profile", "data", f"{agent_type}.json")
        count = 0
        
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                    count = len(profiles)
            except Exception as e:
                logger.error(f"加载{agent_type}的配置文件数据出错: {e}")
        
        # 获取此代理类型的头像值
        portrait_value = portrait.get(agent_type, 1)  # 若未指定则默认为1
        
        profile_options[agent_type] = {
            "count": 1,  # 默认为1或如果配置文件较少则更少
            "max_count": count,  # 添加max_count字段以指示最大可用配置文件
            "portrait": portrait_value  # 添加来自scene_info.json的头像值或默认值
        }
    
    # 创建环境选项
    environment_options = {
        "name": env_name,  # 固定，不可更改
        "mode": "round",  # 默认模式
        "modes": ["round", "tick"],  # 可用模式
        "max_steps": 3  # 默认最大回合数
    }
    
    # 创建代理选项
    agent_options = {
        "profile": profile_options,
        "planning": planning_options,
        "memory": memory_options
    }
    
    # 从model_config.json读取模型选项
    model_options = {
        "chat": [],
        "embedding": []
    }
    if os.path.exists(MODEL_CONFIG_PATH):
        try:
            with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                model_config = json.load(f)
                
            # 提取聊天模型选项
            if "chat" in model_config:
                model_options["chat"] = list({model.get("model_name", "") for model in model_config["chat"]})
            
            # 提取嵌入模型选项
            if "embedding" in model_config:
                model_options["embedding"] = list({model.get("model_name", "") for model in model_config["embedding"]})
        except Exception as e:
            logger.error(f"加载model_config.json出错: {e}")
    
    config_options = {
        "environment": environment_options,
        "agent": agent_options,
        "model": model_options
    }
    
    return config_options

@router.post("/save", response_model=SaveConfigResponse)
async def save_config(data: SaveConfigRequest):
    """
    保存场景的配置并初始化环境和代理。
    从base config.json读取，应用来自请求的更改，并将合并的配置保存到内存中。
    然后准备好环境和代理的初始化参数，以便后续进行模拟。
    """
    env_name = data.env_name
    user_config = data.config

    # 检查场景是否存在
    scenes_root = os.path.join(os.getcwd(),"src", "envs")
    scene_path = os.path.join(scenes_root, env_name)

    if not os.path.exists(scene_path):
        raise HTTPException(status_code=404, detail=f"环境 '{env_name}' 不存在")

    # 从默认配置开始
    merged_config = json.loads(json.dumps(DEFAULT_CONFIG))

    # 如果用户配置中存在则更新模拟器设置
    # if "simulator" in user_config:
    #     if "simulator" not in merged_config:
    #         merged_config["simulator"] = {}

    if "environment" in user_config:
        if "environment" not in merged_config["simulator"]:
            merged_config["simulator"]["environment"] = {}

        # 更新环境设置，保留名称
        env_config = user_config["environment"]
        merged_config["simulator"]["environment"].update(env_config)
        # 确保环境名称设置正确
        merged_config["simulator"]["environment"]["name"] = env_name

    # 如果在用户配置中存在则更新代理设置
    if "agent" in user_config:
        if "agent" not in merged_config:
            merged_config["agent"] = {}

        # 更新配置文件设置
        if "profile" in user_config["agent"]:
            if "profile" not in merged_config["agent"]:
                merged_config["agent"]["profile"] = {}

            # 为用户配置中的每个代理类型更新配置文件计数
            for agent_type, profile_data in user_config["agent"]["profile"].items():
                if agent_type not in merged_config["agent"]["profile"]:
                    merged_config["agent"]["profile"][agent_type] = {}

                # 更新计数但保留其他设置
                if "count" in profile_data:
                    merged_config["agent"]["profile"][agent_type]["count"] = profile_data["count"]

        # 更新规划设置
        if "planning" in user_config["agent"]:
            if user_config["agent"]["planning"]=="None":
                merged_config["agent"]["planning"] = None
            else:
                merged_config["agent"]["planning"] = user_config["agent"]["planning"]

        # 更新内存设置
        if "memory" in user_config["agent"]:
            if "memory" not in merged_config["agent"]:
                merged_config["agent"]["memory"] = {}
            if user_config["agent"]["memory"] == "None":
                merged_config["agent"]["memory"] = None
            else:
                merged_config["agent"]["memory"]["strategy"] = user_config["agent"]["memory"]

    # 如果在用户配置中存在则更新模型设置
    if "model" in user_config:
        if "model" not in merged_config:
            merged_config["model"] = {}

        # 更新聊天模型选择（必需）
        if "chat" in user_config["model"]:
            chat_model = user_config["model"]["chat"]
            if not chat_model:
                raise HTTPException(status_code=400, detail="需要聊天模型选择")
            merged_config["model"]["chat"] = chat_model

        # 更新嵌入模型选择（可选）
        if "embedding" in user_config["model"]:
            merged_config["model"]["embedding"] = user_config["model"]["embedding"]

    embedding_model_name = user_config.get("model", {}).get("embedding")
    agent_memory_config = merged_config.get("agent", {}).get("memory")

    if (
        embedding_model_name
        and agent_memory_config
        and agent_memory_config.get("strategy") == "ShortLongStrategy"
    ):
        embedding_config_name = None
        if os.path.exists(MODEL_CONFIG_PATH):
            try:
                with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                if "embedding" in model_config:
                    for model in model_config["embedding"]:
                        if model.get("model_name") == embedding_model_name:
                            embedding_config_name = model.get("config_name")
                            break
            except Exception as e:
                logger.error(f"Error in finding embedding model config name: {e}")

        if embedding_config_name:
            if (
                "storages" in agent_memory_config
                and "long_term_storage" in agent_memory_config["storages"]
            ):
                agent_memory_config["storages"]["long_term_storage"][
                    "model_config_name"
                ] = embedding_config_name

            if (
                "metrics" in agent_memory_config
                and "relevance" in agent_memory_config["metrics"]
            ):
                agent_memory_config["metrics"]["relevance"][
                    "model_config_name"
                ] = embedding_config_name

    try:
        # 仅在内存中存储用于当前模拟
        USER_CONFIGS[env_name] = merged_config

        return SaveConfigResponse(
            success=True,
            message=f"已保存环境'{env_name}'的配置"
        )
    except Exception as e:
        logger.error(f"保存配置出错: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")


@router.get("/get", response_model=Dict[str, Any])
def get_config(env_name: str):
    """获取特定环境的配置"""
    # 首先检查内存中的配置
    if env_name in USER_CONFIGS:
        return USER_CONFIGS[env_name]
    
    # 如果不在内存中，尝试加载默认配置
    scenes_root = os.path.join(os.getcwd(), "src", "envs")
    scene_path = os.path.join(scenes_root, env_name)
    config_path = os.path.join(scene_path, "config", "simulator_config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"加载配置出错: {e}")
    
    # 如果没有特定配置，返回默认配置
    return DEFAULT_CONFIG

# 获取模型配置
@router.get("/models", response_model=Dict[str, Any])
async def get_models(category: Optional[str] = None):
    """
    获取可用模型列表（按类别筛选）
    
    参数:
        category: 可选的模型类别筛选器（'chat' 或 'embedding'）
    """
    try:
        result = {"models":{}}
        
        # 如果指定了类别
        if category:
            result['models'][category] = await get_available_models(category)
        else:
            # 默认行为：按类别返回所有模型
            result['models']["chat"] = await get_available_models("chat")
            result['models']["embedding"] = await get_available_models("embedding")
        
        return result
    except Exception as e:
        logger.error(f"获取模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型失败: {str(e)}")


@router.put("/models/update", response_model=UpdateModelConfigResponse)
async def update_model_config(request: UpdateModelConfigRequest):
    """
    更新模型配置
    
    接收一个与model_config.json格式相同的配置字典，
    覆盖现有的model_config.json文件，并将新配置应用到内存中的ModelManager。
    
    参数:
        request: 包含新模型配置的请求体
    
    返回:
        UpdateModelConfigResponse: 更新结果
    """
    try:
        config = request.config
        
        # 备份现有配置（如果存在）
        backup_config = None
        if os.path.exists(MODEL_CONFIG_PATH):
            try:
                with open(MODEL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
                logger.info("已备份现有模型配置")
            except Exception as e:
                logger.warning(f"无法备份现有配置: {e}")
        
        # 写入新配置到文件
        try:
            # 确保config目录存在
            config_dir = os.path.dirname(MODEL_CONFIG_PATH)
            os.makedirs(config_dir, exist_ok=True)
            
            # 写入新配置
            with open(MODEL_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"已更新模型配置文件: {MODEL_CONFIG_PATH}")
            
        except Exception as e:
            logger.error(f"写入配置文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"写入配置文件失败: {str(e)}")
        
        # 更新内存中的ModelManager
        try:
            # 获取ModelManager单例实例
            model_manager = ModelManager.get_instance()
            
            # 清除现有配置
            model_manager.clear_configs()
            
            # 加载新配置
            model_manager.load_model_configs(config)
            
            logger.info("已更新内存中的ModelManager配置")
            
        except Exception as e:
            logger.error(f"更新ModelManager失败: {e}")
            
            # 尝试恢复备份配置
            if backup_config:
                try:
                    with open(MODEL_CONFIG_PATH, 'w', encoding='utf-8') as f:
                        json.dump(backup_config, f, indent=4, ensure_ascii=False)
                    logger.info("已恢复备份配置")
                except Exception as restore_e:
                    logger.error(f"恢复备份配置失败: {restore_e}")
            
            raise HTTPException(status_code=500, detail=f"更新ModelManager失败: {str(e)}")
        
        # 尝试更新OneSim的全局配置
        try:
            onesim_config = get_onesim_config()
            if onesim_config and hasattr(onesim_config, 'model_config'):
                # 重新加载模型配置
                onesim_config.model_config.load_from_dict(config)
                logger.info("已更新OneSim全局配置中的模型配置")
        except Exception as e:
            logger.warning(f"更新OneSim全局配置失败（非关键错误）: {e}")
        
        # 收集更新后的模型信息
        updated_models = {
            "chat": [],
            "embedding": []
        }
        
        if "chat" in config:
            updated_models["chat"] = [model.get("config_name", "") for model in config["chat"]]
        
        if "embedding" in config:
            updated_models["embedding"] = [model.get("config_name", "") for model in config["embedding"]]
        
        total_updated = len(updated_models["chat"]) + len(updated_models["embedding"])
        
        return UpdateModelConfigResponse(
            success=True,
            message=f"成功更新模型配置，共更新了 {total_updated} 个模型配置",
            updated_models=updated_models
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"更新模型配置时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"更新模型配置失败: {str(e)}")
