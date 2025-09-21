from onesim.events import Event
from typing import Any, List

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class SocialCapitalEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        social_capital_value: float = 0.0,
        cooperation_potential: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.social_capital_value = social_capital_value
        self.cooperation_potential = cooperation_potential

class CooperationDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        decision: str = 'undecided',
        impact_on_network: str = 'none',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.decision = decision
        self.impact_on_network = impact_on_network

class RelationshipsAnalyzedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        network_id: str = "",
        analysis_summary: str = 'pending',
        potential_updates: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.network_id = network_id
        self.analysis_summary = analysis_summary
        self.potential_updates = potential_updates

class NetworkUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        network_id: str = "",
        update_status: str = 'incomplete',
        changes_applied: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.network_id = network_id
        self.update_status = update_status
        self.changes_applied = changes_applied