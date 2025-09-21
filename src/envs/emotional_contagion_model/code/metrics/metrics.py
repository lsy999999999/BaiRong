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

def Average_Emotional_Intensity(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Emotional Intensity
    描述: Measures the average intensity of emotions communicated by agents in the system.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为系列名称，值为对应数值
    """
    try:
        # Access the 'intensity' variable from CommunicationAgent
        intensity_values = safe_list(safe_get(data, 'intensity', []))

        # Calculate average intensity using safe_avg
        average_intensity = safe_avg(intensity_values, default=0)

        # Return result in the format suitable for line visualization
        return {'Average Emotional Intensity': average_intensity}
    except Exception as e:
        log_metric_error("Average Emotional Intensity", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Average Emotional Intensity': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Emotional_State_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Emotional State Distribution
    描述: Shows the proportion of agents in different emotional states to understand the emotional atmosphere of the group.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为情绪状态，值为对应比例
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'emotional_state' variable from IndividualAgent
        emotional_states = safe_list(safe_get(data, 'emotional_state', []))
        
        # Filter out None and non-string values
        valid_emotional_states = [state for state in emotional_states if isinstance(state, str) and state is not None]

        # Count occurrences of each emotional state
        state_count = {}
        for state in valid_emotional_states:
            if state in state_count:
                state_count[state] += 1
            else:
                state_count[state] = 1

        # Calculate total number of valid entries
        total_valid_states = len(valid_emotional_states)

        # Handle division by zero
        if total_valid_states == 0:
            log_metric_error("Emotional State Distribution", ValueError("No valid emotional states found"))
            return {}

        # Calculate proportions
        state_proportions = {state: count / total_valid_states for state, count in state_count.items()}

        return state_proportions

    except Exception as e:
        log_metric_error("Emotional State Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Contact_Frequency_Analysis(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Contact Frequency Analysis
    描述: Evaluates the frequency of interactions between agents to assess communication patterns.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Define bins for categorizing frequency of contact
        bins = {
            "low": (0, 5),
            "medium": (6, 15),
            "high": (16, float('inf'))
        }
        
        # Initialize results dictionary with bin categories
        result = {bin_name: 0 for bin_name in bins}

        # Access frequency_of_contact data from CommunicationAgent
        frequency_of_contact_list = safe_list(safe_get(data, 'frequency_of_contact', []))
        
        # Iterate over the list and categorize frequencies
        for frequency in frequency_of_contact_list:
            try:
                # Convert frequency to a number safely
                freq_value = safe_get({"value": frequency}, "value")
                if freq_value is None:
                    continue
                
                # Determine the appropriate bin for the frequency value
                for bin_name, (low, high) in bins.items():
                    if low <= freq_value <= high:
                        result[bin_name] += freq_value
                        break
            
            except Exception as inner_error:
                log_metric_error("Contact Frequency Analysis", inner_error, {"frequency": frequency})
                continue

        return result

    except Exception as e:
        log_metric_error("Contact Frequency Analysis", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {bin_name: 0 for bin_name in bins}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Emotional_Intensity': Average_Emotional_Intensity,
    'Emotional_State_Distribution': Emotional_State_Distribution,
    'Contact_Frequency_Analysis': Contact_Frequency_Analysis,
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
