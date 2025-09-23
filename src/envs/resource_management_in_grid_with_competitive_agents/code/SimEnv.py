from __future__ import annotations

import hashlib
import inspect
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from onesim.simulator import BasicSimEnv
from .events import ActionBundleEvent, RoundResolutionEvent, StartEvent

Coordinate = Tuple[int, int]


class SimEnv(BasicSimEnv):
    """Simulation environment for competitive miners on a shared grid."""

    DEFAULT_ROWS = 10
    DEFAULT_COLS = 10
    DEFAULT_STAMINA = 10
    DEFAULT_S_MAX = 3

    def __init__(
        self,
        name: str,
        event_bus,
        data: Optional[Dict[str, Any]] = None,
        start_targets: Optional[Dict[str, Any]] = None,
        end_targets: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        agents: Optional[Dict[str, Any]] = None,
        env_path: Optional[str] = None,
        trail_id: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
            event_bus=event_bus,
            data=data,
            start_targets=start_targets,
            end_targets=end_targets,
            config=config,
            agents=agents,
            env_path=env_path,
            trail_id=trail_id,
            output_dir=output_dir,
        )

        # Register environment-specific events
        self.register_event("ActionBundleEvent", "handle_action_bundle")

        # Ensure default configuration
        self.data.setdefault("grid_rows", self.DEFAULT_ROWS)
        self.data.setdefault("grid_cols", self.DEFAULT_COLS)
        self.data.setdefault("stamina_budget", self.DEFAULT_STAMINA)
        self.data.setdefault("max_mining_per_plot", self.DEFAULT_S_MAX)
        self.data.setdefault("run_seed", "0")
        self.data.setdefault("ownership", {})
        self.data.setdefault("public_log", [])
        self.data.setdefault("round_submissions", {})
        self.data.setdefault("round_agent_summaries", {})
        self.data.setdefault("agent_cumulative_gold", {})

        # Runtime cache that tracks per-round submissions and state snapshots
        self._round_cache: Dict[int, Dict[str, Any]] = {}

    async def initialize(self):
        """Extend base initialization to ensure caches exist."""
        await super().initialize()
        # Warm up cache for the first round
        async with self._lock:
            self._ensure_round_cache(self.current_step)

    async def _create_start_event(self, target_id: str) -> StartEvent:
        """Create the round start event sent to each miner."""
        async with self._lock:
            round_idx = self.current_step
            round_cache = self._ensure_round_cache(round_idx)
            rows, cols = self._grid_dimensions()

            ownership_matrix = self._ownership_matrix(rows, cols, round_cache["ownership_start"])
            last_log = self._latest_public_log()
            personal_summary = self._personal_summary(round_idx - 1, target_id)

            stamina_budget = round_cache.get("stamina_budget", self.DEFAULT_STAMINA)
            max_mining = round_cache.get("max_mining", self.DEFAULT_S_MAX)
            run_seed = str(round_cache.get("run_seed", self.data.get("run_seed", "0")))
            source_id = self.data.get("environment_id", "ENV")

        return StartEvent(
            from_agent_id=source_id,
            to_agent_id=target_id,
            round_index=round_idx,
            stamina_budget=stamina_budget,
            max_mining_per_plot=max_mining,
            ownership_map=ownership_matrix,
            public_log=last_log,
            personal_summary=personal_summary,
            run_seed=run_seed,
        )

    async def handle_action_bundle(self, event: ActionBundleEvent) -> None:
        """Receive and sanitize an action bundle submission from a miner."""
        agent_id = event.from_agent_id
        round_idx = event.round_index or self.current_step

        async with self._lock:
            round_cache = self._ensure_round_cache(round_idx)
            ownership_start = deepcopy(round_cache["ownership_start"])
            stamina_budget = round_cache.get("stamina_budget", self.DEFAULT_STAMINA)
            max_mining = round_cache.get("max_mining", self.DEFAULT_S_MAX)

        parsed_bundle = self._parse_action_bundle_event(event)
        sanitized_plan = self._sanitize_action_bundle(
            agent_id=agent_id,
            bundle=parsed_bundle,
            ownership_start=ownership_start,
            stamina_budget=stamina_budget,
            max_mining=max_mining,
        )

        async with self._lock:
            round_cache = self._ensure_round_cache(round_idx)
            round_cache.setdefault("submissions", {})[agent_id] = sanitized_plan
            serialized = self._serialize_plan_for_storage(sanitized_plan)
            round_cache.setdefault("serialized_submissions", {})[agent_id] = serialized

            submissions = self.data.setdefault("round_submissions", {})
            submissions.setdefault(round_idx, {})[agent_id] = deepcopy(serialized)

            expected_agents = self._resource_miner_ids()
            ready = (
                bool(expected_agents)
                and expected_agents.issubset(round_cache["submissions"].keys())
                and not round_cache.get("resolving")
                and not round_cache.get("resolved")
            )

        if ready:
            await self._resolve_round(round_idx)

    async def _resolve_round(self, round_idx: int) -> None:
        """Resolve claims, raids, and mining once all submissions arrive."""
        async with self._lock:
            round_cache = self._round_cache.get(round_idx)
            if not round_cache:
                logger.warning(f"No round cache found for round {round_idx}; skipping resolution")
                return
            if round_cache.get("resolved") or round_cache.get("resolving"):
                return

            submissions = round_cache.get("submissions", {})
            if not submissions:
                logger.warning(f"No submissions for round {round_idx}; skipping resolution")
                return

            round_cache["resolving"] = True
            ownership_start = deepcopy(round_cache["ownership_start"])
            stamina_budget = round_cache.get("stamina_budget", self.DEFAULT_STAMINA)
            max_mining = round_cache.get("max_mining", self.DEFAULT_S_MAX)
            run_seed = str(round_cache.get("run_seed", self.data.get("run_seed", "0")))
            rows, cols = self._grid_dimensions()
        # --- Conflict resolution executed outside lock ---
        final_ownership, cell_logs, agent_gold, mining_results = self._resolve_conflicts(
            submissions=submissions,
            ownership_start=ownership_start,
            max_mining=max_mining,
            run_seed=run_seed,
            round_idx=round_idx,
            rows=rows,
            cols=cols,
        )

        actual_mining_spent = {
            agent_id: sum(results.values())
            for agent_id, results in mining_results.items()
        }

        agent_summaries: Dict[str, Dict[str, Any]] = {}
        cumulative_gold: Dict[str, int] = {}
        resources_exploited: List[int] = []
        energy_spent: List[int] = []
        land_cells_owned: List[Optional[str]] = []

        for r in range(rows):
            for c in range(cols):
                land_cells_owned.append(final_ownership.get((r, c), None))

        ownership_after_matrix = self._ownership_matrix(rows, cols, final_ownership)
        serialized_log = [self._serialize_cell_log(entry) for entry in cell_logs]

        async with self._lock:
            # Update ownership state
            ownership_dict = {
                self._coord_key(coord): owner for coord, owner in final_ownership.items() if owner is not None
            }
            self.data["ownership"] = ownership_dict

            # Update public log history
            public_log = self.data.setdefault("public_log", [])
            public_log.append(deepcopy(serialized_log))
            self.data["public_log"] = public_log

            # Update cumulative gold
            cumulative_gold = self.data.setdefault("agent_cumulative_gold", {})

            round_cache = self._round_cache.setdefault(round_idx, {})
            start_owner_sets = self._owner_sets_from_map(ownership_start)
            end_owner_sets = self._owner_sets_from_map(final_ownership)

            serialized_store = round_cache.setdefault("serialized_submissions", {})
            submissions_store = self.data.setdefault("round_submissions", {}).setdefault(round_idx, {})

            for agent_id, plan in submissions.items():
                claims_list = plan.get("claims", [])
                raids_list = plan.get("raids", [])
                defend_map = plan.get("defend", {})
                planned_cost = plan.get("planned_cost", plan.get("final_cost", 0))

                base_action_cost = len(claims_list) + len(raids_list) + sum(defend_map.values())
                mining_spent = actual_mining_spent.get(agent_id, 0)
                actual_cost = base_action_cost + mining_spent

                plan["planned_cost"] = planned_cost
                plan["actual_mining_spent"] = mining_spent
                plan["final_cost"] = actual_cost

                plan_serialized = self._serialize_plan_for_storage(plan)
                serialized_store[agent_id] = deepcopy(plan_serialized)
                submissions_store[agent_id] = deepcopy(plan_serialized)

                mined_amount = agent_gold.get(agent_id, 0)
                cumulative_gold[agent_id] = cumulative_gold.get(agent_id, 0) + mined_amount

                summary = self._build_agent_summary(
                    agent_id=agent_id,
                    plan=plan,
                    plan_serialized=plan_serialized,
                    mined_amount=mined_amount,
                    cumulative_gold=cumulative_gold[agent_id],
                    mining_results=mining_results.get(agent_id, {}),
                    start_owned=start_owner_sets.get(agent_id, set()),
                    end_owned=end_owner_sets.get(agent_id, set()),
                    round_idx=round_idx,
                    stamina_budget=stamina_budget,
                )

                agent_summaries[agent_id] = summary
                resources_exploited.append(mined_amount)
                energy_spent.append(plan["final_cost"])

            round_cache["agent_summaries"] = deepcopy(agent_summaries)
            round_cache["resolved"] = True
            round_cache.pop("resolving", None)

            summaries_store = self.data.setdefault("round_agent_summaries", {})
            summaries_store[round_idx] = deepcopy(agent_summaries)

            self.data["resources_exploited"] = resources_exploited
            self.data["energy_investment"] = energy_spent
            self.data["land_cells_owned"] = land_cells_owned

        # Dispatch resolution events outside lock
        await self._dispatch_round_results(
            round_idx=round_idx,
            agent_summaries=agent_summaries,
            ownership_after=ownership_after_matrix,
            public_log_entry=serialized_log,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _grid_dimensions(self) -> Tuple[int, int]:
        rows = int(self.data.get("grid_rows", self.DEFAULT_ROWS))
        cols = int(self.data.get("grid_cols", self.DEFAULT_COLS))
        return rows, cols

    def _ensure_round_cache(self, round_idx: int) -> Dict[str, Any]:
        cache = self._round_cache.setdefault(round_idx, {})
        if "ownership_start" not in cache:
            cache["ownership_start"] = self._current_ownership_dict()
            cache["stamina_budget"] = int(self.data.get("stamina_budget", self.DEFAULT_STAMINA))
            cache["max_mining"] = int(self.data.get("max_mining_per_plot", self.DEFAULT_S_MAX))
            cache["run_seed"] = str(self.data.get("run_seed", "0"))
            cache["submissions"] = {}
            cache["serialized_submissions"] = {}
            cache["resolved"] = False
            self.data.setdefault("round_submissions", {}).setdefault(round_idx, {})
        return cache

    def _current_ownership_dict(self) -> Dict[Coordinate, Optional[str]]:
        rows, cols = self._grid_dimensions()
        ownership_raw = self.data.get("ownership", {}) or {}
        result: Dict[Coordinate, Optional[str]] = {}
        for r in range(rows):
            for c in range(cols):
                key = self._coord_key((r, c))
                owner = ownership_raw.get(key)
                if owner in ("", None):
                    owner = None
                result[(r, c)] = owner
        return result

    def _ownership_matrix(
        self,
        rows: int,
        cols: int,
        ownership_dict: Optional[Dict[Coordinate, Optional[str]]] = None,
    ) -> List[List[Optional[str]]]:
        if ownership_dict is None:
            ownership_dict = self._current_ownership_dict()
        matrix: List[List[Optional[str]]] = []
        for r in range(rows):
            row_data: List[Optional[str]] = []
            for c in range(cols):
                row_data.append(ownership_dict.get((r, c)))
            matrix.append(row_data)
        return matrix

    def _latest_public_log(self) -> List[Dict[str, Any]]:
        public_log = self.data.get("public_log", [])
        if public_log:
            return deepcopy(public_log[-1])
        return []

    def _personal_summary(self, round_idx: int, agent_id: str) -> Dict[str, Any]:
        if round_idx < 0:
            return {}
        summaries = self.data.get("round_agent_summaries", {})
        round_summary = summaries.get(round_idx, {})
        summary = round_summary.get(agent_id, {})
        return deepcopy(summary)

    def _resource_miner_ids(self) -> Set[str]:
        if not self.agents:
            return set()
        miners = self.agents.get("ResourceMiner", {})
        if isinstance(miners, dict):
            return set(miners.keys())
        return set()

    def _parse_action_bundle_event(self, event: ActionBundleEvent) -> Dict[str, Any]:
        return {
            "claims": self._normalize_coord_list(event.claims),
            "raids": self._normalize_coord_list(event.raids),
            "defend": self._normalize_defense(event.defend),
            "mining": self._normalize_mining(event.mining),
            "priority": self._normalize_priority(event.priority),
        }

    def _normalize_coord(self, value: Any) -> Optional[Coordinate]:
        if isinstance(value, dict) and "cell" in value:
            value = value["cell"]
        if isinstance(value, str):
            value = value.strip().strip("()[]")
            if not value:
                return None
            parts = value.split(",")
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

    def _normalize_coord_list(self, values: Optional[List[Any]]) -> List[Coordinate]:
        coords: List[Coordinate] = []
        if not values:
            return coords
        for item in values:
            coord = self._normalize_coord(item)
            if coord is not None:
                coords.append(coord)
        return coords

    def _normalize_defense(self, entries: Optional[List[Dict[str, Any]]]) -> Dict[Coordinate, int]:
        defense: Dict[Coordinate, int] = {}
        if not entries:
            return defense
        for item in entries:
            coord = self._normalize_coord(item)
            commit = 1
            if isinstance(item, dict):
                commit = int(item.get("commit", 1))
            if coord is not None:
                defense[coord] = 1 if commit else 0
        return defense

    def _normalize_mining(self, entries: Optional[List[Dict[str, Any]]]) -> Dict[Coordinate, int]:
        mining: Dict[Coordinate, int] = {}
        if not entries:
            return mining
        for item in entries:
            if isinstance(item, dict):
                coord = self._normalize_coord(item.get("cell"))
                try:
                    stamina = int(item.get("stamina", 0))
                except (TypeError, ValueError):
                    stamina = 0
            else:
                coord = self._normalize_coord(item)
                stamina = 0
            if coord is not None:
                mining[coord] = max(0, stamina)
        return mining

    def _normalize_priority(self, priority: Optional[Dict[str, Any]]) -> Dict[str, List[Coordinate]]:
        if not isinstance(priority, dict):
            priority = {}
        normalized: Dict[str, List[Coordinate]] = {}
        for key, values in priority.items():
            if key == "category_order" and isinstance(values, list):
                normalized[key] = [
                    str(v)
                    for v in values
                    if isinstance(v, str) and v in {"claims", "raids", "defend", "mining"}
                ]
            elif isinstance(values, list):
                normalized[key] = self._normalize_coord_list(values)
        return normalized

    def _sanitize_action_bundle(
        self,
        agent_id: str,
        bundle: Dict[str, Any],
        ownership_start: Dict[Coordinate, Optional[str]],
        stamina_budget: int,
        max_mining: int,
    ) -> Dict[str, Any]:
        claims = []
        raids = []
        defense: Dict[Coordinate, int] = {}
        mining: Dict[Coordinate, int] = {}

        invalid: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in ["claims", "raids", "defend", "mining"]}
        clipped: Dict[str, Any] = {"claims": [], "raids": [], "defend": [], "mining": {}}

        seen_claims: Set[Coordinate] = set()
        seen_raids: Set[Coordinate] = set()

        for coord in bundle.get("claims", []):
            if not self._in_bounds(coord):
                invalid["claims"].append({"cell": coord, "reason": "out_of_bounds"})
                continue
            if ownership_start.get(coord) is not None:
                invalid["claims"].append({"cell": coord, "reason": "already_owned"})
                continue
            if coord in seen_claims:
                invalid["claims"].append({"cell": coord, "reason": "duplicate"})
                continue
            seen_claims.add(coord)
            claims.append(coord)

        for coord in bundle.get("raids", []):
            if not self._in_bounds(coord):
                invalid["raids"].append({"cell": coord, "reason": "out_of_bounds"})
                continue
            owner = ownership_start.get(coord)
            if owner is None:
                invalid["raids"].append({"cell": coord, "reason": "unowned"})
                continue
            if owner == agent_id:
                invalid["raids"].append({"cell": coord, "reason": "self_owned"})
                continue
            if coord in seen_raids:
                invalid["raids"].append({"cell": coord, "reason": "duplicate"})
                continue
            seen_raids.add(coord)
            raids.append(coord)

        for coord, commit in bundle.get("defend", {}).items():
            if not self._in_bounds(coord):
                invalid["defend"].append({"cell": coord, "reason": "out_of_bounds"})
                continue
            owner = ownership_start.get(coord)
            if owner != agent_id:
                invalid["defend"].append({"cell": coord, "reason": "not_owned"})
                continue
            if commit not in (0, 1):
                invalid["defend"].append({"cell": coord, "reason": "invalid_commit"})
                continue
            if commit == 1:
                defense[coord] = 1

        for coord, stamina in bundle.get("mining", {}).items():
            if not self._in_bounds(coord):
                invalid["mining"].append({"cell": coord, "reason": "out_of_bounds"})
                continue
            owner = ownership_start.get(coord)
            if owner != agent_id:
                invalid["mining"].append({"cell": coord, "reason": "not_owned"})
                continue
            if stamina <= 0:
                continue
            if stamina > max_mining:
                invalid["mining"].append({"cell": coord, "reason": "exceeds_cap"})
                continue
            mining[coord] = stamina

        submitted_cost = (
            len(claims)
            + len(raids)
            + sum(defense.values())
            + sum(mining.values())
        )

        category_order = bundle.get("priority", {}).get("category_order") or [
            "mining",
            "raids",
            "claims",
            "defend",
        ]
        category_order = [cat for cat in category_order if cat in {"claims", "raids", "defend", "mining"}]
        if not category_order:
            category_order = ["mining", "raids", "claims", "defend"]

        claims_order = bundle.get("priority", {}).get("claims_order") or list(claims)
        raids_order = bundle.get("priority", {}).get("raids_order") or list(raids)
        defend_order = bundle.get("priority", {}).get("defend_order") or list(defense.keys())
        mining_order = bundle.get("priority", {}).get("mining_order") or list(mining.keys())

        total_cost = submitted_cost

        for category in category_order:
            if total_cost <= stamina_budget:
                break
            if category == "mining":
                mining_order = [coord for coord in mining_order if coord in mining]
                while mining_order and total_cost > stamina_budget:
                    coord = mining_order[-1]
                    if coord not in mining:
                        mining_order.pop()
                        continue
                    mining[coord] -= 1
                    clipped["mining"][coord] = clipped["mining"].get(coord, 0) + 1
                    total_cost -= 1
                    if mining[coord] <= 0:
                        mining_order.pop()
                        mining.pop(coord)
            elif category == "raids":
                raids_order = [coord for coord in raids_order if coord in raids]
                while raids_order and total_cost > stamina_budget:
                    coord = raids_order.pop()
                    if coord in raids:
                        raids.remove(coord)
                        clipped["raids"].append(coord)
                        total_cost -= 1
            elif category == "claims":
                claims_order = [coord for coord in claims_order if coord in claims]
                while claims_order and total_cost > stamina_budget:
                    coord = claims_order.pop()
                    if coord in claims:
                        claims.remove(coord)
                        clipped["claims"].append(coord)
                        total_cost -= 1
            elif category == "defend":
                defend_order = [coord for coord in defend_order if coord in defense]
                while defend_order and total_cost > stamina_budget:
                    coord = defend_order.pop()
                    if coord in defense:
                        defense.pop(coord)
                        clipped["defend"].append(coord)
                        total_cost -= 1

        plan = {
            "agent_id": agent_id,
            "claims": claims,
            "raids": raids,
            "defend": defense,
            "mining": mining,
            "orders": {
                "category_order": category_order,
                "claims_order": claims_order,
                "raids_order": raids_order,
                "defend_order": defend_order,
                "mining_order": mining_order,
            },
            "invalid": invalid,
            "clipped": clipped,
            "submitted_cost": submitted_cost,
            "planned_cost": total_cost,
            "final_cost": total_cost,
            "actual_mining_spent": 0,
        }
        return plan

    def _resolve_conflicts(
        self,
        submissions: Dict[str, Dict[str, Any]],
        ownership_start: Dict[Coordinate, Optional[str]],
        max_mining: int,
        run_seed: str,
        round_idx: int,
        rows: int,
        cols: int,
    ) -> Tuple[Dict[Coordinate, Optional[str]], List[Dict[str, Any]], Dict[str, int], Dict[str, Dict[Coordinate, int]]]:
        ownership = deepcopy(ownership_start)
        claims_per_cell: Dict[Coordinate, List[str]] = defaultdict(list)
        raids_per_cell: Dict[Coordinate, List[str]] = defaultdict(list)
        defense_map: Dict[Coordinate, str] = {}
        mining_requests: Dict[str, Dict[Coordinate, int]] = {}

        for agent_id, plan in submissions.items():
            for coord in plan["claims"]:
                claims_per_cell[coord].append(agent_id)
            for coord in plan["raids"]:
                raids_per_cell[coord].append(agent_id)
            for coord in plan["defend"]:
                defense_map[coord] = agent_id
            mining_requests[agent_id] = plan["mining"]

        cell_logs: List[Dict[str, Any]] = []
        cell_log_map: Dict[Coordinate, Dict[str, Any]] = {}

        for r in range(rows):
            for c in range(cols):
                coord = (r, c)
                start_owner = ownership_start.get(coord)
                log_entry: Dict[str, Any] = {
                    "cell": coord,
                    "start_owner": start_owner,
                    "claims": sorted(claims_per_cell.get(coord, [])),
                    "raids": sorted(raids_per_cell.get(coord, [])),
                    "defended": False,
                    "defender": None,
                    "claim_winner": None,
                    "raid_winner": None,
                }

                if start_owner is None:
                    claimants = claims_per_cell.get(coord, [])
                    if claimants:
                        winner = self._deterministic_pick(
                            participants=claimants,
                            run_seed=run_seed,
                            round_idx=round_idx,
                            coord=coord,
                            event_type="claim",
                        )
                        ownership[coord] = winner
                        log_entry["claim_winner"] = winner
                    else:
                        ownership[coord] = None
                else:
                    ownership[coord] = start_owner
                    if defense_map.get(coord) == start_owner:
                        log_entry["defended"] = True
                        log_entry["defender"] = start_owner
                    else:
                        raiders = raids_per_cell.get(coord, [])
                        if raiders:
                            winner = self._deterministic_pick(
                                participants=raiders,
                                run_seed=run_seed,
                                round_idx=round_idx,
                                coord=coord,
                                event_type="raid",
                            )
                            ownership[coord] = winner
                            log_entry["raid_winner"] = winner

                log_entry["owner_after"] = ownership.get(coord)
                log_entry["mined_output"] = {"owner": ownership.get(coord), "amount": 0}
                cell_logs.append(log_entry)
                cell_log_map[coord] = log_entry

        agent_gold: Dict[str, int] = defaultdict(int)
        mining_results: Dict[str, Dict[Coordinate, int]] = defaultdict(dict)

        for agent_id, allocations in mining_requests.items():
            for coord, amount in allocations.items():
                if ownership.get(coord) == agent_id and amount > 0:
                    mined = min(amount, max_mining)
                    agent_gold[agent_id] += mined
                    mining_results[agent_id][coord] = mined
                else:
                    mining_results[agent_id][coord] = 0

        for agent_id, results in mining_results.items():
            for coord, mined in results.items():
                entry = cell_log_map.get(coord)
                if entry is not None:
                    entry["mined_output"] = {"owner": ownership.get(coord), "amount": mined}

        return ownership, cell_logs, agent_gold, mining_results

    def _build_agent_summary(
        self,
        agent_id: str,
        plan: Dict[str, Any],
        plan_serialized: Dict[str, Any],
        mined_amount: int,
        cumulative_gold: int,
        mining_results: Dict[Coordinate, int],
        start_owned: Set[Coordinate],
        end_owned: Set[Coordinate],
        round_idx: int,
        stamina_budget: int,
    ) -> Dict[str, Any]:
        plots_owned_after = sorted(end_owned)
        plots_gained = sorted(end_owned - start_owned)
        plots_lost = sorted(start_owned - end_owned)

        summary = {
            "round_index": round_idx,
            "stamina_budget": stamina_budget,
            "stamina_submitted": plan["submitted_cost"],
            "stamina_planned": plan.get("planned_cost", plan["final_cost"]),
            "stamina_spent": plan["final_cost"],
            "mining_stamina_spent": plan.get("actual_mining_spent", 0),
            "gold_mined": mined_amount,
            "cumulative_gold": cumulative_gold,
            "executed_plan": plan_serialized,
            "invalid_actions": self._serialize_invalid(plan["invalid"]),
            "clipped_actions": self._serialize_clipped(plan["clipped"]),
            "plots_owned_after": [list(coord) for coord in plots_owned_after],
            "plots_gained": [list(coord) for coord in plots_gained],
            "plots_lost": [list(coord) for coord in plots_lost],
            "mining_results": [
                {"cell": list(coord), "output": amount}
                for coord, amount in mining_results.items()
            ],
        }
        return summary

    async def _dispatch_round_results(
        self,
        round_idx: int,
        agent_summaries: Dict[str, Dict[str, Any]],
        ownership_after: List[List[Optional[str]]],
        public_log_entry: List[Dict[str, Any]],
    ) -> None:
        env_id = self.data.get("environment_id", "ENV")
        for agent_id, summary in agent_summaries.items():
            event = RoundResolutionEvent(
                from_agent_id=env_id,
                to_agent_id=agent_id,
                round_index=round_idx,
                stamina_budget=summary.get("stamina_budget", self.DEFAULT_STAMINA),
                stamina_spent=summary.get("stamina_spent", 0),
                stamina_submitted=summary.get("stamina_submitted", 0),
                gold_mined=summary.get("gold_mined", 0),
                cumulative_gold=summary.get("cumulative_gold", 0),
                executed_plan=summary.get("executed_plan", {}),
                invalid_actions=summary.get("invalid_actions", {}),
                clipped_actions=summary.get("clipped_actions", {}),
                plots_owned_after=summary.get("plots_owned_after", []),
                plots_gained=summary.get("plots_gained", []),
                plots_lost=summary.get("plots_lost", []),
                mining_results=summary.get("mining_results", []),
                ownership_after=ownership_after,
                public_log_entry=public_log_entry,
            )
            await self.queue_event(event.to_dict())

            if self.event_bus is not None:
                dispatcher = getattr(self.event_bus, "dispatch_event", None)
                if callable(dispatcher):
                    result = dispatcher(event)
                    if inspect.isawaitable(result):
                        await result

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _in_bounds(self, coord: Coordinate) -> bool:
        rows, cols = self._grid_dimensions()
        r, c = coord
        return 0 <= r < rows and 0 <= c < cols

    def _coord_key(self, coord: Coordinate) -> str:
        return f"{coord[0]},{coord[1]}"

    def _serialize_plan_for_storage(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "claims": [list(coord) for coord in plan["claims"]],
            "raids": [list(coord) for coord in plan["raids"]],
            "defend": [
                {"cell": list(coord), "commit": commit}
                for coord, commit in plan["defend"].items()
            ],
            "mining": [
                {"cell": list(coord), "stamina": stamina}
                for coord, stamina in plan["mining"].items()
            ],
            "orders": {
                key: [list(coord) if isinstance(coord, tuple) else coord for coord in values]
                for key, values in plan["orders"].items()
            },
            "submitted_cost": plan["submitted_cost"],
            "planned_cost": plan.get("planned_cost", plan["final_cost"]),
            "final_cost": plan["final_cost"],
            "actual_mining_spent": plan.get("actual_mining_spent", 0),
            "invalid_actions": self._serialize_invalid(plan["invalid"]),
            "clipped_actions": self._serialize_clipped(plan["clipped"]),
        }

    def _serialize_invalid(self, invalid: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        serialized: Dict[str, List[Dict[str, Any]]] = {}
        for category, entries in invalid.items():
            serialized[category] = []
            for item in entries:
                coord = item.get("cell")
                serialized[category].append(
                    {
                        "cell": list(coord) if isinstance(coord, tuple) else coord,
                        "reason": item.get("reason"),
                    }
                )
        return serialized

    def _serialize_clipped(self, clipped: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(clipped, dict):
            clipped = {}

        serialized: Dict[str, Any] = {"claims": [], "raids": [], "defend": [], "mining": []}
        for category in ("claims", "raids", "defend"):
            serialized[category] = [
                list(coord) if isinstance(coord, tuple) else coord
                for coord in clipped.get(category, [])
            ]
        mining_entries = []
        for coord, amount in clipped.get("mining", {}).items():
            mining_entries.append({"cell": list(coord), "amount": amount})
        serialized["mining"] = mining_entries
        return serialized

    def _serialize_cell_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        serialized = {
            "cell": list(log_entry.get("cell", (0, 0))),
            "start_owner": log_entry.get("start_owner"),
            "claims": log_entry.get("claims", []),
            "raids": log_entry.get("raids", []),
            "defended": log_entry.get("defended", False),
            "defender": log_entry.get("defender"),
            "claim_winner": log_entry.get("claim_winner"),
            "raid_winner": log_entry.get("raid_winner"),
            "owner_after": log_entry.get("owner_after"),
            "mined_output": log_entry.get("mined_output"),
        }
        return serialized

    def _deterministic_pick(
        self,
        participants: List[str],
        run_seed: str,
        round_idx: int,
        coord: Coordinate,
        event_type: str,
    ) -> str:
        best_participant = participants[0]
        best_hash = None
        for participant in sorted(participants):
            payload = f"{run_seed}:{round_idx}:{coord[0]}:{coord[1]}:{event_type}:{participant}"
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if best_hash is None or digest < best_hash:
                best_hash = digest
                best_participant = participant
        return best_participant

    def _owner_sets_from_map(self, ownership: Dict[Coordinate, Optional[str]]) -> Dict[str, Set[Coordinate]]:
        owner_sets: Dict[str, Set[Coordinate]] = defaultdict(set)
        for coord, owner in ownership.items():
            if owner:
                owner_sets[owner].add(coord)
        return owner_sets
