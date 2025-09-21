from onesim.events import Event
from typing import Dict, List, Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        market_conditions: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.market_conditions = market_conditions

class SetReservePriceEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        seller_id: str = "",
        reserve_price: float = 0.0,
        auction_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.seller_id = seller_id
        self.reserve_price = reserve_price
        self.auction_id = auction_id

class ReservePriceSetEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        seller_id: str = "",
        reserve_price: float = 0.0,
        auction_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.seller_id = seller_id
        self.reserve_price = reserve_price
        self.auction_id = auction_id

class BidDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        buyer_id: str = "",
        bid_amount: float = 0.0,
        auction_id: str = "",
        bid_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.buyer_id = buyer_id
        self.bid_amount = bid_amount
        self.auction_id = auction_id
        self.bid_id = bid_id

class AuctionInitializedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        auction_id: str = "",
        mechanism_type: str = "",
        fee_structure: str = "",
        transparency_level: str = "",
        market_conditions: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.auction_id = auction_id
        self.mechanism_type = mechanism_type
        self.fee_structure = fee_structure
        self.transparency_level = transparency_level
        self.market_conditions = market_conditions

class MarketInfluenceEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        seller_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.speculator_id = from_agent_id
        self.seller_id = seller_id

class BiddingProcessAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        adjustment_reason: str = "",
        auction_id: str = "",
        seller_id: str = "",
        reserve_price: float = 0.0,
        buyer_id: str = "",
        bid_amount: float = 0.0,
        speculator_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.adjustment_reason = adjustment_reason
        self.auction_id = auction_id
        self.seller_id = seller_id
        self.reserve_price = reserve_price
        self.buyer_id = buyer_id
        self.bid_amount = bid_amount
        self.speculator_id = speculator_id

class BidReceivedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        bid_id: str = "",
        bid_amount: float = 0.0,
        buyer_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.bid_id = bid_id
        self.bid_amount = bid_amount
        self.buyer_id = buyer_id

class BiddingEligibilityConfirmedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        eligible_bids: List[Any] = [],
        auction_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.eligible_bids = eligible_bids
        self.auction_id = auction_id

class MarketConditionChangedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        market_volatility: float = 0.0,
        information_asymmetry: float = 0.0,
        speculator_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.market_volatility = market_volatility
        self.information_asymmetry = information_asymmetry
        self.speculator_id = speculator_id

class AuctionOutcomeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        auction_id: str = "",
        outcome: str = "",
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.auction_id = auction_id
        self.outcome = outcome
        self.completion_status = completion_status