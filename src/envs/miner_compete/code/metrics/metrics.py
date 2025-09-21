# -*- coding: utf-8 -*-
"""
自动生成的监控指标计算模块
"""

from typing import Dict, Any, List, Optional, Union, Callable
from loguru import logger
from onesim.monitor.utils import (
    safe_get, safe_number, safe_list, safe_sum,
    safe_count, log_metric_error
)

# ====== 可选：首次打印 data 的 key，帮助排查数据管道 ======
_PRINTED_KEYS_ONCE = {"done": False}
def _debug_print_keys_once(data: Dict[str, Any], where: str):
    if not _PRINTED_KEYS_ONCE["done"]:
        try:
            logger.debug(f"[metrics:{where}] incoming keys: {list(data.keys())}")
        finally:
            _PRINTED_KEYS_ONCE["done"] = True

# ========== 1) 资源开采率 ==========

def ResourceExploitationRate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: ResourceExploitationRate
    描述: The rate at which resources are being exploited by miners over time.
    可视化类型: line
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("ResourceExploitationRate", ValueError("Invalid data input"), {"data": data})
            return {}

        # Access global_map_state
        global_map_state = safe_get(data, 'global_map_state')
        if global_map_state is None:
            log_metric_error("ResourceExploitationRate", ValueError("Missing global_map_state"))
            return {}

        # Access current_state list
        current_state_list = safe_list(safe_get(data, 'current_state', []))
        if not current_state_list:
            log_metric_error("ResourceExploitationRate", ValueError("Missing current_state"))
            return {}

        # Count the number of cells being exploited
        exploitation_count = safe_count(current_state_list, predicate=lambda x: x == 'exploited')

        # Return result in appropriate format
        result = {'exploitation_rate': exploitation_count}
        return result
    except Exception as e:
        log_metric_error("ResourceExploitationRate", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def EnergyInvestmentDistribution(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: EnergyInvestmentDistribution
    描述: The distribution of energy investments made by miners over time.
    可视化类型: bar
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Check if required variables exist and validate input data
        if not data or not isinstance(data, dict):
            log_metric_error("EnergyInvestmentDistribution", ValueError("Invalid data input"), {"data": data})
            return {}

        # Access miner_id and investment_strategy
        miner_ids = safe_list(safe_get(data, 'miner_id', []))
        investment_strategies = safe_list(safe_get(data, 'investment_strategy', []))

        # Check if lists are empty
        if not miner_ids or not investment_strategies:
            log_metric_error("EnergyInvestmentDistribution", ValueError("Empty lists for miner_id or investment_strategy"))
            return {}

        # Initialize result dictionary
        result = {}

        # Iterate over miner_ids and investment_strategies
        for miner_id, investment_strategy in zip(miner_ids, investment_strategies):
            if miner_id is None or investment_strategy is None:
                continue

            # Sum energy investments for each miner
            total_energy_investment = safe_sum(investment_strategy.get('energy_investment', []))
            result[miner_id] = total_energy_investment

        return result
    except Exception as e:
        log_metric_error("EnergyInvestmentDistribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}

from typing import Dict, Any

def ResolutionOutcomeSuccessRate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算指标: ResolutionOutcomeSuccessRate
    描述: The success rate of resolution outcomes in land disputes over time.
    可视化类型: pie
    更新频率: 5 秒
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        根据可视化类型返回不同格式的结果:
        - line: 返回字典，键为系列名称，值为对应数值
        - bar/pie: 返回字典，键为分类，值为对应数值
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        if not isinstance(data, dict):
            log_metric_error("ResolutionOutcomeSuccessRate", ValueError("Invalid data"))
            return {"Success": 0, "Failure": 0}

        _debug_print_keys_once(data, "ResolutionOutcomeSuccessRate")

        def _count_from_any(obj: Any) -> (int, int):
            """返回 (successes, failures)"""
            if obj is None:
                return 0, 0
            # 1) list 形态
            if isinstance(obj, list):
                # 支持 list[str] 或 list[dict]
                succ = 0
                fail = 0
                for it in obj:
                    if isinstance(it, str):
                        if it.lower() == "success":
                            succ += 1
                        elif it.lower() == "failure":
                            fail += 1
                    elif isinstance(it, dict):
                        # 尝试从键里找 "status"/"outcome"/"result"
                        val = it.get('status') or it.get('outcome') or it.get('result')
                        if isinstance(val, str):
                            if val.lower() == "success":
                                succ += 1
                            elif val.lower() == "failure":
                                fail += 1
                return succ, fail

            # 2) dict 形态
            if isinstance(obj, dict):
                # 两种语义：
                # a) 计数字典：{"success": 3, "failure": 1}
                lower_keys = {str(k).lower(): k for k in obj.keys()}
                if "success" in lower_keys or "failure" in lower_keys:
                    s_k = lower_keys.get("success")
                    f_k = lower_keys.get("failure")
                    succ = int(obj.get(s_k, 0) or 0)
                    fail = int(obj.get(f_k, 0) or 0)
                    return succ, fail
                # b) 映射：coord -> "success"/"failure"
                succ = 0
                fail = 0
                for v in obj.values():
                    if isinstance(v, str):
                        if v.lower() == "success":
                            succ += 1
                        elif v.lower() == "failure":
                            fail += 1
                    elif isinstance(v, dict):
                        val = v.get('status') or v.get('outcome') or v.get('result')
                        if isinstance(val, str):
                            if val.lower() == "success":
                                succ += 1
                            elif val.lower() == "failure":
                                fail += 1
                return succ, fail

            # 3) str 形态
            if isinstance(obj, str):
                s = obj.lower().strip()
                if s == "success":
                    return 1, 0
                if s == "failure":
                    return 0, 1
                return 0, 0

            # 其它形态
            return 0, 0

        # 主数据源
        status = safe_get(data, 'resolution_status')
        s1, f1 = _count_from_any(status)

        # 兜底数据源（按需启用你们的真实键名）
        if s1 + f1 == 0:
            for alt_key in ('resolution_outcome', 'adjudication_results', 'resolve_log'):
                alt = safe_get(data, alt_key)
                s1, f1 = _count_from_any(alt)
                if s1 + f1 > 0:
                    break

        total = s1 + f1
        if total == 0:
            # 没有任何判例，返回“零饼图”，而不是报错
            return {"Success": 0, "Failure": 0}

        success_rate = safe_number(s1 / total)
        return {"Success": success_rate, "Failure": 1 - success_rate}

    except Exception as e:
        log_metric_error("ResolutionOutcomeSuccessRate", e, {"has_data": isinstance(data, dict)})
        return {"Success": 0, "Failure": 0}

# 注册字典
METRIC_FUNCTIONS: Dict[str, Callable] = {
    'ResourceExploitationRate': ResourceExploitationRate,
    'EnergyInvestmentDistribution': EnergyInvestmentDistribution,
    'ResolutionOutcomeSuccessRate': ResolutionOutcomeSuccessRate,
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
