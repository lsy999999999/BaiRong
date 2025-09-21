from onesim.events import Event
from typing import Any, List, Optional

class InterventionCompleteEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        intervention_status: str = 'pending',
        environment_update: str = "",
        **kwargs: Any
    ) -> None:
        allowed_statuses = ['completed', 'failed', 'pending']
        if intervention_status not in allowed_statuses:
            intervention_status = 'pending'  # Fallback to default status
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.intervention_status = intervention_status
        self.environment_update = environment_update

class ContentCreatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        content: str = "",
        media_org_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.content = content
        self.media_org_id = media_org_id

class ContentMonitoredEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        monitored_content: str = "",
        risk_level: str = 'low',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.monitored_content = monitored_content
        self.risk_level = risk_level

class InformationSpreadEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        information_content: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.information_content = information_content

class VerificationCompleteEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        verification_result: str = 'unverified',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.verification_result = verification_result

class InformationAmplifiedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        amplified_content: str = "",
        media_org_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.amplified_content = amplified_content
        self.media_org_id = media_org_id

class OpinionExpressedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        opinion_content: str = "",
        target_audience: Optional[List[Any]] = None,
        **kwargs: Any
    ) -> None:
        if target_audience is None:
            target_audience = []
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.opinion_content = opinion_content
        self.target_audience = target_audience

class RumorDetectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        rumor_content: str = "",
        detection_confidence: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.rumor_content = rumor_content
        self.detection_confidence = detection_confidence

class EvaluationCompleteEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_result: str = 'undecided',
        expression_willingness: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_result = evaluation_result
        self.expression_willingness = expression_willingness

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ContentPublishedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        published_content: str = "",
        fact_check_org_id: str = "",
        **kwargs: Any
    ) -> None:
        if not fact_check_org_id:
            fact_check_org_id = ""  # Default to an empty string for consistency
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.published_content = published_content
        self.fact_check_org_id = fact_check_org_id

class ContentSelectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        selected_content: str = "",
        selection_criteria: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.selected_content = selected_content
        self.selection_criteria = selection_criteria

class InformationReceivedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        information_content: str = "",
        source_user_id: str = "",
        credibility_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.information_content = information_content
        self.source_user_id = source_user_id
        self.credibility_score = credibility_score