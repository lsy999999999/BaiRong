from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent
from datetime import datetime

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        source_id = self.data.get('id', 'ENV')
        cultural_context = self.data.get('cultural_context', {})
        event_time = datetime.now()
        
        return StartEvent(
            from_agent_id=source_id,
            to_agent_id=target_id,
            cultural_context=cultural_context,
            event_time=event_time
        )