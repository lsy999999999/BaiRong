from onesim.events import Event
from typing import Any

class AlternativesPresentedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        alternative_id: str = "",
        alternative_details: object = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.alternative_id = alternative_id
        self.alternative_details = alternative_details

class DecisionMadeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        decision_id: str = "",
        decision_result: str = 'success',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.decision_id = decision_id
        self.decision_result = decision_result

class ExternalFactorsSimulatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        factor_type: str = "",
        impact_level: str = '0',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.factor_type = factor_type
        self.impact_level = impact_level

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class OptionsEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        option_id: str = "",
        evaluation_criteria: object = {},
        evaluation_result: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.option_id = option_id
        self.evaluation_criteria = evaluation_criteria
        self.evaluation_result = evaluation_result

class InformationGatheredEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        source: str = 'EnvironmentAgent',
        information_content: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.source = source
        self.information_content = information_content