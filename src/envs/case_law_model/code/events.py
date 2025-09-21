from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class PrecedentInterpretedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        precedent_details: str = "",
        case_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.precedent_details = precedent_details
        self.case_id = case_id

class JudgmentAppliedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        judgment_result: str = "",
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.judgment_result = judgment_result
        self.completion_status = completion_status

class LegalContextDefinedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        legal_context: str = "",
        precedent_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.legal_context = legal_context
        self.precedent_id = precedent_id

class InterpretationAppliedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        interpretation_details: str = "",
        analysis_request_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.interpretation_details = interpretation_details
        self.analysis_request_id = analysis_request_id

class PrinciplesStoredEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        stored_principles: str = "",
        judge_request_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.stored_principles = stored_principles
        self.judge_request_id = judge_request_id

class InfluencesAnalyzedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        socio_political_influences: str = "",
        judgment_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.socio_political_influences = socio_political_influences
        self.judgment_id = judgment_id

class OutcomesAnalyzedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        outcome_analysis: str = "",
        workflow_status: str = 'terminated',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.outcome_analysis = outcome_analysis
        self.workflow_status = workflow_status