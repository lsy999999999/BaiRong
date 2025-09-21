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

def Manipulation_Strategy_Distribution(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Antisocial Behavior Frequency
    描述: Measures the frequency of antisocial behaviors exhibited by agents, based on their interaction status and manipulation strategy.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类（interaction_status和manipulation_strategy），值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Retrieve agent variables
        # interaction_status_list = safe_list(safe_get(data, 'interaction_status', []))
        manipulation_strategy_list = safe_list(safe_get(data, 'manipulation_strategy', []))


        # Initialize counts dictionary
        counts = {}


        # Process manipulation_strategy_list
        for strategy in manipulation_strategy_list:
            if strategy:  # Ensure strategy is not None or empty
                if strategy in counts:
                    counts[strategy] += 1
                else:
                    counts[strategy] = 1

        return counts

    except Exception as e:
        log_metric_error("Manipulation Strategy Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}


# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Manipulation_Strategy_Distribution': Manipulation_Strategy_Distribution,
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
