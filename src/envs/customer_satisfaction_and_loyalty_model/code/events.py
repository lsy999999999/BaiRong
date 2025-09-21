from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class SatisfactionEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        satisfaction_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.satisfaction_score = satisfaction_score

class CustomerInitializedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        customer_id: str = None,
        initial_loyalty: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.customer_id = customer_id
        self.initial_loyalty = initial_loyalty

class QualityAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        new_service_quality: float = 0.0,
        new_product_quality: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.new_service_quality = new_service_quality
        self.new_product_quality = new_product_quality

class MerchantInitializedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        merchant_id: str = None,
        baseline_service_quality: float = 0.0,
        baseline_product_quality: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.merchant_id = merchant_id
        self.baseline_service_quality = baseline_service_quality
        self.baseline_product_quality = baseline_product_quality

class EndEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        completion_status: str = "Completed",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.completion_status = completion_status

class QualityPerceptionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        perceived_service_quality: float = 0.0,
        product_experience_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.perceived_service_quality = perceived_service_quality
        self.product_experience_score = product_experience_score

class PurchaseDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        purchase_decision: bool = False,
        purchase_probability: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.purchase_decision = purchase_decision
        self.purchase_probability = purchase_probability

class FeedbackCollectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        average_feedback_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.average_feedback_score = average_feedback_score

class LoyaltyUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        loyalty_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.loyalty_score = loyalty_score