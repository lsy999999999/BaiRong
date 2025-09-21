from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


class QuarantineStatusUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        household_id: int = 0,
        quarantine_status: str = 'none',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.household_id = household_id
        self.quarantine_status = quarantine_status

class InterventionDeployedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        public_health_authority_id: int = 0,
        intervention_type: str = "",
        target_individual_id: int = 0,
        healthcare_facility_id: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.public_health_authority_id = public_health_authority_id
        self.intervention_type = intervention_type
        self.target_individual_id = target_individual_id
        self.healthcare_facility_id = healthcare_facility_id

class ResourcesAllocatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        healthcare_facility_id: int = 0,
        resources_allocated: dict = {},
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.healthcare_facility_id = healthcare_facility_id
        self.resources_allocated = resources_allocated
        self.completion_status = completion_status

class HealthcareServiceProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        healthcare_facility_id: int = 0,
        service_type: str = "",
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.healthcare_facility_id = healthcare_facility_id
        self.service_type = service_type
        self.completion_status = completion_status

class EpidemiologicalDataEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        public_health_authority_id: int = 0,
        epidemiological_data: dict = {},
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.public_health_authority_id = public_health_authority_id
        self.epidemiological_data = epidemiological_data

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class RiskPerceptionUpdatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = 0,
        risk_perception: float = 0.0,
        information_sources: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.risk_perception = risk_perception
        self.information_sources = information_sources

class BehaviorAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        individual_id: int = 0,
        healthcare_facility_id: int = 0,
        household_id: int = 0,
        behavior_changes: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.individual_id = individual_id
        self.healthcare_facility_id = healthcare_facility_id
        self.household_id = household_id
        self.behavior_changes = behavior_changes