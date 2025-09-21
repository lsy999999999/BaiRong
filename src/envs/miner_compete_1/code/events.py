
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class OccupyMaintainSuccessEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        new_owner: str = 'None',
        cell_coordinates: tuple = '(0,0)',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.new_owner = new_owner
        self.cell_coordinates = cell_coordinates

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class CompeteSuccessEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        new_owner: str = 'None',
        cell_coordinates: tuple = '(0,0)',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.new_owner = new_owner
        self.cell_coordinates = cell_coordinates

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class CompeteLandDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        energy_investment: int = 0,
        cell_coordinates: tuple = '(0,0)',
        current_owner: str = 'None',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.energy_investment = energy_investment
        self.cell_coordinates = cell_coordinates
        self.current_owner = current_owner

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class OccupyLandDecisionEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        energy_investment: int = 0,
        cell_coordinates: tuple = '(0,0)',
        previous_owner: str = 'None',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.energy_investment = energy_investment
        self.cell_coordinates = cell_coordinates
        self.previous_owner = previous_owner

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class ResourceExploitedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        units_exploited: int = 0,
        cell_coordinates: tuple = '(0,0)',
        exploit_success: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.units_exploited = units_exploited
        self.cell_coordinates = cell_coordinates
        self.exploit_success = exploit_success

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class MapObservedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)