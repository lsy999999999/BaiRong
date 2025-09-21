from onesim.events import Event
from typing import Any

class StrategyAdjustmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        strategy_changes: str = 'N/A',
        adjustment_reason: str = 'N/A',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.strategy_changes = strategy_changes
        self.adjustment_reason = adjustment_reason

class ReflectionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        reflection_summary: str = 'N/A',
        feedback_requested: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.reflection_summary = reflection_summary
        self.feedback_requested = feedback_requested

class ObservationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        observation_data: str = 'N/A',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.observation_data = observation_data

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class FeedbackEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        feedback_details: str = 'N/A',
        recommendations: str = 'N/A',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback_details = feedback_details
        self.recommendations = recommendations

class TaskExecutionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        task_id: str = "",
        task_details: str = 'N/A',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.task_id = task_id
        self.task_details = task_details

class PerformanceAnalysisEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        performance_summary: str = 'N/A',
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.performance_summary = performance_summary
        self.completion_status = completion_status