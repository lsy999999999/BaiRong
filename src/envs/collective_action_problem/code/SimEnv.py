from onesim.simulator import BasicSimEnv
from .events import StartEvent
from datetime import datetime

class SimEnv(BasicSimEnv):

    async def _create_start_event(self, target_id: str) -> StartEvent:
        source_id = await self.get_data('id', 'ENV')
        timestamp = datetime.now()
        event_data = {
            'timestamp': timestamp,
            'scene_name': 'collective_action_problem',
            'domain': 'Economics'
        }
        return StartEvent(from_agent_id=source_id, to_agent_id=target_id, **event_data)
