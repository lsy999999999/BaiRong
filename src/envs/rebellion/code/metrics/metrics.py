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
    safe_get, safe_list, safe_avg, log_metric_error
)

def Average_Grievance_Level(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate metric: Average Grievance Level
    Description: Measures the average level of grievance among citizens, indicating potential unrest.
    Visualization Type: line

    Args:
        data: Dictionary containing all variables collected by the monitor, with agent variables as lists.

    Returns:
        For line visualization: Returns a dictionary where keys are series names and values are data points.
    
    Note:
        This function handles various edge cases, including None values, empty lists, and type errors.
    """
    try:
        # Access the grievance_level list from the data
        grievance_levels = safe_list(safe_get(data, 'grievance_level', []))

        # Filter out None and non-float values
        valid_grievance_levels = [level for level in grievance_levels if isinstance(level, (int, float))]

        # Calculate the average grievance level
        average_grievance = safe_avg(valid_grievance_levels, default=0)

        # Return the result formatted for a line chart
        return {'Average Grievance Level': average_grievance}
    
    except Exception as e:
        log_metric_error("Average Grievance Level", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Average Grievance Level': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Rebellion_Decision_Ratio(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Rebellion Decision Ratio
    描述: Tracks the proportion of citizens deciding to rebel, reflecting the effectiveness of government strategies.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应比例
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Safely retrieve the rebellion_decision list from the data
        rebellion_decisions = safe_list(safe_get(data, 'rebellion_decision', []))

        # Count the number of True values in the rebellion_decision list
        rebellion_count = safe_count(rebellion_decisions, predicate=lambda x: x is True)

        # Count the number of valid (non-None) entries in the rebellion_decision list
        valid_entries = safe_count(rebellion_decisions, predicate=lambda x: x is not None)

        # Calculate the rebellion decision ratio
        if valid_entries == 0:
            ratio = 0.0  # Default ratio if no valid entries
        else:
            ratio = rebellion_count / valid_entries

        # Return result formatted for pie chart visualization
        return {'Rebellion': ratio, 'Non-Rebellion': 1 - ratio}
    
    except Exception as e:
        log_metric_error("Rebellion Decision Ratio", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Rebellion': 0.0, 'Non-Rebellion': 1.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_sum, log_metric_error

def Resource_Utilization_Efficiency(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Resource Utilization Efficiency
    描述: Evaluates the government's effectiveness in utilizing available resources against rebellion levels.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the available_resources from the environment
        available_resources = safe_number(safe_get(data, 'available_resources'), default=None)
        
        # Access the rebellion_level list from the Government agent
        rebellion_levels = safe_list(safe_get(data, 'rebellion_level', []))
        
        # Filter out None values from the rebellion_level list
        valid_rebellion_levels = [level for level in rebellion_levels if isinstance(level, (int, float)) and level is not None]
        
        # Calculate the sum of valid rebellion levels
        total_rebellion = safe_sum(valid_rebellion_levels, default=0)
        
        # Calculate efficiency
        if available_resources is None or total_rebellion == 0:
            efficiency = 0
        else:
            efficiency = available_resources / total_rebellion
        
        # Return the result in the format suitable for a bar chart
        return {"Resource Utilization Efficiency": efficiency}
    
    except Exception as e:
        log_metric_error("Resource Utilization Efficiency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Resource Utilization Efficiency": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Grievance_Level': Average_Grievance_Level,
    'Rebellion_Decision_Ratio': Rebellion_Decision_Ratio,
    'Resource_Utilization_Efficiency': Resource_Utilization_Efficiency,
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
