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

def Task_Execution_Success_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Task Execution Success Rate
    描述: Measures the percentage of tasks successfully completed by the Task Executor agents.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应比例
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access completion_status from Evaluator
        completion_status_list = safe_list(safe_get(data, 'completion_status', []))
        
        if not completion_status_list:
            # Handle empty list scenario
            return {"completed": 0.0, "not_completed": 1.0}

        # Count completed tasks
        completed_count = safe_count(completion_status_list, lambda status: status == 'completed')

        # Count valid (non-None) entries
        valid_entries_count = safe_count(completion_status_list, lambda status: status is not None)

        if valid_entries_count == 0:
            # Handle division by zero scenario
            return {"completed": 0.0, "not_completed": 1.0}

        # Calculate success rate
        success_rate = completed_count / valid_entries_count

        # Return result as proportions for pie chart
        return {
            "completed": success_rate,
            "not_completed": 1.0 - success_rate
        }

    except Exception as e:
        log_metric_error("Task Execution Success Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"completed": 0.0, "not_completed": 1.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, safe_count, log_metric_error

def Average_Strategy_Adjustments(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Strategy Adjustments
    描述: Calculates the average number of strategy changes made by Task Executor agents during task execution.
    可视化类型: bar

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Average Strategy Adjustments", ValueError("Invalid data input"), {"data": data})
            return {"Average Strategy Adjustments": 0.0}

        # Access the 'strategy_changes' variable from TaskExecutor agents
        strategy_changes_list = safe_list(safe_get(data, 'strategy_changes', []))

        # Filter out None values and ensure they are numeric
        valid_strategy_changes = [change for change in strategy_changes_list if change != 'none' and change != 'no_changes']
        # valid_strategy_changes = [change for change in valid_strategy_changes if isinstance(change, (int, float))]

        # Calculate the total number of strategy changes
        # total_changes = safe_sum(valid_strategy_changes)

        # Calculate the number of valid entries
        num_valid_entries = safe_count(valid_strategy_changes)

        # Calculate the average number of strategy changes
        # average_changes = total_changes / num_valid_entries if num_valid_entries > 0 else 0.0

        # Return the result in the appropriate format for a bar chart
        return {"Average Strategy Adjustments": num_valid_entries}

    except Exception as e:
        log_metric_error("Average Strategy Adjustments", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Average Strategy Adjustments": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Feedback_Utilization_Rate(data: Dict[str, Any]) -> Any:
    """
    计算指标: Feedback Utilization Rate
    描述: Shows the rate at which Task Executor agents utilize feedback from Monitor agents to adjust their strategies.
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
        # Retrieve feedback details and strategy changes lists
        feedback_details = safe_list(safe_get(data, 'feedback_details', []))
        strategy_changes = safe_list(safe_get(data, 'strategy_changes', []))
        
        # Initialize the result dictionary
        result = {}
        
        # Iterate over the agents' data, assuming each agent has one entry in the lists
        for idx, (feedback, strategy_change) in enumerate(zip(feedback_details, strategy_changes)):
            # Safely count valid entries in feedback and strategy changes
            feedback_count = safe_count(feedback_details, lambda x: x is not None)
            strategy_change_count = safe_count(strategy_changes, lambda x: x is not None)
            
            # Calculate the feedback utilization rate
            if feedback_count > 0:
                utilization_rate = strategy_change_count / feedback_count
            else:
                utilization_rate = 0  # Default to 0 if no feedback is present
            
            # Add to result with a series name for each Task Executor agent
            series_name = f"agent_{idx+1}"
            result[series_name] = utilization_rate
        
        return result
    
    except Exception as e:
        log_metric_error("Feedback Utilization Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"default": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Task_Execution_Success_Rate': Task_Execution_Success_Rate,
    'Average_Strategy_Adjustments': Average_Strategy_Adjustments,
    'Feedback_Utilization_Rate': Feedback_Utilization_Rate,
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
