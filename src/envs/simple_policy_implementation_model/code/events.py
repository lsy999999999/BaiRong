
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class ComplianceDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        compliance_level: float = 0.0,
        policy_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.compliance_level = compliance_level
        self.policy_id = policy_id

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class PolicyStrengthAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        new_strength: float = 0.0,
        adjustment_reason: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.new_strength = new_strength
        self.adjustment_reason = adjustment_reason

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class SatisfactionAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        satisfaction_level: float = 0.0,
        adjustment_reason: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.satisfaction_level = satisfaction_level
        self.adjustment_reason = adjustment_reason

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class PolicyExecutedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        efficiency_metrics: float = 0.0,
        policy_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.efficiency_metrics = efficiency_metrics
        self.policy_id = policy_id