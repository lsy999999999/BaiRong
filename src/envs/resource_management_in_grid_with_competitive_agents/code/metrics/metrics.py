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
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Total_Resource_Exploitation(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Total Resource Exploitation
    描述: Measures the total resources exploited by all miners each round, providing an overview of system-level resource utilization.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回字典，键为系列名称，值为资源利用总和
    
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'resources_exploited' list from the data
        resources_exploited_list = safe_list(safe_get(data, 'resources_exploited', []))

        # Sum the resources exploited using the safe_sum function
        total_exploitation = safe_sum(resources_exploited_list)

        # Return the result as a dictionary with a series name
        result = {'Total Resource Exploitation': total_exploitation}
        return result

    except Exception as e:
        log_metric_error("Total Resource Exploitation", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Total Resource Exploitation': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_avg, log_metric_error

def Average_Energy_Investment(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Energy Investment
    描述: Shows the average energy investment by miners to contest land ownership each round, highlighting strategic behavior patterns.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回结果:
        - line: 返回字典，键为系列名称，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the 'energy_investment' list safely
        energy_investment = safe_list(safe_get(data, 'energy_investment', []))
        
        if not energy_investment:
            # Returning zero if the list is empty
            return {'Average Energy Investment': 0}

        # Calculate the average of non-None values
        valid_energy_values = [safe_number(value, default=None) for value in energy_investment if value is not None]
        
        # Calculate average, handling cases where valid values list might be empty
        average_energy_investment = safe_avg(valid_energy_values, default=0)
        
        return {'Average Energy Investment': average_energy_investment}

    except Exception as e:
        # Log any exceptions with details
        log_metric_error("Average Energy Investment", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Average Energy Investment': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

def Land_Ownership_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Land Ownership Distribution
    描述: Provides a breakdown of current land ownership among miners, indicating control distribution and dominance in grid cells.
    可视化类型: pie
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应比例
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Land Ownership Distribution", ValueError("Invalid data input"), {"data": data})
            return {}

        # Access the land_cells_owned variable
        land_cells_owned = safe_list(safe_get(data, 'land_cells_owned', []))
        
        # Count the number of land cells owned by each miner type
        ownership_counts = {}
        for cell in land_cells_owned:
            if cell is None:
                continue
            if cell not in ownership_counts:
                ownership_counts[cell] = 0
            ownership_counts[cell] += 1

        # Calculate the total number of land cells owned
        total_cells = safe_count(land_cells_owned)
        if total_cells == 0:
            log_metric_error("Land Ownership Distribution", ValueError("No land cells owned"))
            return {}

        # Calculate the proportion of land cells owned by each miner type
        ownership_proportions = {miner: count / total_cells for miner, count in ownership_counts.items()}

        return ownership_proportions
    except Exception as e:
        log_metric_error("Land Ownership Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Total_Resource_Exploitation': Total_Resource_Exploitation,
    'Average_Energy_Investment': Average_Energy_Investment,
    'Land_Ownership_Distribution': Land_Ownership_Distribution,
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
