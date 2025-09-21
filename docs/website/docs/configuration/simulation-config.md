---
sidebar_position: 2
title: Simulation Configuration
---

# Simulation Configuration

**Simulation configuration is configured in `config/config.json`.**

The simulation configuration file controls general simulation parameters:

```jsonc
{
  "simulator": {
    "environment": {
      "name": "labor_market_matching_process",  // Environment scenario to simulate
      "mode": "round",                          // Simulation execution mode
      "max_steps": 3,                           // Maximum simulation steps
      "interval": 60.0,                         // Interval between simulation steps
      "export_training_data": false,            // Whether to export training data
      "export_event_data": false                // Whether to export event data
    }
  },
  "agent": {
    "profile": {
      "Employer": {
        "count": 5,                             // Number of agents
        "profile_path": "Employer.json",        // Path to the profile data file under the profile/data folder
        "schema_path": "Employer.json"          // Path to the profile schema file under the profile/schema folder
      },
      "JobSeeker": {
        "count": 5,
        "profile_path": "JobSeeker.json",
        "schema_path": "JobSeeker.json"
      },
      "RecruitmentChannel": {
        "count": 5,
        "profile_path": "RecruitmentChannel.json",
        "schema_path": "RecruitmentChannel.json"
      }
    },
    "planning": "COTPlanning",                  // Agent planning algorithm
    "memory": {
      "strategy": "ShortLongStrategy",          // Memory management strategy
      "storages": {
        "short_term_storage": {
          "class": "ListMemoryStorage",         // Short-term memory storage type
          "capacity": 100                       // Maximum memory capacity
        },
        "long_term_storage": {
          "class": "VectorMemoryStorage",       // Long-term memory storage type
          "capacity": 100,
          "model_config_name": "openai_embedding-bert"  // Embedding model for memory
        }
      },
      "metric_weights": {
        "recency": 0.7                          // Weight for recency in memory retrieval
      }
    }
  },
  "database": {
    "enabled": false,                           // Enable/disable database
    "host": "localhost",                        // Database host
    "port": 5432,                               // Database port
    "dbname": "onesim"                          // Database name
  },
  "distribution": {
    "enabled": false,                           // Enable/disable distributed mode
    "mode": "single",                           // Running mode: single/distributed
    "node_id": "1"                              // Node identifier for distributed mode
  },
  "monitor": {
    "enabled": true,                            // Enable/disable monitoring
    "update_interval": 30                       // Monitor update interval
  }
}
```

## Field Definitions

| Field               | Type    | Default   | Description                                                   |
|---------------------|---------|-----------|---------------------------------------------------------------|
| `mode`              | `string`  | `"tick"`  | Simulation mode: `"tick"` (timed) or `"round"` (round-based)  |
| `max_steps`         | `int`     | `1`       | Maximum number of steps/rounds                                |
| `interval`          | `float`   | `60.0`    | Time interval (seconds) between steps in timed mode           |
| `bus_idle_timeout`  | `float`   | `120.0`   | Time (seconds) to consider the event bus as idle              |
| `export_training_data` | `bool` | `false`   | Whether to export training data                               |
| `export_event_data` | `bool`    | `false`   | Whether to export event data                                  |
| `additional_config` | `dict`    | `{}`      | Additional custom configuration                               |
| `collection_interval` | `int`   | `30`      | Interval (seconds) for periodic data/metrics collection       |

## Simple Example

**Find `database` in `config/config.json`**

Then replace this with:

```jsonc
{
  "simulator": {
    "environment": {
      "name": "labor_market_matching_process",
      "mode": "round",
      "max_steps": 5,
      "interval": 30.0,
      "bus_idle_timeout": 60.0,
      "export_training_data": true,
      "export_event_data": false,
      "additional_config": {
        "export_event_flow": true,
        "event_flow_output_file": "flow.json"
      },
      "collection_interval": 15
    }
  }
}

```
- This example runs the labor_market_matching_process in round mode for 5 rounds.
- Steps advance every 30 s, and the event bus is considered idle after 60 s.
- Training data is exported, but event data is not.
- An event flow JSON will be written to flow.json.
- Metrics are collected every 15 s.