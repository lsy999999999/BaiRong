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

def Average_Customer_Satisfaction(data: Dict[str, Any]) -> Any:
    """
    计算指标: Average Customer Satisfaction
    描述: Measures the average satisfaction level of all customers in the system, indicating overall customer contentment with service and product quality.
    可视化类型: line
    更新频率: 1 秒
    
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
            log_metric_error("Average Customer Satisfaction", ValueError("Invalid data input"), {"data": data})
            return None
        
        # Extract the satisfaction list from CustomerAgent
        satisfaction_list = safe_list(safe_get(data, "satisfaction", []))
        
        # Filter out None values
        valid_satisfaction_values = [safe_number(value, None) for value in satisfaction_list if value is not None]
        
        # Check if the list is empty after filtering
        if not valid_satisfaction_values:
            return None
        
        # Calculate the average satisfaction
        average_satisfaction = safe_avg(valid_satisfaction_values, None)
        
        return average_satisfaction
    except Exception as e:
        log_metric_error("Average Customer Satisfaction", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return None

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Customer_Loyalty_Distribution(data: Dict[str, Any]) -> Any:
    """
    计算指标: Customer Loyalty Distribution
    描述: Shows the distribution of customer loyalty levels, helping to understand how many customers are loyal versus those who are not.
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
            log_metric_error("Customer Loyalty Distribution", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve the loyalty data from CustomerAgent
        loyalty_data = safe_list(data.get("CustomerAgent", {}).get("profile.loyalty"))

        # Filter out None values and ensure we have a list of numbers
        valid_loyalty_data = [value for value in loyalty_data if isinstance(value, (int, float)) and value is not None]

        # Define bins for the loyalty distribution
        bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        distribution = {f"{start}-{end}": 0 for start, end in bins}

        # Populate the distribution bins
        for loyalty_score in valid_loyalty_data:
            for start, end in bins:
                if start <= loyalty_score < end:
                    distribution[f"{start}-{end}"] += 1
                    break

        return distribution

    except Exception as e:
        log_metric_error("Customer Loyalty Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_list, safe_count, log_metric_error
)

def Purchase_Decision_Rate(data: Dict[str, Any]) -> Any:
    """
    Calculates the Purchase Decision Rate metric, which is the proportion of True values
    in the 'purchase_decision' list from CustomerAgent profiles.

    Args:
        data (Dict[str, Any]): Dictionary containing all system variables.

    Returns:
        float: The Purchase Decision Rate, or None if the input is invalid or empty.
    """
    try:
        # Validate input data structure
        if not data or not isinstance(data, dict):
            log_metric_error("Purchase Decision Rate", ValueError("Invalid data input"), {"data": data})
            return None

        # Extract CustomerAgent purchase_decision data
        # customer_agents = safe_get(data, "agents", {}).get("CustomerAgent", {})
        purchase_decisions = safe_list(safe_get(data, "purchase_decision"))

        # Handle edge cases: empty list or list consisting solely of None values
        if not purchase_decisions or all(value is None for value in purchase_decisions):
            log_metric_error("Purchase Decision Rate", ValueError("No valid purchase decisions found"), {"purchase_decisions": purchase_decisions})
            return None

        # Count True values in purchase_decisions list
        true_count = safe_count(purchase_decisions, predicate=lambda x: x is True)
        total_count = safe_count(purchase_decisions, predicate=lambda x: x is not None)

        # Handle division by zero scenario
        if total_count == 0:
            log_metric_error("Purchase Decision Rate", ZeroDivisionError("Division by zero when calculating rate"), {"purchase_decisions": purchase_decisions})
            return None

        # Calculate the purchase decision rate
        purchase_decision_rate = true_count / total_count

        # Return the result (single value as visualization type is "line")
        return purchase_decision_rate

    except Exception as e:
        # Log any unexpected errors with context
        log_metric_error("Purchase Decision Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return None

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Customer_Satisfaction': Average_Customer_Satisfaction,
    'Customer_Loyalty_Distribution': Customer_Loyalty_Distribution,
    'Purchase_Decision_Rate': Purchase_Decision_Rate,
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

