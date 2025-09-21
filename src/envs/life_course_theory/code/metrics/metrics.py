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

def Average_Educational_Resources_Utilization(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Educational Resources Utilization
    描述: Measures the average utilization of educational resources across the system.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应的平均利用率
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the educational_resources from environment
        educational_resources = safe_get(data, 'educational_resources')
        logger.info(f"educational_resources: {educational_resources}")
        if educational_resources is None:
            log_metric_error("Average Educational Resources Utilization", ValueError("Missing educational_resources"))
            return {"Utilization": 0.0}

        # Access the education_impact_assessed list from EducationSystemAgent
        education_impact_assessed = safe_list(safe_get(data, 'education_impact_assessed', []))
        logger.info(f"education_impact_assessed: {education_impact_assessed}")
        # Count the number of True values in education_impact_assessed
        count_impact_assessed = safe_count(education_impact_assessed, predicate=lambda x: x is True)

        # Total number of EducationSystemAgents
        total_agents = len(education_impact_assessed)

        # Calculate the utilization proportion
        if total_agents == 0:
            utilization_proportion = 0.0
        else:
            utilization_proportion = count_impact_assessed / total_agents

        # Return result as a dictionary for bar visualization
        return {"Utilization": utilization_proportion}

    except Exception as e:
        log_metric_error("Average Educational Resources Utilization", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Utilization": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Healthcare_Service_Evaluation_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Healthcare Service Evaluation Rate
    描述: Tracks the rate at which healthcare services are evaluated by HealthcareSystemAgents.
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
        # Accessing the 'health_services_evaluated' variable from the data
        health_services_evaluated = safe_list(safe_get(data, 'health_services_evaluated', []))

        # Count the number of agents that have evaluated health services
        evaluated_count = safe_count(health_services_evaluated, predicate=lambda x: x is True)

        # Total number of HealthcareSystemAgents
        total_agents = len(health_services_evaluated)

        # Calculate the evaluation rate
        if total_agents == 0:
            evaluation_rate = 0.0  # Avoid division by zero
        else:
            evaluation_rate = (evaluated_count / total_agents) * 100

        # Return the result as a dictionary for line visualization
        return {"Healthcare Service Evaluation Rate": evaluation_rate}
        
    except Exception as e:
        log_metric_error("Healthcare Service Evaluation Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Healthcare Service Evaluation Rate": 0.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Policy_Implementation_Success_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Policy Implementation Success Rate
    描述: Represents the proportion of policies successfully implemented by GovernmentAgents.
    可视化类型: pie
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应比例，用于饼图可视化。
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'policy_implemented' list from the data dictionary
        policy_implemented_list = safe_list(safe_get(data, 'policy_implemented', []))
        # Count the total number of policies and those implemented successfully
        total_policies = safe_count(policy_implemented_list)
        successful_policies = safe_count(policy_implemented_list, lambda x: x is True)
        
        # Calculate the success rate, handling division by zero
        success_rate = (successful_policies / total_policies) if total_policies > 0 else 0.0
        
        # Return the result as a dictionary suitable for pie chart visualization
        return {
            "Success": success_rate,
            "Failure": 1 - success_rate
        }
    except Exception as e:
        log_metric_error("Policy Implementation Success Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Success": 0.0, "Failure": 1.0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Educational_Resources_Utilization': Average_Educational_Resources_Utilization,
    'Healthcare_Service_Evaluation_Rate': Healthcare_Service_Evaluation_Rate,
    'Policy_Implementation_Success_Rate': Policy_Implementation_Success_Rate,
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
