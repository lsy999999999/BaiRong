
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class ResponseSentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        status: str,
        response_data: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.status = status
        self.response_data = response_data

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

class RequestProcessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        response_data: str,
        status: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.response_data = response_data
        self.status = status