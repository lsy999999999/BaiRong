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


def Media_Ideology_Bias_Distribution(data: Dict[str, Any]) -> Any:
    """
    计算指标: Media Ideology Bias Distribution
    描述: Proportion of media outlets with different ideological biases to understand the media landscape's diversity.
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
    from onesim.monitor.utils import (
        safe_get, safe_list, log_metric_error
    )
    
    try:
        # Check if the data is a dictionary
        if not data or not isinstance(data, dict):
            log_metric_error("Media Ideology Bias Distribution", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve the media_ideology_bias list
        media_ideology_bias_list = safe_get(data, "media_ideology_bias", [])

        # Ensure it is a list
        media_ideology_bias_list = safe_list(media_ideology_bias_list)

        # Handle empty list scenario
        if not media_ideology_bias_list:
            return {}

        # Count occurrences of each ideology bias
        bias_count = {}
        for bias in media_ideology_bias_list:
            # Treat None values as 'Unknown'
            bias = bias if bias is not None else 'Unknown'
            if not isinstance(bias, str):
                log_metric_error("Media Ideology Bias Distribution", ValueError("Invalid data type in media_ideology_bias"), {"bias": bias})
                continue
            bias_count[bias] = bias_count.get(bias, 0) + 1

        # Calculate total number of biases for proportion calculation
        total_biases = sum(bias_count.values())

        # Handle division by zero scenario
        if total_biases == 0:
            return {}

        # Calculate proportion for each bias
        bias_distribution = {bias: count / total_biases for bias, count in bias_count.items()}

        return bias_distribution

    except Exception as e:
        log_metric_error("Media Ideology Bias Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

def Average_Voter_Information_Level(data: Dict[str, Any]) -> Any:
    """
    计算指标: Average Voter Information Level
    描述: Average level of information among voters, indicating how informed the electorate is.
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
    from onesim.monitor.utils import (
        safe_get, safe_number, safe_list, safe_avg, log_metric_error
    )
    
    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Average Voter Information Level", ValueError("Invalid data input"), {"data": data})
            return 0
        
        # Extract voter_information_level using safe_get and safe_list
        voter_information_levels = safe_list(safe_get(data, "voter_information_level", []))
        
        # Filter out invalid types and None values
        valid_information_levels = [
            safe_number(level, None) for level in voter_information_levels if isinstance(level, (int, float))
        ]
        
        # Calculate average using safe_avg, default to 0 for empty or invalid lists
        average_information_level = safe_avg(valid_information_levels, default=0)
        
        # Return the result for line visualization
        return average_information_level
    
    except Exception as e:
        log_metric_error("Average Voter Information Level", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Party_Strategy_Change_Rate(data: Dict[str, Any]) -> Any:
    """
    计算指标: Party Strategy Change Rate
    描述: Percentage of parties that have changed their strategy in the current cycle, indicating strategic shifts.
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
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Party Strategy Change Rate", ValueError("Invalid data input"), {"data": data})
            return {}

        # Safely extract the current_strategy and new_strategy lists
        current_strategy = safe_list(safe_get(data, "current_strategy", []))
        new_strategy = safe_list(safe_get(data, "new_strategy", []))

        # Check if both lists are of the same length
        if len(current_strategy) != len(new_strategy):
            log_metric_error("Party Strategy Change Rate", ValueError("Mismatched list lengths"), {
                "current_strategy_length": len(current_strategy),
                "new_strategy_length": len(new_strategy)
            })
            return {}

        # Count the number of strategy changes
        strategy_changes = safe_count(
            zip(current_strategy, new_strategy),
            predicate=lambda pair: pair[0] is not None and pair[1] is not None and pair[0] != pair[1]
        )

        # Count the total number of parties with valid strategies
        total_valid_parties = safe_count(
            zip(current_strategy, new_strategy),
            predicate=lambda pair: pair[0] is not None and pair[1] is not None
        )

        # Calculate the change rate
        if total_valid_parties == 0:
            change_rate = 0.0
        else:
            change_rate = (strategy_changes / total_valid_parties) * 100

        # Return the result as a dictionary for bar visualization
        return {"Party Strategy Change Rate": change_rate}

    except Exception as e:
        log_metric_error("Party Strategy Change Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Media_Ideology_Bias_Distribution': Media_Ideology_Bias_Distribution,
    'Average_Voter_Information_Level': Average_Voter_Information_Level,
    'Party_Strategy_Change_Rate': Party_Strategy_Change_Rate,
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

