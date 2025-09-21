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

def Average_Compensation_Awarded(data: Dict[str, Any]) -> Any:
    """
    计算指标: Average Compensation Awarded
    描述: Measures the average compensation awarded across all cases.
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
        # Safely get the compensation_awarded values from the environment
        compensation_awarded = safe_get(data, 'compensation_awarded', None)
        
        # Check for None or invalid type for compensation_awarded
        if compensation_awarded is None or not isinstance(compensation_awarded, (float, int)):
            log_metric_error("Average Compensation Awarded", ValueError("Invalid or missing compensation_awarded"), {"data": data})
            return {"average_compensation": 0}

        # Handle the case where compensation_awarded might be a list (though it's expected as a single float)
        compensation_awarded_list = safe_list(compensation_awarded)
        
        # Calculate the average compensation awarded using safe_avg
        average_compensation = safe_avg(compensation_awarded_list, default=0)

        # Return the result as a dictionary suitable for a line chart
        return {"average_compensation": average_compensation}

    except Exception as e:
        log_metric_error("Average Compensation Awarded", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"average_compensation": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Plaintiff_Compensation_Request_Submission_Rate(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Plaintiff Compensation Request Submission Rate
    描述: Tracks the rate at which plaintiffs submit compensation requests.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类（每个原告），值为提交请求的计数。
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'compensation_request_submitted' list from the data
        submitted_requests = safe_list(safe_get(data, 'compensation_request_submitted', []))
        
        # Count the number of True values, treating None as False
        submission_rate = safe_count(submitted_requests, predicate=lambda x: x is True)
        
        # Prepare the result as a dictionary for bar chart visualization
        result = {'Plaintiffs': submission_rate}
        
        return result
    
    except Exception as e:
        log_metric_error("Plaintiff Compensation Request Submission Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Evidence_Utilization_by_Defendant(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Evidence Utilization by Defendant
    描述: Analyzes how defendants utilize counter evidence in their defense.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为证据利用比例
    """
    try:
        # Access the counter_evidence_list for the Defendant
        counter_evidence_lists = safe_list(safe_get(data, 'counter_evidence_list', []))

        # Calculate the total evidence utilization
        total_evidence_utilization = safe_sum(
            [len(safe_list(evidence)) for evidence in counter_evidence_lists]
        )

        # Handle division by zero and prepare pie chart data
        if total_evidence_utilization == 0:
            log_metric_error("Evidence Utilization by Defendant", ZeroDivisionError("Total evidence utilization is zero"), {"data_keys": list(data.keys())})
            return {"No Evidence Utilized": 1.0}

        # Calculate proportions for pie chart
        evidence_utilization_proportions = {}
        for idx, evidence in enumerate(counter_evidence_lists):
            evidence_count = len(safe_list(evidence))
            category_name = f"Defendant {idx + 1}"
            evidence_utilization_proportions[category_name] = evidence_count / total_evidence_utilization

        return evidence_utilization_proportions

    except Exception as e:
        log_metric_error("Evidence Utilization by Defendant", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Error": 1.0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Compensation_Awarded': Average_Compensation_Awarded,
    'Plaintiff_Compensation_Request_Submission_Rate': Plaintiff_Compensation_Request_Submission_Rate,
    'Evidence_Utilization_by_Defendant': Evidence_Utilization_by_Defendant,
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
