---
sidebar_position: 5
title: Events System API
---

# Event API 

## Event

Base event class for the agent communication system. All events in the system should inherit from this class.

### Constructor

```python
class Event:
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    )
```

| Parameter       | Type | Description                                                                 |
| --------------- | ---- | --------------------------------------------------------------------------- |
| from\_agent\_id | str  | The ID of the agent sending the event                                       |
| to\_agent\_id   | str  | The ID of the agent receiving the event                                     |
| \*\*kwargs      | Any  | Additional event attributes (e.g., event\_id, timestamp, parent\_event\_id) |

### Methods

* `to_dict(self) -> dict`: Convert event to a dictionary format with standard fields.
* `get(self, key: str, default: Any = None) -> Any`: Get an attribute value by key with a default fallback.
* `__getitem__(self, key: str) -> Any`: Access event attributes using dictionary-style syntax.
* `__str__(self) -> str`: Return a string representation of the event.

---

## EndEvent

Event to signal agent termination. Inherits from Event.

### Constructor

```python
class EndEvent(Event):
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        reason: str = "normal_termination",
        **kwargs: Any
    )
```

| Parameter       | Type | Description                                           |
| --------------- | ---- | ----------------------------------------------------- |
| from\_agent\_id | str  | ID of the sender                                      |
| to\_agent\_id   | str  | ID of the receiver (use "all" for global termination) |
| reason          | str  | Reason for termination                                |
| \*\*kwargs      | Any  | Additional keyword arguments                          |

---

## DataEvent

Event for data access across agents and environment. Inherits from Event.

### Constructor

```python
class DataEvent(Event):
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        source_type: str,
        target_type: str,
        key: str,
        default: Any = None,
        **kwargs
    )
```

| Parameter       | Type | Description                                  |
| --------------- | ---- | -------------------------------------------- |
| from\_agent\_id | str  | ID of requesting entity                      |
| to\_agent\_id   | str  | ID of entity that should receive request     |
| source\_type    | str  | Type of requesting entity ("AGENT" or "ENV") |
| target\_type    | str  | Type of target entity ("AGENT" or "ENV")     |
| key             | str  | Data key to access                           |
| default         | Any  | Default value if key not found               |
| \*\*kwargs      | Any  | Additional keyword arguments                 |

---

## DataResponseEvent

Event for data access response. Inherits from Event.

### Constructor

```python
class DataResponseEvent(Event):
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        request_id: str,
        key: str,
        data_value: Any = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
    )
```

| Parameter       | Type           | Description                      |
| --------------- | -------------- | -------------------------------- |
| from\_agent\_id | str            | ID of responding entity          |
| to\_agent\_id   | str            | ID of requesting entity          |
| request\_id     | str            | ID of the originating request    |
| key             | str            | Data key that was accessed       |
| data\_value     | Any            | Value of the data if success     |
| success         | bool           | Whether the query was successful |
| error           | Optional\[str] | Error message if not successful  |
| \*\*kwargs      | Any            | Additional keyword arguments     |

---

## DataUpdateEvent

Event for updating data across agents and environment. Inherits from Event.

### Constructor

```python
class DataUpdateEvent(Event):
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        source_type: str,
        target_type: str,
        key: str,
        value: Any,
        **kwargs
    )
```

| Parameter       | Type | Description                                  |
| --------------- | ---- | -------------------------------------------- |
| from\_agent\_id | str  | ID of requesting entity                      |
| to\_agent\_id   | str  | ID of entity that should receive update      |
| source\_type    | str  | Type of requesting entity ("AGENT" or "ENV") |
| target\_type    | str  | Type of target entity ("AGENT" or "ENV")     |
| key             | str  | Data key to update                           |
| value           | Any  | New value to set                             |
| \*\*kwargs      | Any  | Additional keyword arguments                 |

---

## DataUpdateResponseEvent

Event for data update response. Inherits from Event.

### Constructor

```python
class DataUpdateResponseEvent(Event):
    def __init__(
        self,
        from_agent_id: str,
        to_agent_id: str,
        request_id: str,
        key: str,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
    )
```

| Parameter       | Type           | Description                       |
| --------------- | -------------- | --------------------------------- |
| from\_agent\_id | str            | ID of responding entity           |
| to\_agent\_id   | str            | ID of requesting entity           |
| request\_id     | str            | ID of the originating request     |
| key             | str            | Data key that was updated         |
| success         | bool           | Whether the update was successful |
| error           | Optional\[str] | Error message if not successful   |
| \*\*kwargs      | Any            | Additional keyword arguments      |

---

## EventBus

Event bus responsible for handling all event distribution in the system.

### Constructor

```python
class EventBus:
    def __init__(self)
```

### Methods

* `async def dispatch_event(self, event: Event) -> None`: Dispatch an event, choosing local or remote distribution based on distributed mode.
* `async def run(self)`: Start processing the event queue. Runs until `stop()` is called.
* `stop(self)`: Stop the event bus processing.
* `async def pause(self)`: Pause the event bus processing.
* `async def resume(self)`: Resume the event bus processing.
* `is_paused(self) -> bool`: Check if the event bus is paused.
* `is_empty(self) -> bool`: Check if the event queue is empty.
* `is_stopped(self) -> bool`: Check if the event bus is stopped.
* `register_event(self, event_kind: str, agent: Any) -> None`: Register an agent to listen for a specific event kind.
* `register_agent(self, agent_id: str, agent: Any) -> None`: Register an agent in the event bus registry.
* `setup_distributed(self, node)`: Configure the event bus for distributed mode.
* `async def log_event_flows(self) -> None`: Log all tracked event flows at the end of simulation.
* `async def export_event_flow_data(self, output_file: str = None) -> Dict[str, Any]`: Export event flow data to a file or return as a dictionary.
* `async def cleanup_expired_locks(self)`: Clean up expired locks - should be called periodically in distributed systems.

---

## Scheduler

Scheduler for managing timed and recurring events.

### Constructor

```python
class Scheduler:
    def __init__(
        self,
        event_bus: EventBus
    )
```

| Parameter  | Type     | Description                                         |
| ---------- | -------- | --------------------------------------------------- |
| event\_bus | EventBus | Event bus instance for dispatching scheduled events |

### Methods

* `schedule_task(self, interval: float, event: Any, max_count: Optional[int] = None) -> asyncio.Task`: Schedule a new task with the given interval and event.
* `async def run(self)`: Start running all scheduled tasks.
* `async def stop(self)`: Stop all tasks and clean up.
* `async def pause(self, task: asyncio.Task = None)`: Pause specific task or all tasks if no task is specified.
* `async def resume(self, task: asyncio.Task = None)`: Resume specific task or all tasks if no task is specified.
* `is_done(self) -> bool`: Check if all scheduled tasks have completed.
* `get_task_info(self, task: asyncio.Task) -> Dict[str, Any]`: Get information about a specific task.
* `get_remaining_executions(self, task: asyncio.Task) -> Optional[int]`: Get the number of remaining executions for a task. Returns None if the task has infinite executions.

---

## Factory Functions

### get\_event\_bus

Get the global EventBus instance, ensuring only one instance exists throughout the application.

```python
def get_event_bus() -> EventBus
```

| Returns    | Type     | Description                  |
| ---------- | -------- | ---------------------------- |
| event\_bus | EventBus | The global EventBus instance |

### reset\_event\_bus

Reset the global EventBus instance.

```python
def reset_event_bus() -> None
```

---

*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
