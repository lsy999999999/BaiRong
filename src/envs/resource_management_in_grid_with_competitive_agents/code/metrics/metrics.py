# -*- coding: utf-8 -*-
"""Metric calculations for the competitive resource management environment."""

from typing import Any, Callable, Dict, Optional

from onesim.monitor.utils import (
    safe_avg,
    safe_get,
    safe_list,
    safe_number,
    safe_sum,
    log_metric_error,
)


def Total_Resource_Exploitation(data: Dict[str, Any]) -> Dict[str, float]:
    """Sum mined gold across miners for the current round."""
    try:
        raw_values = safe_list(safe_get(data, "resources_exploited", []))
        numeric_values = [safe_number(value, default=0) for value in raw_values]
        total = safe_sum(numeric_values)
        return {"Total Resource Exploitation": total}
    except Exception as exc:  # pragma: no cover - defensive
        log_metric_error("Total Resource Exploitation", exc, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Total Resource Exploitation": 0.0}


def Average_Energy_Investment(data: Dict[str, Any]) -> Dict[str, float]:
    """Average stamina spent (after clipping) by miners in the current round."""
    try:
        raw_values = safe_list(safe_get(data, "energy_investment", []))
        numeric_values = [safe_number(value, default=None) for value in raw_values if value is not None]
        if not numeric_values:
            return {"Average Stamina Spending": 0.0}
        return {"Average Stamina Spending": safe_avg(numeric_values, default=0.0)}
    except Exception as exc:  # pragma: no cover - defensive
        log_metric_error("Average Stamina Spending", exc, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {"Average Stamina Spending": 0.0}


def Land_Ownership_Distribution(data: Dict[str, Any]) -> Dict[str, float]:
    """Compute ownership share per miner."""
    try:
        owners = safe_list(safe_get(data, "land_cells_owned", []))
        counts: Dict[str, int] = {}
        for owner in owners:
            if owner in (None, "", "None"):
                continue
            owner_id = str(owner)
            counts[owner_id] = counts.get(owner_id, 0) + 1
        total_owned = safe_sum(list(counts.values()))
        if total_owned == 0:
            return {}
        return {owner: count / total_owned for owner, count in counts.items()}
    except Exception as exc:  # pragma: no cover - defensive
        log_metric_error("Land Ownership Distribution", exc, {"data_keys": list(data.keys()) if isinstance(data, dict) else None})
        return {}


METRIC_FUNCTIONS: Dict[str, Callable[[Dict[str, Any]], Dict[str, float]]] = {
    "Total_Resource_Exploitation": Total_Resource_Exploitation,
    "Average_Energy_Investment": Average_Energy_Investment,
    "Land_Ownership_Distribution": Land_Ownership_Distribution,
}


def get_metric_function(function_name: str) -> Optional[Callable[[Dict[str, Any]], Dict[str, float]]]:
    """Retrieve a metric function by name."""
    return METRIC_FUNCTIONS.get(function_name)
