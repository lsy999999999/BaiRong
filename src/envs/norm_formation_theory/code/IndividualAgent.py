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

class IndividualAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: Optional[asyncio.Queue] = None,
                 profile: Optional[AgentProfile] = None,
                 memory: Optional[MemoryStrategy] = None,
                 planning: Optional[PlanningBase] = None,
                 relationship_manager: Optional[RelationshipManager] = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initialize_behavior_tendencies")
        self.register_event("StartEvent", "assign_to_social_group")
        self.register_event("BehaviorTendenciesInitializedEvent", "assign_to_social_group")
        self.register_event("MemberAddedEvent", "observe_and_interact")
        self.register_event("InteractionObservedEvent", "adjust_behavior")

    async def initialize_behavior_tendencies(self, event: Event) -> List[Event]:
        behavior_tendencies = await self.get_env_data("behavior_tendencies", [])
        self.profile.update_data("behavior_tendencies", behavior_tendencies)

        instruction = """
        You are tasked with setting initial behavior tendencies for an individual agent. 
        Use the provided environmental data to determine the initial behavior tendencies. 
        Please return the information in the following JSON format:

        {
        "behavior_tendencies": <Updated list of behavior tendencies>,
        "target_ids": <The string ID or list of string IDs of the target agents>
        }
        """

        result = await self.generate_reaction(instruction)
        updated_behavior_tendencies = result.get('behavior_tendencies', behavior_tendencies)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("behavior_tendencies", updated_behavior_tendencies)

        events = []
        for target_id in target_ids:
            event = BehaviorTendenciesInitializedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                individual_id=self.profile_id,
                behavior_tendencies=updated_behavior_tendencies
            )
            events.append(event)

        return events

    async def assign_to_social_group(self, event: Event) -> List[Event]:
        if not isinstance(event, BehaviorTendenciesInitializedEvent):
            return []

        individual_id = event.individual_id

        instruction = """Assign the individual agent to a social group based on random selection or predefined criteria.
        Please return the information in the following JSON format:

        {
        "group_id": "<The string ID of the social group to which the individual is assigned>",
        "target_ids": ["<The string ID of the SocialGroupAgent>"]
        }
        """
        observation = f"Individual ID: {individual_id}, Behavior Tendencies: {event.behavior_tendencies}"
        result = await self.generate_reaction(instruction, observation)

        group_id = result.get('group_id', 0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("group_id", group_id)

        events = []
        for target_id in target_ids:
            assigned_event = AssignedToGroupEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                individual_id=individual_id,
                group_id=group_id
            )
            events.append(assigned_event)

        return events

    async def observe_and_interact(self, event: Event) -> List[Event]:
        group_id = self.profile.get_data("group_id", 0)
        if group_id == 0:
            return []

        individual_id = self.profile_id

        observation = f"Individual {individual_id} observing interactions in group {group_id}."
        instruction = """Please generate details of the observed interaction and specify target_ids 
        which can be a single ID or a list of IDs, indicating which agents are affected by the observed interactions.
        Return the information in the following JSON format:

        {
        "interaction_details": "<Details of the observed interaction>",
        "target_ids": ["<The string ID of the affected agents>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        interaction_details = result.get('interaction_details', "")
        # target_ids = result.get('target_ids', [])
        target_ids = [self.profile_id]
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("interaction_details", interaction_details)

        events = []
        for target_id in target_ids:
            interaction_event = InteractionObservedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                observer_id=individual_id,
                interaction_details=interaction_details
            )
            events.append(interaction_event)

        return events

    async def adjust_behavior(self, event: Event) -> List[Event]:
        if not isinstance(event, InteractionObservedEvent):
            return []

        interaction_details = event.interaction_details
        group_pressure = await self.get_env_data("group_pressure", 0.0)
        norm_acceptance = self.profile.get_data("norm_acceptance", 0.0)
        group_ids = await self.env.get_agent_data_by_type("SocialGroupAgent", "id")

        instruction = """
        Based on the observed interaction details and the level of group pressure, adjust the behavior tendencies of the individual agent.
        Please return the information in the following JSON format:

        {
        "adjusted_norm_acceptance": "<New norm acceptance score.>",
        "adjusted_behavior_tendencies": ["<List of new behavior tendencies>"],
        "target_ids": ["<The string ID(s) of the SocialGroupAgent(s) to notify>"]
        }
        """
        observation = f"Interaction details: {interaction_details}, Group pressure: {group_pressure}, Norm Acceptance: {norm_acceptance}, Candidate IDs of SocialGroupAgent(s): {group_ids}"
        result = await self.generate_reaction(instruction, observation)

        adjusted_behavior_tendencies = result.get('adjusted_behavior_tendencies', [])
        new_norm_acceptance = result.get("adjusted_norm_acceptance", 0.0)
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("adjusted_behavior_tendencies", adjusted_behavior_tendencies)
        self.profile.update_data("norm_acceptance", new_norm_acceptance)

        events = []
        for target_id in target_ids:
            behavior_adjusted_event = BehaviorAdjustedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                individual_id=self.profile_id,
                adjusted_behavior_tendencies=adjusted_behavior_tendencies
            )
            events.append(behavior_adjusted_event)

        return events