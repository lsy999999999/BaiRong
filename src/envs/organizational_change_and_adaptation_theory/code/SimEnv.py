from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent
from datetime import datetime

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        # Extract relevant information from self.data according to StartEvent
        source_id = self.data.get('source_id', 'ENV')
        change_type = self.data.get('change_type', 'incremental')
        timestamp = self.data.get('timestamp', datetime.now())
        
        # Create and return a StartEvent instance
        return StartEvent(
            from_agent_id=source_id,
            to_agent_id=target_id,
            change_type=change_type,
            timestamp=timestamp
        )