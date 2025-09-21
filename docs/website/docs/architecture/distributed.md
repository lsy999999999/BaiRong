# Distributed Architecture

YuLan-OneSim supports large-scale simulations using Master-Worker architecture with gRPC communication.

## Master-Worker Pattern

### Master Node
- **Agent Registry**: Maintains mapping of agents to workers
- **Global State Management**: Coordinates simulation state across workers  
- **Load Balancing**: Distributes agents optimally across workers
- **Event Routing**: Routes events between agents on different workers
- **Health Monitoring**: Tracks worker status and handles failures

### Worker Node  
- **Agent Hosting**: Executes agent logic and decision-making
- **Local Processing**: Handles agent interactions within the worker
- **Resource Management**: Manages compute and memory resources
- **Heartbeat Mechanism**: Reports status to master node
- **Event Processing**: Processes events for hosted agents

## Node Configuration

### Initialize Master Node
```python
from onesim.distribution.node import initialize_node

# Master node configuration
master_config = {
    "listen_port": 10051,
    "expected_workers": 3,
    "health_check_interval": 1800,  # seconds
    "worker_timeout": 3600
}

master = await initialize_node("master_001", "master", master_config)
```

### Initialize Worker Node
```python
# Worker node configuration
worker_config = {
    "master_address": "192.168.1.100",
    "master_port": 10051,
    "listen_port": 10052,
    "worker_address": "192.168.1.101",  # Optional: explicit worker address
    "heartbeat_interval": 300,
    "heartbeat_max_retries": 5
}

worker = await initialize_node("worker_001", "worker", worker_config)
```

## Intelligent Agent Allocation

### Community-Based Allocation
The system uses advanced algorithms to optimize agent placement:

- **Relationship Analysis**: Groups agents with strong interactions
- **Type Diversity**: Ensures different agent types can interact efficiently
- **Load Balancing**: Distributes computational load evenly
- **Topology Awareness**: Considers network topology for optimization

### Allocation Strategies
- **Community Detection**: Groups highly connected agents
- **Cross-Type Interaction**: Prioritizes different agent types working together
- **Load Constraints**: Respects maximum load per worker

## Connection Management & Communication

### Sharded Connection Pool
- **Connection Sharding**: Reduces lock contention with hash-based sharding
- **Connection Reuse**: Maintains persistent gRPC connections
- **Automatic Cleanup**: Removes idle connections after timeout
- **Circuit Breaker**: Protects against cascading failures

### Fault Tolerance Features
- **Circuit Breaker Pattern**: Prevents requests to failed services
- **Automatic Reconnection**: Recovers from network failures
- **Heartbeat Monitoring**: Detects and handles worker failures
- **Graceful Degradation**: Continues operation with reduced capacity

```python
# Circuit breaker configuration
circuit_config = {
    "failure_threshold": 5,      # Failures before circuit opens
    "recovery_timeout": 30.0,    # Time before retry attempt
    "half_open_success": 2       # Successes needed to close circuit
}
```

## Distributed Synchronization

### Distributed Locks
Ensures data consistency across the distributed system:

```python
from onesim.distribution.distributed_lock import get_lock

# Acquire distributed lock
async with await get_lock("shared_resource", timeout=30.0) as lock:
    # Critical section - guaranteed exclusive access
    await update_shared_data(key, value)
```

### Lock Features
- **Automatic Timeout**: Prevents deadlocks with configurable timeouts
- **Node Failure Recovery**: Releases locks when nodes become unavailable
- **Mode-Aware**: Uses local locks in single-node mode for efficiency

## Performance Optimizations

### Connection Optimization
- **Pre-connection**: Establishes connections before simulation starts
- **Connection Pooling**: Reuses connections to minimize overhead
- **Batch Processing**: Groups multiple operations for efficiency
- **Asynchronous I/O**: Non-blocking communication patterns


