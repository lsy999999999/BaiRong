from onesim.events import Event
from typing import Any

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class InteractionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        interaction_type: str = 'dialogue',
        initiator_emotion: str = 'neutral',
        receiver_role: str = 'TeamLeader',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.interaction_type = interaction_type
        self.initiator_emotion = initiator_emotion
        self.receiver_role = receiver_role

class FeedbackProcessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        feedback_type: str = 'positive',
        processing_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback_type = feedback_type
        self.processing_status = processing_status

class FeedbackEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        feedback_content: str = 'general',
        receiver_id: str = None,  # Corrected to be set during event creation
        **kwargs: Any
    ) -> None:
        receiver_id = receiver_id or to_agent_id  # Ensure receiver_id matches the actual target agent
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.feedback_content = feedback_content
        self.receiver_id = receiver_id

class EmotionAnalyzedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        emotion_analysis_result: str = 'neutral',
        analysis_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.emotion_analysis_result = emotion_analysis_result
        self.analysis_status = analysis_status