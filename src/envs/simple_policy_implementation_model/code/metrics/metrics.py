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

def Government_Policy_Efficiency(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Government Policy Efficiency
    描述: Measures the average efficiency of government policy execution.
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
        # Access the efficiency_metrics list from the Government agent
        efficiency_metrics = safe_list(safe_get(data, 'efficiency_metrics', []))

        # Calculate the average efficiency, handling empty lists and None values
        average_efficiency = safe_avg(efficiency_metrics)

        # Return the result as a dictionary suitable for line visualization
        # return {'Government Policy Efficiency': average_efficiency}
        return average_efficiency

    except Exception as e:
        log_metric_error("Government Policy Efficiency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Government Policy Efficiency': 0.0}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_list, safe_avg, log_metric_error
)

def Citizen_Policy_Acceptance(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Citizen Policy Acceptance
    描述: Represents the average level of citizen acceptance towards government policies.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        line: 返回字典，键为系列名称，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Validate the input data
        if not data or not isinstance(data, dict):
            log_metric_error("Citizen Policy Acceptance", ValueError("Invalid data input"), {"data": data})
            return {"average_acceptance": 0}

        # Access the 'acceptance_level' variable from the Citizens agent
        acceptance_levels = safe_list(safe_get(data, 'satisfaction_level', []))

        # Calculate the average acceptance level, excluding None values
        average_acceptance = safe_avg(acceptance_levels, default=0)

        # Return result in appropriate format for line visualization
        # return {"average_acceptance": average_acceptance}
        return average_acceptance

    except Exception as e:
        log_metric_error("Citizen Policy Acceptance", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"average_acceptance": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Policy_Strength_Adjustment_Reasons(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Policy Strength Adjustment Reasons
    描述: Analyzes the reasons for adjustments in policy strength by the government.
    可视化类型: bar

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为分类，值为对应数值

    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Initialize the result dictionary
        result = {}

        # Retrieve the adjustment reasons list from the data dictionary
        adjustment_reasons = safe_list(safe_get(data, 'adjustment_reason'))

        # Validate the adjustment_reasons list
        if not adjustment_reasons:
            log_metric_error("Policy Strength Adjustment Reasons", ValueError("Adjustment reasons list is empty or missing"), {"data": data})
            return result
        
        # Count occurrences of each adjustment reason
        for reason in adjustment_reasons:
            if reason is None or not isinstance(reason, str):
                # Log error for invalid reason type
                log_metric_error("Policy Strength Adjustment Reasons", ValueError("Invalid adjustment reason type"), {"reason": reason})
                continue
            
            # Increment the count for the reason in the result dictionary
            if reason in result:
                result[reason] += 1
            else:
                result[reason] = 1

        return result

    except Exception as e:
        log_metric_error("Policy Strength Adjustment Reasons", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Government_Policy_Efficiency': Government_Policy_Efficiency,
    'Citizen_Policy_Acceptance': Citizen_Policy_Acceptance,
    'Policy_Strength_Adjustment_Reasons': Policy_Strength_Adjustment_Reasons,
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
