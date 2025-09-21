from typing import Any, List, Optional
import asyncio
from onesim.models import JsonBlockParser
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import *
from onesim.relationship import RelationshipManager
from .events import *

class SocialGroupAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("AssignedToGroupEvent", "add_member")
        self.register_event("BehaviorAdjustedEvent", "update_group_norms")

    async def add_member(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "AssignedToGroupEvent":
            return []

        individual_id = event.individual_id
        current_members = self.profile.get_data("members", [])
        if individual_id not in current_members:
            current_members.append(individual_id)
            self.profile.update_data("members", current_members)

        instruction = """Incorporate the new individual agent into the social group and update the group composition.
        Please return the information in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the IndividualAgent(s) to notify>"]
        }
        """
        result = await self.generate_reaction(instruction, observation=f"New member added: {individual_id}")

        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            member_added_event = MemberAddedEvent(self.profile_id, target_id, group_id=event.group_id, individual_id=individual_id)
            events.append(member_added_event)

        return events

    async def update_group_norms(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "BehaviorAdjustedEvent":
            return []

        adjusted_behavior_tendencies = event.adjusted_behavior_tendencies

        observation = f"Adjusted behavior tendencies: {adjusted_behavior_tendencies}"
        instruction = """Reassess and update the social group's norms based on the collective behavior adjustments of its members.
        Please return the information in the following JSON format:

        {
        "updated_norms": "<A list of updated norms for the social group>",
        "target_ids": ["ENV"],
        "status": "success"
        }
        """

        result = await self.generate_reaction(instruction, observation)

        updated_norms = result.get('updated_norms', [])
        target_ids = result.get('target_ids', [])
        group_id = self.profile.get_data("group_id", 0)
        status = result.get('status', "success")

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("updated_norms", updated_norms)

        events = []
        for target_id in target_ids:
            norms_updated_event = GroupNormsUpdatedEvent(self.profile_id, target_id, group_id=group_id, updated_norms=updated_norms, status=status)
            events.append(norms_updated_event)

        return events