from onesim.events import Event
from typing import Any, List
from datetime import datetime

class FeedbackRecordedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        media_id: int = 0,
        completion_status: str = "completed",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.media_id = media_id
        self.completion_status = completion_status

class FeedbackProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        audience_id: int = 0,
        media_id: int = 0,
        satisfaction_level: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.audience_id = audience_id
        self.media_id = media_id
        self.satisfaction_level = satisfaction_level

class MediaSelectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        audience_id: int = 0,
        media_id: int = 0,
        need_type: str = "unknown",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.audience_id = audience_id
        self.media_id = media_id
        self.need_type = need_type

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ContentProvidedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        media_id: int = 0,
        content_type: str = "unknown",
        target_need: str = "unknown",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.media_id = media_id
        self.content_type = content_type
        self.target_need = target_need