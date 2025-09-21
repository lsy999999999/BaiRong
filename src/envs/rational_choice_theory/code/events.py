from onesim.events import Event
from typing import Any, List, Dict
from datetime import datetime

class DecisionMadeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        decision: str = "",
        influencing_factors: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.decision = decision
        self.influencing_factors = influencing_factors

class ChoicesEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        choices_list: List[Any] = [],
        evaluation_criteria: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.choices_list = choices_list
        self.evaluation_criteria = evaluation_criteria

class UtilityCalculatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        utility_value: float = 0.0,
        calculation_details: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.utility_value = utility_value
        self.calculation_details = calculation_details

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class AdjustmentObservedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        adjustment_status: str = 'completed',
        results_summary: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.adjustment_status = adjustment_status
        self.results_summary = results_summary