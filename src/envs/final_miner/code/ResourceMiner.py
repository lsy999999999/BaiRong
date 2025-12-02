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


# World for debugging: 2x2 grid, S=10 stamina per round, per-plot mining cap = 3.
# RULES (the LLM must follow; also repeated in prompts):
# 1) You can ONLY mine plots you OWN.
# 2) If a plot you own is challenged this round and you did NOT DEFEND (maintain) it,
#    you may LOSE ownership (one challenger is chosen uniformly). Defend costs 1 and
#    blocks ALL raids on that plot for this round (even if nobody raids).
# 3) Claiming (occupy) an empty plot costs 1; competing/raiding (compete) someone else’s
#    plot costs 1.
# 4) Settlement order each round: raids/defense -> empty-plot claims -> mining.
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
        instruction = """You are a ResourceMiner in a 2×2 homogeneous grid world.
Each round you have S = 10 stamina. Each plot can receive 0..3 mining stamina
this round and yields output = min(stamina, 3).

CRITICAL RULES
- You can ONLY mine plots you OWN.
- If your plot is raided this round and you did NOT DEFEND (maintain) it, you LOSE ownership
  (one challenger is chosen uniformly). Defending a plot costs 1 and blocks ALL raids on that
  plot this round; the cost is paid even if unraided.
- Costs: occupy (claim empty) = 1 per plot; compete/raid (challenge others) = 1 per plot.
- Settlement order: raids/defense -> empty-plot claims -> mining. Therefore, defense decisions
  affect whether you still own a plot by the time mining occurs.
-This is the **observe** phase before the turn, used to refresh your visible grid state and proceed to the next "decision."
Important: Your agent ID is "{agent_id}". This framework requires **all internal phase events to be delivered to you**.
Therefore, `target_ids` in the JSON returned by this step **must** equal ["{agent_id}"]
Return ONLY the following JSON (no extra keys) to move to the decision phase:
{
  "map_state": "<List describing current grid (recommended: [{\"cell\":[r,c],\"owner\":\"agent_id|none\",\"resources_available\":3}], 0-based index)>",
  "target_ids": ["<agent ids to notify for decide_action, usually your own id>"]
}
"""
        observation = "Observing the current state of the grid and resource availability."
        result = await self.generate_reaction(instruction, observation)

        new_map_state = result.get('map_state', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        await self.profile.update_data("map_state", new_map_state)

        events = []
        for target_id in target_ids:
            map_observed_event = MapObservedEvent(self.profile_id, target_id)
            events.append(map_observed_event)

        return events

    async def decide_action(self, event: Event) -> List[Event]:
        map_state = self.profile.get_data("map_state", None)
        if map_state is None:
            return []

        observation = f"Map state: {map_state}"
        instruction = """
Based on the map, produce ONE action decision for this round among:
- "occupy": claim an EMPTY plot (cost=1 per plot).
- "maintain": DEFEND a plot you ALREADY own (cost=1 per plot); if defended, ALL raids on that plot fail this round.
- "compete": RAID a plot currently owned by someone else (cost=1 per plot). If the owner did NOT defend this round,
  exactly one challenger wins uniformly; if defended, ALL raids on that plot fail.

Budget: S=10 total this round. Use INTEGERS only. Coordinates use 0-based index as "(row,col)".

Return STRICT JSON with EXACTLY these keys (no extras):
{
  "action_type": "<occupy|maintain|compete>",
  "energy_investment": <int>,
  "cell_coordinates": "(row,col)",
  "target_ids": ["<string agent id(s)>"]
}
Guidance:
- For "compete", include the CURRENT OWNER's id in "target_ids".
- For "occupy"/"maintain", you may use your own id or environment id in "target_ids".
- Do NOT include any keys other than the four above.
"""
        result = await self.generate_reaction(instruction, observation)

        action_type = result.get('action_type')
        energy_investment = result.get('energy_investment', 0)
        cell_coordinates = result.get('cell_coordinates', "(0,0)")
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

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
        cell_coordinates = event.cell_coordinates
        action_executed = self.profile.get_data(f"action_executed_{cell_coordinates}", False)
        if action_executed or not (event.energy_investment and event.cell_coordinates):
            return []

        energy_investment = event.energy_investment
        previous_owner = event.previous_owner

        observation = f"Energy Investment: {energy_investment}, Cell Coordinates: {cell_coordinates}, Previous Owner: {previous_owner}"
        instruction = """You are executing either OCCUPY (claim empty) or MAINTAIN (defend owned) on the specified cell.

Decision rule (for this JSON-only acknowledgement step):
- OCCUPY: set "success": true ONLY if the cell is EMPTY (previous_owner is "None"/"none"); otherwise false.
  (If multiple agents also occupy the same empty cell, the environment will resolve tie-break uniformly.)
- MAINTAIN: set "success": true ONLY if you ALREADY own the cell (previous_owner equals your id); defending consumes 1 stamina
  and blocks ALL raids on that plot this round (even if unraided). Otherwise false.

Return STRICT JSON (no extra keys):
{
  "success": <true|false>,
  "target_ids": ["<resource agent ID(s) or environment id>"]
}
"""
        result = await self.generate_reaction(instruction, observation)

        success = result.get('success', False)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

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
        instruction = """
        You are about to COMPETE (raid) for an occupied plot.

        Resolution principle (to keep outputs consistent with the environment):
        - If (and only if) the CURRENT OWNER did NOT defend the plot this round, one challenger is chosen uniformly as the NEW owner.
        - If the CURRENT OWNER DID defend, ALL raids FAIL on that plot this round.

        DEFAULT when defense status is UNKNOWN in the observation: assume the owner DEFENDED -> set result = "failure" and keep the current owner.

        Return STRICT JSON:
        {
        "competition_result": { "result": "success" | "failure", "new_owner": "<agent id of winner or current owner>" },
        "target_ids": ["<agent id(s) to notify (e.g., environment id)>"]
        }
        """
        result = await self.generate_reaction(instruction, observation)

        competition_result = result.get('competition_result', {})
        new_owner = competition_result.get('new_owner', None)
        result_status = competition_result.get('result', None)
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        self.profile.update_data(f"compete_triggered_{cell_coordinates}", True)
        self.env.update_data("competition_result", competition_result)

        if result_status == "success":
            for target_id in target_ids:
                compete_success_event = CompeteSuccessEvent(new_owner, target_id, cell_coordinates)
                events.append(compete_success_event)

        return events

    async def exploit_resources(self, event: Event) -> List[Event]:
        new_owner = event.new_owner
        if new_owner != self.profile_id:
            return []

        cell_coordinates = event.cell_coordinates

        occupy_maintain_success_received = self.profile.get_data("OccupyMaintainSuccessEvent", False)
        compete_success_received = self.profile.get_data("CompeteSuccessEvent", False)

        if not (occupy_maintain_success_received or compete_success_received):
            return []

        resource_count = self.profile.get_data("resource_count", 0)

        instruction = """You may EXPLOIT (mine) resources ONLY on plots you OWN after raids/claims are resolved.
Mining budget per plot this round is 0..3; realized output per plot is min(stamina, 3).
Return ONLY the routing wrapper below (no extra keys); the environment handles the actual mining tally:

{
  "target_ids": ["<ID of the EnvAgent or other agents to notify>"]
}
"""
        observation = f"Ownership secured. Preparing to mine up to 3 units on cell {cell_coordinates}. Current recorded mined units: {resource_count}."

        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            exploit_event = ResourceExploitedEvent(self.profile_id, target_id, resource_count, cell_coordinates, True)
            events.append(exploit_event)

        return events
