from onesim.simulator import BasicSimEnv
from .events import StartEvent
from datetime import datetime

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> StartEvent:
        # Extract relevant information from self.data according to StartEvent
        source_id = self.data.get('source_id', 'ENV')
        event_time = self.data.get('event_time', datetime.now())
        return StartEvent(from_agent_id=source_id, to_agent_id=target_id, timestamp=event_time)