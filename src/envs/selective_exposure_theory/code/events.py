from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.fields = {}

class MediaSelectionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: int = 0,
        selected_media_id: int = -1,
        bias_alignment_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.selected_media_id = selected_media_id
        self.bias_alignment_score = bias_alignment_score
        self.fields = {
            "voter_id": voter_id,
            "selected_media_id": selected_media_id,
            "bias_alignment_score": bias_alignment_score
        }

class PreferenceAdjustmentEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        voter_id: int = 0,
        adjusted_preference_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.voter_id = voter_id
        self.adjusted_preference_score = adjusted_preference_score
        self.fields = {
            "voter_id": voter_id,
            "adjusted_preference_score": adjusted_preference_score
        }

class ContentDeliveryEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        media_id: int = 0,
        voter_id: int = 0,
        content_bias_score: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.media_id = media_id
        self.voter_id = voter_id
        self.content_bias_score = content_bias_score
        self.fields = {
            "media_id": media_id,
            "voter_id": voter_id,
            "content_bias_score": content_bias_score
        }