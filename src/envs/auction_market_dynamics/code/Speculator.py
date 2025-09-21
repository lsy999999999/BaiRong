
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


class Speculator(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile=None,
                 memory: MemoryStrategy=None,
                 planning: PlanningBase=None,
                 relationship_manager: RelationshipManager=None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("AuctionInitializedEvent", "evaluate_auction")

    async def evaluate_auction(self, event: Event) -> List[Event]:
        # Retrieve required variables from event and agent profile
        auction_id = event.auction_id
        mechanism_type = event.mechanism_type
        fee_structure = event.fee_structure
        transparency_level = event.transparency_level
        capital = self.profile.get_data("capital", 0.0)

        seller_id = await self.env.get_agent_data_by_type('Seller', 'id')

        # Define instruction for generating reaction
        instruction = """
        Evaluate the auction details provided in the observation to decide on an influence strategy.
        Decide the Seller you want to trade with, and report the result to the AuctionPlatform. You can only choose one Seller at a time. 
        Return the decision in the following JSON format:
        {
            "seller_id": "<The string ID of the choosen Seller>"
            "target_ids": ["<The string ID of the AuctionPlatform agent>"]
        }
        """
    
        # Set observation context
        observation = f"Auction ID: {auction_id} Candidate Seller ID: {seller_id}"

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract influence strategy and target IDs from the result
        seller_id = result.get('seller_id', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Prepare and send MarketInfluenceEvent(s) to the AuctionPlatform
        events = []
        for target_id in target_ids:
            influence_event = MarketInfluenceEvent(self.profile_id, target_id, seller_id)
            events.append(influence_event)

        return events
