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
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_sum, log_metric_error

def Family_Education_Investment_Ratio(data: Dict[str, Any]) -> Any:
    """
    计算指标: Family Education Investment Ratio
    描述: This metric measures the ratio of resources allocated to education versus total collective resources within families, indicating the prioritization of educational investments.
    可视化类型: pie
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Validate data input
        if not data or not isinstance(data, dict):
            log_metric_error("Family Education Investment Ratio", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve and validate the list of collective resources and education investments
        collective_resources_list = safe_list(safe_get(data, "collective_resources", []))
        education_investment_list = safe_list(safe_get(data, "education_investment", []))

        # Check if lists are empty
        if not collective_resources_list or not education_investment_list:
            log_metric_error("Family Education Investment Ratio", ValueError("Empty lists for required variables"), {
                "collective_resources_list": collective_resources_list,
                "education_investment_list": education_investment_list
            })
            return {}

        # Initialize total variables
        total_collective_resources = 0
        total_education_investment = 0

        # Calculate ratios and aggregate totals
        for collective_resources, education_investment in zip(collective_resources_list, education_investment_list):
            # Safely convert values to numbers
            collective_resources = safe_number(collective_resources, None)
            education_investment = safe_number(education_investment, None)

            # Skip invalid entries
            if collective_resources is None or education_investment is None or collective_resources == 0:
                continue

            # Aggregate totals
            total_collective_resources += collective_resources
            total_education_investment += education_investment

        # Calculate the overall ratio
        if total_collective_resources == 0:
            log_metric_error("Family Education Investment Ratio", ZeroDivisionError("Total collective resources is zero"), {
                "total_collective_resources": total_collective_resources,
                "total_education_investment": total_education_investment
            })
            return {}

        # Return the ratio in pie chart format as a proportion
        return {
            "Education Investment": total_education_investment / total_collective_resources,
            "Other Resources": 1 - (total_education_investment / total_collective_resources)
        }

    except Exception as e:
        log_metric_error("Family Education Investment Ratio", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error


def Student_Candidate_Selection_Effectiveness(data: Dict[str, Any]) -> Any:
    """
    计算指标: Student Candidate Selection Effectiveness
    描述: This metric evaluates the effectiveness of employers in selecting candidates by comparing the number of candidates evaluated versus those hired.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid data input")

        # Retrieve candidates_list and hiring_decision
        candidates_list = safe_list(safe_get(data, "all_applications_received", []))
        hiring_decisions = safe_list(safe_get(data, "all_selected_students", []))


        # Count candidates and successful hiring decisions
        total_candidates, successful_hires = 0, 0
        for x in candidates_list:
            total_candidates += len(x)
        for x in hiring_decisions:
            successful_hires += len(x)
            
        # total_candidates = safe_count(candidates_list)
        # successful_hires = safe_count(hiring_decisions)

        # # Calculate effectiveness ratio
        if total_candidates == 0:
            return 0.0  # Avoid division by zero
        
        effectiveness_ratio = successful_hires / total_candidates

        # return effectiveness_ratio
        return {"Average Effectiveness Ratio": effectiveness_ratio}
        # return successful_hires

    except Exception as e:
        log_metric_error("Student Candidate Selection Effectiveness", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0.0


# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Family_Education_Investment_Ratio': Family_Education_Investment_Ratio,
    'Student_Candidate_Selection_Effectiveness': Student_Candidate_Selection_Effectiveness,
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

