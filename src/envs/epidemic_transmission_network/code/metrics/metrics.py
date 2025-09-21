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
    safe_get, safe_list, safe_count, log_metric_error
)

def Infection_Rate_Over_Time(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Infection Rate Over Time
    描述: Measures the percentage of the population that is infected over time, providing insights into the spread of the disease and the effectiveness of interventions.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the health_status list from the data dictionary
        health_status_list = safe_list(safe_get(data, 'health_status', []))
        
        # Count total number of individuals
        total_individuals = safe_count(health_status_list)
        
        if total_individuals == 0:
            # Handle division by zero scenario
            return {"infection_rate": 0.0}
        
        # Count the number of infected individuals
        number_of_infected_individuals = safe_count(
            health_status_list, 
            predicate=lambda status: status == 'infected'
        )
        
        # Calculate infection rate
        infection_rate = (number_of_infected_individuals / total_individuals) * 100
        
        # Return the result as a dictionary suitable for line visualization
        return {"infection_rate": infection_rate}
    
    except Exception as e:
        log_metric_error("Infection Rate Over Time", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"infection_rate": 0.0}

from typing import Dict, Any

def Resource_Utilization_by_Healthcare_Facilities(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Resource Utilization by Healthcare Facilities
    描述: Measures the utilization of healthcare facilities in terms of occupancy and staff levels, providing insights into the strain on the healthcare system.
    可视化类型: bar
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - bar: 返回字典，键为设施ID，值为对应利用率
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Resource Utilization by Healthcare Facilities", ValueError("Invalid data input"), {"data": data})
            return {}

        current_occupancy = safe_list(safe_get(data, 'current_occupancy', []))
        staff_level = safe_list(safe_get(data, 'staff_level', []))

        # Ensure both lists have the same length
        if len(current_occupancy) != len(staff_level):
            log_metric_error("Resource Utilization by Healthcare Facilities", ValueError("Lists of current_occupancy and staff_level do not match in length"))
            return {}

        # Define the capacity (constant value)
        capacity = 100  # Example capacity value, should be defined based on actual data or provided as a parameter

        # Initialize result dictionary
        result = {}

        # Calculate utilization for each facility
        for i in range(len(current_occupancy)):
            if current_occupancy[i] is None or staff_level[i] is None:
                continue
            if current_occupancy[i] == 0:
                utilization = 0
            else:
                utilization = current_occupancy[i] / capacity
            result[i] = utilization

        return result
    except Exception as e:
        log_metric_error("Resource Utilization by Healthcare Facilities", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_avg, safe_sum, log_metric_error

def Behavioral_Compliance_by_Demographic_Groups(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Behavioral Compliance by Demographic Groups
    描述: Measures the compliance tendency of individuals across different demographic groups, providing insights into how different segments of the population respond to interventions and information dissemination.
    可视化类型: pie
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回一个字典，键为分类（demographic group），值为平均合规倾向
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Behavioral Compliance by Demographic Groups", ValueError("Invalid data input"), {"data": data})
            return {}

        compliance_tendency = safe_list(safe_get(data, 'compliance_tendency', []))
        demographic_group = safe_list(safe_get(data, 'demographic_group', []))

        if len(compliance_tendency) != len(demographic_group):
            log_metric_error("Behavioral Compliance by Demographic Groups", ValueError("Unequal length of compliance_tendency and demographic_group"), {"compliance_tendency": compliance_tendency, "demographic_group": demographic_group})
            return {}

        if not compliance_tendency or not demographic_group:
            log_metric_error("Behavioral Compliance by Demographic Groups", ValueError("Empty compliance_tendency or demographic_group"), {"compliance_tendency": compliance_tendency, "demographic_group": demographic_group})
            return {}

        compliance_by_group = {}
        for i in range(len(compliance_tendency)):
            if compliance_tendency[i] is None or demographic_group[i] is None:
                continue

            compliance_tendency_val = safe_number(compliance_tendency[i])
            demographic_group_val = demographic_group[i]

            if demographic_group_val not in compliance_by_group:
                compliance_by_group[demographic_group_val] = []

            compliance_by_group[demographic_group_val].append(compliance_tendency_val)

        result = {group: safe_avg(values) for group, values in compliance_by_group.items()}
        return result
    except Exception as e:
        log_metric_error("Behavioral Compliance by Demographic Groups", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Infection_Rate_Over_Time': Infection_Rate_Over_Time,
    'Resource_Utilization_by_Healthcare_Facilities': Resource_Utilization_by_Healthcare_Facilities,
    'Behavioral_Compliance_by_Demographic_Groups': Behavioral_Compliance_by_Demographic_Groups,
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
