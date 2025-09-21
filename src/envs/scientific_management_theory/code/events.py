from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class WorkflowDesignedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        workflow_id: str = "",
        designer_id: str = "",
        design_details: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.workflow_id = workflow_id
        self.designer_id = designer_id
        self.design_details = design_details

class TasksAllocatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        task_list: List[Any] = [],
        worker_ids: List[Any] = [],
        allocation_strategy: str = 'skill_based',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.task_list = task_list
        self.worker_ids = worker_ids
        self.allocation_strategy = allocation_strategy

class FeedbackAndIncentivesProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        feedback: str = "",
        incentives: List[Any] = [],
        worker_ids: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback = feedback
        self.incentives = incentives
        self.worker_ids = worker_ids

class TasksExecutedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        task_results: List[Any] = [],
        worker_ids: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.task_results = task_results
        self.worker_ids = worker_ids

class PerformanceAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        adjustments: str = "",
        worker_ids: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.adjustments = adjustments
        self.worker_ids = worker_ids

class PerformanceEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_report: str = "",
        evaluator_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_report = evaluation_report
        self.evaluator_id = evaluator_id

class WorkflowFinalizedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        completion_status: str = 'completed',
        final_report: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.completion_status = completion_status
        self.final_report = final_report