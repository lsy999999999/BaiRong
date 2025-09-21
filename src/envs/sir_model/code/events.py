from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        social_contact_pattern: str = 'normal',
        policy_effect: str = 'none',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.social_contact_pattern = social_contact_pattern
        self.policy_effect = policy_effect

class HealthStateChangeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        previous_health_state: str = 'S',
        current_health_state: str = 'S',
        requires_treatment: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.previous_health_state = previous_health_state
        self.current_health_state = current_health_state
        self.requires_treatment = requires_treatment

class TreatmentOutcomeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        treatment_status: str = 'pending',
        recovery_status: str = 'not_recovered',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.treatment_status = treatment_status
        self.recovery_status = recovery_status

class SocialContactPatternEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        group_id: str,
        contact_pattern: str = 'normal',
        risk_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        if not group_id:
            raise ValueError("group_id must be specified for SocialContactPatternEvent")
        self.group_id = group_id
        self.contact_pattern = contact_pattern
        self.risk_level = risk_level

class RiskAssessmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str,
        risk_level: float = 0.0,
        social_contact_pattern: str = 'normal',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        if not individual_id:
            raise ValueError("individual_id must be specified for RiskAssessmentEvent")
        self.individual_id = individual_id
        self.risk_level = risk_level
        self.social_contact_pattern = social_contact_pattern

class PolicyImplementationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        policy_id: str = "",
        individual_id: str = "",
        policy_effect: str = 'none',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.policy_id = policy_id
        self.individual_id = individual_id
        self.policy_effect = policy_effect

class PolicyImpactEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        policy_id: str = "",
        group_id: str = "",
        impact_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.policy_id = policy_id
        self.group_id = group_id
        self.impact_level = impact_level