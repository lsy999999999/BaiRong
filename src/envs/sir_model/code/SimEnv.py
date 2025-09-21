from onesim.simulator import BasicSimEnv
from onesim.events import Event
from .events import StartEvent

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> Event:
        # Extract relevant information from self.data
        source_id = await self.get_data('id', 'ENV')
        social_contact_pattern = await self.get_data('social_contact_pattern', 'normal')
        policy_effect = await self.get_data('policy_effect', 'none')

        # Create and return the StartEvent instance
        return StartEvent(
            from_agent_id=source_id,
            to_agent_id=target_id,
            social_contact_pattern=social_contact_pattern,
            policy_effect=policy_effect
        )
