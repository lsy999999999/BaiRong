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
    safe_get, safe_number, safe_list, safe_avg, log_metric_error
)

def average_voter_political_preference_change(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate the metric: average_voter_political_preference_change.
    Description: Measures the average change in voters' political preferences after consuming media content.
    Visualization Type: line

    Args:
        data: Dictionary containing all variables collected by the monitor. Note that agent variables are lists.

    Returns:
        A dictionary suitable for line chart visualization, with series names as keys and values as data points.

    Note:
        This function handles various edge cases, including None values, empty lists, and type errors.
    """
    try:
        # Retrieve the lists of current and adjusted political preferences
        current_preferences = safe_list(safe_get(data, 'current_political_preference', []))
        adjusted_preferences = safe_list(safe_get(data, 'adjusted_political_preference', []))

        if not current_preferences or not adjusted_preferences:
            log_metric_error("average_voter_political_preference_change", ValueError("Missing or empty preference lists"), {"data_keys": list(data.keys())})
            return {"average_change": 0.0}

        # Calculate the change in political preferences
        changes = []
        for current, adjusted in zip(current_preferences, adjusted_preferences):
            if current is not None and adjusted is not None:
                try:
                    current_value = safe_number(current)
                    adjusted_value = safe_number(adjusted)
                    changes.append(adjusted_value - current_value)
                except (TypeError, ValueError) as e:
                    log_metric_error("average_voter_political_preference_change", e, {"current": current, "adjusted": adjusted})

        # Calculate the average change
        average_change = safe_avg(changes, default=0.0)

        return {"average_change": average_change}

    except Exception as e:
        log_metric_error("average_voter_political_preference_change", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"average_change": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def media_bias_distribution(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: media_bias_distribution
    描述: Shows the distribution of media bias scores across available media sources.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Access media_bias_score list from MediaAgent
        media_bias_scores = safe_list(safe_get(data, 'media_bias_score', []))

        # Define bias categories
        bias_categories = {
            'low': lambda score: score < 0.3,
            'medium': lambda score: 0.3 <= score < 0.7,
            'high': lambda score: score >= 0.7
        }

        # Initialize category counts
        category_counts = {category: 0 for category in bias_categories}

        # Count occurrences in each category, excluding None values
        for score in media_bias_scores:
            if score is None:
                continue
            for category, condition in bias_categories.items():
                if condition(score):
                    category_counts[category] += 1

        return category_counts

    except Exception as e:
        log_metric_error("media_bias_distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def voter_media_selection_count(data: Dict[str, Any]) -> Dict[int, int]:
    """
    计算指标: voter_media_selection_count
    描述: Counts how many voters have selected each media source, indicating preference alignment.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为媒体源ID，值为选中次数
    """
    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("voter_media_selection_count", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve the list of selected media IDs from VoterAgent
        selected_media_ids = safe_list(safe_get(data, 'selected_media_id', []))
        
        # Retrieve available media sources from the environment
        available_media_sources = safe_list(safe_get(data, 'available_media_sources', []))

        # Check if the media sources list is empty
        if not available_media_sources:
            log_metric_error("voter_media_selection_count", ValueError("No available media sources"), {"available_media_sources": available_media_sources})
            return {}

        # Initialize a dictionary to count selections
        media_selection_count = {media_id: 0 for media_id in available_media_sources}

        # Count occurrences of each valid media ID
        for media_id in selected_media_ids:
            if media_id in media_selection_count:
                media_selection_count[media_id] += 1

        return media_selection_count

    except Exception as e:
        log_metric_error("voter_media_selection_count", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'average_voter_political_preference_change': average_voter_political_preference_change,
    'media_bias_distribution': media_bias_distribution,
    'voter_media_selection_count': voter_media_selection_count,
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
