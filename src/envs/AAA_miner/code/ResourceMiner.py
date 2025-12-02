from typing import Any, List, Optional
import json
import asyncio
from loguru import logger
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
                 sys_prompt: str | None = None,
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
        self.register_event("CompeteLandDecisionEvent", "execute_compete")
        self.register_event("OccupyMaintainSuccessEvent", "exploit_resources")
        self.register_event("CompeteSuccessEvent", "exploit_resources")

    async def observe_global_map(self, event: Event) -> List[Event]:
            # 先定义 agent_id，再写 prompt
        agent_id = self.profile_id
        instruction = f"""
            你是资源矿工代理（ResourceMiner），位于 2×2 网格，S=10/回合，每块地本回合采矿上限 3。
            核心规则：
            - 只能在**拥有**的地块上采矿；
            - 若本回合被抢占且**未防御(maintain)**，会丢失该地块；防御每块消耗 1，能挡住当回合所有抢占；
            - 占领(occupy)空地=1，抢占(compete)=1；
            - 结算顺序：抢占/防御 → 占空地 → 采矿。

            你的代理ID是 "{agent_id}"。本框架内部阶段事件必须投给你自己，所以 "target_ids" 必须是 ["{agent_id}"]。
            请仅返回以下 JSON（不要多余字段）。其中 `map_state` 请直接**回显** observation 中给出的 `ownership_map`（如果 observation 没有提供，则返回空数组 []）：
            {
            "map_state": [...],
            "target_ids": ["{agent_id}"]
            }
"""
    
        observation = "Observing the current state of the grid and resource availability."
        result = await self.generate_reaction(instruction, observation)
        
        new_map_state = result.get('map_state', None)
        target_ids = [agent_id]
    
        await self.profile.update_data("map_state", new_map_state)
        
        events = []
        for target_id in target_ids:
            map_observed_event = MapObservedEvent(self.profile_id, target_id)
            events.append(map_observed_event)
    
        return events

    async def decide_action(self, event: Event) -> List[Event]:
            # 先定义 agent_id，再写 prompt
        agent_id = self.profile_id
        map_state = self.profile.get_data("map_state", None)
        if map_state is None:
            return []
        
        observation = f"Map state: {map_state}"
        agent_id = self.profile_id
        instruction = f"""
这是**决策阶段**，你有 S=10。仅三选一动作推动流程：
- "occupy": 占领空地（cost=1）。
- "maintain": 防御你拥有的地块（cost=1；当回合阻断所有抢占）。
- "compete": 抢占他人地块（cost=1；若对方未防御则在挑战者中等概率选 1 人成功；若已防御则全部失败）。
提示：不防御就可能丢地，且只有拥有（并应当已防御）的地块才能稳定采矿。
你的代理ID="{agent_id}"，所有内部事件必须投给你自己：`target_ids=["{agent_id}"]`。
严格 JSON（坐标字符串形式，如 "(0,1)"；不要多余字段）：
{
  "action_type":"occupy"|"maintain"|"compete",
  "energy_investment": 1,
  "cell_coordinates": "(row,col)",
  "target_ids": ["{agent_id}"]
}
"""
        result = await self.generate_reaction(instruction, observation)
        
        action_type = result.get('action_type')
        energy_investment = result.get('energy_investment', 0)
        cell_coordinates = result.get('cell_coordinates', "(0,0)")
        target_ids = [agent_id]
    
        events = []
        if action_type in ["occupy", "maintain", "compete"]:
            for target_id in target_ids:
                if action_type in ["occupy", "maintain"]:
                    event = OccupyLandDecisionEvent(
                        self.profile_id,
                        target_id,
                        energy_investment=energy_investment,
                        cell_coordinates=cell_coordinates,
                        previous_owner=self.profile.get_data("previous_owner", "None")
                    )
                elif action_type == "compete":
                    event = CompeteLandDecisionEvent(
                        self.profile_id,
                        target_id,
                        energy_investment=energy_investment,
                        cell_coordinates=cell_coordinates,
                        current_owner=self.profile.get_data("current_owner", "None")
                    )
                
                events.append(event)
        
        return events

    async def execute_occupy_or_maintain(self, event: Event) -> List[Event]:
        agent_id = self.profile_id
        cell_coordinates = event.cell_coordinates
        action_executed = self.profile.get_data(f"action_executed_{cell_coordinates}", False)
        if action_executed or not (event.energy_investment and event.cell_coordinates):
            return []
    
        energy_investment = event.energy_investment
        previous_owner = event.previous_owner
    
        observation = f"Energy Investment: {energy_investment}, Cell Coordinates: {cell_coordinates}, Previous Owner: {previous_owner}"
        instruction = f"""
这是**占领/维护执行**阶段：
- 占领空地：投入=1 记为成功；
- 维护自己拥有的地：投入=1 记为成功（阻断当回合所有抢占）。
成功后才进入采矿；失败则不采矿。下一事件必须投给自己 `target_ids=["{agent_id}"]`。
严格 JSON：
{
  "success": true|false,
  "target_ids": ["{agent_id}"]
}
"""
        
        result = await self.generate_reaction(instruction, observation)
        
        success = result.get('success', False)
        target_ids = [agent_id]
    
        self.profile.update_data(f"action_executed_{cell_coordinates}", True)
    
        events = []
        
        if success:
            new_land_status = {"owner": self.profile_id, "cell": cell_coordinates}
            await self.env.update_data("new_land_status", new_land_status)
            
            for target_id in target_ids:
                success_event = OccupyMaintainSuccessEvent(self.profile_id, target_id, self.profile_id, cell_coordinates)
                events.append(success_event)
        
        return events

    async def execute_compete(self, event: Event) -> List[Event]:
        agent_id = self.profile_id
        if event.__class__.__name__ != "CompeteLandDecisionEvent":
            return []
    
        energy_investment = event.energy_investment
        cell_coordinates = event.cell_coordinates
        current_owner = event.current_owner
        
        if current_owner == self.profile_id:
            return []
    
        already_competed = self.profile.get_data(f"compete_triggered_{cell_coordinates}", False)
        if already_competed:
            return []
    
        observation = f"Competing for cell at {cell_coordinates} with current owner {current_owner}. Energy investment is {energy_investment}."
        instruction = f"""
这是**抢占执行**阶段：
- 若对方本回合已防御，则所有抢占失败；未防御则在挑战者中等概率选 1 人成功。
若防御状态未知，可保守默认失败，避免错误篡改所有权。下一步事件投给自己 `target_ids=["{agent_id}"]`。
严格 JSON：
{
  "competition_result": { "result": "success"|"failure", "new_owner": "<winner or current owner>" },
  "target_ids": ["{agent_id}"]
}
"""
        result = await self.generate_reaction(instruction, observation)
    
        competition_result = result.get('competition_result', {})
        new_owner = competition_result.get('new_owner', None)
        result_status = competition_result.get('result', None)
        target_ids = [agent_id]
    
        events = []
        self.profile.update_data(f"compete_triggered_{cell_coordinates}", True)
        self.env.update_data("competition_result", competition_result)
    
        if result_status == "success":
            for target_id in target_ids:
                compete_success_event = CompeteSuccessEvent(new_owner, target_id, cell_coordinates)
                events.append(compete_success_event)
    
        return events

    async def exploit_resources(self, event: Event) -> List[Event]:
        agent_id = self.profile_id
        new_owner = event.new_owner
        if new_owner != self.profile_id:
            return []

        cell_coordinates = event.cell_coordinates
    
        occupy_maintain_success_received = self.profile.get_data("OccupyMaintainSuccessEvent", False)
        compete_success_received = self.profile.get_data("CompeteSuccessEvent", False)
    
        if not (occupy_maintain_success_received or compete_success_received):
            return []
        
        resource_count = self.profile.get_data("resource_count", 0)
        
        instruction = f"""
        这是**采矿**阶段。只能在你**拥有**（并已合理防御）的地块上采矿；单地上限 3。
        为保持流程一致，此处仅返回路由包装，目标写你自己：
        {
        "target_ids": ["{agent_id}"]
        }
        """
        
        observation = f"Successfully exploited resources: {resource_count} units from cell at {cell_coordinates}."
        
        result = await self.generate_reaction(instruction, observation)
        target_ids = [agent_id]
    
        events = []
        for target_id in target_ids:
            exploit_event = ResourceExploitedEvent(self.profile_id, target_id, resource_count, cell_coordinates, True)
            events.append(exploit_event)
        
        return events