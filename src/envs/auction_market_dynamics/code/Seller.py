
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


class Seller(GeneralAgent):
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
        # Retrieve necessary data from the event and agent profile
        auction_id = event.auction_id
        mechanism_type = event.mechanism_type
        fee_structure = event.fee_structure
        transparency_level = event.transparency_level
        production_cost = self.profile.get_data("production_cost", 0.0)

        auction_platforms = self.env.get_agent_data_by_type('AuctionPlatform', 'id')

        # Prepare observation and instruction for LLM decision making
        observation = f"""Auction ID: {auction_id}, IDs of AuctionPlatform: {auction_platforms} """
        instruction = """Evaluate the auction details to set an appropriate reserve price. Ensure the reserve price is above the production cost. Set the target AuctionPlatforms in target_ids. 
        Return the information in the following JSON format:

        {
        "reserve_price_decision": <Calculated reserve price>,
        "target_ids": ["<Target AuctionPlatform IDs>"]
        }
        """

        # Generate reaction using LLM
        result = await self.generate_reaction(instruction, observation)

        # Extract reserve price decision and target IDs from the result
        reserve_price_decision = result.get('reserve_price_decision', production_cost)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Update the agent's profile with the new reserve price decision
        self.profile.update_data("reserve_price_decision", reserve_price_decision)

        # Prepare and send SetReservePriceEvent to each target
        events = []
        for target_id in target_ids:
            reserve_price_event = SetReservePriceEvent(self.profile_id, target_id, self.profile_id, reserve_price_decision, auction_id)
            events.append(reserve_price_event)

        return events
