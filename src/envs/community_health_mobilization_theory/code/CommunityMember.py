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

class CommunityMember(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("MobilizationEvent", "engage_in_mobilization")
        self.register_event("PeerInfluenceEvent", "engage_in_mobilization")
        self.register_event("BehaviorChangeEvent", "influence_peer_behavior")

    async def engage_in_mobilization(self, event: Event) -> List[Event]:
        # Access required variables from the event
        activity_details = getattr(event, 'activity_details', 'None')
        leader_id = getattr(event, 'leader_id', 'unknown')
    
        # Update agent's participation status based on event details
        participation_status = f"Participated in {activity_details} organized by leader {leader_id}"
        self.profile.update_data("participation_status", participation_status)
    
        # Prepare instruction for generate_reaction
        instruction = """
        Based on the current mobilization activity and peer influence, decide the next actions. 
        You need to identify the target_ids for further peer influence or to mark the mobilization completion.
        Please return the information in the following JSON format:
        
        {
            "target_ids": ["<List of target IDs for further influence or 'ENV' for completion>"]
        }
        """
        
        # Observation context
        observation = f"Activity: {activity_details}, Leader: {leader_id}"
    
        # Generate reaction to decide on further actions
        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Prepare outgoing events based on target_ids
        events = []
        for target_id in target_ids:
            if target_id == "ENV":
                # Create MobilizationCompletedEvent
                completion_status = "success"
                summary = f"Mobilization activity '{activity_details}' completed successfully."
                mobilization_completed_event = MobilizationCompletedEvent(self.profile_id, "ENV", completion_status, summary)
                events.append(mobilization_completed_event)
            else:
                # Create BehaviorChangeEvent for peer influence
                influencing_member_id = self.profile_id
                influenced_member_id = target_id
                behavior_change = f"Influenced by participation in {activity_details}"
                behavior_change_event = BehaviorChangeEvent(influencing_member_id, influenced_member_id, behavior_change=behavior_change)
                events.append(behavior_change_event)
    
        return events

    async def influence_peer_behavior(self, event: Event) -> List[Event]:
        # Extract event data
        influencing_member_id = getattr(event, 'influencing_member_id', 'unknown')
        influenced_member_id = getattr(event, 'influenced_member_id', 'unknown')
        behavior_change = getattr(event, 'behavior_change', 'None')
    
        # Create observation and instruction for generate_reaction
        observation = f"Influencing member ID: {influencing_member_id}, Influenced member ID: {influenced_member_id}, Behavior change: {behavior_change}"
        instruction = """Based on the social interaction and shared experiences, determine the influence on health behavior.
        Please return the information in the following JSON format:
    
        {
        "behavior_status": "<Updated health behavior status>",
        "target_ids": ["<The string ID(s) of the influenced community member(s)>"]
        }
        """
    
        # Generate reaction
        result = await self.generate_reaction(instruction, observation)
    
        # Extract results from LLM response
        behavior_status = result.get('behavior_status', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the influenced member's behavior status if not None
        if behavior_status is not None:
            self.profile.update_data("behavior_status", behavior_status)
    
        # Prepare and send PeerInfluenceEvent to the influenced member(s)
        events = []
        for target_id in target_ids:
            peer_influence_event = PeerInfluenceEvent(self.profile_id, target_id, influence_type=behavior_change)
            events.append(peer_influence_event)
    
        return events