# -*- coding: utf-8 -*-
"""
自动生成的监控指标计算模块
"""

from typing import Dict, Any, List, Optional, Union, Callable
import math
from loguru import logger
from onesim.monitor.utils import (
    safe_get, safe_number, safe_list, safe_sum, 
    safe_avg, safe_max, safe_min, safe_count, log_metric_error
)


from typing import Dict, Any

def SystemStatusOverTime(data: Dict[str, Any]) -> Any:
    """
    计算指标: SystemStatusOverTime
    描述: Tracks the current status of the environment to monitor system health and transitions between states.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # 验证输入数据有效性
        if not data or not isinstance(data, dict):
            log_metric_error("SystemStatusOverTime", ValueError("Invalid data input"), {"data": data})
            return {"environment_status": "unknown"}
        
        # 获取环境status变量
        status_value = safe_get(data, 'status')
        
        # 处理缺失或无效值
        if status_value is None:
            log_metric_error("SystemStatusOverTime", ValueError("Missing required variable: status"), {"data": data})
            return {"environment_status": "unknown"}
        
        # 确保返回字符串类型
        current_status = str(status_value)
        
        # 返回折线图需要的单系列数据结构
        return {"environment_status": [current_status]}
    
    except Exception as e:
        log_metric_error("SystemStatusOverTime", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"environment_status": ["unknown"]}

from typing import Dict, Any
from collections import Counter

def DecisionMakerStatusDistribution(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: DecisionMakerStatusDistribution
    描述: Analyzes the distribution of statuses among DecisionMaker agents to identify common operational states or anomalies.
    可视化类型: bar
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - bar: 返回字典，键为分类（状态值），值为对应数值（出现次数）
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # 检查数据有效性
        if not data or not isinstance(data, dict):
            log_metric_error("DecisionMakerStatusDistribution", ValueError("Invalid data input"), {"data": data})
            return {}
        
        # 获取DecisionMaker的status列表
        status_list = safe_get(data, 'status')
        status_list = safe_list(status_list)  # 确保是列表
        
        # 过滤掉None值
        filtered_statuses = [s for s in status_list if s is not None]
        
        # 统计状态分布
        status_distribution = Counter(filtered_statuses)
        
        # 返回结果字典
        return dict(status_distribution)
    
    except Exception as e:
        log_metric_error("DecisionMakerStatusDistribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_number, log_metric_error

def ResponseDataConsistency(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: ResponseDataConsistency
    描述: Measures the percentage of DecisionMaker agents whose response_data matches the environment's response_data, indicating alignment between agent outputs and system state.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # 验证输入数据结构
        if not data or not isinstance(data, dict):
            log_metric_error("ResponseDataConsistency", ValueError("Invalid data input"), {"data": data})
            return {"consistency": 0.0}
        
        # 获取环境response_data
        env_response = safe_get(data, 'response_data', default=None)
        # 获取DecisionMaker的response_data列表
        agent_responses = safe_list(safe_get(data, 'response_data', default=[]))
        
        # 处理环境值为None或空列表的情况
        if env_response is None or not agent_responses:
            return {"consistency": 0.0}
        
        # 确保环境值是字符串类型
        env_response = safe_number(env_response, default=None)
        if env_response is None:
            return {"consistency": 0.0}
        
        # 统计匹配数量（处理列表中可能的None值）
        match_count = safe_count(agent_responses, predicate=lambda x: x == env_response)
        total_agents = safe_number(len(agent_responses), default=0)
        
        # 处理除零错误
        if total_agents == 0:
            return {"consistency": 0.0}
        
        # 计算一致性百分比
        consistency = (match_count / total_agents) * 100
        return {"consistency": float(consistency)}
    
    except Exception as e:
        log_metric_error("ResponseDataConsistency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"consistency": 0.0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'SystemStatusOverTime': SystemStatusOverTime,
    'DecisionMakerStatusDistribution': DecisionMakerStatusDistribution,
    'ResponseDataConsistency': ResponseDataConsistency,
}


def get_metric_function(function_name: str) -> Optional[Callable]:
    """
    根据函数名获取对应的指标计算函数
    
    Args:
        function_name: 函数名
        
    Returns:
        指标计算函数或None
    """
    return METRIC_FUNCTIONS.get(function_name)
'System_Status_Over_Time': System_Status_Over_Time,
    'DecisionMaker_Status_Distribution': DecisionMaker_Status_Distribution,
    'Average_Response_Data_Length': Average_Response_Data_Length,
}


def get_metric_function(function_name: str) -> Optional[Callable]:
    """
    根据函数名获取对应的指标计算函数
    
    Args:
        function_name: 函数名
        
    Returns:
        指标计算函数或None
    """
    return METRIC_FUNCTIONS.get(function_name)
