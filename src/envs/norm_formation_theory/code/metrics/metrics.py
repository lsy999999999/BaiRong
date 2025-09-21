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


from typing import Dict, Any, List
from onesim.monitor.utils import safe_get, safe_list, safe_avg, log_metric_error

def average_group_norm_conformity(data: Dict[str, Any]) -> Any:
    """
    计算指标: average_group_norm_conformity
    描述: Measures the average level of conformity to group norms across all individual agents.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("average_group_norm_conformity", ValueError("Invalid data input"), {"data": data})
            return 0.0
        
        # Retrieve adjusted_behavior_tendencies from IndividualAgent
        adjusted_behavior_tendencies_list = safe_get(data, "adjusted_behavior_tendencies", [])
        adjusted_behavior_tendencies_list = safe_list(adjusted_behavior_tendencies_list)

        # Check if list is empty
        if not adjusted_behavior_tendencies_list:
            log_metric_error("average_group_norm_conformity", ValueError("No adjusted_behavior_tendencies data available"), {"data_keys": list(data.keys())})
            return 0.0
        
        # Calculate average conformity for each agent
        agent_averages = []
        for tendencies in adjusted_behavior_tendencies_list:
            tendencies_list = safe_list(tendencies)
            if tendencies_list:
                agent_avg = safe_avg(tendencies_list)
                agent_averages.append(agent_avg)

        # Calculate overall average conformity
        if not agent_averages:
            log_metric_error("average_group_norm_conformity", ValueError("No valid agent averages computed"), {"adjusted_behavior_tendencies_list": adjusted_behavior_tendencies_list})
            return 0.0

        overall_average = safe_avg(agent_averages)
        return overall_average

    except Exception as e:
        log_metric_error("average_group_norm_conformity", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0.0

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_sum, safe_avg, log_metric_error

def group_pressure_distribution(data: Dict[str, Any]) -> Any:
    """
    计算指标: group_pressure_distribution
    描述: Shows the distribution of group pressure experienced by individual agents, indicating how pressure is spread across different groups.
    可视化类型: bar
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("group_pressure_distribution", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve and validate group_pressure from environment variables
        group_pressure = safe_number(safe_get(data, "group_pressure", None))
        if group_pressure is None:
            log_metric_error("group_pressure_distribution", ValueError("Missing or invalid group_pressure"), {"data": data})
            return {}

        # Retrieve and validate group_id from agent variables
        group_ids = safe_list(safe_get(data, "group_id", []))
        if not group_ids:
            log_metric_error("group_pressure_distribution", ValueError("Missing or invalid group_id list"), {"data": data})
            return {}

        # Initialize a dictionary to store total pressure and count of agents per group
        group_pressure_map = {}

        # Iterate over agents and calculate total pressure and count per group
        for group_id in group_ids:
            if group_id is None:
                continue  # Skip agents with None group_id

            if group_id not in group_pressure_map:
                group_pressure_map[group_id] = {"total_pressure": 0.0, "agent_count": 0}

            group_pressure_map[group_id]["total_pressure"] += group_pressure
            group_pressure_map[group_id]["agent_count"] += 1

        # Calculate average group pressure for each group
        result = {}
        for group_id, values in group_pressure_map.items():
            agent_count = values["agent_count"]
            total_pressure = values["total_pressure"]
            if agent_count > 0:
                result[group_id] = total_pressure / agent_count
            else:
                result[group_id] = 0.0

        return result

    except Exception as e:
        log_metric_error("group_pressure_distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def average_norm_acceptance(data: Dict[str, Any]) -> Any:
    """
    计算指标: norm_change_proportion
    描述: Represents the proportion of social groups that have undergone norm changes.
    可视化类型: pie
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        norm_acceptance = safe_list(data.get("norm_acceptance"))
        avg_norm_acceptance = safe_avg(norm_acceptance)
        return {"average_group_norm_conformity": avg_norm_acceptance}

    except Exception as e:
        return {"average_group_norm_conformity": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'average_group_norm_conformity': average_group_norm_conformity,
    'group_pressure_distribution': group_pressure_distribution,
    'average_norm_acceptance': average_norm_acceptance,
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


