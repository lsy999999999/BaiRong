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

class GroupAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "track_opinion_distribution")
        self.register_event("InitialJudgmentFormedEvent", "update_group_opinion")
        self.register_event("ConformityDecisionEvent", "update_group_opinion")
        self.register_event("BeliefUpdatedEvent", "update_group_opinion")

    async def track_opinion_distribution(self, event: Event) -> List[Event]:
        member_opinions = self.profile.get_data("member_opinions", [])

        instruction = """
        You are tasked with tracking the opinion distribution within a group. 
        Based on the member opinions provided, calculate the distribution and 
        decide on the target agent(s) to send this information to. 
        Please return the information in the following JSON format:

        {
            "opinion_distribution": "<A dictionary representing the opinion distribution>",
            "target_ids": ["<The string ID(s) of the DecisionContextAgent>"]
        }
        """

        observation = f"Member Opinions: {member_opinions}"

        result = await self.generate_reaction(instruction, observation)

        opinion_distribution = result.get('opinion_distribution', {})
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("opinion_distribution", opinion_distribution)

        events = []
        for target_id in target_ids:
            opinion_event = OpinionDistributionTrackedEvent(
                self.profile_id, target_id, group_id=self.profile_id, opinion_distribution=opinion_distribution
            )
            events.append(opinion_event)

        return events

    async def update_group_opinion(self, event: Event) -> List[Event]:
        valid_event_types = ['InitialJudgmentFormedEvent', 'ConformityDecisionEvent', 'BeliefUpdatedEvent']
        if event.__class__.__name__ not in valid_event_types:
            return []

        individual_inputs = self.profile.get_data("individual_inputs", [])

        if isinstance(event, InitialJudgmentFormedEvent):
            individual_inputs.append({
                "individual_id": event.individual_id,
                "initial_judgment": event.initial_judgment
            })
        elif isinstance(event, ConformityDecisionEvent):
            individual_inputs.append({
                "individual_id": event.individual_id,
                "conformity_decision": event.conformity_decision
            })
        elif isinstance(event, BeliefUpdatedEvent):
            individual_inputs.append({
                "individual_id": event.individual_id,
                "updated_belief": event.updated_belief
            })
        else:
            return []

        self.profile.update_data("individual_inputs", individual_inputs)

        decision_agents = await self.env.get_agent_data_by_type('DecisionContextAgent', 'id')

        instruction = """
        The group needs to update its collective opinion based on the received individual inputs.
        Consider the dynamics of social influence and conformity processes.
        Please return the information in the following JSON format:

        {
            "updated_group_opinion": "<The updated collective opinion of the group>",
            "target_ids": ["<The string ID(s) of the Decision Context Agent>"]
        }
        """

        observation = f"Individual inputs: {individual_inputs} IDs of Candidate Decision Context Agents: {decision_agents}"
        result = await self.generate_reaction(instruction, observation)

        updated_group_opinion = result.get('updated_group_opinion', "")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.profile.update_data("updated_group_opinion", updated_group_opinion)

        events = []
        for target_id in target_ids:
            group_opinion_event = GroupOpinionUpdatedEvent(self.profile_id, target_id, group_id=self.profile_id, updated_group_opinion=updated_group_opinion)
            events.append(group_opinion_event)

        return events