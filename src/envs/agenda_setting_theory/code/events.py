
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class FocusAdjustedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        public_agent_id: str = "",
        topic_id: str = "",
        new_focus_value: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.public_agent_id = public_agent_id
        self.topic_id = topic_id
        self.new_focus_value = new_focus_value

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

class TopicEmphasizedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        topic_id: str = "",
        reporting_frequency: int = 0,
        emotional_tone: str = 'neutral',
        media_agent_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.topic_id = topic_id
        self.reporting_frequency = reporting_frequency
        self.emotional_tone = emotional_tone
        self.media_agent_id = media_agent_id

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class TopicSelectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        topic_id: str = "",
        media_agent_id: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.topic_id = topic_id
        self.media_agent_id = media_agent_id