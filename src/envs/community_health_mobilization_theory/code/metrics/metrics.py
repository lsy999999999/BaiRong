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

def Community_Mobilization_Status(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Community Mobilization Status
    描述: Tracks the proportion of community leaders actively engaged in mobilization activities.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类（'Active', 'Inactive'），值为对应计数
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the mobilization_status list from the data
        mobilization_status_list = safe_list(safe_get(data, 'mobilization_status', []))

        # Define predicates for counting active and inactive statuses
        def is_active(status):
            return status == 'active'

        def is_inactive(status):
            return status is None or status != 'active'

        # Count active and inactive statuses
        active_count = safe_count(mobilization_status_list, is_active)
        inactive_count = safe_count(mobilization_status_list, is_inactive)

        # Return the result as a dictionary suitable for a pie chart
        result = {
            'Active': active_count,
            'Inactive': inactive_count
        }
        return result

    except Exception as e:
        log_metric_error("Community Mobilization Status", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Active': 0, 'Inactive': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Community_Participation_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Community Participation Rate
    描述: Measures the average participation rate of community members in health mobilization activities.
    可视化类型: bar

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值，适用于bar图表。
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等。
    """
    try:
        # Access the participation_status list safely
        participation_status_list = safe_list(safe_get(data, 'participation_status', []))
        
        if not participation_status_list:
            # If the list is empty, log an error and return a default value
            log_metric_error("Community Participation Rate", ValueError("Participation status list is empty or not found"), {"data": data})
            return {"Participation Rate": 0.0}
        
        # Count the number of 'participating' statuses
        participating_count = safe_count(participation_status_list, lambda status: status == 'participating')
        
        # Calculate the participation rate
        total_count = len(participation_status_list)
        
        if total_count == 0:
            # Handle division by zero if the list is empty
            log_metric_error("Community Participation Rate", ZeroDivisionError("Total count of members is zero"), {"data": data})
            return {"Participation Rate": 0.0}
        
        participation_rate = (participating_count / total_count) * 100
        
        return {"Participation Rate": participation_rate}
    
    except Exception as e:
        # Log any unexpected errors
        log_metric_error("Community Participation Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Participation Rate": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Guidance_Provision_Status(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Guidance Provision Status
    描述: Analyzes the distribution of guidance statuses provided by public health experts.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为指导状态（包括'None'），值为对应计数
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Accessing the guidance_status variable from PublicHealthExpert
        guidance_status_list = safe_list(safe_get(data, 'guidance_status', []))

        # Initialize a dictionary to count occurrences of each status
        status_count = {}

        # Iterate over the list and count each unique status
        for status in guidance_status_list:
            # Handle None values by categorizing them under 'None'
            if status is None:
                status = 'None'
            
            # Count occurrences of each status
            if status in status_count:
                status_count[status] += 1
            else:
                status_count[status] = 1

        return status_count

    except Exception as e:
        log_metric_error("Guidance Provision Status", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Community_Mobilization_Status': Community_Mobilization_Status,
    'Community_Participation_Rate': Community_Participation_Rate,
    'Guidance_Provision_Status': Guidance_Provision_Status,
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
