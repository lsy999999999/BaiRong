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

def Agent_Negotiation_Success_Rate(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Agent Negotiation Success Rate
    描述: Measures the proportion of successful negotiations by Individual Agents.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Access negotiation_status list for IndividualAgent
        negotiation_status_list = safe_list(safe_get(data, 'negotiation_status', []))

        if not negotiation_status_list:
            # If the list is empty, log an error and return default values
            log_metric_error("Agent Negotiation Success Rate", ValueError("Empty negotiation_status list"), {"data": data})
            return {"successful": 0.0, "unsuccessful": 1.0}

        # Count successful negotiations
        successful_count = safe_count(negotiation_status_list, lambda status: status == 'successful')

        # Count unsuccessful negotiations (including None or invalid types treated as unsuccessful)
        unsuccessful_count = len(negotiation_status_list) - successful_count

        # Handle division by zero scenario
        total_count = len(negotiation_status_list)
        if total_count == 0:
            log_metric_error("Agent Negotiation Success Rate", ZeroDivisionError("Total negotiation count is zero"), {"data": data})
            return {"successful": 0.0, "unsuccessful": 1.0}

        # Calculate proportions
        successful_rate = successful_count / total_count
        unsuccessful_rate = unsuccessful_count / total_count

        # Return result as a pie chart data structure
        result = {"successful": successful_rate, "unsuccessful": unsuccessful_rate}
        return result

    except Exception as e:
        log_metric_error("Agent Negotiation Success Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"successful": 0.0, "unsuccessful": 1.0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Government_Enforcement_Rate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: Government Enforcement Rate
    描述: Tracks the enforcement status of laws by Government Agents over time.
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
        # Access the enforcement_status list for GovernmentAgent
        enforcement_status_list = safe_list(safe_get(data, 'enforcement_status', []))
        logger.info(f"enforcement_status_list: {enforcement_status_list}")
        
        # Count the number of 'enforced' statuses
        enforced_count = safe_count(enforcement_status_list, lambda x: x == 'enforced')
        
        # Prepare the result for line visualization
        result = {'Government Enforcement Rate': enforced_count}
        
        return result
    except Exception as e:
        log_metric_error("Government Enforcement Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Government Enforcement Rate': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Public_Policy_Impact_Analysis(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Public Policy Impact Analysis
    描述: Evaluates the results of impact analyses conducted by Public Policy Agents.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Initialize result dictionary
        result = {}

        # Access 'impact_analysis_results' from PublicPolicyAgent
        impact_analysis_results_list = safe_list(safe_get(data, 'impact_analysis_results', []))

        # Iterate through each agent's impact analysis results
        for index, impact_analysis_results in enumerate(impact_analysis_results_list):
            # Validate the impact_analysis_results as a dictionary
            if not isinstance(impact_analysis_results, dict):
                log_metric_error("Public Policy Impact Analysis", TypeError("Impact analysis results must be a dictionary"), {"agent_index": index})
                continue

            # Sum up the values in the impact_analysis_results dictionary, skipping None values
            for key, value in impact_analysis_results.items():
                if value is None:
                    continue
                try:
                    numeric_value = safe_sum([value])
                except Exception as e:
                    log_metric_error("Public Policy Impact Analysis", e, {"agent_index": index, "key": key})
                    continue

                # Accumulate the sums for each metric key
                if key not in result:
                    result[key] = numeric_value
                else:
                    result[key] += numeric_value

        return result

    except Exception as e:
        log_metric_error("Public Policy Impact Analysis", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Agent_Negotiation_Success_Rate': Agent_Negotiation_Success_Rate,
    'Government_Enforcement_Rate': Government_Enforcement_Rate,
    'Public_Policy_Impact_Analysis': Public_Policy_Impact_Analysis,
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
