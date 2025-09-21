
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


class IndividualAgent(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initiate_contract_negotiation")

    async def initiate_contract_negotiation(self, event: Event) -> List[Event]:
        # Since the condition is 'null', proceed with the handler logic immediately
        
        # Retrieve required data from agent's profile
        individual_interests = self.profile.get_data("individual_interests", [])
        proposal_details = self.profile.get_data("proposal_details", "")
        negotiation_terms = self.profile.get_data("negotiation_terms", {})
        
        # Create observation from the agent's current state
        observation = f"Individual interests: {individual_interests}, Proposal details: {proposal_details}, Negotiation terms: {negotiation_terms}"
        
        # Instruction for LLM to generate reaction
        instruction = """Initiate the contract negotiation process by evaluating individual interests and desired terms.
        Please return the negotiation status and target_ids in the following JSON format:
    
        {
        "negotiation_status": "<Updated negotiation status>",
        "target_ids": ["<The string ID(s) of the target SocialGroupAgent(s)>"]
        }
        """
        
        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)
        
        # Extract negotiation status and target_ids from the result
        negotiation_status = result.get('negotiation_status', "Pending")
        target_ids = result.get('target_ids', [])
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
        
        # Update agent's profile with the new negotiation status
        self.profile.update_data("negotiation_status", negotiation_status)
        
        # Prepare and send ContractProposalEvent to each target agent
        events = []
        for target_id in target_ids:
            contract_proposal_event = ContractProposalEvent(
                from_agent_id=self.profile_id,
                to_agent_id=target_id,
                individual_interests=individual_interests,
                proposal_details=proposal_details,
                negotiation_terms=negotiation_terms
            )
            events.append(contract_proposal_event)
        
        return events
