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
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Case_Completion_Status_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Case Completion Status Distribution
    描述: This metric shows the distribution of cases based on their completion status, providing insights into how many cases are completed, pending, or in other states.
    可视化类型: pie

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为分类，值为对应数值比例
    """
    try:
        # Initialize a dictionary to hold the count of each status
        status_counts = {}

        # Access the completion_status variable from the environment
        completion_status_list = safe_list(safe_get(data, 'completion_status', []))

        # Count occurrences of each status
        for status in completion_status_list:
            # Handle None values by categorizing them as 'Unknown'
            if status is None:
                status = 'Unknown'
            # Increment the count for the status
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1

        # Calculate total number of statuses for proportion calculation
        total_count = sum(status_counts.values())

        # Handle division by zero scenario
        if total_count == 0:
            log_metric_error("Case Completion Status Distribution", ValueError("No valid completion status data found"), {"data_keys": list(data.keys())})
            return {}

        # Calculate proportions for pie chart
        status_proportions = {status: count / total_count for status, count in status_counts.items()}

        return status_proportions

    except Exception as e:
        log_metric_error("Case Completion Status Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Evidence_Submission_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Evidence Submission Rate
    描述: This metric tracks the rate of evidence submission by Plaintiffs, indicating how actively Plaintiffs are engaging in the process.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
        - bar: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'evidence_submitted' list from Plaintiff data
        evidence_submitted_list = safe_list(safe_get(data, 'evidence_submitted', []))
        
        # Count the number of True values indicating evidence submission
        submitted_count = safe_count(evidence_submitted_list, lambda x: x is True)
        
        # Count the number of False or None values indicating no evidence submission
        not_submitted_count = safe_count(evidence_submitted_list, lambda x: x is False or x is None)
        
        # Total number of Plaintiffs
        total_count = submitted_count + not_submitted_count
        
        # Calculate submission rate percentage
        if total_count == 0:
            submission_rate = 0.0  # Avoid division by zero
        else:
            submission_rate = (submitted_count / total_count) * 100

        # Prepare result for bar chart visualization
        result = {
            'Submitted': submission_rate,
            'Not Submitted': 100 - submission_rate
        }
        
        return result

    except Exception as e:
        log_metric_error("Evidence Submission Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Submitted': 0.0, 'Not Submitted': 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Judgment_Result_Trends(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: Judgment Result Trends
    描述: This metric shows the trend of different judgment results over time, providing insights into the outcomes of cases.
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
        # Initialize a dictionary to hold counts of each judgment result
        judgment_trends = {}

        # Access the judgment_result variable from the environment
        judgment_results = safe_list(safe_get(data, 'judgment_result', []))

        # Iterate through each result and count occurrences
        for result in judgment_results:
            if result is None:
                result = 'Undecided'
            if not isinstance(result, str):
                log_metric_error("Judgment Result Trends", TypeError(f"Invalid type for judgment result: {type(result)}"), {"result": result})
                continue
            if result not in judgment_trends:
                judgment_trends[result] = 0
            judgment_trends[result] += 1

        # Return the trends as a dictionary suitable for a line chart
        return judgment_trends

    except Exception as e:
        log_metric_error("Judgment Result Trends", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Undecided": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Case_Completion_Status_Distribution': Case_Completion_Status_Distribution,
    'Evidence_Submission_Rate': Evidence_Submission_Rate,
    'Judgment_Result_Trends': Judgment_Result_Trends,
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
