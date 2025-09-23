from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from onesim.agent import GeneralAgent
from onesim.events import Event
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.profile import AgentProfile
from onesim.relationship import RelationshipManager
from .events import ActionBundleEvent, MapObservedEvent, RoundResolutionEvent, StartEvent

Coordinate = Tuple[int, int]


class ResourceMiner(GeneralAgent):
    """Miner agent that submits action bundles for each round."""

    def __init__(
        self,
        sys_prompt: Optional[str] = None,
        model_config_name: Optional[str] = None,
        event_bus_queue=None,
        profile: Optional[AgentProfile] = None,
        memory: Optional[MemoryStrategy] = None,
        planning: Optional[PlanningBase] = None,
        relationship_manager: Optional[RelationshipManager] = None,
    ) -> None:
        super().__init__(
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            event_bus_queue=event_bus_queue,
            profile=profile,
            memory=memory,
            planning=planning,
            relationship_manager=relationship_manager,
        )

        self.register_event("StartEvent", "observe_round_state")
        self.register_event("MapObservedEvent", "decide_action_bundle")
        self.register_event("RoundResolutionEvent", "handle_round_resolution")

    async def observe_round_state(self, event: StartEvent) -> List[Event]:
        """Store the round context and trigger decision making."""
        round_index = getattr(event, "round_index", 0)
        ownership_map = getattr(event, "ownership_map", [])
        public_log = getattr(event, "public_log", [])
        stamina_budget = getattr(event, "stamina_budget", 10)
        max_mining = getattr(event, "max_mining_per_plot", 3)
        personal_summary = getattr(event, "personal_summary", {})
        run_seed = getattr(event, "run_seed", "0")

        round_context = {
            "round_index": round_index,
            "ownership_map": ownership_map,
            "previous_public_log": public_log,
            "stamina_budget": stamina_budget,
            "max_mining_per_plot": max_mining,
            "personal_summary": personal_summary,
            "run_seed": run_seed,
        }

        self.profile.update_data("round_context", round_context)
        self.profile.update_data("action_bundle_submitted", False)

        observation_event = MapObservedEvent(
            from_agent_id=self.profile_id,
            to_agent_id=self.profile_id,
            round_index=round_index,
        )
        return [observation_event]

    async def decide_action_bundle(self, event: MapObservedEvent) -> List[Event]:
        """Generate an action bundle proposal for the current round."""
        context = self.profile.get_data("round_context", {}) or {}
        if not context:
            logger.warning("Round context missing; skipping action bundle generation")
            return []

        round_index = context.get("round_index", 0)
        stamina_budget = context.get("stamina_budget", 10)
        max_mining = context.get("max_mining_per_plot", 3)
        ownership_map = context.get("ownership_map", [])
        public_log = context.get("previous_public_log", [])
        personal_summary = context.get("personal_summary", {})

        observation_payload = {
            "round_index": round_index,
            "stamina_budget": stamina_budget,
            "max_mining_per_plot": max_mining,
            "ownership_map": ownership_map,
            "previous_public_log": public_log,
            "previous_round_summary": personal_summary,
        }

        observation = json.dumps(observation_payload, ensure_ascii=False)

        instruction = (
            "You are a miner competing for gold on a 10x10 grid.\n"
            "Each round you have a stamina budget S = {stamina_budget}.\n"
            "Valid actions are: CLAIM (cost 1) on currently unowned plots, RAID (cost 1) on plots owned by other agents, DEFEND (0 or 1) on plots you currently own, and MINE allocating integer stamina in [0, {max_mining}] on plots you currently own.\n"
            "Illegal actions (out of bounds targets, claiming owned plots, raiding unowned plots, mining or defending plots you do not own, mining over the cap) will be removed before budgeting.\n"
            "If the total stamina exceeds S, the simulator removes actions starting from the end of your declared priority order; if none provided the default removal order is Mining → Raids → Claims → Defense.\n"
            "Return a JSON object with this structure: \n"
            "{{\n"
            "  \"claims\": [[row, col], ...],\n"
            "  \"raids\": [[row, col], ...],\n"
            "  \"defend\": [[row, col], ...] or [{{\"cell\": [row, col], \"commit\": 1}}],\n"
            "  \"mining\": [{{\"cell\": [row, col], \"stamina\": n}}, ...],\n"
            "  \"priority\": {{\n"
            "      \"category_order\": [\"mining\", \"raids\", \"claims\", \"defend\"],\n"
            "      \"claims_order\": [[row, col], ...],\n"
            "      \"raids_order\": [[row, col], ...],\n"
            "      \"defend_order\": [[row, col], ...],\n"
            "      \"mining_order\": [[row, col], ...]\n"
            "  }}\n"
            "}}\n"
            "Only include categories you wish to prioritise. Use integers for stamina allocations."
        ).format(stamina_budget=stamina_budget, max_mining=max_mining)

        raw_result = await self.generate_reaction(instruction, observation)
        result = self._coerce_to_dict(raw_result)
        action_payload = self._parse_action_plan(result)

        if not action_payload:
            logger.warning("No valid action payload generated; submitting empty bundle")
            action_payload = {
                "claims": [],
                "raids": [],
                "defend": [],
                "mining": [],
                "priority": {},
            }

        self.profile.update_data("proposed_action_bundle", action_payload)
        self.profile.update_data("action_bundle_submitted", True)

        action_event = ActionBundleEvent(
            from_agent_id=self.profile_id,
            to_agent_id="ENV",
            round_index=round_index,
            claims=action_payload["claims"],
            raids=action_payload["raids"],
            defend=action_payload["defend"],
            mining=action_payload["mining"],
            priority=action_payload["priority"],
        )
        return [action_event]

    async def handle_round_resolution(self, event: RoundResolutionEvent) -> List[Event]:
        """Process the environment's round summary."""
        round_summary = {
            "round_index": getattr(event, "round_index", 0),
            "stamina_budget": getattr(event, "stamina_budget", 0),
            "stamina_spent": getattr(event, "stamina_spent", 0),
            "stamina_submitted": getattr(event, "stamina_submitted", 0),
            "stamina_breakdown": getattr(event, "stamina_breakdown", {}),
            "gold_mined": getattr(event, "gold_mined", 0),
            "cumulative_gold": getattr(event, "cumulative_gold", 0),
            "executed_plan": getattr(event, "executed_plan", {}),
            "invalid_actions": getattr(event, "invalid_actions", {}),
            "clipped_actions": getattr(event, "clipped_actions", {}),
            "land_summary": getattr(event, "land_summary", {}),
            "plots_owned_before": getattr(event, "plots_owned_before", []),
            "plots_owned_before_count": getattr(event, "plots_owned_before_count", 0),
            "plots_owned_after": getattr(event, "plots_owned_after", []),
            "plots_owned_after_count": getattr(event, "plots_owned_after_count", 0),
            "plots_gained": getattr(event, "plots_gained", []),
            "plots_lost": getattr(event, "plots_lost", []),
            "mining_results": getattr(event, "mining_results", []),
            "public_log_entry": getattr(event, "public_log_entry", []),
        }

        self.profile.update_data("last_round_summary", round_summary)
        self.profile.update_data("round_context", {
            **self.profile.get_data("round_context", {}),
            "previous_public_log": getattr(event, "public_log_entry", []),
            "ownership_map": getattr(event, "ownership_after", []),
            "personal_summary": round_summary,
        })

        total_gold = self.profile.get_data("total_gold", 0) or 0
        total_gold += round_summary.get("gold_mined", 0)
        self.profile.update_data("total_gold", total_gold)

        return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _coerce_to_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned.replace("json", "", 1)
            try:
                return json.loads(cleaned)
            except Exception:
                logger.debug("Failed to parse string response into JSON")
                return {}
        return {}

    def _parse_action_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        claims = self._normalize_coord_list(plan.get("claims"))
        raids = self._normalize_coord_list(plan.get("raids"))
        defend_entries = self._normalize_defend_entries(plan.get("defend"))
        mining_entries = self._normalize_mining_entries(plan.get("mining"))
        priority_payload = self._normalize_priority(plan.get("priority"))

        return {
            "claims": [list(coord) for coord in claims],
            "raids": [list(coord) for coord in raids],
            "defend": defend_entries,
            "mining": mining_entries,
            "priority": priority_payload,
        }

    def _normalize_coord(self, value: Any) -> Optional[Coordinate]:
        if isinstance(value, dict) and "cell" in value:
            value = value["cell"]
        if isinstance(value, str):
            cleaned = value.strip().strip("()[]")
            if not cleaned:
                return None
            parts = cleaned.split(",")
            if len(parts) != 2:
                return None
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                return None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            try:
                return int(value[0]), int(value[1])
            except (TypeError, ValueError):
                return None
        return None

    def _normalize_coord_list(self, values: Any) -> List[Coordinate]:
        coords: List[Coordinate] = []
        if not isinstance(values, list):
            return coords
        for item in values:
            coord = self._normalize_coord(item)
            if coord is not None:
                coords.append(coord)
        return coords

    def _normalize_defend_entries(self, values: Any) -> List[Dict[str, Any]]:
        if values is None:
            return []
        entries: List[Dict[str, Any]] = []
        if isinstance(values, dict):
            for key, commit in values.items():
                coord = self._normalize_coord(key)
                if coord is None:
                    continue
                try:
                    commit_val = int(commit)
                except (TypeError, ValueError):
                    commit_val = 1
                entries.append({"cell": list(coord), "commit": 1 if commit_val else 0})
            return entries
        if isinstance(values, list):
            for item in values:
                coord = self._normalize_coord(item)
                if coord is not None:
                    entries.append({"cell": list(coord), "commit": 1})
        return entries

    def _normalize_mining_entries(self, values: Any) -> List[Dict[str, Any]]:
        if not isinstance(values, list):
            return []
        entries: List[Dict[str, Any]] = []
        for item in values:
            if isinstance(item, dict):
                coord = self._normalize_coord(item.get("cell"))
                try:
                    stamina = int(item.get("stamina", 0))
                except (TypeError, ValueError):
                    stamina = 0
            else:
                coord = self._normalize_coord(item)
                stamina = 0
            if coord is None:
                continue
            entries.append({"cell": list(coord), "stamina": max(0, stamina)})
        return entries

    def _normalize_priority(self, values: Any) -> Dict[str, Any]:
        if not isinstance(values, dict):
            return {}
        normalized: Dict[str, Any] = {}
        category_order = values.get("category_order")
        if isinstance(category_order, list):
            normalized["category_order"] = [
                str(cat)
                for cat in category_order
                if str(cat) in {"claims", "raids", "defend", "mining"}
            ]
        for key in ["claims_order", "raids_order", "defend_order", "mining_order"]:
            if isinstance(values.get(key), list):
                normalized[key] = [list(coord) for coord in self._normalize_coord_list(values[key])]
        return normalized
