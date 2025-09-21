from __future__ import annotations

from typing import Any, Dict, List, Optional

from onesim.events import Event


def _coord_to_list(value: Any) -> List[int]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return [int(value[0]), int(value[1])]
        except (TypeError, ValueError):
            return []
    if isinstance(value, str):
        stripped = value.strip().strip("()[]")
        if not stripped:
            return []
        parts = stripped.split(",")
        if len(parts) != 2:
            return []
        try:
            return [int(parts[0]), int(parts[1])]
        except ValueError:
            return []
    return []


class StartEvent(Event):
    """Start-of-round observation event."""

    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        round_index: int,
        stamina_budget: int,
        max_mining_per_plot: int,
        ownership_map: List[List[Optional[str]]],
        public_log: List[Dict[str, Any]],
        personal_summary: Optional[Dict[str, Any]] = None,
        run_seed: str = "0",
        **kwargs: Any,
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.round_index = int(round_index)
        self.stamina_budget = int(stamina_budget)
        self.max_mining_per_plot = int(max_mining_per_plot)
        self.ownership_map = ownership_map
        self.public_log = public_log
        self.personal_summary = personal_summary or {}
        self.run_seed = str(run_seed)


class MapObservedEvent(Event):
    """Internal trigger for the miner to decide actions."""

    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        round_index: int,
        **kwargs: Any,
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.round_index = int(round_index)


class ActionBundleEvent(Event):
    """Submission of an action bundle from a miner to the environment."""

    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        round_index: int,
        claims: Optional[List[Any]] = None,
        raids: Optional[List[Any]] = None,
        defend: Optional[List[Dict[str, Any]]] = None,
        mining: Optional[List[Dict[str, Any]]] = None,
        priority: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.round_index = int(round_index)
        self.claims = [coord for coord in (self._normalize_coords(claims))]
        self.raids = [coord for coord in (self._normalize_coords(raids))]
        self.defend = self._normalize_defend(defend)
        self.mining = self._normalize_mining(mining)
        self.priority = self._normalize_priority(priority)

    def _normalize_coords(self, coords: Optional[List[Any]]) -> List[List[int]]:
        if not coords:
            return []
        result: List[List[int]] = []
        for coord in coords:
            coord_list = _coord_to_list(coord)
            if coord_list:
                result.append(coord_list)
        return result

    def _normalize_defend(self, defend: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if not defend:
            return []
        normalized: List[Dict[str, Any]] = []
        for entry in defend:
            if isinstance(entry, dict):
                coord = _coord_to_list(entry.get("cell"))
                if coord:
                    commit = entry.get("commit", 1)
                    try:
                        commit_val = 1 if int(commit) else 0
                    except (TypeError, ValueError):
                        commit_val = 1
                    normalized.append({"cell": coord, "commit": commit_val})
            else:
                coord = _coord_to_list(entry)
                if coord:
                    normalized.append({"cell": coord, "commit": 1})
        return normalized

    def _normalize_mining(self, mining: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if not mining:
            return []
        normalized: List[Dict[str, Any]] = []
        for entry in mining:
            if isinstance(entry, dict):
                coord = _coord_to_list(entry.get("cell"))
                if not coord:
                    continue
                try:
                    stamina = int(entry.get("stamina", 0))
                except (TypeError, ValueError):
                    stamina = 0
                normalized.append({"cell": coord, "stamina": max(0, stamina)})
            else:
                coord = _coord_to_list(entry)
                if coord:
                    normalized.append({"cell": coord, "stamina": 0})
        return normalized

    def _normalize_priority(self, priority: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(priority, dict):
            return {}
        normalized: Dict[str, Any] = {}
        category_order = priority.get("category_order")
        if isinstance(category_order, list):
            normalized["category_order"] = [
                str(cat)
                for cat in category_order
                if str(cat) in {"claims", "raids", "defend", "mining"}
            ]
        for key in ["claims_order", "raids_order", "defend_order", "mining_order"]:
            values = priority.get(key)
            if isinstance(values, list):
                normalized[key] = [coord for coord in self._normalize_coords(values)]
        return normalized


class RoundResolutionEvent(Event):
    """Round summary dispatched by the environment."""

    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        round_index: int,
        stamina_budget: int,
        stamina_spent: int,
        stamina_submitted: int,
        gold_mined: int,
        cumulative_gold: int,
        executed_plan: Dict[str, Any],
        invalid_actions: Dict[str, Any],
        clipped_actions: Dict[str, Any],
        plots_owned_after: List[Any],
        plots_gained: List[Any],
        plots_lost: List[Any],
        mining_results: List[Dict[str, Any]],
        ownership_after: List[List[Optional[str]]],
        public_log_entry: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.round_index = int(round_index)
        self.stamina_budget = int(stamina_budget)
        self.stamina_spent = int(stamina_spent)
        self.stamina_submitted = int(stamina_submitted)
        self.gold_mined = int(gold_mined)
        self.cumulative_gold = int(cumulative_gold)
        self.executed_plan = executed_plan
        self.invalid_actions = invalid_actions
        self.clipped_actions = clipped_actions
        self.plots_owned_after = plots_owned_after
        self.plots_gained = plots_gained
        self.plots_lost = plots_lost
        self.mining_results = mining_results
        self.ownership_after = ownership_after
        self.public_log_entry = public_log_entry
