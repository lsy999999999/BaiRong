from onesim.events import Event
from typing import Any

class JudgmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        judgment_result: str = 'undecided',
        judge_id: str = "",
        case_id: str = "",
        completion_status: str = 'incomplete',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.judgment_result = judgment_result
        self.judge_id = judge_id
        self.case_id = case_id
        self.completion_status = completion_status

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class EvidenceEvaluationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_result: str = 'pending',
        judge_id: str = "",
        case_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_result = evaluation_result
        self.judge_id = judge_id
        self.case_id = case_id

class EvidenceSubmittedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evidence_details: str = "",
        plaintiff_id: str = "",
        case_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evidence_details = evidence_details
        self.plaintiff_id = plaintiff_id
        self.case_id = case_id

class DefenseEvaluationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_result: str = 'pending',
        judge_id: str = "",
        case_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_result = evaluation_result
        self.judge_id = judge_id
        self.case_id = case_id

class DefensePreparedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        defense_arguments: str = "",
        defendant_id: str = "",
        case_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.defense_arguments = defense_arguments
        self.defendant_id = defendant_id
        self.case_id = case_id