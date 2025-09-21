from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ChangeInitiatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        change_type: str = 'incremental',
        change_goals: str = "",
        leader_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.change_type = change_type
        self.change_goals = change_goals
        self.leader_id = leader_id

class ChangeExecutionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        manager_id: str,
        execution_plan: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.manager_id = manager_id
        self.execution_plan = execution_plan

class FeedbackEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employee_id: str,
        feedback: str = "",
        emotional_response: str = 'neutral',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.employee_id = employee_id
        self.feedback = feedback
        self.emotional_response = emotional_response

class StrategyAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        manager_id: str = "",
        adjusted_strategy: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.manager_id = manager_id
        self.adjusted_strategy = adjusted_strategy

class ChangeFinalizedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        leader_id: str = "",
        completion_status: str = 'success',
        results: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.leader_id = leader_id
        self.completion_status = completion_status
        self.results = results