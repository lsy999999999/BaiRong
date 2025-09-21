# Simulation Environment & Execution

YuLan-OneSim provides a flexible simulation environment system that manages agent interactions and execution flow.

## Execution Modes

### Round Mode
- All agents act simultaneously in each round
- Waits for all agents to complete before advancing
- Use cases: Voting, auctions, turn-based scenarios
- Benefits: Deterministic, consistent timing

### Tick Mode
- Agents act independently at their own pace
- Continuous event processing without waiting
- Use cases: Social networks, epidemic spread, markets
- Benefits: Realistic interaction patterns


## Configuration Options

### SimulationConfig
Configure your simulation environment with these key parameters:

| Parameter              | Description                           | Default |
| ---------------------- | ------------------------------------- | ------- |
| `mode`                 | Execution mode (`ROUND` or `TIMED`)   | `ROUND` |
| `max_steps`            | Maximum simulation steps/rounds       | `1`     |
| `interval`             | Time interval between ticks (seconds) | `60.0`  |
| `bus_idle_timeout`     | Timeout for idle detection (seconds)  | `120.0` |
| `export_training_data` | Export decisions for training         | `False` |
| `export_event_data`    | Export event logs                     | `False` |
| `collection_interval`  | Metrics collection interval           | `30`    |

## Simulation Lifecycle

### Starting a Simulation
```python
# Initialize environment
env = BasicSimEnv(
    name="my_simulation",
    event_bus=event_bus,
    config=config,
    agents=agents,
    start_targets={"agent_type": [1, 2, 3]},
    end_targets={"agent_type": [1, 2, 3]}
)

# Run simulation
tasks = await env.run()
```

### Simulation States
The environment tracks these states:
- **INITIALIZED**: Ready to start
- **RUNNING**: Active execution  
- **PAUSED**: Temporarily suspended
- **COMPLETED**: Finished normally
- **TERMINATED**: Stopped externally
- **ERROR**: Error occurred

### Lifecycle Control
```python
# Pause simulation
await env.pause_simulation()

# Resume simulation  
await env.resume_simulation()

# Stop simulation
await env.stop_simulation()

# Check status
if env.is_running():
    print("Simulation is active")
```

## State Management

**Global State**: Shared information accessible to all agents

### Data Access
```python
# Get data with dot notation support
value = await env.get_data("path.to.data", default=None)

# Update shared data
await env.update_data("key", new_value)

# Get data from specific agent
agent_data = await env.get_agent_data("agent_id", "key")

# Update agent data
success = await env.update_agent_data("agent_id", "key", value)
```

### Batch Operations
```python
# Get data from all agents of a type
type_data = await env.get_agent_data_by_type("agent_type", "key")
```

## Event Processing

The environment processes events asynchronously and handles:
- Agent communications
- State changes
- Data requests/updates
- Simulation control commands

## Data Persistence

### Exported Data
When enabled, the system exports:
- **Training Data**: Agent decisions and contexts
- **Event Logs**: Complete interaction history  
- **Metrics**: Performance and token usage statistics

### Metrics Collection
Automatic collection includes:
- Step duration and timing
- Event counts per step
- Token usage statistics
- System performance metrics


## Best Practices

### Performance Optimization
- Use appropriate `bus_idle_timeout` for your scenario
- Enable data export only when needed
- Configure `collection_interval` based on simulation duration

### Error Handling
- Monitor simulation state regularly
- Implement proper timeout handling
- Use try-catch blocks around lifecycle operations

### Resource Management
- Set reasonable `max_steps` limits
- Monitor memory usage with large agent populations
- Clean up resources with `stop_simulation()`

