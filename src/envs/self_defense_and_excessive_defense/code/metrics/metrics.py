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
    safe_get,
    safe_list,
    safe_sum,
    safe_count,
    log_metric_error
)

def Average_Threat_Level(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates the metric: Average Threat Level
    Description: Measures the average threat level posed by aggressors in the scenario.
    Visualization Type: line

    Args:
        data: Dictionary containing all variables collected by the monitor.

    Returns:
        For line visualization type: Returns a dictionary with series names as keys and values as data points.
    """
    try:
        # Access the 'threat_level' data for Aggressors
        threat_levels = safe_list(safe_get(data, 'threat_level', []))

        # Filter out non-integer and None values
        valid_threat_levels = [level for level in threat_levels if isinstance(level, int)]

        # Calculate the average threat level
        total_threat = safe_sum(valid_threat_levels)
        count = safe_count(valid_threat_levels)

        # Avoid division by zero
        average_threat_level = total_threat / count if count > 0 else 0

        # Return the result in the appropriate format for a line chart
        return {"Average Threat Level": average_threat_level}
    except Exception as e:
        log_metric_error("Average Threat Level", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Average Threat Level": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Defense_Action_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Defense Action Distribution
    描述: Shows the distribution of different types of defensive actions taken by defenders.
    可视化类型: pie

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为防御动作类型，值为对应比例
    """
    try:
        # Accessing the list of defensive actions
        defensive_action_types = safe_list(safe_get(data, 'defensive_action_type', []))

        # Filter out None values and count occurrences of each action type
        action_counts = {}
        for action in defensive_action_types:
            if action is not None:
                action_counts[action] = action_counts.get(action, 0) + 1

        # Calculate total number of valid actions
        total_actions = sum(action_counts.values())

        # Handle division by zero and prepare the result
        if total_actions == 0:
            return {}

        # Calculate proportions for the pie chart
        distribution = {action: count / total_actions for action, count in action_counts.items()}

        return distribution

    except Exception as e:
        log_metric_error("Defense Action Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Judgment_Result_Summary(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Judgment Result Summary
    描述: Summarizes the results of judgments made by the judge, indicating the frequency of different outcomes.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典
    
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Extract the judgment_result list safely
        judgment_results = safe_list(safe_get(data, 'judgment_result'))
        
        # Initialize a dictionary to store the frequency of each judgment result
        result_summary = {}
        
        # Iterate over the judgment results and count occurrences, ignoring None values
        for result in judgment_results:
            if result is not None and isinstance(result, str):  # Ensure valid string type
                if result in result_summary:
                    result_summary[result] += 1
                else:
                    result_summary[result] = 1

        return result_summary
    
    except Exception as e:
        log_metric_error("Judgment Result Summary", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Threat_Level': Average_Threat_Level,
    'Defense_Action_Distribution': Defense_Action_Distribution,
    'Judgment_Result_Summary': Judgment_Result_Summary,
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
