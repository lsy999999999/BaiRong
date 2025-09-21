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
from onesim.monitor.utils import safe_get, safe_list, safe_sum, safe_count, log_metric_error

def Average_Precedents_Interpreted_Per_Judge(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Precedents Interpreted Per Judge
    描述: Measures the average number of precedents interpreted by JudgeAgents, indicating their workload and engagement with past cases.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类（例如"Average Precedents"），值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the interpreted_precedents list from JudgeAgent
        interpreted_precedents = safe_list(safe_get(data, 'interpreted_precedents', []))
        
        # Calculate total interpreted precedents safely
        total_precedents = safe_sum(interpreted_precedents, default=0)
        
        # Calculate number of JudgeAgents
        num_judges = safe_count(interpreted_precedents, predicate=lambda x: x is not None)
        
        # Calculate average, handling division by zero
        if num_judges == 0:
            average_precedents = 0
        else:
            average_precedents = total_precedents / num_judges
        
        # Return result in the format for bar visualization
        return {"Average Precedents": average_precedents}
    
    except Exception as e:
        log_metric_error("Average Precedents Interpreted Per Judge", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Average Precedents": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Legal_Context_Influence_on_Judgment(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Legal Context Influence on Judgment
    描述: Analyzes how different legal contexts influence judgment results, providing insights into systemic biases or trends.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Safely retrieve the legal context from the environment
        legal_context = safe_get(data, 'legal_context')
        if legal_context is None or not isinstance(legal_context, str):
            log_metric_error("Legal Context Influence on Judgment", ValueError("Invalid or missing legal_context"), {"data": data})
            return {}

        # Safely retrieve the list of judgment results from JudgeAgent
        judgment_results = safe_list(safe_get(data, 'judgment_result', []))
        if not judgment_results:
            log_metric_error("Legal Context Influence on Judgment", ValueError("Empty or missing judgment_result list"), {"data": data})
            return {}

        # Count occurrences of each unique judgment result
        result_counts = {}
        for result in judgment_results:
            if result is not None and isinstance(result, str):
                result_counts[result] = result_counts.get(result, 0) + 1

        # Calculate proportions based on legal context
        total_count = sum(result_counts.values())
        if total_count == 0:
            log_metric_error("Legal Context Influence on Judgment", ZeroDivisionError("Total count of judgment results is zero"), {"data": data})
            return {}

        proportions = {result: count / total_count for result, count in result_counts.items()}

        # Return the proportions categorized by legal context for pie chart visualization
        return {f"{legal_context}: {result}": proportion for result, proportion in proportions.items()}

    except Exception as e:
        log_metric_error("Legal Context Influence on Judgment", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_avg, log_metric_error

def Socio_Political_Influence_on_Case_Outcomes(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: Socio-Political Influence on Case Outcomes
    描述: Examines the impact of socio-political factors on case outcomes, highlighting potential external influences on legal interpretations.
    可视化类型: line

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为系列名称，值为对应数值
    """
    try:
        # Access socio_political_influences and outcome_analysis from the data dictionary
        socio_political_influences = safe_list(safe_get(data, 'socio_political_influences', []))
        outcome_analysis = safe_list(safe_get(data, 'outcome_analysis', []))

        # Validate and aggregate socio-political influences
        if not socio_political_influences:
            log_metric_error("Socio-Political Influence on Case Outcomes", ValueError("socio_political_influences list is empty or None"))
            socio_political_avg = 0
        else:
            socio_political_avg = safe_avg(socio_political_influences)

        # Validate and aggregate outcome analysis
        if not outcome_analysis:
            log_metric_error("Socio-Political Influence on Case Outcomes", ValueError("outcome_analysis list is empty or None"))
            outcome_avg = 0
        else:
            outcome_avg = safe_avg(outcome_analysis)

        # Prepare the result dictionary for line visualization
        result = {
            'Socio-Political Influences': socio_political_avg,
            'Outcome Analysis': outcome_avg
        }
        
        return result

    except Exception as e:
        log_metric_error("Socio-Political Influence on Case Outcomes", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Socio-Political Influences": 0, "Outcome Analysis": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Precedents_Interpreted_Per_Judge': Average_Precedents_Interpreted_Per_Judge,
    'Legal_Context_Influence_on_Judgment': Legal_Context_Influence_on_Judgment,
    'Socio_Political_Influence_on_Case_Outcomes': Socio_Political_Influence_on_Case_Outcomes,
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
