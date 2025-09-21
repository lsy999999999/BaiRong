
from typing import Any, List,Optional
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


class GovernmentAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "enforce_laws")
        self.register_event("CollectiveInterestEvent", "review_social_contract")

    async def enforce_laws(self, event: Event) -> List[Event]:
        # Condition check: The action condition is 'null', so proceed directly.
        
        # Retrieve law details from the agent's profile
        law_details = self.profile.get_data("law_details", "")
        
        # Prepare observation and instruction for LLM
        observation = f"Law details: {law_details}"
        instruction = """Please determine if the enforcement of the given law triggers a conflict. 
        Return the information in the following JSON format:
    
        {
        "conflict_trigger": "<Boolean indicating if a conflict is triggered>",
        "target_ids": ["<The string ID of the ContractBreakdownAgent>"]
        }
        """
        
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        conflict_trigger = result.get('conflict_trigger', False)
        target_ids = result.get('target_ids', None)
        
        # Ensure target_ids is a list
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Prepare outgoing events
        events = []
        for target_id in target_ids:
            law_enforcement_event = LawEnforcementEvent(
                self.profile_id, 
                target_id, 
                law_details=law_details, 
                conflict_trigger=conflict_trigger
            )
            events.append(law_enforcement_event)
        
        return events

    async def review_social_contract(self, event: Event) -> List[Event]:
        # Condition Check: Ensure the event is CollectiveInterestEvent
        if event.__class__.__name__ != "CollectiveInterestEvent":
            return []
    
        # Access required variables from the event
        collective_interests = event.collective_interests
        evaluation_criteria = event.evaluation_criteria
    
        # Generate reaction to decide on actions based on contract terms
        observation = f"Received collective interests: {collective_interests}, evaluation criteria: {evaluation_criteria}"
        instruction = """Please review the terms of the social contract and decide on the review status. 
        If the terms are acceptable, update review_status to 'approved'; otherwise, set it to 'pending further review'.
        Return the information in the following JSON format:
    
        {
        "review_status": "<The status of the contract review process>",
        "target_ids": ["<The string ID(s) of the PublicPolicyAgent(s)>"]
        }
        """
        
        result = await self.generate_reaction(instruction, observation)
        
        # Process the LLM's returned results
        review_status = result.get('review_status', "pending further review")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        # Update the agent's state with review_status
        self.profile.update_data("review_status", review_status)
    
        # Prepare and send the SocialContractApprovalEvent to the PublicPolicyAgent(s)
        events = []
        for target_id in target_ids:
            approval_event = SocialContractApprovalEvent(
                self.profile_id, target_id, approval_status=review_status
            )
            events.append(approval_event)
    
        return events
