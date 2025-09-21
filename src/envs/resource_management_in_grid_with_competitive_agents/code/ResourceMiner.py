from typing import Any, List, Optional, Tuple
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class ResourceMiner(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "observe_global_map")
        self.register_event("MapObservedEvent", "decide_action")
        self.register_event("OccupyLandDecisionEvent", "execute_occupy_or_maintain")
        self.register_event("CompeteSuccessEvent", "exploit_resources")

    async def observe_global_map(self, event: Event) -> List[Event]:
        map_state = "The current state of the grid and resource availability."
        self.profile.update_data("map_state", map_state)
        
        instruction = """
        The ResourceMiner agent needs to observe the global map to assess the current state of the grid and resource availability. 
        Based on this observation, the agent should decide on the next action. Please return the information in the following JSON format:
    
        {
        "target_ids": ["<The string ID of the ResourceMiner agent>"]
        }
        """
        
        result = await self.generate_reaction(instruction, map_state)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        events = []
        for target_id in target_ids:
            map_observed_event = MapObservedEvent(self.profile_id, target_id)
            events.append(map_observed_event)
        
        return events

    async def decide_action(self, event: Event) -> List[Event]:
        map_state = self.profile.get_data("map_state", [])
        if not map_state:
            return []
    
        observation = f"Current map state: {map_state}"
        instruction = """
        Based on the current map state observed, decide the next action for the ResourceMiner agent. 
        The map state is provided as follows: {map_state}.
        The decision should be one of the following actions: occupy, maintain, or compete for a cell.
        For 'occupy' or 'maintain', provide the cell coordinates, energy investment, and previous owner.
        For 'compete', provide the cell coordinates and energy investment.
        Please return the information according to the decided action.
        """
        
        result = await self.generate_reaction(instruction.format(map_state=map_state), observation)
        action_plan = result.get('action', None)
        cell_coordinates = result.get('cell_coordinates', (0, 0))
        energy_investment = result.get('energy_investment', 0)
        previous_owner = result.get('previous_owner', "None")
        
        if not isinstance(cell_coordinates, tuple):
            cell_coordinates = (0, 0)
        
        if not isinstance(energy_investment, int):
            energy_investment = 0
        
        if not isinstance(previous_owner, str):
            previous_owner = "None"
        
        events = []
        
        if action_plan in ["occupy", "maintain"]:
            occupy_land_event = OccupyLandDecisionEvent(self.profile_id, self.profile_id, energy_investment=energy_investment, cell_coordinates=cell_coordinates, previous_owner=previous_owner)
            events.append(occupy_land_event)
        elif action_plan == "compete":
            compete_decision_event = CompeteSuccessEvent(self.profile_id, self.profile_id, new_owner=self.profile_id, cell_coordinates=cell_coordinates)
            events.append(compete_decision_event)
        
        return events

    async def execute_occupy_or_maintain(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "OccupyLandDecisionEvent":
            return []
    
        energy_investment = event.energy_investment
        cell_coordinates = event.cell_coordinates
        previous_owner = event.previous_owner
    
        instruction = """
        The ResourceMiner agent is deciding whether to occupy or maintain land ownership based on the current energy investment and cell coordinates.
        The cell coordinates are {cell_coordinates}. The previous owner of the land is {previous_owner}.
        The energy investment is {energy_investment}.
        Please return the information in the following JSON format:
    
        {
            "target_ids": ["<The string ID of the target cell>"],
            "new_land_status": {
                "owner": "<The new owner of the land>",
                "energy_investment": "<The energy investment for the new owner>"
            }
        }
        """
        
        result = await self.generate_reaction(instruction.format(cell_coordinates=cell_coordinates, previous_owner=previous_owner, energy_investment=energy_investment))
    
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        new_land_status = result.get('new_land_status', None)
        if new_land_status:
            owner = new_land_status.get('owner', None)
            energy_investment = new_land_status.get('energy_investment', None)
            if owner and energy_investment:
                self.env.update_data("land_status", {cell_coordinates: {"owner": owner, "energy_investment": energy_investment}})
        
        return []

    async def exploit_resources(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "CompeteSuccessEvent":
            return []

        new_owner = event.new_owner if hasattr(event, 'new_owner') else None
        cell_coordinates = event.cell_coordinates

        instruction = """
        The ResourceMiner agent, having secured land ownership, should now proceed to exploit resources.
        The coordinates of the exploited land are {cell_coordinates} and the new owner is {new_owner}.
        Immediate tasks include determining the number of resources to extract.
        Return the information in this JSON format:
    
        {
            "units_exploited": "<Number of units exploited>",
            "exploit_success": "<Boolean value if the exploitation was successful or not>"
        }
        """
        
        result = await self.generate_reaction(instruction.format(cell_coordinates=cell_coordinates, new_owner=new_owner))
    
        units_exploited = result.get('units_exploited', 0)
        exploit_success = result.get('exploit_success', True)
        
        resource_exploited_event = ResourceExploitedEvent(
            from_agent_id=self.profile_id,
            to_agent_id="EnvAgent", 
            units_exploited=units_exploited,
            cell_coordinates=cell_coordinates,
            exploit_success=exploit_success
        )
        
        return [resource_exploited_event]
    
    async def execute_compete(self, event: Event) -> List[Event]:
        """
        读取上一轮所有矿工对各地块的投入(compete_intents)，
        以投入加权、确定性RNG的方式为每个地块选出赢家，
        更新环境ownership，并仅向胜者发送 CompeteSuccessEvent。

        兼容事件名：
          - "NewEvent" / "CompeteIntentEvent"（图中第7条边）
        兼容字段：
          - event.cell_coordinates: Tuple[int, int]
          - event.energy_investment: int
          - event.miner_id: str  （可无）

        共享环境键：
          - "compete_intents": List[{"agent": str, "cell": (r,c), "energy": int}]
          - "ownership": { "(r,c)": "agent_id", ... }
          - "resolved_cells": Set[str]  # 字符串化坐标 "(r,c)"
          - "seed": int | str            # 可选，用于确定性随机
        """
        try:
            # -------- 1) 读取共享的所有竞争意图 ----------
            intents = await self.get_env_data("compete_intents", [])
            if not isinstance(intents, list):
                intents = []

            # 兼容：如果调用方把当前事件也带了坐标/投入，就补上一条（幂等去重）
            def _tuple(x):
                try:
                    return (int(x[0]), int(x[1]))
                except Exception:
                    return None

            evt_cell = getattr(event, "cell_coordinates", None)
            evt_cell = _tuple(evt_cell) if evt_cell is not None else None
            evt_energy = getattr(event, "energy_investment", None)
            evt_agent = getattr(event, "miner_id", None) or self.profile_id

            if evt_cell is not None and isinstance(evt_energy, (int, float)):
                evt_rec = {"agent": evt_agent, "cell": evt_cell, "energy": int(evt_energy)}
                # 如果不存在完全相同记录，则追加（避免重复）
                if not any(
                    rec.get("agent") == evt_rec["agent"]
                    and tuple(rec.get("cell", ())) == evt_rec["cell"]
                    and int(rec.get("energy", 0)) == evt_rec["energy"]
                    for rec in intents
                ):
                    intents.append(evt_rec)
                    # 回写到环境，保证后到的agent也能看到
                    self.env.update_data("compete_intents", intents)

            if not intents:
                # 没有竞争意图，直接不做任何事
                return []

            # -------- 2) 分组：每个地块的参与者 ----------
            from collections import defaultdict
            groups = defaultdict(list)  # cell -> List[(agent, energy)]
            for rec in intents:
                cell = rec.get("cell") or rec.get("cell_coordinates")
                agent = rec.get("agent") or rec.get("miner_id") or ""
                energy = int(rec.get("energy") or rec.get("energy_investment") or 0)
                try:
                    cell = (int(cell[0]), int(cell[1]))
                except Exception:
                    continue
                groups[cell].append((str(agent), max(0, int(energy))))

            if not groups:
                return []

            # -------- 3) 读取/初始化环境状态 ----------
            ownership = await self.get_env_data("ownership", {}) or {}
            if not isinstance(ownership, dict):
                ownership = {}
            resolved_cells = set(await self.get_env_data("resolved_cells", []))

            # 确定性种子（可选）
            seed = await self.get_env_data("seed", 0)
            try:
                seed = str(seed)
            except Exception:
                seed = "0"

            # -------- 4) 为每个地块决定赢家（投入加权 + 确定性RNG） ----------
            import hashlib
            import json

            def _weighted_deterministic_pick(cell, entries, seed_str):
                """
                entries: List[(agent, energy)]
                返回: agent_id (赢家)
                """
                # 排序后编码，保证确定性
                ser = json.dumps({
                    "cell": list(cell),
                    "entries": sorted([(a, int(e)) for a, e in entries]),
                    "seed": seed_str
                }, sort_keys=True)
                h = hashlib.sha256(ser.encode()).hexdigest()
                r = int(h, 16)

                total = sum(max(0, int(e)) for _, e in entries)
                if total <= 0:
                    # 全是0投入：按均匀随机/哈希取模
                    idx = r % len(entries)
                    return entries[idx][0]

                # 加权“抽签”
                pick = r % total
                acc = 0
                winner = entries[-1][0]
                for a, e in entries:
                    acc += max(0, int(e))
                    if pick < acc:
                        winner = a
                        break
                return winner

            winners = {}  # cell(str) -> agent_id
            for cell, entries in groups.items():
                cell_key = str(tuple(cell))
                # 幂等保护：若已结算过，跳过
                if cell_key in resolved_cells:
                    continue
                if not entries:
                    continue
                winner = _weighted_deterministic_pick(cell, entries, seed)
                winners[cell_key] = winner

            if not winners:
                return []

            # -------- 5) 写回ownership / resolved_cells，并清空意图 ----------
            for cell_key, winner in winners.items():
                ownership[cell_key] = winner
            resolved_cells |= set(winners.keys())

            self.env.update_data("ownership", ownership)
            self.env.update_data("resolved_cells", list(resolved_cells))
            # 注意：只在“所有地块都已结算”的那次清空；这里简单处理为清空，
            # 若你想分批清空，可在此改成只移除已处理cell的意图。
            self.env.update_data("compete_intents", [])

            # -------- 6) 仅给赢家回发 CompeteSuccessEvent ----------
            my_id = self.profile_id
            out_events: List[Event] = []
            for cell_key, owner in winners.items():
                if owner == my_id:
                    # "(r, c)" -> (r, c)
                    r, c = cell_key.strip("()").split(",")
                    cell_tuple = (int(r), int(c))
                    out_events.append(
                        CompeteSuccessEvent(
                            from_agent_id=my_id,
                            to_agent_id=my_id,
                            new_owner=my_id,
                            cell_coordinates=cell_tuple
                        )
                    )
            return out_events

        except Exception as e:
            # 任何异常都不让它中断流程，直接吞掉
            logger.exception(f"[execute_compete] failed: {e}")
            return []
