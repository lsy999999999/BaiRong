from typing import Any, List, Optional
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

class Buyer(GeneralAgent):
    def __init__(self,
                 sys_prompt: Optional[str] = None,
                 model_config_name: Optional[str] = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("AuctionInitializedEvent", "evaluate_auction")

    async def evaluate_auction(self, event: Event) -> List[Event]:
        # Retrieve necessary data from the event and agent profile
        auction_id = event.auction_id
        mechanism_type = event.mechanism_type
        fee_structure = event.fee_structure
        transparency_level = event.transparency_level
        private_value = self.profile.get_data("private_value", 0.0)

        # Formulate the instruction for decision making
        instruction = f"""Evaluate the auction details and decide whether to place a bid. The target_ids must be the IDs of auction platforms.
        Consider the following auction parameters:
        - Auction ID: {auction_id}
        - Mechanism Type: {mechanism_type}
        - Fee Structure: {fee_structure}
        - Transparency Level: {transparency_level}
        - Your Private Value: {private_value}

        Please return the decision in the following JSON format:
        {{
            "bidding_decision": <True/False>,
            "bid_amount": <float, mandatory if bidding_decision is true>,
            "target_ids": ["<The string ID(s) of the AuctionPlatform(s)>"]
        }}
        """

        # Generate reaction using the LLM
        result = await self.generate_reaction(instruction)

        # Parse the LLM's response
        bidding_decision = result.get('bidding_decision', False)

        
        bid_amount = result.get('bid_amount', None)
        target_ids = result.get('target_ids', None)

        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the bidding decision
        self.profile.update_data("bidding_decision", bidding_decision)

        events = []
        if bidding_decision:
            # Validate bid_amount to ensure it's a positive float
            if bid_amount is None or bid_amount <= 0.0:
                logger.error("Bid amount must be positive if bidding_decision is true.")
                return []

            for target_id in target_ids:
                # Create a unique bid_id (simple example using auction_id and buyer_id)
                bid_id = f"{self.profile_id}_{auction_id}"
                # Prepare the BidDecisionEvent
                bid_event = BidDecisionEvent(
                    from_agent_id=self.profile_id,
                    to_agent_id=target_id,
                    buyer_id=self.profile_id,
                    bid_amount=bid_amount,
                    auction_id=auction_id,
                    bid_id=bid_id
                )
                events.append(bid_event)

        return events