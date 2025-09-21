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

class AuctionPlatform(GeneralAgent):
    def __init__(self,
                 sys_prompt: str | None = None,
                 model_config_name: str = None,
                 event_bus_queue: asyncio.Queue = None,
                 profile: AgentProfile = None,
                 memory: MemoryStrategy = None,
                 planning: PlanningBase = None,
                 relationship_manager: RelationshipManager = None) -> None:
        super().__init__(sys_prompt, model_config_name, event_bus_queue, profile, memory, planning, relationship_manager)
        self.register_event("StartEvent", "initialize_auction")
        self.register_event("AuctionInitializedEvent", "initialize_auction")
        self.register_event("BidDecisionEvent", "receive_bid")
        self.register_event("SetReservePriceEvent", "set_reserve_price")
        self.register_event("MarketInfluenceEvent", "finalize_auction")
        self.register_event("BidReceivedEvent", "process_bid")
        self.register_event("ReservePriceSetEvent", "process_bid")
        self.register_event("MarketConditionChangedEvent", "adjust_bidding_process")
        # self.register_event("BiddingEligibilityConfirmedEvent", "finalize_auction")
        self.register_event("BiddingProcessAdjustedEvent", "finalize_auction")

    async def initialize_auction(self, event: Event) -> List[Event]:
        mechanism_type = self.profile.get_data("mechanism_type", "default")
        fee_structure = self.profile.get_data("fee_structure", "default")
        transparency_level = self.profile.get_data("transparency_level", "default")
        market_conditions = event.market_conditions

        instruction = """
        You are tasked with initializing a new auction. Use the following data:
        Mechanism Type: {mechanism_type}
        Fee Structure: {fee_structure}
        Transparency Level: {transparency_level}
        Market Conditions: {market_conditions}
    
        Please generate the auction details including a unique auction_id and update the active_auctions list.
        Return the response in the following JSON format:
    
        {{
            "auction_id": "<Unique identifier for the auction>",
            "mechanism_type": "<Type of auction mechanism>",
            "fee_structure": "<Fee structure applicable>",
            "transparency_level": "<Transparency level>",
            "target_ids": ["<List of target agent IDs to send events to>"]
        }}
        """.format(
            mechanism_type=mechanism_type,
            fee_structure=fee_structure,
            transparency_level=transparency_level,
            market_conditions=market_conditions
        )

        result = await self.generate_reaction(instruction)

        auction_id = result.get('auction_id', None)
        mechanism_type = result.get('mechanism_type', None)
        fee_structure = result.get('fee_structure', None)
        transparency_level = result.get('transparency_level', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        if not target_ids:
            return []

        active_auctions = self.profile.get_data("active_auctions", [])
        active_auctions.append({
            "auction_id": auction_id,
            "mechanism_type": mechanism_type,
            "fee_structure": fee_structure,
            "transparency_level": transparency_level
        })
        self.profile.update_data("active_auctions", active_auctions)

        events = []
        for target_id in target_ids:
            auction_event = AuctionInitializedEvent(
                self.profile_id, target_id, auction_id, mechanism_type, fee_structure, transparency_level
            )
            events.append(auction_event)

        return events

    async def receive_bid(self, event: Event) -> List[Event]:
        bid_id = event.bid_id
        bid_amount = event.bid_amount
        buyer_id = event.buyer_id

        bids = self.profile.get_data("bids", [])
        bids.append({"bid_id": bid_id, "bid_amount": bid_amount, "buyer_id": buyer_id})
        self.profile.update_data("bids", bids)

        observation = f"Received bid with ID: {bid_id}, Amount: {bid_amount}, Buyer ID: {buyer_id}"
        instruction = """You have received a bid and need to confirm its receipt. 
        The confirmation should include the bid_id, bid_amount, and buyer_id. 
        Additionally, determine the appropriate target_ids for further processing of this bid.
        Return the information in the following JSON format:

        {
            "confirmation": "Bid received with ID: <bid_id>, Amount: <bid_amount>, Buyer ID: <buyer_id>",
            "target_ids": ["<The string ID of the AuctionPlatform for processing>"]
        }
        """

        result = await self.generate_reaction(instruction, observation)

        confirmation = result.get('confirmation', None)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            bid_received_event = BidReceivedEvent(self.profile_id, target_id, bid_id=bid_id, bid_amount=bid_amount, buyer_id=buyer_id)
            events.append(bid_received_event)

        return events

    async def set_reserve_price(self, event: Event) -> List[Event]:
        # if event.__class__.__name__ != "SetReservePriceEvent":
        #     return []
        seller_id = event.seller_id
        reserve_price = event.reserve_price
        auction_id = event.auction_id

        auction_details = self.profile.get_data("auction_details", {})
        auction_details[auction_id] = {
            "reserve_price": reserve_price
        }
        self.profile.update_data("auction_details", auction_details)

        instruction = """Please determine the appropriate target(s) for the ReservePriceSetEvent based on the updated auction details.
        Return the information in the following JSON format:

        {
        "target_ids": ["<The string ID(s) of the target agent(s)>"]
        }
        """
        observation = f"Updated auction details: {auction_details}"
        result = await self.generate_reaction(instruction, observation)

        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        events = []
        for target_id in target_ids:
            reserve_price_set_event = ReservePriceSetEvent(self.profile_id, target_id, seller_id, reserve_price, auction_id)
            events.append(reserve_price_set_event)

        return events

    # async def influence_market_conditions(self, event: Event) -> List[Event]:
    #     speculator_id = event.speculator_id
    #     influence_strategy = event.influence_strategy

    #     market_volatility = await self.get_env_data("market_volatility", 0.0)
    #     information_asymmetry = await self.get_env_data("information_asymmetry", 0.0)

    #     instruction = """
    #     Adjust the market conditions based on the speculator's actions and strategy. 
    #     Consider how the influence strategy impacts market volatility and information asymmetry. 
    #     Please return the updated market conditions and specify target_ids for the MarketConditionChangedEvent. 
    #     The response should be in the following JSON format:

    #     {
    #     "market_conditions": {
    #         "market_volatility": <Updated market volatility>,
    #         "information_asymmetry": <Updated information asymmetry>
    #     },
    #     "target_ids": ["<The string ID(s) of the AuctionPlatform agent(s)>"]
    #     }
    #     """
    
    #     observation = f"Speculator ID: {speculator_id}, Influence Strategy: {influence_strategy}, " \
    #                   f"Current Market Volatility: {market_volatility}, Information Asymmetry: {information_asymmetry}"

    #     result = await self.generate_reaction(instruction, observation)

    #     updated_market_conditions = result.get('market_conditions', {})
    #     market_volatility = updated_market_conditions.get('market_volatility', market_volatility)
    #     information_asymmetry = updated_market_conditions.get('information_asymmetry', information_asymmetry)
    #     target_ids = result.get('target_ids', [])

    #     if not isinstance(target_ids, list):
    #         target_ids = [target_ids]

    #     self.env.update_data("market_volatility", market_volatility)
    #     self.env.update_data("information_asymmetry", information_asymmetry)

    #     events = []
    #     for target_id in target_ids:
    #         market_condition_event = MarketConditionChangedEvent(
    #             self.profile_id, target_id, market_volatility, information_asymmetry, speculator_id
    #         )
    #         events.append(market_condition_event)

    #     return events

    async def process_bid(self, event: Event) -> List[Event]:
        if event.__class__.__name__ == "BidReceivedEvent":
            self.profile.update_data("BidReceivedEvent", True)
            self.profile.update_data("bid_id", event.bid_id)
            self.profile.update_data("bid_amount", event.bid_amount)
            self.profile.update_data("buyer_id", event.buyer_id)
        elif event.__class__.__name__ == "ReservePriceSetEvent":
            self.profile.update_data("ReservePriceSetEvent", True)
            self.profile.update_data("auction_id", event.auction_id)
            self.profile.update_data("reserve_price", event.reserve_price)
            self.profile.update_data("seller_id", event.seller_id)
    
        bid_received = self.profile.get_data("BidReceivedEvent", False)
        reserve_price_set = self.profile.get_data("ReservePriceSetEvent", False)

        if not (bid_received and reserve_price_set):
            return []


        bid_id = self.profile.get_data("bid_id", "")
        bid_amount = self.profile.get_data("bid_amount", 0.0)
        reserve_price = self.profile.get_data("reserve_price", 0.0)
        auction_id = self.profile.get_data("auction_id", "")

        eligible_bids = self.profile.get_data("eligible_bids", [])
        if bid_amount >= reserve_price:
            eligible_bids.append(bid_id)
            self.profile.update_data("eligible_bids", eligible_bids)

        observation = f"Bid ID: {bid_id}, Bid Amount: {bid_amount}, Reserve Price: {reserve_price}, Auction ID: {auction_id}"
        instruction = """
        Please adjust the bidding rules based on the current market conditions.
        Consider the market volatility and information asymmetry to determine the adjustments needed.
        Return the information in the following JSON format:

        {
        "bidding_rules": {"<rule_name>": "<rule_value>", ...},
        "adjustment_reason": "<Reason for the adjustment>",
        "auction_id": "<Unique identifier for the auction>",
        "target_ids": ["<The string ID of the AuctionPlatform agent(s)>"]
        }
        """

        # instruction = """Determine the eligible bids and prepare for auction finalization. 
        # Ensure to return the eligible bids and auction_id in the following JSON format:
        # {
        #     "eligible_bids": ["<List of eligible bid IDs>"],
        #     "auction_id": "<The auction ID>",
        #     "target_ids": ["<The string ID(s) of the AuctionPlatform agent(s) for finalization>"]
        # }
        # """
    
        result = await self.generate_reaction(instruction, observation)
    
        # eligible_bids = result.get('eligible_bids', [])
        adjustment_reason = result.get('adjustment_reason', None)
        auction_id = result.get('auction_id', auction_id)
        target_ids = result.get('target_ids', None)
        if not isinstance(target_ids, list):
            target_ids = [target_ids]

        # Reset flags after processing
        self.profile.update_data("BidReceivedEvent", False)
        self.profile.update_data("ReservePriceSetEvent", False)
        self.profile.update_data("adjustment_reason", "")
        # self.profile.update_data("eligible_bids", [])  # Reset eligible bids for new auction

        buyer_id, seller_id = "", ""
        bid_amount, reserve_price = 0.0, 0.0
        if bid_received:
            buyer_id = self.profile.get_data("buyer_id", "")
            bid_amount = self.profile.get_data("bid_amount", 0.0)

        if reserve_price_set:
            seller_id = self.profile.get_data("seller_id", "")
            reserve_price = self.profile.get_data("reserve_price", 0.0)

            
        events = []
        for target_id in target_ids:
            bidding_event = BiddingProcessAdjustedEvent(self.profile_id, target_id, adjustment_reason, auction_id, seller_id, reserve_price, buyer_id, bid_amount)
            events.append(bidding_event)

        # Store events as dictionaries for finalization condition
        bidding_process_adjusted_event = self.profile.get_data("BiddingProcessAdjustedEvent", {})
        bidding_process_adjusted_event["adjustment_reason"] = adjustment_reason
        bidding_process_adjusted_event["auction_id"] = auction_id
        bidding_process_adjusted_event["seller_id"] = seller_id
        bidding_process_adjusted_event["reserve_price"] = reserve_price
        bidding_process_adjusted_event["buyer_id"] = buyer_id
        bidding_process_adjusted_event["bid_amount"] = bid_amount
        bidding_process_adjusted_event["speculator_id"] = ""
        self.profile.update_data("BiddingProcessAdjustedEvent", bidding_process_adjusted_event)

        return events

    async def adjust_bidding_process(self, event: Event) -> List[Event]:
        market_volatility = event.market_volatility
        information_asymmetry = event.information_asymmetry
        speculator_id = event.speculator_id
    
        instruction = """
        Please adjust the bidding rules based on the current market conditions.
        Consider the market volatility and information asymmetry to determine the adjustments needed.
        Return the information in the following JSON format:

        {
        "bidding_rules": {"<rule_name>": "<rule_value>", ...},
        "adjustment_reason": "<Reason for the adjustment>",
        "auction_id": "<Unique identifier for the auction>",
        "target_ids": ["<The string ID of the AuctionPlatform agent(s)>"]
        }
        """
        observation = f"Market Volatility: {market_volatility}, Information Asymmetry: {information_asymmetry}"
    
        result = await self.generate_reaction(instruction, observation)
    
        bidding_rules = result.get('bidding_rules', {})
        adjustment_reason = result.get('adjustment_reason', "")
        auction_id = result.get('auction_id', "")
        target_ids = result.get('target_ids', [])
    
        if not isinstance(target_ids, list):
            target_ids = [target_ids]
    
        self.profile.update_data("bidding_rules", bidding_rules)
    
        events = []
        for target_id in target_ids:
            adjusted_event = BiddingProcessAdjustedEvent(
                self.profile_id, target_id, adjustment_reason=adjustment_reason, auction_id=auction_id, speculator_id=speculator_id
            )
            events.append(adjusted_event)

        # Store events as dictionaries for finalization condition
        bidding_process_adjusted_event = self.profile.get_data("BiddingProcessAdjustedEvent", {})
        bidding_process_adjusted_event["adjustment_reason"] = adjustment_reason
        bidding_process_adjusted_event["auction_id"] = auction_id
        bidding_process_adjusted_event["speculator_id"] = speculator_id
        self.profile.update_data("BiddingProcessAdjustedEvent", bidding_process_adjusted_event)
    
        return events

    async def finalize_auction(self, event: Event) -> List[Event]:
        

        auction_id = event.get("auction_id", "")
        seller_id = event.get("seller_id", "")
        buyer_id = event.get("buyer_id", "")
        speculator_id = event.get("speculator_id", "")

        if seller_id == "" and buyer_id == "" and speculator_id == "":
            return []

        reserve_price, bid_amount = "", ""
        if seller_id != "":
            reserve_price = await self.get_agent_data(seller_id, "reserve_price", 0.0)
        if buyer_id != "":
            bid_amount = await self.get_agent_data(buyer_id, "bid_amount", 0.0)


        if seller_id != "" and buyer_id != "":
            observation = f"Auction ID: {auction_id} Seller ID: {seller_id} Seller's Reserve Price: {reserve_price} Buyer ID: {buyer_id} Buyer's Bid Amount: {bid_amount}"
            instruction = """Finalize the auction based on the seller's reserve price and the buyer's bid amount. Generate the final price of the auction.
            Return the auction outcome in the following JSON format:
            {
                "auction_outcome": {
                    "final_price": "<Final price of the auction>"
                },
                "target_ids": ["ENV"]
            }
            """
            result = await self.generate_reaction(instruction, observation)

            auction_outcome = result.get("auction_outcome", {})
            final_price = auction_outcome['final_price']
            if not final_price.isdigit():
                return []

            target_ids = result.get("target_ids", [])
            if not isinstance(target_ids, list):
                target_ids = [target_ids]

            self.profile.update_data("auction_outcome", auction_outcome)


            await self.update_agent_data(seller_id, "reserve_price", final_price)

            price = await self.get_agent_data(buyer_id, "private_value", None)
            updated_private_value = price - eval(final_price)
            await self.update_agent_data(buyer_id, "private_value", updated_private_value)

            self.profile.update_data("seller_id", "")
            self.profile.update_data("reserve_price", 0.0)
            self.profile.update_data("buyer_id", "")
            self.profile.update_data("bidding_amount", 0.0)

        if seller_id != "" and speculator_id != "":
            observation = f"Auction ID: {auction_id} Seller ID: {seller_id} Seller's Reserve Price: {reserve_price} Speculator ID: {speculator_id}"
            instruction = """Finalize the auction based on the seller's reserve price and the ID of the speculator. Generate the final price of the auction.
            Return the auction outcome in the following JSON format:
            {
                "auction_outcome": {
                    "final_price": "<Final price of the auction>"
                },
                "target_ids": ["ENV"]
            }
            """
            result = await self.generate_reaction(instruction, observation)

            auction_outcome = result.get("auction_outcome", {})
            final_price = auction_outcome['final_price']
            target_ids = result.get("target_ids", [])
            if not isinstance(target_ids, list):
                target_ids = [target_ids]

            self.profile.update_data("auction_outcome", auction_outcome)
            await self.update_agent_data(seller_id, "reserve_price", final_price)
            self.profile.update_data("seller_id", "")
            self.profile.update_data("reserve_price", 0.0)

            # 由于没有评估speculator的指标，所以没有更新speculator

        events = []
        for target_id in target_ids:
            auction_outcome_event = AuctionOutcomeEvent(
                self.profile_id,
                target_id,
                auction_id=auction_id,
                outcome=str(auction_outcome),
                completion_status="completed"
            )
            events.append(auction_outcome_event)

        

        return events