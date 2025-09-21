---

sidebar\_position: 3
title: Environment API
---

# Environment API

The Environment API provides the foundational class **BasicSimEnv** for creating all simulation scenarios within YuLan-OneSim. It defines the core logic for managing the simulation lifecycle, events, and agents.

## BasicSimEnv

### Description

`BasicSimEnv` is the universal base class for all simulation environments. It offers a flexible framework supporting both timed and round-based workflows, providing the essential structure for implementing diverse simulation scenarios. All specific environments, such as those found in the `src/envs/` directory, inherit from this class.

### Configuration Classes

#### `SimulationMode` (Enum)

* `TIMED`: Trigger events at fixed time intervals
* `ROUND`: Execute simulation in discrete rounds

#### `SimulationState` (Enum)

* `INITIALIZED`: Initialization complete but not started
* `RUNNING`: Simulation is actively running
* `PAUSED`: Simulation is paused
* `COMPLETED`: Simulation completed normally
* `TERMINATED`: Simulation terminated externally
* `ERROR`: Error occurred during simulation

#### `SimulationConfig`

Configuration dataclass for the simulation environment:

| Field                  | Type             | Description                                       |
| ---------------------- | ---------------- | ------------------------------------------------- |
| `mode`                 | `SimulationMode` | Simulation execution mode (TIMED or ROUND)        |
| `max_steps`            | `int`            | Maximum number of steps/rounds to execute         |
| `interval`             | `float`          | Time interval between triggers in TIMED mode      |
| `bus_idle_timeout`     | `float`          | Time to wait before considering event bus as idle |
| `export_training_data` | `bool`           | Whether to export training/decision data          |
| `export_event_data`    | `bool`           | Whether to export event flow data                 |
| `additional_config`    | `Dict[str, Any]` | Additional custom configuration                   |
| `collection_interval`  | `int`            | Interval for periodic metrics collection          |

### Constructor

```python
class BasicSimEnv:
    def __init__(
        self,
        name: str,
        event_bus: EventBus,
        data: Optional[Dict[str, Any]] = None,
        start_targets: Optional[Dict[str, Any]] = None,
        end_targets: Optional[Dict[str, Any]] = None,
        config: Optional[Union[Dict[str, Any], SimulationConfig]] = None,
        agents: Optional[Dict[str, GeneralAgent]] = None,
        env_path: Optional[str] = None,
        trail_id: Optional[str] = None,
    ) -> None:
        ...
```

#### Constructor Arguments

| Parameter       | Type                                      | Description                                                                                              |
| --------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `name`          | `str`                                     | The name of the environment.                                                                             |
| `event_bus`     | `EventBus`                                | The event bus instance used for dispatching and listening to events across the simulation.               |
| `data`          | `Optional[Dict[str, Any]]`                | Initial shared data for the environment. Can be accessed and modified by agents.                         |
| `start_targets` | `Optional[Dict[str, Any]]`                | Specifies the agents or conditions that initiate the simulation.                                         |
| `end_targets`   | `Optional[Dict[str, Any]]`                | Defines the conditions or agents that determine the end of a simulation round or the entire simulation.  |
| `config`        | `Optional[Union[Dict, SimulationConfig]]` | Configuration object or dictionary specifying simulation parameters like mode, max\_steps, and interval. |
| `agents`        | `Optional[Dict[str, GeneralAgent]]`       | A dictionary of all agent instances participating in the simulation, keyed by their IDs.                 |
| `env_path`      | `Optional[str]`                           | The file system path for the environment, used for saving logs and metrics.                              |
| `trail_id`      | `Optional[str]`                           | An identifier for the simulation trail, used for data persistence and tracking simulation history.       |

## Main Interfaces

### Core Simulation Control

* `async def run(self) -> List[asyncio.Task]`
  Initializes and starts all core tasks for the environment, including event processing and metrics collection. It's the main entry point for running the simulation.

* `async def start(self, **kwargs: Any) -> None`
  Officially starts the simulation after initialization, triggering the initial events based on `start_targets`.

* `async def stop_simulation(self)`
  Gracefully stops the simulation in both single and distributed modes. Sends termination signal to all registered agents and saves final data.

* `async def pause_simulation(self)`
  Pauses the simulation, suspending event processing and agent activities. The simulation clock and event processing are halted until resumed.

* `async def resume_simulation(self)`
  Resumes a paused simulation, continuing event processing and agent activities. Timing calculations are adjusted to account for time spent paused.

* `def terminate(self, event: Event, **kwargs: Any) -> None`
  Handles agent termination events. Updates tracking for round completion in ROUND mode or trigger counts in TIMED mode.

### Data Access and Management

* `async def get_data(self, key: str = None, default: Optional[Any] = None) -> Any`
  Asynchronously retrieves a value from the environment's shared data store. Supports multi-level dot notation (e.g., `"level1.level2.key"`). If no key is provided, returns the entire data dictionary.

* `async def update_data(self, key: str, data: Any) -> Any`
  Asynchronously updates a value in the environment's shared data store.

* `async def get_agent_data(self, agent_id: str, key: str, default: Optional[Any] = None) -> Any`
  Gets data from a specific agent, handling both local and distributed cases transparently.

* `async def update_agent_data(self, agent_id: str, key: str, value: Any) -> bool`
  Updates data in a specific agent with distributed locking support for consistency.

* `async def get_agent_data_by_type(self, agent_type: str, key: str, default: Optional[Any] = None) -> Any`
  Gets data from all agents of a specific type. Returns a dictionary mapping agent IDs to their data values.

### Event Management

* `def register_event(self, event_kind: str, method_name: str) -> None`
  Registers a handler method for a specific type of event, allowing the environment to react to different occurrences.

* `def add_event(self, event: Event) -> None`
  Adds an event to the internal processing queue of the environment.

* `async def queue_event(self, event_data: Dict[str, Any])`
  Queues an event to be saved at the end of the current step and broadcasts it via WebSocket if available.

* `async def queue_decision(self, decision_data: Dict[str, Any])`
  Queues a decision to be saved at the end of the current step for training data export.

### State and Metrics

* `async def set_simulation_state(self, new_state: SimulationState, reason: str = None) -> bool`
  Updates the state of the simulation with proper state transition handling.

* `def get_statistics(self) -> Dict[str, Any]`
  Returns comprehensive simulation statistics including total steps, agent completion data, and timing information.

* `async def collect_metrics(self)`
  Collects metrics for the current round including duration, event count, and token usage statistics.

* `def is_running(self) -> bool`
  Checks if the simulation is in a running state.

* `def is_paused(self) -> bool`
  Checks if the simulation is in a paused state.

* `def is_terminated(self) -> bool`
  Checks if the simulation has been terminated (including normal completion and external termination).

* `def describe(self) -> str`
  Returns a textual description of the environment's current configuration and state.

* `def get_env_id(self) -> str`
  Retrieves the unique identifier of this environment instance.

### Built-in Event Handlers

The environment automatically handles several types of events:

#### Data Events

* `handle_data_event`: Processes data access requests from agents
* `handle_data_response`: Handles responses to data access requests
* `handle_data_update_event`: Processes data update requests from agents
* `handle_data_update_response`: Handles responses to data update requests

#### Control Events

* `handle_pause_event`: Processes pause requests
* `handle_resume_event`: Processes resume requests

### Data Persistence

When `trail_id` is provided, the environment automatically saves:

* **Environment State**: Complete environment data at each step
* **Agent States**: Profile, memory, relationships, and additional state for each agent
* **Events**: All events that occur during the simulation
* **Decisions**: Agent decisions for training data generation
* **Metrics**: Performance metrics and statistics

Data is saved at the end of each step/round and can be exported in various formats based on configuration.

---

**Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs**
