from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class LoanApplicationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        customer_id: str = "",
        loan_amount: float = 0.0,
        economic_conditions: str = "stable",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.customer_id = customer_id
        self.loan_amount = loan_amount
        self.economic_conditions = economic_conditions

class LoanDecisionProcessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        customer_id: str = "",
        loan_status: str = "pending",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.customer_id = customer_id
        self.loan_status = loan_status

class LoanApprovalEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        customer_id: str = "",
        approved_amount: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.customer_id = customer_id
        self.approved_amount = approved_amount

class LoanRejectionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        customer_id: str = "",
        rejection_reason: str = "insufficient_reserves",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.customer_id = customer_id
        self.rejection_reason = rejection_reason

class ReserveAdjustmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        bank_id: str = "",
        adjustment_amount: float = 0.0,
        new_reserve_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.bank_id = bank_id
        self.adjustment_amount = adjustment_amount
        self.new_reserve_level = new_reserve_level

class ReserveManagementCompletedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        bank_id: str = "",
        completion_status: str = "success",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.bank_id = bank_id
        self.completion_status = completion_status