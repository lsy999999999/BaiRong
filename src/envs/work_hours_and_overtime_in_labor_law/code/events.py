from onesim.events import Event
from typing import Any, List

class DefenseSubmissionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employer_id: str = "",
        defense_arguments: str = "",
        evidence_documents: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, employer_id=employer_id, 
                         defense_arguments=defense_arguments, evidence_documents=evidence_documents, **kwargs)
        self.employer_id = employer_id
        self.defense_arguments = defense_arguments
        self.evidence_documents = evidence_documents

class OvertimeRequestEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employee_id: str = "",
        overtime_hours: float = 0.0,
        overtime_reason: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, employee_id=employee_id, 
                         overtime_hours=overtime_hours, overtime_reason=overtime_reason, **kwargs)
        self.employee_id = employee_id
        self.overtime_hours = overtime_hours
        self.overtime_reason = overtime_reason

class JudgmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        judge_id: str = "",
        ruling: str = "",
        legal_references: List[Any] = [],
        completion_status: str = 'Pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, judge_id=judge_id, 
                         ruling=ruling, legal_references=legal_references, completion_status=completion_status, **kwargs)
        self.judge_id = judge_id
        self.ruling = ruling
        self.legal_references = legal_references
        self.completion_status = completion_status

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)