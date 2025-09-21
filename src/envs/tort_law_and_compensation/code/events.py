from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class CompensationRequestEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        compensation_amount: float = 0.0,
        damage_description: str = "",
        evidence_list: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.compensation_amount = compensation_amount
        self.damage_description = damage_description
        self.evidence_list = evidence_list

class DefensePreparedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        liability_reduction_argument: str = "",
        counter_evidence_list: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.liability_reduction_argument = liability_reduction_argument
        self.counter_evidence_list = counter_evidence_list

class RequestEvaluationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_status: str = 'pending',
        evaluation_notes: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_status = evaluation_status
        self.evaluation_notes = evaluation_notes

class DefenseEvaluationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_status: str = 'pending',
        evaluation_notes: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_status = evaluation_status
        self.evaluation_notes = evaluation_notes

class DecisionMadeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        decision_outcome: str = "",
        compensation_awarded: float = 0.0,
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.decision_outcome = decision_outcome
        self.compensation_awarded = compensation_awarded
        self.completion_status = completion_status