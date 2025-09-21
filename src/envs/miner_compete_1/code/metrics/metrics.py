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
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Total_System_Resource_Count(data: Dict[str, Any]) -> Any:
    """
    计算指标: Total System Resource Count
    描述: Total resources held by all ResourceMiner agents at a given point in time.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为系列名称，值为对应数值
    """
    try:
        if not data or not isinstance(data, dict):
            log_metric_error("Total System Resource Count", ValueError("Invalid data input"), {"data": data})
            return {"default": 0}

        # Access the resource_count for ResourceMiner agents
        resource_counts = safe_list(safe_get(data, 'resource_count', []))

        # Ensure all counts are numbers and ignore None values
        valid_counts = [value for value in (safe_get(agent, None) for agent in resource_counts) if value is not None]
        
        # Sum the resource counts
        total_resources = safe_sum(valid_counts)

        # Prepare the result dictionary for line visualization
        result = {"Total Resources": total_resources}
        
        return result
    
    except Exception as e:
        log_metric_error("Total System Resource Count", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"default": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_count, log_metric_error

def Land_Ownership_Contest_Dynamics(data: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate metric: Land Ownership Contest Dynamics
    Description: Determines the frequency of contests and success rate of land acquisition among miners.
    Visualization Type: bar

    Args:
        data: Dictionary containing all variables collected by the monitor. Agent variables are lists.

    Returns:
        A dictionary with categories 'Total Contests' and 'Successful Contests' as keys and their respective counts as values.

    Notes:
        The function handles various exceptional cases, including None values, empty lists, and type errors.
    """
    try:
        # Accessing the 'competition_result' from the environment
        competition_result = safe_get(data, 'competition_result')

        # Initialize contest counters
        total_contests = 0
        successful_contests = 0

        # Validate competition_result
        if competition_result and isinstance(competition_result, dict):
            # Total contests is simply the number of entries in the competition_result dictionary
            total_contests = len(competition_result)

            # Successful contests are those where the value indicates a win (assuming a win means True or a specific value)
            successful_contests = safe_count(competition_result.values(), lambda v: v is True or v == 'win')

        # Return results for bar chart
        return {
            "Total Contests": total_contests,
            "Successful Contests": successful_contests
        }

    except Exception as e:
        log_metric_error("Land Ownership Contest Dynamics", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get,
    safe_list,
    safe_sum,
    safe_count,
    log_metric_error
)

def Agent_Resource_Utilization_Efficiency(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute the Agent Resource Utilization Efficiency metric.
    Description: Average resources utilized per ResourceMiner agent based on their current land ownership.
    Visualization Type: line
    
    Args:
        data: Dictionary containing all the variables collected by the monitor.
        
    Returns:
        A dictionary where each key represents a data series (e.g., 'average_utilization') for line visualization.
    """
    try:
        # Safely retrieve the list of 'resource_count' values from the data
        resource_count_list = safe_list(safe_get(data, 'resource_count', []))

        # Filter out None values and convert all valid entries to numbers
        valid_resource_counts = [safe_get({'value': val}, 'value') for val in resource_count_list if val is not None]
        valid_resource_counts = [x for x in valid_resource_counts if isinstance(x, int)]
        
        # Calculate the sum of resources used and count of valid entries
        total_resources = safe_sum(valid_resource_counts)
        num_agents = safe_count(valid_resource_counts)
        
        # Calculate average, handling division by zero
        average_utilization = total_resources / num_agents if num_agents > 0 else 0
        
        # Result suitable for line visualization
        result = {'average_utilization': average_utilization}
        return result

    except Exception as e:
        # Log any exception that occurs during processing
        log_metric_error("Agent Resource Utilization Efficiency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        # Return a default result for error robustness
        return {'average_utilization': 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Total_System_Resource_Count': Total_System_Resource_Count,
    'Land_Ownership_Contest_Dynamics': Land_Ownership_Contest_Dynamics,
    'Agent_Resource_Utilization_Efficiency': Agent_Resource_Utilization_Efficiency,
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
