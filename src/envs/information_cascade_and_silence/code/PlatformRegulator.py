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


class PlatformRegulator(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "monitor_content")
        self.register_event("VerificationCompleteEvent", "intervene_content")
        self.register_event("ContentMonitoredEvent", "intervene_content")

    async def monitor_content(self, event: Event) -> List[Event]:
        # Validate incoming event type
        if event.__class__.__name__ != "StartEvent":
            return []

        # Generate reaction using LLM for decision making
        instruction = """
        You are a platform regulator tasked with monitoring content on a social media platform. 
        Your goal is to identify content that violates platform policies or poses risks. 
        Ensure the monitored content aligns with platform policies or previous risk assessments.
        Based on the provided context, decide which content items to monitor and assess their risk levels.
        Return the response in the following JSON format:

        {
            "monitored_content": ["<List of content IDs being monitored>"],
            "risk_levels": ["<List of risk levels corresponding to monitored content>"],
            "target_ids": ["<List of target agent IDs for the next action>"]
        }
        """
        observation = "The platform regulator is monitoring content based on the initial trigger event."
        result = await self.generate_reaction(instruction, observation)

        # Extract and validate data from the LLM response
        monitored_content = result.get("monitored_content", [])
        risk_levels = result.get("risk_levels", [])
        target_ids = result.get("target_ids", [])

        if not isinstance(monitored_content, list):
            monitored_content = [monitored_content]
        if not isinstance(risk_levels, list):
            risk_levels = [risk_levels]
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Validate risk levels
        valid_risk_levels = {"low", "medium", "high"}
        risk_levels = [rl if rl in valid_risk_levels else "low" for rl in risk_levels]

        # Update the agent's state with the monitored content
        current_monitored_content = self.profile.get_data("monitored_content", [])
        if not isinstance(current_monitored_content, list):
            current_monitored_content = [current_monitored_content]
        updated_monitored_content = current_monitored_content + monitored_content
        self.profile.update_data("monitored_content", updated_monitored_content)

        # Prepare and send ContentMonitoredEvent to the next action
        events = []
        for target_id, content, risk_level in zip(target_ids, monitored_content, risk_levels):
            content_event = ContentMonitoredEvent(
                self.profile_id, target_id, monitored_content=content, risk_level=risk_level
            )
            events.append(content_event)

        return events

    async def intervene_content(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the action is triggered only if content is monitored or verification results are received
        verification_result = None
        monitored_content = None
        risk_level = None

        if event.__class__.__name__ == "VerificationCompleteEvent":
            verification_result = event.verification_result
            if verification_result == "unverified":
                return []
        elif event.__class__.__name__ == "ContentMonitoredEvent":
            monitored_content = event.monitored_content
            risk_level = event.risk_level
            if not monitored_content or not risk_level:
                return []
        else:
            return []

        # Ensure both conditions are checked simultaneously
        if verification_result and monitored_content and risk_level:
            observation = f"Verification result: {verification_result}, Monitored content: {monitored_content}, Risk level: {risk_level}"
        elif verification_result:
            observation = f"Verification result: {verification_result}"
        elif monitored_content and risk_level:
            observation = f"Monitored content: {monitored_content}, Risk level: {risk_level}"
        else:
            return []

        # Generate reaction using LLM
        instruction = """You are a platform regulator intervening to enforce policies on monitored content. 
        Based on the risk level and verification results, decide the intervention action. 
        If the risk level is 'high' or the verification result is 'false', remove the content. 
        If the risk level is 'medium', tag the content. 
        If the risk level is 'low', take no action. 
        Validate whether the intervention aligns with the risk level and was successful.
        Return the following JSON format:
        {
            "intervention_status": "<completed, failed, or pending>",
            "environment_update": "<Updates made to the environment>",
            "target_ids": ["ENV"]
        }
        """
        result = await self.generate_reaction(instruction, observation)

        # Parse LLM response
        intervention_status = result.get("intervention_status", "pending")
        environment_update = result.get("environment_update", "")
        target_ids = ["ENV"]

        # Update agent state
        self.profile.update_data("intervention_status", intervention_status)

        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            intervention_event = InterventionCompleteEvent(
                self.profile_id, target_id, intervention_status, environment_update
            )
            events.append(intervention_event)

        return events