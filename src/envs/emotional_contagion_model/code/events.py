
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class EmotionalStateAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        completion_status: str = 'success',
        final_emotional_state: str = 'joy',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.completion_status = completion_status
        self.final_emotional_state = final_emotional_state

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class EmotionTransmittedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        emotion_type: str = 'joy',
        intensity: float = 1.0,
        frequency_of_contact: int = 1,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.emotion_type = emotion_type
        self.intensity = intensity
        self.frequency_of_contact = frequency_of_contact

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

class EmotionalStateInitializedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        emotional_state: str = 'joy',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.emotional_state = emotional_state

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class EmotionalInfluenceEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        evaluation_result: str = 'neutral',
        adjustment_factor: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.evaluation_result = evaluation_result
        self.adjustment_factor = adjustment_factor