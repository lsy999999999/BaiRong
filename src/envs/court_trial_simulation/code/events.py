
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class EvidenceEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evidence_details: str = "",
        ruling_request: str = 'pending',
        prosecution_decision: str = 'undecided',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evidence_details = evidence_details
        self.ruling_request = ruling_request
        self.prosecution_decision = prosecution_decision

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class EvidenceEvaluationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evidence_evaluation: List[Any] = [],
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evidence_evaluation = evidence_evaluation

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class ProsecutionDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        prosecution_decision: str = 'undecided',
        evidence_quality: float = 0.0,
        conviction_likelihood: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.prosecution_decision = prosecution_decision
        self.evidence_quality = evidence_quality
        self.conviction_likelihood = conviction_likelihood

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class VerdictFormedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        verdict: str = 'undecided',
        completion_status: str = 'complete',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.verdict = verdict
        self.completion_status = completion_status

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class DefensePreparedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        defense_strategy: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.defense_strategy = defense_strategy

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class TestimonyPreparedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        testimony_content: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.testimony_content = testimony_content

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class PleaDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        plea_acceptance: str = 'undecided',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.plea_acceptance = plea_acceptance

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class EvidenceRulingEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evidence_admissibility: str = 'pending',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evidence_admissibility = evidence_admissibility

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class TestimonyEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        testimony_details: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.testimony_details = testimony_details

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class PleaNegotiationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        plea_terms: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.plea_terms = plea_terms

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

class WitnessCallEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        witness_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.witness_id = witness_id

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class TrialManagementEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        trial_phase: str = 'ongoing',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.trial_phase = trial_phase