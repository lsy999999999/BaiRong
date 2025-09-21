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
from onesim.monitor.utils import safe_get, safe_list, safe_avg, log_metric_error

def Average_Utility_Value(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Utility Value
    描述: This metric measures the average utility value across all UtilityEvaluator agents, providing insight into overall satisfaction or effectiveness of decision-making.
    可视化类型: line

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为系列名称，值为对应数值
    """
    try:
        # Access the list of utility values for UtilityEvaluator agents
        utility_values = safe_list(safe_get(data, 'utility_value', []))
        
        # Filter out None values
        filtered_values = [value for value in utility_values if value is not None]

        # Calculate the average utility value using safe_avg
        average_utility = safe_avg(filtered_values, default=0)
        
        # Return the result in the appropriate format for a line chart
        return {'Average Utility Value': average_utility}
    
    except Exception as e:
        log_metric_error("Average Utility Value", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Average Utility Value": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Decision_Option_Selection_Distribution(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Decision Option Selection Distribution
    描述: This metric shows the distribution of selected decisions among RationalDecisionMaker agents, indicating which options are most preferred or frequently chosen.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Access the 'selected_decision' list from RationalDecisionMaker agents
        selected_decisions = safe_list(safe_get(data, 'selected_decision', []))
        
        # Initialize a dictionary to count occurrences of each decision
        decision_counts = {}

        # Iterate over the selected decisions to count occurrences
        for decision in selected_decisions:
            if decision is not None and isinstance(decision, str):
                if decision in decision_counts:
                    decision_counts[decision] += 1
                else:
                    decision_counts[decision] = 1

        return decision_counts
    except Exception as e:
        log_metric_error("Decision Option Selection Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Agent_Adjustment_Status_Proportion(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate the Agent Adjustment Status Proportion metric.
    Description: This metric measures the proportion of SocialNetworkInteractor agents in different adjustment statuses, showing how agents adapt their strategies based on social interactions.
    Visualization Type: pie
    
    Args:
        data: A dictionary containing all collected variables, with agent variables in list form.
        
    Returns:
        A dictionary where keys are adjustment statuses and values are their proportions for pie chart visualization.
    """
    try:
        # Retrieve the adjustment_status list from the data
        adjustment_status_list = safe_list(safe_get(data, 'adjustment_status', []))
        
        # Filter out None values from the list
        filtered_status_list = [status for status in adjustment_status_list if status is not None]
        
        # If the list is empty after filtering, return an empty dictionary
        if not filtered_status_list:
            return {}

        # Calculate occurrences of each unique status
        status_count = {}
        total_count = len(filtered_status_list)

        for status in filtered_status_list:
            if not isinstance(status, str):
                log_metric_error("Agent Adjustment Status Proportion", TypeError("Invalid type in adjustment_status list"), {"status": status})
                continue
            if status in status_count:
                status_count[status] += 1
            else:
                status_count[status] = 1

        # Calculate proportions
        status_proportion = {status: count / total_count for status, count in status_count.items()}

        return status_proportion

    except Exception as e:
        log_metric_error("Agent Adjustment Status Proportion", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Utility_Value': Average_Utility_Value,
    'Decision_Option_Selection_Distribution': Decision_Option_Selection_Distribution,
    'Agent_Adjustment_Status_Proportion': Agent_Adjustment_Status_Proportion,
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
