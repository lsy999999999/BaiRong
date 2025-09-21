from onesim.events import Event
from typing import Any

class DissonanceExperiencedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        dissonance_level: float = 0.0,
        dissonance_cause: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.dissonance_level = dissonance_level
        self.dissonance_cause = dissonance_cause

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class StrategyDecidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        strategy_type: str = 'none',
        expected_outcome: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.strategy_type = strategy_type
        self.expected_outcome = expected_outcome

class FeedbackProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        feedback_content: str = "",
        feedback_quality: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback_content = feedback_content
        self.feedback_quality = feedback_quality

class EvaluationCompletedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_result: str = "",
        completion_status: str = 'incomplete',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_result = evaluation_result
        self.completion_status = completion_status