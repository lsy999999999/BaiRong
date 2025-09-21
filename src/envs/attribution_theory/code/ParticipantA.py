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


class ParticipantA(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("BehaviorDisplayedEvent", "observe_behavior")
        self.register_event("BehaviorObservedEvent", "attribute_behavior")

    async def observe_behavior(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is 'BehaviorDisplayedEvent'
        if event.__class__.__name__ != "BehaviorDisplayedEvent":
            return []

        # Access required variables from the event
        behavior_type = event.behavior_type
        intended_outcome = event.intended_outcome

        # Generate reaction and decision-making
        instruction = """
        Participant A has observed a behavior from Participant B. 
        Please generate a description of the observed behavior and the context in which it was observed. 
        Also, determine the target_ids for the subsequent event. 
        Return the information in the following JSON format:

        {
        "behavior_description": "<Description of the behavior>",
        "observation_context": "<Context of observation>",
        "target_ids": ["<Target ID(s) for the next event>"]
        }
        """
        observation = f"Behavior Type: {behavior_type}, Intended Outcome: {intended_outcome}"

        result = await self.generate_reaction(instruction, observation)

        # Extract and validate response data
        behavior_description = result.get('behavior_description', None)
        observation_context = result.get('observation_context', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's state
        self.profile.update_data("behavior_description", behavior_description)
        self.profile.update_data("observation_context", observation_context)

        # Prepare and send the BehaviorObservedEvent
        events = []
        for target_id in target_ids:
            observed_event = BehaviorObservedEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                behavior_description=behavior_description,
                observation_context=observation_context
            )
            events.append(observed_event)

        return events

    async def attribute_behavior(self, event: Event) -> List[Event]:
        # Condition check: Ensure the event is of type 'BehaviorObservedEvent'
        if event.__class__.__name__ != "BehaviorObservedEvent":
            return []

        # Retrieve required variables from the event
        behavior_description = event.behavior_description
        observation_context = event.observation_context

        # Check if the required fields are populated
        if not behavior_description or not observation_context:
            return []

        candidate_ids = await self.env.get_agent_data_by_type("FeedbackerC", "id")

        # Decision Making: Generate reaction for attribution
        observation = f"Behavior: {behavior_description}, Context: {observation_context}, Candidate IDs of Feedbacker C agent: {candidate_ids}"
        instruction = """Based on the observed behavior and context, determine whether it should be attributed to internal or external causes according to attribution theory principles. 
        Please return the information in the following JSON format:

        {
        "attribution_type": "<internal or external>",
        "reasoning": "<Reasoning behind the decision>",
        "target_ids": ["<The string ID(s) of the Feedbacker C agent>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        attribution_type = result.get('attribution_type', 'external')
        self.profile.update_data("attribution_type", attribution_type)
        reasoning = result.get('reasoning', '')
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send the AttributionDecisionEvent to each target
        events = []
        for target_id in target_ids:
            attribution_event = AttributionDecisionEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                attribution_type=attribution_type,
                reasoning=reasoning
            )
            events.append(attribution_event)

        return events