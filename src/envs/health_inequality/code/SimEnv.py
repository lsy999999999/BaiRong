from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        source_id = await self.get_data('environment_id', 'ENV')
        return StartEvent(from_agent_id=source_id, to_agent_id=target_id)
