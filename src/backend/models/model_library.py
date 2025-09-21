"""
模型库管理
处理模型的注册、加载和元数据管理
"""
import os
import json
import shutil
from datetime import datetime
import re
from typing import List, Dict, Any, Optional
from loguru import logger
from pydantic import BaseModel

# 模型库路径
MODEL_REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models", "registry.json")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models")

# 模型元数据
class ModelMetadata(BaseModel):
    model_id: str
    model_name: str
    model_type: str  # "base", "fine_tuned", "embedding" 
    description: Optional[str] = None
    path: str
    created_at: str
    config_file: Optional[str] = None
    base_model_id: Optional[str] = None  # 用于微调模型
    fine_tuning_params: Optional[Dict[str, Any]] = None  # 用于微调模型
    version: Optional[str] = None
    size: Optional[str] = None  # 文件大小，如"14B"
    tags: Optional[List[str]] = []


class ModelLibrary:
    def __init__(self):
        """初始化模型库"""
        self._ensure_registry_exists()
    
    def _ensure_registry_exists(self) -> None:
        """确保模型注册表存在"""
        if not os.path.exists(MODEL_REGISTRY_PATH):
            # 创建目录
            os.makedirs(os.path.dirname(MODEL_REGISTRY_PATH), exist_ok=True)
            # 创建默认注册表
            with open(MODEL_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    "models": []
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"创建新的模型注册表: {MODEL_REGISTRY_PATH}")
    
    def _load_registry(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载模型注册表"""
        try:
            with open(MODEL_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                registry = json.load(f)
                # 兼容旧格式
                if not "models" in registry and any(k in registry for k in ["base_models", "fine_tuned_models", "embedding_models"]):
                    # 转换旧格式到新格式
                    models = []
                    if "base_models" in registry:
                        models.extend(registry["base_models"])
                    if "fine_tuned_models" in registry:
                        models.extend(registry["fine_tuned_models"])
                    if "embedding_models" in registry:
                        models.extend(registry["embedding_models"])
                    registry = {"models": models}
                    # 保存新格式
                    self._save_registry(registry)
                return registry
        except Exception as e:
            logger.error(f"加载模型注册表失败: {str(e)}")
            return {"models": []}
    
    def _save_registry(self, registry: Dict[str, List[Dict[str, Any]]]) -> None:
        """保存模型注册表"""
        try:
            with open(MODEL_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)
            logger.info("模型注册表已更新")
        except Exception as e:
            logger.error(f"保存模型注册表失败: {str(e)}")
    
    def _try_extract_parameter_size(self, model_name: str) -> Optional[str]:
        """尝试从模型名称中提取参数量"""
        # 尝试匹配常见模式如 "7B", "14B", "175B" 等
        patterns = [
            r'(\d+)[Bb]',  # 匹配 7B, 14B 等
            r'(\d+)[Mm]',  # 匹配 7M, 14M 等
            r'(\d+(?:\.\d+)?)[\s-]*[Bb]illion',  # 匹配 7 Billion, 14-Billion 等
            r'(\d+(?:\.\d+)?)[\s-]*[Tt]rillion',  # 匹配 1 Trillion 等
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_name)
            if match:
                size = match.group(1)
                # 确定单位
                if 'rillion' in pattern:
                    if 'illion' in pattern and 'B' in pattern:
                        return f"{size}B"
                    elif 'illion' in pattern and 'T' in pattern:
                        return f"{size}T"
                elif 'B' in pattern or 'b' in pattern:
                    return f"{size}B"
                elif 'M' in pattern or 'm' in pattern:
                    return f"{size}M"
                
        return None
    
    def get_all_models(self, model_type: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有模型，可按类型或标签筛选
        
        参数:
            model_type: 可选的模型类型筛选，如 "base", "fine_tuned" 等
            tag: 可选的标签筛选
        """
        registry = self._load_registry()
        models = registry["models"]
        
        # 应用筛选
        if model_type:
            models = [model for model in models if model.get("model_type") == model_type]
        if tag:
            models = [model for model in models if tag in model.get("tags", [])]
            
        return models
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取模型"""
        registry = self._load_registry()
        for model in registry["models"]:
            if model.get("model_id") == model_id:
                return model
        return None
    
    def register_model(self, model_metadata: ModelMetadata) -> str:
        """注册模型"""
        registry = self._load_registry()
        
        # 检查是否微调模型并验证base_model_id
        if model_metadata.model_type == "fine_tuned" and not model_metadata.base_model_id:
            raise ValueError("微调模型必须指定base_model_id")
        
        # 如果是微调模型，检查基础模型是否存在
        if model_metadata.model_type == "fine_tuned" and model_metadata.base_model_id:
            base_model = self.get_model_by_id(model_metadata.base_model_id)
            if not base_model:
                raise ValueError(f"找不到基础模型ID: {model_metadata.base_model_id}")
        
        # 检查模型ID是否已存在
        for i, model in enumerate(registry["models"]):
            if model.get("model_id") == model_metadata.model_id:
                logger.warning(f"模型ID '{model_metadata.model_id}'已存在，更新现有记录")
                registry["models"][i] = model_metadata.dict()
                self._save_registry(registry)
                return model_metadata.model_id
        
        # 尝试从模型名称中提取参数量
        if not model_metadata.size:
            size = self._try_extract_parameter_size(model_metadata.model_name)
            if size:
                model_metadata.size = size
                # 如果标签中没有参数量信息，也添加到标签中
                if size not in model_metadata.tags:
                    model_metadata.tags.append(size)
        
        # 添加新模型
        registry["models"].append(model_metadata.dict())
        self._save_registry(registry)
        logger.info(f"已注册模型: {model_metadata.model_name} (ID: {model_metadata.model_id})")
        return model_metadata.model_id
    
    def delete_model(self, model_id: str) -> bool:
        """删除模型记录"""
        registry = self._load_registry()
        
        for i, model in enumerate(registry["models"]):
            if model.get("model_id") == model_id:
                del registry["models"][i]
                self._save_registry(registry)
                logger.info(f"已删除模型ID: {model_id}")
                return True
        
        logger.warning(f"找不到要删除的模型ID: {model_id}")
        return False

    def update_model_metadata(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """更新模型元数据"""
        registry = self._load_registry()
        
        for i, model in enumerate(registry["models"]):
            if model.get("model_id") == model_id:
                registry["models"][i].update(updates)
                self._save_registry(registry)
                logger.info(f"已更新模型ID '{model_id}'的元数据")
                return True
        
        logger.warning(f"找不到要更新的模型ID: {model_id}")
        return False

# 单例模式实现
_instance = None

def get_model_library() -> ModelLibrary:
    """获取模型库单例"""
    global _instance
    if _instance is None:
        _instance = ModelLibrary()
    return _instance 
 