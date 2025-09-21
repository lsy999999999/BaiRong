---
sidebar_position: 4
title: Distributed Configuration
---

# Distributed Mode Configuration

**YuLan-OneSim supports distributed multi-node simulation via a configurable `distribution` section in `config/config.json`.**

This section allows users to define whether the simulation runs in standalone (`single`) mode or across master/worker nodes.

Example block from `config/config.json`:
```jsonc
"distribution": {
  "enabled": false,               // Enable/disable distributed mode
  "mode": "single",               // Node mode: "single", "master", or "worker"
  "node_id": "1",                 // Unique identifier for the node
  "master_address": "localhost",  // Address of the master node (used by workers)
  "master_port": 10051            // Port used by the master for coordination
}
```
## Field Definitions

| Field            | Type    | Default     | Description                                                      |
|------------------|---------|-------------|------------------------------------------------------------------|
| `enabled`          | `bool`    | `false`      | Whether to enable distributed mode                               |
| `mode`             | `string`  | `single`    | Node mode: "single", "master", or "worker"                    |
| `node_id`          | `string`  | None    | Unique identifier for the node                                   |
| `master_address`   | `string`  | `localhost` | Address of the master node (used by workers)                     |
| `master_port`      | `int`     | `10051`       | Port used by the master for coordination                         |
| `worker_address`   | `string` | None        | (Optional) Listening address for worker node                     |
| `worker_port`      | `int`     | `0`           | (Optional) Listening port for worker node, 0 means auto-assign   |
| `expected_workers` | `int`     | `1`           | (Optional, master only) Expected number of worker nodes          |


## Simple sample

### 1. Open `config/config.json` and locate the `distribution` block.

### 2. Change `enabled` to `true` to enable distributed mode.

### 3. Decide on the current node’s role.

Decide the role of the current node:

#### Master node:

```jsonc
"distribution": {
  "enabled": true,
  "mode": "master",
  "node_id": "1",
  "master_address": "localhost",
  "master_port": 10051,
  "worker_address": null,
  "worker_port": 0,
  "expected_workers": 2
}
```

#### Worker node:

```jsonc
"distribution": {
  "enabled": true,
  "mode": "worker",
  "node_id": "worker_1", #worker_2 for another one
  "master_address": "localhost",
  "master_port": 10051,
  "worker_address": null,
  "worker_port": 0,
  "expected_workers": 2
}
```

- Optionally, you can specify the `worker_address` and `worker_port` to set where the worker listens; if you leave them empty, the system will assign them automatically.
- Worker nodes should set mode to "worker" and configure master_address/master_port to point to the master node.
- Arguments in Cli commands (including scripts) would override distribution settings.
- Content placeholder - Usage of Worker node