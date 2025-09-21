from onesim.events import Event
from typing import Any, List
from datetime import datetime

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ActivityCompletionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        completion_status: str = 'success',
        miner_id: str = "",
        activities_completed: str = "",
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.completion_status = completion_status
        self.miner_id = miner_id
        self.activities_completed = activities_completed

class InvestmentStrategyEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        miner_id: str = "",
        grid_cell_id: str = "",
        investment_amount: int = 0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.miner_id = miner_id
        self.grid_cell_id = grid_cell_id
        self.investment_amount = investment_amount

class LandOwnershipEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

class ResolutionOutcomeEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        miner_id: str = "",
        grid_cell_id: str = "",
        winner_id: str = "",
        investment_amount: int = 0,
        tie_resolution: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.miner_id = miner_id
        self.grid_cell_id = grid_cell_id
        self.winner_id = winner_id
        self.investment_amount = investment_amount
        self.tie_resolution = tie_resolution

class ResourceAvailabilityEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)