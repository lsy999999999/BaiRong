# Event-Driven System

YuLan-OneSim uses a queue-based event-driven architecture that enables asynchronous agent interactions through a centralized event bus system.

## Event Architecture

### Core Event Structure
```python
class Event:
    def __init__(self, from_agent_id: str, to_agent_id: str, **kwargs):
        self.event_id: str = gen_id()
        self.timestamp: float = time.time()
        self.event_kind: str = self.__class__.__name__
        self.from_agent_id: str = from_agent_id
        self.to_agent_id: str = to_agent_id
        self.parent_event_id: Optional[str] = kwargs.get("parent_event_id")
```

### Built-in Event Types

**Control Events**
- `Event`: Base event class for all communications
- `StartEvent`: Begin simulation
- `EndEvent`: Terminate agent or simulation
- `PauseEvent`/`ResumeEvent`: Control simulation flow

**Data Events**
- `DataEvent`: Request data from agents or environment
- `DataResponseEvent`: Provide requested data
- `DataUpdateEvent`: Update shared state
- `DataUpdateResponseEvent`: Confirm data updates

**Custom Events**
You can create domain-specific events by inheriting from the base Event class:
```python
class MessageEvent(Event):
    def __init__(self, from_agent_id, to_agent_id, content, **kwargs):
        super().__init__(from_agent_id, to_agent_id, **kwargs)
        self.content = content

class TransactionEvent(Event):
    def __init__(self, from_agent_id, to_agent_id, amount, **kwargs):
        super().__init__(from_agent_id, to_agent_id, **kwargs)
        self.amount = amount
```

## Event Bus System

### Queue-Based Architecture
```python
class EventBus:
    def __init__(self):
        self.agent_registry = {}  # Maps agent_id to agent instances
        self.queue = asyncio.Queue()  # Central event queue
        self._running = False
        self._paused = False
```

### Agent Registration
Agents must register with the event bus to receive events:
```python
# Register an agent
event_bus.register_agent("agent_001", agent_instance)

# Agent registry maps agent IDs to agent objects
# When events arrive, the bus calls agent.add_event(event)
```

### Event Routing

**Direct Routing**: Events are routed by `to_agent_id`
```python
# Event targeted to specific agent
event = MessageEvent(
    from_agent_id="sender_123",
    to_agent_id="receiver_456", 
    content="Hello!"
)
```

**Broadcast Routing**: Special agent ID for environment-wide events
```python
# Broadcast to all agents
termination_event = EndEvent(
    from_agent_id="ENV",
    to_agent_id="all",  # Special broadcast target
    reason="simulation_complete"
)
```

**Environment Routing**: Events to environment use "ENV" as target
```python
# Send to environment
data_request = DataEvent(
    from_agent_id="agent_001",
    to_agent_id="ENV",
    source_type="AGENT",
    target_type="ENV",
    key="global_state"
)
```

## Event Lifecycle

### 1. Event Creation
Agents create events during action execution:
```python
# Create interaction event
event = MessageEvent(
    from_agent_id=self.agent_id,
    to_agent_id="colleague_123",
    content="Let's collaborate on this project"
)
```

### 2. Event Dispatch
Events are dispatched to the event bus:
```python
# Dispatch to event bus
await event_bus.dispatch_event(event)
```

### 3. Event Queuing
The event bus queues events for processing:
- Local events: Added to local queue
- Remote events: Forwarded to appropriate worker node
- Broadcast events: Distributed to all nodes

### 4. Event Processing
The event bus processes events from the queue:
```python
async def _process_event(self, event):
    # Find target agent
    agent = self.agent_registry.get(event.to_agent_id)
    
    if agent:
        # Deliver event to agent
        agent.add_event(event)
    else:
        # Handle routing errors
        logger.warning(f"Agent {event.to_agent_id} not found")
```

### 5. Agent Event Handling
Agents receive events through their event queue:
```python
class GeneralAgent:
    def add_event(self, event):
        """Add event to agent's processing queue"""
        self._event_queue.put_nowait(event)
    
    async def handle_event(self, event):
        """Process individual events"""
        if event.event_kind == "MessageEvent":
            await self.process_message(event)
        elif event.event_kind == "DataEvent":
            await self.handle_data_request(event)
```

## Distributed Event Handling

### Cross-Node Communication
Events between agents on different nodes are automatically routed:

**Master Node Routing**:
```python
# Master determines agent location
worker_id = master.agent_locations.get(event.to_agent_id)
if worker_id:
    # Forward to worker via gRPC
    await master.forward_event_to_worker(worker_id, event)
```

**Worker Node Routing**:
```python
# Worker checks if agent is local
if event.to_agent_id in local_agent_registry:
    # Process locally
    agent.add_event(event)
else:
    # Forward to master for routing
    await send_event_to_master(event)
```

### Event Serialization
Events are serialized for network transmission:
```python
def to_dict(self):
    return {
        "event_type": self.event_kind,
        "event_id": self.event_id,
        "source_id": str(self.from_agent_id),
        "target_id": str(self.to_agent_id),
        "timestamp": self.timestamp,
        "data": {/* event-specific data */}
    }
```

## Event Flow Control

### Pause/Resume Mechanism
```python
# Pause event processing
await event_bus.pause()

# Resume event processing  
await event_bus.resume()

# Check status
if event_bus.is_paused():
    print("Event bus is paused")
```

### Graceful Shutdown
```python
# Stop event processing
event_bus.stop()

# Send termination to all agents
termination_event = EndEvent(
    from_agent_id="ENV",
    to_agent_id="all",
    reason="simulation_complete"
)
await event_bus.dispatch_event(termination_event)
```

## Event Tracking & Analysis

### Workflow Visualization
The event bus automatically tracks event flows for analysis:
```python
# Events are tracked in sequences
self._event_sequence = []  # List of event records
self._event_flows = {}     # Groups related events
self._event_to_flow = {}   # Maps events to flows
```

### Event Flow Export
```python
# Export event flow data
flow_data = await event_bus.export_event_flow_data("flows.json")

# Contains:
{
    "flows": [
        {
            "id": "flow_001",
            "steps": [
                {
                    "timestamp": 1640995200.123,
                    "event_kind": "StartEvent",
                    "from_agent_id": "ENV",
                    "to_agent_id": "agent_001"
                }
            ]
        }
    ]
}
```

The queue-based event architecture ensures reliable, ordered event delivery while supporting both local and distributed agent interactions efficiently. 