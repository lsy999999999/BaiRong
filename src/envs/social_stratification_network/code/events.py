from onesim.events import Event
from typing import Dict, List, Any

class HiringDecisionMadeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employer_id: int = 0,
        hired_candidate_id: int = 0,
        hiring_status: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.employer_id = employer_id
        self.hired_candidate_id = hired_candidate_id
        self.hiring_status = hiring_status


class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)


class CandidatesEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employer_id: int = 0,
        candidate_ids: List[int] = [],
        evaluation_scores: Dict[int, float] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.employer_id = employer_id
        self.candidate_ids = candidate_ids
        self.evaluation_scores = evaluation_scores


class ExchangeEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        initiator_id: int = 0,
        partner_id: int = 0,
        exchange_value: float = 0.0,
        risk_assessment: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.initiator_id = initiator_id
        self.partner_id = partner_id
        self.exchange_value = exchange_value
        self.risk_assessment = risk_assessment


class StudentsSelectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        institution_id: int = 0,
        selected_students_ids: List[int] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.institution_id = institution_id
        self.selected_students_ids = selected_students_ids


class ExchangeExecutedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        initiator_id: int = 0,
        partner_id: int = 0,
        resources_exchanged: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.initiator_id = initiator_id
        self.partner_id = partner_id
        self.resources_exchanged = resources_exchanged


class ExchangePartnerIdentifiedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        initiator_id: int = 0,
        partner_id: int = 0,
        trust_level: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.initiator_id = initiator_id
        self.partner_id = partner_id
        self.trust_level = trust_level


class EducationInvestmentDecidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        family_id: int = 0,
        institution_id: int = 0,
        investment_amount: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.family_id = family_id
        self.institution_id = institution_id
        self.investment_amount = investment_amount


class AdmissionDecisionReceivedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        family_id: int = 0,
        admission_status: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.family_id = family_id
        self.admission_status = admission_status


class SocialCapitalUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = 0,
        social_capital_change: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.social_capital_change = social_capital_change


class ApplicationReceivedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        institution_id: int = 0,
        application_id: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.institution_id = institution_id
        # self.application_id = application_id


class EducationResourcesAllocatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        family_id: int = 0,
        resources_allocated: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.family_id = family_id
        self.resources_allocated = resources_allocated