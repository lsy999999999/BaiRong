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
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_avg, log_metric_error

def average_decision_making_time(data: Dict[str, Any]) -> Any:
    """
    计算指标: average_decision_making_time
    描述: Measures the average time taken by Decision Maker Agents to make a decision.
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
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("average_decision_making_time", ValueError("Invalid data input"), {"data": data})
            return 0

        # Retrieve decision_id and decision_result from data
        decision_ids = safe_list(safe_get(data, "decision_id"))
        decision_results = safe_list(safe_get(data, "decision_result"))

        # Check if both lists are available and have the same length
        if len(decision_ids) != len(decision_results):
            log_metric_error("average_decision_making_time", ValueError("Mismatched list lengths"), {
                "decision_ids_length": len(decision_ids),
                "decision_results_length": len(decision_results)
            })
            return 0

        # Calculate time differences
        time_differences = []
        for decision_id, decision_result in zip(decision_ids, decision_results):
            try:
                # Convert to numbers (assuming they are timestamps)
                start_time = safe_number(decision_id)
                end_time = safe_number(decision_result)

                # Calculate the time difference
                if start_time is not None and end_time is not None:
                    time_diff = end_time - start_time
                    time_differences.append(time_diff)
            except Exception as e:
                log_metric_error("average_decision_making_time", e, {
                    "decision_id": decision_id,
                    "decision_result": decision_result
                })

        # Calculate average time difference
        average_time = safe_avg(time_differences)

        # Return result as a single value for line visualization
        return average_time

    except Exception as e:
        log_metric_error("average_decision_making_time", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0

def decision_quality_distribution(data: Dict[str, Any]) -> Any:
    """
    计算指标: decision_quality_distribution
    描述: Shows the distribution of decision qualities (e.g., optimal, suboptimal) made by Decision Maker Agents.
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
        safe_get,
        safe_list,
        log_metric_error
    )

    try:
        # Validate and extract evaluation_result data
        evaluation_results = safe_get(data, "evaluation_result", default=[])
        evaluation_results = safe_list(evaluation_results)

        # Initialize a dictionary to count occurrences of each category
        category_counts = {}

        # Count occurrences of each evaluation_result category
        for result in evaluation_results:
            if result is not None and isinstance(result, str):
                if result in category_counts:
                    category_counts[result] += 1
                else:
                    category_counts[result] = 1

        # Calculate total number of valid results
        total_valid_results = sum(category_counts.values())

        # Handle division by zero scenario
        if total_valid_results == 0:
            return {}

        # Calculate proportions for pie chart
        category_proportions = {category: count / total_valid_results for category, count in category_counts.items()}

        return category_proportions

    except Exception as e:
        log_metric_error("decision_quality_distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

def information_collection_rate(data: Dict[str, Any]) -> Any:
    """
    计算指标: information_collection_rate
    描述: Measures the rate at which Decision Maker Agents collect information over time.
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
    from onesim.monitor.utils import (
        safe_get, safe_list, safe_count, log_metric_error
    )

    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("information_collection_rate", ValueError("Invalid data input"), {"data": data})
            return []
        
        collected_information = safe_list(safe_get(data, "collected_information", []))

        count = safe_count(collected_information, lambda x: x is not None and isinstance(x, str) and x != "awaiting_input")

        # Return the counts as the result for a line chart
        return count / len(collected_information)

    except Exception as e:
        log_metric_error("information_collection_rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return []

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'average_decision_making_time': average_decision_making_time,
    'decision_quality_distribution': decision_quality_distribution,
    'information_collection_rate': information_collection_rate,
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


