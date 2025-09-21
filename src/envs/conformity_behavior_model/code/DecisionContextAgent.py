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

class DecisionContextAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("OpinionDistributionTrackedEvent", "handle_decision_context")
        self.register_event("GroupOpinionUpdatedEvent", "handle_decision_context")

    async def handle_decision_context(self, event: Event) -> List[Event]:
        # Determine event type and update profile flags
        if event.__class__.__name__ == "OpinionDistributionTrackedEvent":
            self.profile.update_data("opinion_distribution_received", True)
            self.profile.update_data("opinion_distribution", event.opinion_distribution)
        elif event.__class__.__name__ == "GroupOpinionUpdatedEvent":
            self.profile.update_data("group_opinion_update_received", True)
            self.profile.update_data("group_opinion", event.updated_group_opinion)

        # Check if all required events have been received
        opinion_distribution_received = self.profile.get_data("opinion_distribution_received", False)
        group_opinion_update_received = self.profile.get_data("group_opinion_update_received", False)

        if not (opinion_distribution_received and group_opinion_update_received):
            return []

        # Retrieve required variables
        group_opinion = self.profile.get_data("group_opinion", "")
        opinion_distribution = self.profile.get_data("opinion_distribution", {})
        environmental_factors = await self.get_env_data("environmental_factors", {})

        # Generate reaction
        instruction = """
        Process the decision context using the given group opinion, opinion distribution, and environmental factors.
        Provide the results and completion status. Return the information in the following JSON format:
        {
            "completion_status": "<Status of processing>",
            "results": <Outcomes of processing as a dictionary>,
            "target_ids": ["ENV"]
        }
        """
        # ["<List of target IDs to send the results>"]
        observation = f"Group Opinion: {group_opinion}, Opinion Distribution: {opinion_distribution}, Environmental Factors: {environmental_factors}"
        result = await self.generate_reaction(instruction, observation)

        # Parse the LLM's JSON response
        completion_status = result.get('completion_status', 'pending')
        results = result.get('results', {})
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update environment with results
        self.env.update_data("completion_status", completion_status)
        self.env.update_data("results", results)

        # Prepare and send DecisionContextHandledEvent to each target
        events = []
        decision_context_id = self.profile.get_data("decision_context_id", "")
        for target_id in target_ids:
            decision_context_event = DecisionContextHandledEvent(
                self.profile_id, target_id, decision_context_id=decision_context_id,
                completion_status=completion_status, results=results
            )
            events.append(decision_context_event)

        # Reset flags after processing
        self.profile.update_data("opinion_distribution_received", False)
        self.profile.update_data("group_opinion_update_received", False)

        return events