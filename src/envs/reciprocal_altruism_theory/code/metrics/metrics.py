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
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def health_behavior_spread_completion_rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: health_behavior_spread_completion_rate
    描述: Measures the proportion of completed health behavior spread efforts within the community network.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值, 适用于pie图
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Safely retrieve the completion_status list from the data
        completion_status_list = safe_list(safe_get(data, 'completion_status', []))
        
        # Count completed efforts (True values) and total efforts
        completed_count = safe_count(completion_status_list, lambda x: x is True)
        total_count = safe_count(completion_status_list)
        
        # Handle division by zero scenario
        if total_count == 0:
            log_metric_error("health_behavior_spread_completion_rate", ZeroDivisionError("Total count is zero"), {"completion_status": completion_status_list})
            return {"completed": 0.0, "incomplete": 0.0}
        
        # Calculate proportions
        completed_proportion = completed_count / total_count
        incomplete_proportion = (total_count - completed_count) / total_count
        
        # Return the result in pie format
        return {
            "completed": completed_proportion,
            "incomplete": incomplete_proportion
        }
    
    except Exception as e:
        log_metric_error("health_behavior_spread_completion_rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"completed": 0.0, "incomplete": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_avg, safe_list, log_metric_error

def average_behavior_change_intensity(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: average_behavior_change_intensity
    描述: Calculates the average intensity of health behavior changes initiated by advocates.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Access the 'intensity' values from HealthBehaviorAdvocate agents
        intensity_values = safe_list(safe_get(data, 'intensity', []))
        
        # Calculate the average intensity using safe_avg, ignoring None values
        average_intensity = safe_avg([value for value in intensity_values if value is not None])

        # Return result in the format required for a bar chart
        return {"Average Intensity": average_intensity}
    
    except Exception as e:
        log_metric_error("average_behavior_change_intensity", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Average Intensity": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def commitment_level_distribution(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: commitment_level_distribution
    描述: Shows the distribution of commitment levels among recipients of health behavior changes.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        line: 返回字典，键为系列名称，值为对应数值
    """
    try:
        # Initialize result dictionary for line chart
        result = {}

        # Access commitment_level data from BehaviorChangeRecipient
        commitment_levels = safe_list(safe_get(data, 'commitment_level', []))

        # Validate and filter commitment_levels
        valid_commitment_levels = [level for level in commitment_levels if isinstance(level, int) and level is not None]

        # Calculate frequency distribution of commitment levels
        frequency_distribution = {}
        for level in valid_commitment_levels:
            if level in frequency_distribution:
                frequency_distribution[level] += 1
            else:
                frequency_distribution[level] = 1

        # Populate result dictionary for line visualization
        for level, count in frequency_distribution.items():
            result[f"commitment_level_{level}"] = count

        return result

    except Exception as e:
        log_metric_error("commitment_level_distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"default": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'health_behavior_spread_completion_rate': health_behavior_spread_completion_rate,
    'average_behavior_change_intensity': average_behavior_change_intensity,
    'commitment_level_distribution': commitment_level_distribution,
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
