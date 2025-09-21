from onesim.events import Event
from typing import Dict, List, Any

class CollectiveInterestEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        collective_interests: List[Any] = [],
        evaluation_criteria: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.collective_interests = collective_interests
        self.evaluation_criteria = evaluation_criteria

class LawEnforcementEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        law_details: str = "",
        conflict_trigger: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.law_details = law_details
        self.conflict_trigger = conflict_trigger

class ContractProposalEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_interests: List[Any] = [],
        proposal_details: str = "",
        negotiation_terms: Dict[str, Any] = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_interests = individual_interests
        self.proposal_details = proposal_details
        self.negotiation_terms = negotiation_terms

class ConflictResolutionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        conflict_details: str = "",
        resolution_method: str = "",
        resolution_status: str = 'in_progress',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.conflict_details = conflict_details
        self.resolution_method = resolution_method
        self.resolution_status = resolution_status

class PolicyImpactAnalysisEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        policy_details: str = "",
        impact_analysis_results: Dict[str, Any] = {},
        analysis_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.policy_details = policy_details
        self.impact_analysis_results = impact_analysis_results
        self.analysis_status = analysis_status

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class SocialContractApprovalEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        contract_terms: Dict[str, Any] = {},
        approval_status: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.contract_terms = contract_terms
        self.approval_status = approval_status