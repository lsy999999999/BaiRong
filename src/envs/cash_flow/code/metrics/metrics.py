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
from onesim.monitor.utils import safe_get, safe_list, safe_avg, log_metric_error

def Average_Cash_Reserves_of_Companies(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Average Cash Reserves of Companies
    描述: Measures the average cash reserves across all CompanyAgents to assess overall liquidity in the system.
    可视化类型: line
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为系列名称，值为对应数值
    """
    try:
        # Access the 'cash_reserves' variable from CompanyAgent
        cash_reserves_list = safe_list(safe_get(data, 'cash_reserves', []))
        
        # Calculate the average cash reserves excluding None values
        average_cash_reserves = safe_avg(cash_reserves_list, default=0)
        
        # Return result as a dictionary for line visualization
        return {'Average Cash Reserves': average_cash_reserves}
    
    except Exception as e:
        # Log any errors encountered during metric calculation
        log_metric_error("Average Cash Reserves of Companies", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {'Average Cash Reserves': 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Total_Loan_Amount_Approved_by_Banks(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Total Loan Amount Approved by Banks
    描述: Tracks the total amount of loans approved by all BankAgents, indicating the level of financial support provided to companies.
    可视化类型: bar
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
    """
    try:
        # Attempt to retrieve the 'approved_loan_amount' list from the data
        approved_loan_amounts = safe_list(safe_get(data, 'approved_loan_amount', []))

        # Calculate the total sum of approved loan amounts, ignoring None values
        total_approved_loans = safe_sum(approved_loan_amounts, default=0)

        # Return the result in the appropriate format for a bar chart
        return {"Total Approved Loan Amount": total_approved_loans}

    except Exception as e:
        # Log any exceptions that occur during the calculation
        log_metric_error("Total Loan Amount Approved by Banks", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Total Approved Loan Amount": 0}

from typing import Dict, Any
from onesim.monitor.utils import safe_get, safe_list, safe_sum, log_metric_error

def Consumer_Spending_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """
    计算指标: Consumer Spending Distribution
    描述: Shows the distribution of spending amounts by consumers, providing insight into consumer behavior and its impact on company revenue.
    可视化类型: pie
    
    Args:
        data: 包含所有变量的数据字典，注意agent变量是列表形式
        
    Returns:
        返回字典，键为分类，值为对应数值
        - pie: 返回字典，键为分类，值为对应比例
        
    注意:
        此函数处理各种异常情况，包括None值、空列表和类型错误等
    """
    try:
        # Access the spending_amount list from ConsumerAgent
        spending_amounts = safe_list(safe_get(data, 'spending_amount', []))
        
        # Define spending categories
        categories = {
            'low': (0, 50),
            'medium': (50, 200),
            'high': (200, float('inf'))
        }

        # Initialize category totals
        category_totals = {category: 0 for category in categories.keys()}

        # Aggregate spending amounts into categories
        for amount in spending_amounts:
            try:
                amount = float(amount)  # Ensure the amount is a float
                if amount is not None:
                    for category, (low, high) in categories.items():
                        if low <= amount < high:
                            category_totals[category] += amount
                            break
            except (TypeError, ValueError):
                log_metric_error("Consumer Spending Distribution", ValueError("Invalid spending amount"), {"amount": amount})

        # Calculate total spending for proportion calculation
        total_spending = safe_sum(category_totals.values())

        # Calculate proportions
        if total_spending > 0:
            category_proportions = {category: total / total_spending for category, total in category_totals.items()}
        else:
            category_proportions = {category: 0 for category in categories.keys()}

        return category_proportions

    except Exception as e:
        log_metric_error("Consumer Spending Distribution", e, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {category: 0 for category in categories.keys()}

# 指标函数字典，用于查找
METRIC_FUNCTIONS = {
    'Average_Cash_Reserves_of_Companies': Average_Cash_Reserves_of_Companies,
    'Total_Loan_Amount_Approved_by_Banks': Total_Loan_Amount_Approved_by_Banks,
    'Consumer_Spending_Distribution': Consumer_Spending_Distribution,
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
