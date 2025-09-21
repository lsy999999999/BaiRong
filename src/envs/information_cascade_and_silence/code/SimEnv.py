from onesim.simulator import BasicSimEnv
from .events import StartEvent
from datetime import datetime

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> StartEvent:
        source_id = self.data.get('environment_id', 'ENV')
        timestamp = self.data.get('start_time', datetime.now())
        return StartEvent(
            from_agent_id=source_id,
            to_agent_id=target_id,
            timestamp=timestamp
        )