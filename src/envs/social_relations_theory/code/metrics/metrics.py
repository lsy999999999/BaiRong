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
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_avg, log_metric_error

def Average_Work_Motivation_of_Experienced_Employees(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Work Motivation of Experienced Employees
    描述: This metric measures the average work motivation level among experienced employees, providing insight into their overall engagement and motivation.
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
        # Access the work motivation data for ExperiencedEmployee
        work_motivation_data = safe_list(safe_get(data, 'work_motivation', []))

        # Filter out None values and convert to numbers
        valid_motivations = [safe_number(value) for value in work_motivation_data if value is not None]

        # Calculate average work motivation
        average_motivation = safe_avg(valid_motivations, default=0)

        # Return the result in the format suitable for a line chart
        return {'Average Work Motivation': average_motivation}

    except Exception as e:
        log_metric_error("Average Work Motivation of Experienced Employees", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Average Work Motivation': 0}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_list, safe_avg, log_metric_error
)

def Feedback_Impact_on_Employee_Motivation(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Feedback Impact on Employee Motivation
    描述: This metric evaluates how feedback from team leaders affects the motivation levels of experienced employees over time.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为反馈内容，值为对应的平均工作动机水平
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Extract feedback content and work motivation lists from the data
        feedback_content_list = safe_list(safe_get(data, 'feedback_content', []))
        work_motivation_list = safe_list(safe_get(data, 'work_motivation', []))
        
        # Check if either list is empty
        if not feedback_content_list or not work_motivation_list:
            return {}
        
        # Initialize a dictionary to hold aggregated motivation values
        feedback_motivation_map = {}
        
        # Iterate over feedback content and corresponding motivation levels
        for feedback, motivation in zip(feedback_content_list, work_motivation_list):
            # Skip None values
            if feedback is None or motivation is None:
                continue
            
            # Initialize list for each feedback if not already present
            if feedback not in feedback_motivation_map:
                feedback_motivation_map[feedback] = []
            
            # Append motivation to the corresponding feedback list
            feedback_motivation_map[feedback].append(motivation)
        
        # Calculate average motivation for each feedback
        result = {}
        for feedback, motivations in feedback_motivation_map.items():
            if motivations:  # Ensure the list is not empty
                avg_motivation = safe_avg(motivations)
                result[feedback] = avg_motivation
        
        return result
    
    except Exception as e:
        log_metric_error("Feedback Impact on Employee Motivation", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Distribution_of_Emotional_Results_from_Emotional_Analyzer(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Distribution of Emotional States in Experienced Employees
    描述: This metric shows the distribution of different emotional states among experienced employees, indicating the emotional climate within the organization.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为情绪状态，值为对应比例
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Accessing the emotional_state list from ExperiencedEmployee agents
        emotional_states = safe_list(safe_get(data, 'emotion_analysis_result', []))

        if not emotional_states:
            # Log and return an empty dictionary if the list is empty
            log_metric_error("Distribution of Emotional States in Experienced Employees", ValueError("No emotional states available"), {"data": data})
            return {}
        
        cnt = 0
        for state in emotional_states:
            if state == 'positive':
                cnt += 1
                

        # Count occurrences of each emotional state, ignoring None values
        # state_counts = {}
        # for state in emotional_states:
        #     if state is not None and isinstance(state, str):
        #         if state in state_counts:
        #             state_counts[state] += 1
        #         else:
        #             state_counts[state] = 1

        # total_states = sum(state_counts.values())
        # if total_states == 0:
        #     # Log and return an empty dictionary if there are no valid states
        #     log_metric_error("Distribution of Emotional States in Experienced Employees", ValueError("No valid emotional states found"), {"data": data})
        #     return {}

        # # Calculate proportions for pie chart visualization
        # state_proportions = {state: count / total_states for state, count in state_counts.items()}

        # return state_proportions
        return cnt

    except Exception as e:
        log_metric_error("Distribution of Emotional States in Experienced Employees", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Work_Motivation_of_Experienced_Employees': Average_Work_Motivation_of_Experienced_Employees,
    'Feedback_Impact_on_Employee_Motivation': Feedback_Impact_on_Employee_Motivation,
    'Distribution_of_Emotional_Results_from_Emotional_Analyzer': Distribution_of_Emotional_Results_from_Emotional_Analyzer,
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
