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

class ActorA(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "experience_dissonance")
        self.register_event("FeedbackProvidedEvent", "decide_strategy")

    async def experience_dissonance(self, event: Event) -> List[Event]:
        # Retrieve the dissonance scenario from the environment
        dissonance_scenario = await self.get_env_data("dissonance_scenario", "default_scenario")
        
        # Prepare instruction for the LLM
        instruction = """
        Actor A is experiencing cognitive dissonance due to a particular scenario. 
        Analyze the scenario and determine the intensity of the dissonance and identify 
        the cause. Please return the information in the following JSON format:
        
        {
        "dissonance_level": <A float representing the intensity of the dissonance>,
        "dissonance_cause": "<A string describing the cause of dissonance>",
        "target_ids": ["<The string ID of Observer B>"]
        }
        """
        
        # Generate the LLM reaction
        observation = f"Dissonance scenario: {dissonance_scenario}"
        result = await self.generate_reaction(instruction, observation)
        
        # Parse the LLM's response
        dissonance_level = result.get('dissonance_level', 0.0)
        dissonance_cause = result.get('dissonance_cause', "")
        target_ids = result.get('target_ids', None)
        
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update Actor A's profile with dissonance details
        self.profile.update_data("dissonance_level", dissonance_level)
        self.profile.update_data("dissonance_cause", dissonance_cause)
        
        # Create and send DissonanceExperiencedEvent to Observer B
        events = []
        for target_id in target_ids:
            dissonance_event = DissonanceExperiencedEvent(self.profile_id, target_id, dissonance_level, dissonance_cause)
            events.append(dissonance_event)
        
        return events

    async def decide_strategy(self, event: Event) -> List[Event]:
        # Condition Check: Ensure feedback from Observer B is received
        if event.__class__.__name__ != "FeedbackProvidedEvent":
            return []
        
        # Retrieve necessary data from agent and event context
        dissonance_level = self.profile.get_data("dissonance_level", 0.0)
        dissonance_cause = self.profile.get_data("dissonance_cause", "")
        feedback_content = event.feedback_content
        feedback_quality = event.feedback_quality
        
        # Generate reaction to decide strategy using LLM
        instruction = """Decide on a strategy to reduce cognitive dissonance based on the following inputs:
        - Dissonance Level: {dissonance_level}
        - Dissonance Cause: {dissonance_cause}
        - Feedback Content: {feedback_content}
        - Feedback Quality: {feedback_quality}
        Choose between belief change, behavior change, or rationalization.
        Return the decision in the following JSON format:
        {{
        "strategy_type": "<The type of strategy chosen>",
        "expected_outcome": "<Expected outcome of the chosen strategy>",
        "target_ids": ["<The ID(s) of Feedbacker C for evaluation>"]
        }}
        """.format(dissonance_level=dissonance_level, dissonance_cause=dissonance_cause,
                   feedback_content=feedback_content, feedback_quality=feedback_quality)
        
        result = await self.generate_reaction(instruction)
        
        # Parse the LLM's response
        strategy_type = result.get('strategy_type', 'none')
        expected_outcome = result.get('expected_outcome', '')
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update agent data with strategy decision
        self.profile.update_data("strategy_type", strategy_type)
        self.profile.update_data("expected_outcome", expected_outcome)
        
        # Prepare and send StrategyDecidedEvent to Feedbacker C
        events = []
        for target_id in target_ids:
            strategy_event = StrategyDecidedEvent(self.profile_id, target_id, strategy_type, expected_outcome)
            events.append(strategy_event)
        
        return events