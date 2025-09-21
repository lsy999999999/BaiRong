from typing import Any, List
import asyncio
from onesim.agent import GeneralAgent
from onesim.profile import AgentProfile
from onesim.memory import MemoryStrategy
from onesim.planning import PlanningBase
from onesim.events import Event
from onesim.relationship import RelationshipManager
from .events import FeedbackProvidedEvent, DissonanceExperiencedEvent

class ObserverB(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("DissonanceExperiencedEvent", "observe_and_provide_feedback")

    async def observe_and_provide_feedback(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is of type DissonanceExperiencedEvent
        if not isinstance(event, DissonanceExperiencedEvent):
            return []
    
        # Retrieve required variables from the event
        dissonance_level = event.dissonance_level
        dissonance_cause = event.dissonance_cause
    
        # Construct observation for the LLM
        observation = f"Dissonance Level: {dissonance_level}, Cause: {dissonance_cause}"
    
        # Define the instruction for LLM to generate feedback content and quality
        instruction = """Please generate feedback content based on the observed dissonance level and cause. 
        The feedback should assist Actor A in selecting a strategy to reduce cognitive dissonance.
        Return the information in the following JSON format:
        
        {
        "feedback_content": "<Feedback content to assist Actor A>",
        "feedback_quality": <Quality rating from 1 to 5>,
        "target_ids": ["<The string ID of Actor A or other agents>"]
        }
        """
    
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
    
        # Parse the LLM's response
        feedback_content = result.get('feedback_content', "")
        feedback_quality = result.get('feedback_quality', 0)
        target_ids = result.get('target_ids', [])
    
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare and send FeedbackProvidedEvent to each target
        events = []
        for target_id in target_ids:
            feedback_event = FeedbackProvidedEvent(self.profile_id, target_id, feedback_content, feedback_quality)
            events.append(feedback_event)
    
        return events