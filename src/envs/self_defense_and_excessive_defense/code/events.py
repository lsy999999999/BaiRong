from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ThreatEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        threat_level: int = 1,
        aggressor_id: str = "",
        defender_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.threat_level = threat_level
        self.aggressor_id = aggressor_id
        self.defender_id = defender_id

class DefenseActionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        defensive_action_type: str = 'basic',
        defense_intensity: int = 1,
        evidence_collected: List[Any] = None,
        defender_id: str = "",
        judge_id: str = "",
        **kwargs: Any
    ) -> None:
        if evidence_collected is None:
            evidence_collected = []
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.defensive_action_type = defensive_action_type
        self.defense_intensity = defense_intensity
        self.evidence_collected = evidence_collected
        self.defender_id = defender_id
        self.judge_id = judge_id

class JudgmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        judgment_result: str = 'undecided',
        legal_reasons: str = "",
        threat_assessment: int = 0,
        defense_assessment: int = 0,
        judge_id: str = "",
        completion_status: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.judgment_result = judgment_result
        self.legal_reasons = legal_reasons
        self.threat_assessment = threat_assessment
        self.defense_assessment = defense_assessment
        self.judge_id = judge_id
        self.completion_status = completion_status