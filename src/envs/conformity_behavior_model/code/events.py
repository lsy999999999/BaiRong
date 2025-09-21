from onesim.events import Event
from typing import Dict, List, Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class InitialJudgmentFormedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        initial_judgment: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.initial_judgment = initial_judgment

class ConformityDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        conformity_decision: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.conformity_decision = conformity_decision

class BeliefUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: str = "",
        updated_belief: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.updated_belief = updated_belief

class OpinionDistributionTrackedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        group_id: str = "",
        opinion_distribution: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.group_id = group_id
        self.opinion_distribution = opinion_distribution

class GroupOpinionUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        group_id: str = "",
        updated_group_opinion: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.group_id = group_id
        self.updated_group_opinion = updated_group_opinion

class InfluenceExertedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        leader_id: str = "",
        target_individual_id: str = "",
        influence_strength: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.leader_id = leader_id
        self.target_individual_id = target_individual_id
        self.influence_strength = influence_strength

class LeaderInfluenceUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        leader_id: str = "",
        target_individual_id: str = "",
        updated_belief: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.leader_id = leader_id
        self.target_individual_id = target_individual_id
        self.updated_belief = updated_belief

class DecisionContextHandledEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        decision_context_id: str = "",
        completion_status: str = 'pending',
        results: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.decision_context_id = decision_context_id
        self.completion_status = completion_status
        self.results = results