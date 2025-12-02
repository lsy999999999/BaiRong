
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
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        round_index: int,
        stamina_budget: int,
        max_mining_per_plot: int,
        ownership_map: list,
        public_log_last_log: list | None = None,
        personal_summary_overall: dict | None = None,
        run_seed: str | None = None,
    ):
        super().__init__(from_agent_id, to_agent_id)
        # 这些字段名要与 ResourceMiner.observe_global_map 里 getattr(...) 的键完全一致
        self.round_index = int(round_index)
        self.stamina_budget = int(stamina_budget)
        self.max_mining_per_plot = int(max_mining_per_plot)
        self.ownership_map = ownership_map or []                 # [{ "cell":[r,c], "owner":"agent_id|none" }, ...]
        self.previous_public_log = public_log_last_log or []     # optional
        self.personal_summary = personal_summary_overall or {}   # optional
        self.run_seed = str(run_seed or "0")                     # optional


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