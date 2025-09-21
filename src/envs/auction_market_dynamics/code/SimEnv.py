from onesim.simulator import BasicSimEnv
from .events import StartEvent

class SimEnv(BasicSimEnv):
    async def _create_start_event(self, target_id: str) -> StartEvent:
        # Extract relevant information from self.data according to StartEvent
        source_id = await self.get_data('id', 'ENV')
        market_conditions = {
            'market_liquidity': self.data.get('market_liquidity', 'medium'),
            'information_asymmetry': self.data.get('information_asymmetry', 'low'),
            'market_volatility': self.data.get('market_volatility', 'stable'),
            'regulation_strictness': self.data.get('regulation_strictness', 'moderate')
        }
        return StartEvent(
            from_agent_id=source_id,
            to_agent_id=target_id,
            market_conditions=market_conditions
        )
