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
from onesim.monitor.utils import (
    safe_get, safe_number, safe_list, safe_sum, safe_avg, log_metric_error
)

def Average_Conformity_Tendency(data: Dict[str, Any]) -> Any:
    """
    计算指标: Average Conformity Tendency
    描述: Measures the average tendency of individual agents to conform within the system, providing insight into overall conformity behavior.
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
        # Check if data is a valid dictionary
        if not data or not isinstance(data, dict):
            log_metric_error("Average Conformity Tendency", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve the list of conformity tendencies from IndividualAgent
        conformity_tendencies = safe_list(safe_get(data, "conformity_tendency", []))

        # Convert all values in the list to numbers, treating None as zero
        conformity_tendencies = [safe_number(value, default=0) for value in conformity_tendencies]

        # Calculate the average conformity tendency
        average_conformity_tendency = safe_avg(conformity_tendencies, default=0)

        # Prepare the result as a dictionary for bar visualization
        result = {"Average Conformity Tendency": average_conformity_tendency}

        return result
    except Exception as e:
        log_metric_error("Average Conformity Tendency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_number, log_metric_error
)

def System_Social_Pressure(data: Dict[str, Any]) -> Any:
    """
    计算指标: System Social Pressure
    描述: Tracks the level of social pressure in the environment, which influences agent decision-making and conformity.
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
            log_metric_error("System Social Pressure", ValueError("Invalid data input"), {"data": data})
            return 0
        
        # Extract social_pressure from environment variables
        social_pressure = safe_get(data.get("environment", {}), "social_pressure", None)
        
        # Convert social_pressure to a number, defaulting to 0 if None or invalid type
        social_pressure_value = safe_number(social_pressure, default=0)
        
        # Return the calculated social pressure value for line visualization
        return social_pressure_value

    except Exception as e:
        log_metric_error("System Social Pressure", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0

def Opinion_Leader_Influence_Strength_Distribution(data: Dict[str, Any]) -> Any:
    """
    计算指标: Opinion Leader Influence Strength Distribution
    描述: Analyzes the distribution of influence strength among opinion leaders, indicating their potential impact on group dynamics.
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
    from onesim.monitor.utils import (
        safe_get, safe_list, safe_sum, log_metric_error
    )

    try:
        # Validate input data
        if not isinstance(data, dict):
            log_metric_error("Opinion Leader Influence Strength Distribution", ValueError("Invalid data input"), {"data": data})
            return {}

        valid_influence_strengths = data['influence_strength']
        total_strength = safe_sum(valid_influence_strengths)

        # Calculate proportional values for pie chart
        distribution = {
            f"Leader {i+1}": strength / total_strength
            for i, strength in enumerate(valid_influence_strengths)
        }


        return distribution

    except Exception as e:
        log_metric_error("Opinion Leader Influence Strength Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Conformity_Tendency': Average_Conformity_Tendency,
    'System_Social_Pressure': System_Social_Pressure,
    'Opinion_Leader_Influence_Strength_Distribution': Opinion_Leader_Influence_Strength_Distribution,
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


