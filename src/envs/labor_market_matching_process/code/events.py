from onesim.events import Event
from typing import Dict, List, Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class JobOfferDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        job_seeker_id: int = 0,
        offer_accepted: bool = False,
        offer_details: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.job_seeker_id = job_seeker_id
        self.offer_accepted = offer_accepted
        self.offer_details = offer_details

class InterviewEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employer_id: int = 0,
        candidate_id: int = 0,
        interview_outcome: str = 'pending',
        offer_details: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.employer_id = employer_id
        self.candidate_id = candidate_id
        self.interview_outcome = interview_outcome
        self.offer_details = offer_details

class JobApplicationEvaluationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        job_seeker_id: int = 0,
        job_id: int = 0,
        application_value: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.job_seeker_id = job_seeker_id
        self.job_id = job_id
        self.application_value = application_value

class JobPostingDistributionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        channel_type: str = 'online',
        job_id: int = 0,
        application_cost: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.channel_type = channel_type
        self.job_id = job_id
        self.application_cost = application_cost

class JobMarketEntryEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        skills: List[Any] = [],
        education: str = "",
        experience: int = 0,
        job_preferences: List[Any] = [],
        network: List[Any] = [],
        risk_attitude: str = 'neutral',
        job_search_strategy: str = 'active',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.skills = skills
        self.education = education
        self.experience = experience
        self.job_preferences = job_preferences
        self.network = network
        self.risk_attitude = risk_attitude
        self.job_search_strategy = job_search_strategy

class SalaryNegotiationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        job_seeker_id: int = 0,
        employer_id: int = 0,
        proposed_salary: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.job_seeker_id = job_seeker_id
        self.employer_id = employer_id
        self.proposed_salary = proposed_salary

class CandidateScreeningEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employer_id: int = 0,
        candidate_id: int = 0,
        screening_result: str = 'pending',
        proposed_salary: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.employer_id = employer_id
        self.candidate_id = candidate_id
        self.screening_result = screening_result
        self.proposed_salary = proposed_salary

class JobPostingEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        employer_id: int = 0,
        job_id: int = 0,
        job_description: str = "",
        required_skills: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.employer_id = employer_id
        self.job_id = job_id
        self.job_description = job_description
        self.required_skills = required_skills