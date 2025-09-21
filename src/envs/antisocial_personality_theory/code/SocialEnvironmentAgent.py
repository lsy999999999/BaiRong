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

class SocialEnvironmentAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("InteractionInitiatedEvent", "engage_with_individual")
        self.register_event("ManipulationAttemptEvent", "handle_manipulation")
        self.register_event("DisrespectActionEvent", "handle_disrespect")

    async def engage_with_individual(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "InteractionInitiatedEvent":
            return []

        self.env.update_data("engagement_status", "active")

        instruction = """
        The social environment agent needs to respond to an interaction initiated by an antisocial agent. 
        Consider the context where the antisocial agent might manipulate or disrespect during interaction. 
        Strategize a response including the type and intensity. 
        Provide the result in the following JSON format:

        {
            "response_type": "<Type of response, e.g., positive, negative, or neutral>",
            "response_intensity": <Integer indicating the intensity of the response>,
            "target_ids": ["<The string ID of the Antisocial agent>"]
        }
        """

        result = await self.generate_reaction(instruction)

        response_type = result.get('response_type', "neutral")
        response_intensity = result.get('response_intensity', 0)
        target_ids = result.get('target_ids', None)

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            response_event = EnvironmentResponseEvent(
                self.profile_id,
                target_id,
                response_type=response_type,
                response_intensity=response_intensity
            )
            events.append(response_event)

        return events

    async def handle_manipulation(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "ManipulationAttemptEvent":
            return []

        manipulation_strategy = event.manipulation_strategy
        target_agent = event.target_agent

        instruction = f"""
        The agent has received a manipulation attempt using the strategy '{manipulation_strategy}' targeting '{target_agent}'.
        Please decide on the handling method and outcome. Determine the appropriate target_ids for the next step.
        Return the information in the following JSON format:
        {{
            "handling_method": "<The method chosen to handle the manipulation>",
            "outcome": "<Result of the handling process>",
            "target_ids": ["ENV"]
        }}
        """
        observation = f"Manipulation strategy: {manipulation_strategy}, Target agent: {target_agent}"
        result = await self.generate_reaction(instruction, observation)

        handling_method = result.get('handling_method', 'ignore')
        outcome = result.get('outcome', 'unresolved')
        target_ids = result.get('target_ids', [])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.env.update_data("handling_method", handling_method)
        self.env.update_data("outcome", outcome)

        events = []
        for target_id in target_ids:
            manipulation_handled_event = ManipulationHandledEvent(self.profile_id, target_id, handling_method, outcome)
            events.append(manipulation_handled_event)

        return events

    async def handle_disrespect(self, event: Event) -> List[Event]:
        if event.__class__.__name__ != "DisrespectActionEvent":
            return []

        disrespect_type = event.disrespect_type
        severity_level = event.severity_level

        instruction = """
        Based on the disrespect type and severity level, decide on the appropriate response action and resolution status.
        Ensure to return the data in the following JSON format:
        {
            "response_action": "<Action taken by the environment in response to the disrespectful behavior>",
            "resolution_status": "<Status of the resolution process>",
            "target_ids": ["ENV"]
        }
        """
        observation = f"Disrespect type: {disrespect_type}, Severity level: {severity_level}"

        result = await self.generate_reaction(instruction, observation)

        response_action = result.get('response_action', "reprimand")
        resolution_status = result.get('resolution_status', "pending")
        target_ids = result.get('target_ids', ["ENV"])

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        self.env.update_data("response_action", response_action)
        self.env.update_data("resolution_status", resolution_status)

        events = []
        for target_id in target_ids:
            handled_event = DisrespectHandledEvent(self.profile_id, target_id, response_action, resolution_status)
            events.append(handled_event)

        return events