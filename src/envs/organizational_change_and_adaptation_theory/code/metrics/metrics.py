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
from onesim.monitor.utils import (
    safe_get,
    safe_list,
    log_metric_error
)

def Employee_Feedback_Sentiment(data: Dict[str, Any]) -> Any:
    """
    计算指标: Employee Feedback Sentiment
    描述: Measures the overall sentiment of employee feedback regarding organizational changes.
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
        # Validate input
        if not data or not isinstance(data, dict):
            log_metric_error("Employee Feedback Sentiment", ValueError("Invalid data input"), {"data": data})
            return {}

        # Extract and validate employee feedback
        feedback_list = safe_list(safe_get(data, "feedback", []))

        logger.info(f"feedback_list: {feedback_list}")
        
        if not feedback_list:
            log_metric_error("Employee Feedback Sentiment", ValueError("Feedback list is empty or invalid"), {"feedback": feedback_list})
            return {}

        # Initialize sentiment counters
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}

        # Dummy sentiment analysis function
        def analyze_sentiment(feedback):
            # Placeholder for actual sentiment analysis logic
            if "positive" in feedback.lower() or "appreciate" in feedback.lower() or "well" in feedback.lower():
                return "positive"
            elif "negative" in feedback.lower() or "dislike" in feedback.lower() or "bad" in feedback.lower():
                return "negative"
            else:
                return "neutral"

        # Process each feedback entry
        for feedback in feedback_list:
            if feedback is None or not isinstance(feedback, str) or feedback.strip() == "":
                continue  # Skip invalid feedback entries

            sentiment = analyze_sentiment(feedback)
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1

        # Calculate total feedback count
        total_feedback = sum(sentiment_counts.values())
        if total_feedback == 0:
            log_metric_error("Employee Feedback Sentiment", ValueError("No valid feedback entries processed"), {"feedback": feedback_list})
            return {}

        # Calculate proportions
        sentiment_proportions = {key: count / total_feedback for key, count in sentiment_counts.items()}

        return sentiment_proportions

    except Exception as e:
        log_metric_error("Employee Feedback Sentiment", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Change_Goals_Completion_Rate(data: Dict[str, Any]) -> Any:
    """
    计算指标: Change Goals Completion Rate
    描述: Tracks the percentage of change goals set by LeaderAgents that have been successfully reported as completed.
    可视化类型: bar
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
        # Ensure the data is a valid dictionary
        if not data or not isinstance(data, dict):
            log_metric_error("Change Goals Completion Rate", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve change goals and final reports safely
        change_goals_list = safe_list(safe_get(data, "change_goals", []))
        final_report_list = safe_list(safe_get(data, "final_report", []))

        # Calculate the number of goals and completed goals
        total_goals = safe_count(change_goals_list)
        completed_goals = safe_count(final_report_list, predicate=lambda x: x in change_goals_list)

        # Handle division by zero scenario
        if total_goals == 0:
            completion_rate = 0.0
        else:
            completion_rate = (completed_goals / total_goals) * 100

        # Return result as a dictionary suitable for bar visualization
        return {"Change Goals Completion Rate": completion_rate}
    except Exception as e:
        log_metric_error("Change Goals Completion Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_list, safe_avg, log_metric_error
)

def Manager_Execution_Effectiveness(data: Dict[str, Any]) -> Any:
    """
    计算指标: Manager Execution Effectiveness
    描述: Evaluates how effectively managers are executing change strategies by comparing planned strategies to execution status.
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
            log_metric_error("Manager Execution Effectiveness", ValueError("Invalid data input"), {"data": data})
            return 0

        # Extract ManagerAgent variables
        execution_status_list = safe_list(safe_get(data, "execution_status", []))
        adjusted_strategy_list = safe_list(safe_get(data, "adjusted_strategy", []))

        # Ensure both lists are of the same length
        if len(execution_status_list) != len(adjusted_strategy_list):
            log_metric_error(
                "Manager Execution Effectiveness",
                ValueError("Mismatched list lengths"),
                {"execution_status_list_length": len(execution_status_list), "adjusted_strategy_list_length": len(adjusted_strategy_list)}
            )
            return 0

        # Calculate effectiveness for each ManagerAgent
        effectiveness_scores = []
        for execution_status, adjusted_strategy in zip(execution_status_list, adjusted_strategy_list):
            try:
                # Check both values for validity
                if execution_status is None or adjusted_strategy is None:
                    effectiveness_scores.append(0)
                elif isinstance(execution_status, str) and isinstance(adjusted_strategy, str):
                    # Evaluate match (exact match or similarity can be customized here)
                    effectiveness_scores.append(1 if execution_status == adjusted_strategy else 0)
                else:
                    effectiveness_scores.append(0)
            except Exception as e:
                log_metric_error(
                    "Manager Execution Effectiveness",
                    e,
                    {"execution_status": execution_status, "adjusted_strategy": adjusted_strategy}
                )
                effectiveness_scores.append(0)

        # Aggregate effectiveness scores (average for line chart)
        overall_effectiveness = safe_avg(effectiveness_scores)

        # Return result for line visualization
        return overall_effectiveness

    except Exception as e:
        log_metric_error("Manager Execution Effectiveness", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Employee_Feedback_Sentiment': Employee_Feedback_Sentiment,
    'Change_Goals_Completion_Rate': Change_Goals_Completion_Rate,
    'Manager_Execution_Effectiveness': Manager_Execution_Effectiveness,
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

