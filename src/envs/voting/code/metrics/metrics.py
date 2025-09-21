# -*- coding: utf-8 -*-
"""
自动生成的监控指标计算模块
"""

from typing import Dict, Any, List, Optional, Union, Callable
import math
from loguru import logger
from typing import Dict, Any
from onesim.monitor.utils import (
    safe_get, safe_number, safe_list, safe_sum, 
    safe_avg, safe_max, safe_min, safe_count, log_metric_error
)
from onesim.monitor.utils import safe_get, safe_list, safe_sum, safe_count, safe_number, log_metric_error

def Candidate_Selection_Distribution(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Candidate Selection Distribution
    描述: Examines the distribution of selected candidates among the voters.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为候选人ID，值为对应的投票数
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the list of selected candidate IDs from VoterAgent
        selected_candidate_ids = safe_list(safe_get(data, 'selected_candidate_id', []))

        # Initialize a dictionary to store the count of votes for each candidate
        candidate_vote_count = {}

        # Iterate over the list of selected candidate IDs
        for candidate_id in selected_candidate_ids:
            # Skip None values
            if candidate_id is None:
                continue
            
            # Count occurrences of each candidate ID
            if candidate_id in candidate_vote_count:
                candidate_vote_count[candidate_id] += 1
            else:
                candidate_vote_count[candidate_id] = 1

        # Return the result in the format suitable for a bar chart
        return candidate_vote_count

    except Exception as e:
        log_metric_error("Candidate Selection Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Candidate_Selection_Distribution': Candidate_Selection_Distribution,
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
