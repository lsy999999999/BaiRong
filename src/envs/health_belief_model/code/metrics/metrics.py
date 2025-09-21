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

def average_perceived_threat_level(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: average_perceived_threat_level
    描述: Measures the average perceived threat level across all IndividualAgents, indicating overall perception of health threats in the system.
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
        # Accessing perceived_threat_level from IndividualAgent
        perceived_threat_levels = safe_list(safe_get(data, 'perceived_threat_level', []))
        
        # Calculate the average perceived threat level, handling None and empty lists
        average_threat_level = safe_avg(perceived_threat_levels, default=0)
        
        # Return result in the appropriate format for a line chart
        return {'average_perceived_threat_level': average_threat_level}
    
    except Exception as e:
        log_metric_error("average_perceived_threat_level", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'average_perceived_threat_level': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def policy_impact_distribution(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: policy_impact_distribution
    描述: Shows the distribution of policy impact across GovernmentAgents, providing insights into how various policies are influencing health behaviors.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - bar: 返回字典，键为分类，值为对应数值
    """
    try:
        # Access the 'policy_impact' variable from the data dictionary
        policy_impact_values = safe_list(safe_get(data, 'policy_impact', []))
        
        # Initialize bins for categorizing policy impacts
        impact_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0
        }
        
        # Categorize policy impacts into bins
        for impact in policy_impact_values:
            if impact is None:
                continue  # Skip None values
            try:
                impact_value = float(impact)
                if impact_value < 3.0:
                    impact_distribution['low'] += 1
                elif 3.0 <= impact_value < 7.0:
                    impact_distribution['medium'] += 1
                else:
                    impact_distribution['high'] += 1
            except (ValueError, TypeError):
                log_metric_error("policy_impact_distribution", ValueError("Invalid impact value"), {"impact": impact})
        
        return impact_distribution

    except Exception as e:
        log_metric_error("policy_impact_distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'low': 0, 'medium': 0, 'high': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def behavior_adoption_success_rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: behavior_adoption_success_rate
    描述: Tracks the success rate of adopted health behaviors among IndividualAgents, indicating the effectiveness of health belief factors in behavior change.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应比例，适用于饼图
    """
    try:
        # Access the 'adoption_success' list from the data
        adoption_success_list = safe_list(safe_get(data, 'adoption_success', []))

        # Count the number of successful and unsuccessful adoptions
        success_count = safe_count(adoption_success_list, lambda x: x is True)
        failure_count = safe_count(adoption_success_list, lambda x: x is False)

        # Calculate total valid entries
        total_count = success_count + failure_count

        # Handle division by zero and return equal proportions if the list is empty
        if total_count == 0:
            return {"Success": 0.5, "Failure": 0.5}

        # Calculate proportions
        success_rate = success_count / total_count
        failure_rate = failure_count / total_count

        # Return the result as a dictionary for pie chart visualization
        return {"Success": success_rate, "Failure": failure_rate}

    except Exception as e:
        log_metric_error("behavior_adoption_success_rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Success": 0.5, "Failure": 0.5}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'average_perceived_threat_level': average_perceived_threat_level,
    'policy_impact_distribution': policy_impact_distribution,
    'behavior_adoption_success_rate': behavior_adoption_success_rate,
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
