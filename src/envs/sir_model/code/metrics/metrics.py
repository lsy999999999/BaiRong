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

def infection_rate_over_time(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate the infection rate over time, which tracks the percentage of IndividualAgents currently infected (I).

    Args:
        data: Dictionary containing all variables collected by the monitor.

    Returns:
        A dictionary with the series name 'infection_rate' and the calculated percentage for line visualization.
    """
    try:
        # Access the current_health_state list from IndividualAgent data
        current_health_states = safe_list(safe_get(data, 'current_health_state', []))

        # Count the number of infected agents ('I')
        infected_count = safe_count(current_health_states, predicate=lambda state: state == 'I')

        # Total number of agents
        total_agents = len(current_health_states)

        # Calculate infection rate percentage, handle division by zero
        infection_rate = (infected_count / total_agents * 100) if total_agents > 0 else 0.0

        # Return the result in the required format for line visualization
        return {'infection_rate': infection_rate}

    except Exception as e:
        # Log any errors encountered during calculation
        log_metric_error("infection_rate_over_time", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'infection_rate': 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def policy_effectiveness(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: policy_effectiveness
    描述: Evaluates the effectiveness of government policies based on the proportion of policies that are active and their reported effects.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类（如'positive', 'neutral', 'negative'），值为对应的活跃政策数量
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the policy_status and policy_effect lists
        policy_status_list = safe_list(safe_get(data, 'policy_status', []))
        policy_effect_list = safe_list(safe_get(data, 'policy_effect', []))

        logger.info(f"policy_status_list: {policy_status_list}")
        logger.info(f"policy_effect_list: {policy_effect_list}")

        # Validate that both lists are of the same length
        if len(policy_status_list) != len(policy_effect_list):
            raise ValueError("Mismatched lengths for policy_status and policy_effect lists")

        # Initialize a dictionary to hold counts of active policies by effect
        effect_counts = {'positive': 0, 'neutral': 0, 'negative': 0}

        # Iterate over the policies and count active ones by effect
        for status, effect in zip(policy_status_list, policy_effect_list):
            if status is None or effect is None:
                continue  # Skip None values
            if "enhance" in effect.lower() or "increase" in effect.lower():
                effect_counts["positive"] += 1
            elif "reduce" in effect.lower() or "decrease" in effect.lower():
                effect_counts["negative"] += 1
            else:
                effect_counts["neutral"] += 1

        return effect_counts
    except Exception as e:
        log_metric_error("policy_effectiveness", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'positive': 0, 'neutral': 0, 'negative': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def healthcare_treatment_success_rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: healthcare_treatment_success_rate
    描述: Monitors the success rate of treatments managed by HealthcareSystemAgents based on recovery statuses.
    可视化类型: pie
    更新频率: 10 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Retrieve treatment_status and recovery_status lists from data
        treatment_statuses = safe_list(safe_get(data, 'treatment_status', []))
        recovery_statuses = safe_list(safe_get(data, 'recovery_status', []))

        # Ensure both lists are of the same length, otherwise log an error
        if len(treatment_statuses) != len(recovery_statuses):
            log_metric_error("healthcare_treatment_success_rate", ValueError("Mismatched list lengths for treatment and recovery statuses"), 
                             {"treatment_statuses_length": len(treatment_statuses), "recovery_statuses_length": len(recovery_statuses)})
            return {"successful": 0.0, "unsuccessful": 1.0}

        # Count successful recoveries
        successful_count = safe_count(recovery_statuses, lambda status: status == 'recovered')

        # Total treatments considered
        total_treatments = len(treatment_statuses)

        # Calculate proportions
        if total_treatments == 0:
            successful_proportion = 0.0
            unsuccessful_proportion = 1.0
        else:
            successful_proportion = successful_count / total_treatments
            unsuccessful_proportion = 1.0 - successful_proportion

        return {
            "successful": successful_proportion,
            "unsuccessful": unsuccessful_proportion
        }

    except Exception as e:
        log_metric_error("healthcare_treatment_success_rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"successful": 0.0, "unsuccessful": 1.0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'infection_rate_over_time': infection_rate_over_time,
    'policy_effectiveness': policy_effectiveness,
    'healthcare_treatment_success_rate': healthcare_treatment_success_rate,
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
