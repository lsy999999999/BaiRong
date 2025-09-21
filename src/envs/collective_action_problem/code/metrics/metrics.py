# -*- coding: utf-8 -*-
"""
自动生成的监控指标计算模块
"""

from typing import Dict, Any, List, Optional, Union, Callable
import math
from loguru import logger
from onesim.monitor.utils import (
    safe_get,
    safe_number,
    safe_list,
    safe_sum,
    safe_avg,
    safe_max,
    safe_min,
    safe_count,
    log_metric_error,
)


from typing import Dict, Any
from onesim.monitor.utils import safe_list, safe_avg, log_metric_error

def Average_Cooperation_Willingness(data: Dict[str, Any]) -> Any:
    """
    计算指标: Average Cooperation Willingness
    描述: Measures the average willingness of individuals to cooperate in collective actions.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Average Cooperation Willingness", ValueError("Invalid data input"), {"data": data})
            return 0.0
        
        # Extract cooperation_willingness values from individuals
        cooperation_willingness_values = safe_list(data.get("cooperation_willingness", []))

        # Calculate the average cooperation willingness, excluding None values
        average_willingness = safe_avg(cooperation_willingness_values, default=0.0)

        # Return the result as a single value for line visualization type
        return average_willingness
    
    except Exception as e:
        log_metric_error("Average Cooperation Willingness", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0.0

def Collective_Action_Success_Rate(data: Dict[str, Any]) -> Any:
    """
    计算指标: Collective Action Success Rate
    描述: Indicates the proportion of time the collective action is successful.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    from onesim.monitor.utils import safe_get, safe_list, safe_count, log_metric_error

    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Collective Action Success Rate", ValueError("Invalid data input"), {"data": data})
            return 0.0

        # Retrieve collective_success variable, ensuring it's a list
        collective_success_list = safe_list(safe_get(data, "collective_success", []))

        # Count the number of successful actions (True values)
        success_count = safe_count(collective_success_list, predicate=lambda x: x is True)

        # Count the number of valid observations (non-None values)
        total_count = safe_count(collective_success_list, predicate=lambda x: x is not None)

        # Calculate the success rate
        if total_count == 0:
            return 0.0  # Avoid division by zero

        success_rate = success_count / total_count
        return success_rate

    except Exception as e:
        log_metric_error("Collective Action Success Rate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return 0.0

def Total_Group_Benefit(data: Dict[str, Any]) -> Any:
    """
    计算指标: Total Group Benefit
    描述: Represents the total benefit achieved by the group from individual cooperation.
    可视化类型: bar
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回单个数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    from onesim.monitor.utils import safe_get, safe_number, log_metric_error

    try:
        # Validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("Total Group Benefit", ValueError("Invalid data input"), {"data": data})
            return {}

        # Retrieve group_benefit from the environment variables
        group_benefit = safe_get(data, "group_benefit")
        group_benefit = safe_number(group_benefit, default=0.0)

        # Prepare result for bar visualization
        result = {"Total Group Benefit": group_benefit}

        return result

    except Exception as e:
        log_metric_error("Total Group Benefit", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Cooperation_Willingness': Average_Cooperation_Willingness,
    'Collective_Action_Success_Rate': Collective_Action_Success_Rate,
    'Total_Group_Benefit': Total_Group_Benefit,
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


def test_metric_function(function_name: str, test_data: Dict[str, Any]) -> Any:
    """
    测试指标计算函数
    
    Args:
        function_name: 函数名
        test_data: 测试数据
        
    Returns:
        指标计算结果
    """
    func = get_metric_function(function_name)
    if func is None:
        raise ValueError(f"找不到指标函数: {function_name}")
    
    try:
        result = func(test_data)
        print(f"指标 {function_name} 计算结果: {result}")
        return result
    except Exception as e:
        log_metric_error(function_name, e, {"test_data": test_data})
        raise


def generate_test_data() -> Dict[str, Any]:
    """
    生成用于测试的示例数据
    
    Returns:
        示例数据字典
    """
    # 创建一个包含常见数据类型和边界情况的测试数据字典
    return {
        # 环境变量示例
        "total_steps": 100,
        "current_time": 3600,
        "resource_pool": 1000,
        
        # 正常代理变量示例（列表）
        "agent_health": [100, 90, 85, 70, None, 60],
        "agent_resources": [50, 40, 30, 20, 10, None],
        "agent_age": [10, 20, 30, 40, 50, 60],
        
        # 边界情况
        "empty_list": [],
        "none_value": None,
        "zero_value": 0,
        
        # 错误类型示例
        "should_be_list_but_single": 42,
        "invalid_number": "not_a_number",
    }


def test_all_metrics(test_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    测试所有指标函数
    
    Args:
        test_data: 测试数据，如果为None则使用生成的示例数据
        
    Returns:
        测试结果字典，键为函数名，值为计算结果或错误信息
    """
    if test_data is None:
        test_data = generate_test_data()
        
    results = {}
    for func_name, func in METRIC_FUNCTIONS.items():
        try:
            result = func(test_data)
            results[func_name] = result
        except Exception as e:
            results[func_name] = f"ERROR: {str(e)}"
            log_metric_error(func_name, e, {"test_data": test_data})
    
    return results


# 如果直接运行此模块，执行所有指标的测试
if __name__ == "__main__":
    
    print("生成测试数据...")
    test_data = generate_test_data()
    
    print("测试所有指标函数...")
    results = test_all_metrics(test_data)
    
    print("\n测试结果:")
    for func_name, result in results.items():
        print(f"{func_name}: {result}")
