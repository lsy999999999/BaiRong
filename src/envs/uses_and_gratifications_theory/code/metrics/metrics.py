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

def average_satisfaction_level(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: average_satisfaction_level
    描述: Measures the average satisfaction level of AudienceAgents with the media they consume.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'satisfaction_level' variable from the data
        satisfaction_levels = safe_list(safe_get(data, 'satisfaction_level', []))

        # Calculate the average satisfaction level
        average_satisfaction = safe_avg(satisfaction_levels, default=0)

        # Return the result formatted for a line visualization
        return {'average_satisfaction_level': average_satisfaction}

    except Exception as e:
        # Log any exceptions that occur during the calculation
        log_metric_error("average_satisfaction_level", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'average_satisfaction_level': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def media_type_selection_distribution(data: Dict[str, Any]) -> Dict[int, int]:
    """
    计算指标: media_type_selection_distribution
    描述: Shows the distribution of selected media types by AudienceAgents.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为媒体类型ID，值为选择次数
    """
    try:
        # Access the 'selected_media' variable from AudienceAgents
        selected_media_list = safe_list(safe_get(data, 'selected_media', []))
        
        # Initialize the result dictionary
        media_distribution = {}

        # Count the occurrences of each media type ID in the selected_media list
        for media_id in selected_media_list:
            if media_id is None or not isinstance(media_id, int):
                continue  # Ignore None values and non-integer types
            if media_id in media_distribution:
                media_distribution[media_id] += 1
            else:
                media_distribution[media_id] = 1

        return media_distribution

    except Exception as e:
        log_metric_error("media_type_selection_distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_number, safe_list, safe_sum,
    safe_avg, safe_max, safe_min, safe_count, log_metric_error
)
import numpy as np

def feedback_satisfaction_correlation(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: feedback_satisfaction_correlation
    描述: Analyzes the correlation between feedback history and satisfaction levels of AudienceAgents.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为系列名称，值为对应数值
    """
    try:
        # Access the agent variables
        satisfaction_levels = safe_list(safe_get(data, 'satisfaction_level', []))
        feedback_histories = safe_list(safe_get(data, 'feedback_history', []))

        # Initialize the result dictionary
        correlation_results = {}

        # Check if both lists are of the same length
        if len(satisfaction_levels) != len(feedback_histories):
            log_metric_error("feedback_satisfaction_correlation", ValueError("Mismatched list lengths"), {
                "satisfaction_levels_length": len(satisfaction_levels),
                "feedback_histories_length": len(feedback_histories)
            })
            return {"default": 0}

        # Calculate correlation for each agent
        for i, (satisfaction, feedback) in enumerate(zip(satisfaction_levels, feedback_histories)):
            # Ensure both satisfaction and feedback are lists and not empty
            feedback = safe_list(feedback)
            if feedback is None or satisfaction is None or len(feedback) == 0:
                correlation_results[f"agent_{i}"] = 0  # Default correlation value
                continue

            try:
                # Convert satisfaction to a list for consistency
                satisfaction_values = [safe_number(satisfaction)]
                feedback_values = [safe_number(f) for f in feedback if f is not None]

                # Calculate correlation using numpy if possible
                if len(feedback_values) > 1:
                    correlation = np.corrcoef(satisfaction_values * len(feedback_values), feedback_values)[0, 1]
                else:
                    correlation = 0  # Not enough data to calculate correlation

                # Store the result
                correlation_results[f"agent_{i}"] = correlation
            except Exception as e:
                log_metric_error("feedback_satisfaction_correlation", e, {"agent_index": i})
                correlation_results[f"agent_{i}"] = 0  # Default correlation value in case of error

        return correlation_results

    except Exception as e:
        log_metric_error("feedback_satisfaction_correlation", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"default": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'average_satisfaction_level': average_satisfaction_level,
    'media_type_selection_distribution': media_type_selection_distribution,
    'feedback_satisfaction_correlation': feedback_satisfaction_correlation,
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
