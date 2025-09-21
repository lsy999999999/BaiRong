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

def Information_Spread_Success_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Information Spread Success Rate
    描述: Measures the percentage of public agents that have received any information.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
        - pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the received_information list for PublicAgent
        received_information_list = safe_list(safe_get(data, 'received_information', []))
        
        if not received_information_list:
            # If the list is empty, log the error and return 0% success rate
            log_metric_error("Information Spread Success Rate", ValueError("Empty or missing received_information list"))
            return {"Received": 0.0, "Not Received": 100.0}

        # Count the number of agents that have received information (non-None and non-empty)
        received_count = safe_count(received_information_list, lambda x: x is not None and x != "")

        # Calculate total number of agents
        total_agents = len(received_information_list)

        if total_agents == 0:
            # Handle division by zero scenario
            log_metric_error("Information Spread Success Rate", ZeroDivisionError("No agents found"))
            return {"Received": 0.0, "Not Received": 100.0}

        # Calculate the percentage of agents that received information
        success_rate = (received_count / total_agents) * 100.0
        not_received_rate = 100.0 - success_rate

        # Return the result in the format suitable for a pie chart
        return {"Received": success_rate, "Not Received": not_received_rate}

    except Exception as e:
        log_metric_error("Information Spread Success Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Received": 0.0, "Not Received": 100.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Opinion_Modification_Rate(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Opinion Modification Rate
    描述: Tracks how often opinion leaders modify the information before passing it to public agents.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类（"Modified", "Unmodified"），值为对应数值
    """
    try:
        # Access the required variables
        original_information_list = safe_list(safe_get(data, 'original_information', []))
        modified_information_list = safe_list(safe_get(data, 'modified_information', []))
        
        # Initialize counters
        modified_count = 0
        unmodified_count = 0

        # Ensure both lists are of the same length
        if len(original_information_list) != len(modified_information_list):
            log_metric_error("Opinion Modification Rate", ValueError("Mismatched list lengths"), {
                "original_information_length": len(original_information_list),
                "modified_information_length": len(modified_information_list)
            })
            return {"Modified": modified_count, "Unmodified": unmodified_count}

        # Iterate through both lists and compare
        for original, modified in zip(original_information_list, modified_information_list):
            if original is None or modified is None:
                continue  # Skip None values

            if modified != "ready":
                modified_count += 1
            else:
                unmodified_count += 1

        return {"Modified": modified_count, "Unmodified": unmodified_count}

    except Exception as e:
        log_metric_error("Opinion Modification Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Modified": 0, "Unmodified": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Agent_Communication_Load(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Agent Communication Load
    描述: Evaluates the distribution of communication load among opinion leaders by counting how many public agents each opinion leader targets.
    可视化类型: bar

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式

    Returns:
        返回字典，键为opinion_leader_id，值为对应的目标公共代理数量
    """
    try:
        # Retrieve opinion leader IDs and target public agents lists
        opinion_leader_ids = safe_list(safe_get(data, 'opinion_leader_id', []))
        target_public_agents_lists = safe_list(safe_get(data, 'target_public_agents', []))
        # logger.info(f"opinion_leader_ids: {opinion_leader_ids}")
        # logger.info(f"target_public_agents_lists: {target_public_agents_lists}")

        # Check if both lists are of the same length
        if len(opinion_leader_ids) != len(target_public_agents_lists):
            log_metric_error("Agent Communication Load", ValueError("Mismatched lengths of opinion_leader_id and target_public_agents"), {
                "opinion_leader_ids_length": len(opinion_leader_ids),
                "target_public_agents_length": len(target_public_agents_lists)
            })
            return {}

        # Calculate communication load for each opinion leader
        communication_load = {}
        for leader_id, targets in zip(opinion_leader_ids, target_public_agents_lists):
            if leader_id is None:
                continue
            targets_list = safe_list(targets)
            communication_load[leader_id] = len(targets_list)

        return communication_load

    except Exception as e:
        log_metric_error("Agent Communication Load", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Information_Spread_Success_Rate': Information_Spread_Success_Rate,
    'Opinion_Modification_Rate': Opinion_Modification_Rate,
    'Agent_Communication_Load': Agent_Communication_Load,
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
