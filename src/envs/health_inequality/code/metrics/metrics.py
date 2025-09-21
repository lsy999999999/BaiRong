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
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_avg, log_metric_error

def Average_Income_Level_by_Education(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Income Level by Education
    描述: This metric measures the average income level of individuals categorized by their education level. It provides insight into how income varies with education, which is a key factor in health inequalities.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为教育水平，值为对应平均收入水平
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access income levels and education levels from the data
        income_levels = safe_list(safe_get(data, 'income_level', []))
        education_levels = safe_list(safe_get(data, 'education_level', []))

        if not income_levels or not education_levels:
            log_metric_error("Average Income Level by Education", ValueError("Missing or empty data lists"), {"income_levels": income_levels, "education_levels": education_levels})
            return {}

        # Dictionary to hold sum and count of income levels for each education level
        education_income_data = {}

        # Process each individual's data
        for income, education in zip(income_levels, education_levels):
            if education is None or not isinstance(education, str):
                continue
            income_value = safe_number(income, None)
            if income_value is None:
                continue

            # Initialize dictionary entry if not present
            if education not in education_income_data:
                education_income_data[education] = {'sum': 0.0, 'count': 0}

            # Accumulate sum and count
            education_income_data[education]['sum'] += income_value
            education_income_data[education]['count'] += 1

        # Calculate average income for each education level
        average_income_by_education = {}
        for education, data in education_income_data.items():
            if data['count'] == 0:
                log_metric_error("Average Income Level by Education", ZeroDivisionError("Division by zero when calculating average"), {"education": education})
                average_income_by_education[education] = 0.0
            else:
                average_income_by_education[education] = data['sum'] / data['count']

        return average_income_by_education

    except Exception as e:
        log_metric_error("Average Income Level by Education", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_number, safe_list, safe_sum, log_metric_error

def Resource_Distribution_Efficiency(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Resource Distribution Efficiency
    描述: This metric evaluates how efficiently government resources are being distributed across different target populations. It helps identify disparities in resource allocation.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        对于pie图，返回字典，键为分类，值为对应比例
    """
    try:
        # Access and validate the resource_distribution and target_population lists
        resource_distribution_list = safe_list(safe_get(data, 'resource_distribution', []))
        target_population_list = safe_list(safe_get(data, 'target_population', []))
        
        # Check if lists are empty or unequal in length
        if not resource_distribution_list or not target_population_list:
            log_metric_error("Resource Distribution Efficiency", ValueError("Empty or missing data in resource_distribution or target_population"), {"resource_distribution": resource_distribution_list, "target_population": target_population_list})
            return {}
        
        if len(resource_distribution_list) != len(target_population_list):
            log_metric_error("Resource Distribution Efficiency", ValueError("Mismatch in length of resource_distribution and target_population lists"), {"resource_distribution_length": len(resource_distribution_list), "target_population_length": len(target_population_list)})
            return {}

        # Calculate the total resources distributed
        total_resources = safe_sum(resource_distribution_list)
        
        if total_resources == 0:
            log_metric_error("Resource Distribution Efficiency", ValueError("Total resources distributed is zero, leading to division by zero"), {"resource_distribution": resource_distribution_list})
            return {}

        # Calculate the distribution proportions
        distribution_efficiency = {}
        for resource, population in zip(resource_distribution_list, target_population_list):
            resource_value = safe_number(resource)
            if resource_value is not None:
                proportion = resource_value / total_resources
                distribution_efficiency[population] = distribution_efficiency.get(population, 0) + proportion
        
        return distribution_efficiency

    except Exception as e:
        log_metric_error("Resource Distribution Efficiency", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_avg, log_metric_error

def Healthcare_Accessibility_Impact(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Healthcare Accessibility Impact
    描述: This metric tracks changes in healthcare accessibility by analyzing the average resource availability in healthcare systems over time. It indicates the impact of policy interventions on healthcare access.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为时间点，值为对应的平均资源可用性
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access resource availability data from HealthcareSystemAgent
        resource_availability_list = safe_list(safe_get(data, 'resource_availability', []))

        # Filter out None and non-numeric values
        valid_resource_availability = [safe_get(item, 'value') for item in resource_availability_list if isinstance(safe_get(item, 'value'), (int, float))]

        # Calculate the average resource availability
        average_resource_availability = safe_avg(valid_resource_availability, default=0)

        # Prepare the result as a line chart series
        result = {'Healthcare Accessibility Impact': average_resource_availability}
        
        return result

    except Exception as e:
        log_metric_error("Healthcare Accessibility Impact", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Healthcare Accessibility Impact": 0}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Income_Level_by_Education': Average_Income_Level_by_Education,
    'Resource_Distribution_Efficiency': Resource_Distribution_Efficiency,
    'Healthcare_Accessibility_Impact': Healthcare_Accessibility_Impact,
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
