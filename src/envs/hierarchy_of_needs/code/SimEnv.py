from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        # Extract the source agent ID from self.data, assuming 'source_agent_id' is a key
        source_id = self.data.get('source_agent_id', 'ENV')
        # Create and return a StartEvent with the extracted source_id and given target_id
        return StartEvent(from_agent_id=source_id, to_agent_id=target_id)