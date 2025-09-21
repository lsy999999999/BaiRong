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
from onesim.monitor.utils import safe_get, safe_list, safe_sum, safe_count, log_metric_error

def Average_Overtime_Hours_per_Employee(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Overtime Hours per Employee
    描述: This metric calculates the average number of overtime hours claimed by employees.
    可视化类型: bar

    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - bar: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access overtime_hours from Employee agent data
        overtime_hours_list = safe_list(safe_get(data, 'overtime_hours', []))
        
        logger.info(f"overtime_hours_list: {overtime_hours_list}")
        # Filter and validate overtime hours
        valid_overtime_hours = [safe_get(item, None) for item in overtime_hours_list if isinstance(item, (int, float)) and item is not None]
        
        # Calculate the average
        total_hours = safe_sum(valid_overtime_hours)
        count = safe_count(valid_overtime_hours)
        
        # Handle division by zero
        average_overtime_hours = total_hours / count if count > 0 else 0
        
        # Return result in bar format
        return {'Average Overtime Hours': average_overtime_hours}
    
    except Exception as e:
        log_metric_error("Average Overtime Hours per Employee", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Average Overtime Hours': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Ruling_Outcome_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate metric: Ruling Outcome Distribution
    Description: This metric shows the distribution of different ruling outcomes in the simulation.
    Visualization Type: pie

    Args:
        data: A dictionary containing all collected variables. Note that agent variables are lists.

    Returns:
        A dictionary where keys are ruling outcomes and values are their proportions.
        
    Note:
        This function handles various edge cases including None values, empty lists, and type errors.
    """
    try:
        # Safely get the 'ruling' variable from the environment
        ruling_data = safe_get(data, 'ruling')

        # Ensure ruling_data is a list for consistent processing
        ruling_data_list = safe_list(ruling_data)

        # Filter out None values and count occurrences of each ruling
        ruling_counts = {}
        for ruling in ruling_data_list:
            if ruling is not None and isinstance(ruling, str):
                if ruling in ruling_counts:
                    ruling_counts[ruling] += 1
                else:
                    ruling_counts[ruling] = 1

        # Calculate total number of non-None rulings
        total_rulings = sum(ruling_counts.values())

        # Handle division by zero scenario
        if total_rulings == 0:
            log_metric_error("Ruling Outcome Distribution", ValueError("No valid ruling outcomes to calculate distribution"))
            return {}

        # Calculate proportions for each ruling outcome
        ruling_distribution = {outcome: count / total_rulings for outcome, count in ruling_counts.items()}

        return ruling_distribution

    except Exception as e:
        log_metric_error("Ruling Outcome Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, log_metric_error

def Legal_References_Usage(data: Dict[str, Any]) -> Dict[str, int]:
    """
    计算指标: Legal References Usage
    描述: This metric tracks how often different legal references are cited during the simulation.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为法律引用，值为引用次数
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'legal_references' variable from the data
        legal_references = safe_list(safe_get(data, 'legal_references', []))

        # Initialize a dictionary to count occurrences of each legal reference
        reference_count = {}

        # Iterate through the legal references and count each occurrence
        for reference in legal_references:
            if isinstance(reference, str) and reference:  # Ensure the reference is a valid non-empty string
                if reference in reference_count:
                    reference_count[reference] += 1
                else:
                    reference_count[reference] = 1

        return reference_count

    except Exception as e:
        log_metric_error("Legal References Usage", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Overtime_Hours_per_Employee': Average_Overtime_Hours_per_Employee,
    'Ruling_Outcome_Distribution': Ruling_Outcome_Distribution,
    'Legal_References_Usage': Legal_References_Usage,
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
