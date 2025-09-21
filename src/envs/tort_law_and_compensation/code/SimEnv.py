from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        # Extract relevant information from self.data according to StartEvent
        source_id = await self.get_data('id', 'ENV')
        # Additional information extraction can be done here if needed
        # Return the StartEvent instance
        return StartEvent(from_agent_id=source_id, to_agent_id=target_id)
