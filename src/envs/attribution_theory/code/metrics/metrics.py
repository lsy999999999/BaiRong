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

def Attribution_Type_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate the Attribution Type Distribution metric.
    Description: Proportion of internal vs external attributions made by Participant A.
    Visualization Type: pie

    Args:
        data: A dictionary containing all variables collected by the monitor.

    Returns:
        A dictionary where keys are attribution types ('internal', 'external') and values are their proportions.
    """
    try:
        # Attempt to retrieve the attribution_type list from the data dictionary
        attribution_type_list = safe_list(safe_get(data, 'attribution_type', []))

        # Filter out None values from the list
        # valid_attributions = [attr for attr in attribution_type_list if attr is not None]


        results = {}
        for x in attribution_type_list:
            if x not in results.keys():
                results[x] = 1
            else:
                results[x] += 1
        
        return results

        # # Handle empty list scenario
        # if not valid_attributions:
        #     return {}

        # # Count occurrences of each attribution type
        # internal_count = safe_count(valid_attributions, lambda x: x == 'internal')
        # external_count = safe_count(valid_attributions, lambda x: x == 'external')

        # # Calculate total valid attributions
        # total_valid_attributions = internal_count + external_count

        # # Handle division by zero scenario
        # if total_valid_attributions == 0:
        #     return {}

        # # Calculate proportions
        # internal_proportion = internal_count / total_valid_attributions
        # external_proportion = external_count / total_valid_attributions

        # # Return the result as a dictionary suitable for pie chart visualization
        # return {
        #     'internal': internal_proportion,
        #     'external': external_proportion
    #     # }

    except Exception as e:
        log_metric_error("Attribution Type Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Bias_Detection_Frequency(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Bias Detection Frequency
    描述: Frequency of bias detection by Feedbacker C over time.
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
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Bias Detection Frequency", ValueError("Invalid data input"), {"data": data})
            return {"default": 0}

        # Access the bias_detected variable from FeedbackerC
        bias_detected_list = safe_list(safe_get(data, 'bias_detected', []))

        # Count the number of times bias is detected, treating None as 'no bias detected'
        bias_count = safe_count(bias_detected_list, lambda x: x is True)

        # Return result in the format suitable for line visualization
        result = {"Bias Detection Frequency": bias_count}
        return result

    except Exception as e:
        log_metric_error("Bias Detection Frequency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"default": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Behavior_Type_Analysis(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Behavior Type Analysis
    描述: Distribution of different behavior types exhibited by Participant B.
    可视化类型: bar

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为行为类型，值为对应的计数
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'behavior_type' list for Participant B
        behavior_types = safe_list(safe_get(data, 'behavior_type', []))

        # Initialize an empty dictionary to store the count of each behavior type
        behavior_count = {}

        # Iterate over the list and count occurrences of each behavior type
        for behavior in behavior_types:
            if behavior is not None and isinstance(behavior, str):
                if behavior in behavior_count:
                    behavior_count[behavior] += 1
                else:
                    behavior_count[behavior] = 1

        return behavior_count

    except Exception as e:
        # Log any exceptions that occur during processing
        log_metric_error("Behavior Type Analysis", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Attribution_Type_Distribution': Attribution_Type_Distribution,
    'Bias_Detection_Frequency': Bias_Detection_Frequency,
    'Behavior_Type_Analysis': Behavior_Type_Analysis,
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
