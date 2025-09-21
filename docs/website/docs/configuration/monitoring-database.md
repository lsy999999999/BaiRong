---
sidebar_position: 5
title: Monitoring and Database
---

# Monitoring and Database 

**Both the monitoring and the database are configured in `config/config.json`.**

## Monitor Configuration

Controls runtime monitoring and visualization during simulations.

```jsonc
"monitor": {
  "enabled": true,             // Whether to enable the monitoring system
  "update_interval": 30,       // Interval (in seconds) to update visualization
  "visualization_defaults": {
    "line": {
      "max_points": 100        // Maximum number of data points for line charts
    },
    "bar": {
      "sort": true             // Whether to sort bars by value
    },
    "pie": {
      "sort": true,            // Whether to sort pie slices
      "merge_threshold": 0.05  // Merge small slices into "Others" if below this ratio
    }
  }
}
```
### Field Definitions
| Field                   | Type               | Default                                                                                 | Description                                              |
|-------------------------|--------------------|-----------------------------------------------------------------------------------------|----------------------------------------------------------|
| `enabled`               | `bool`             | `false`                                                                                 | Enable or disable the monitoring component               |
| `update_interval`       | `int` \| `null`    | `null`                                                                                  | Interval (in seconds) between metric updates             |
| `metrics_path`          | `string` \| `null` | `null`                                                                                  | File path to the directory containing metric definitions |
| `visualization_defaults`| `dict`             | `{ "line": {"max_points": 100}, "bar": {"sort": true}, "pie": {"sort": true, "merge_threshold": 0.05} }` | Default chart visualization settings (line, bar, pie)    |

### Simple Example

**Find `monitor` in `config/config.json`**

```jsonc
"monitor": {
  "enabled": true,
  "update_interval": 15,
  "visualization_defaults": {
    "line": {
      "max_points": 50
    },
    "bar": {
      "sort": false
    },
    "pie": {
      "sort": true,
      "merge_threshold": 0.05
    }
  }
}
```
- Enables real-time monitoring with updates every 15 seconds.
- Line charts will display up to 50 points before dropping older data.
- Bar charts will not auto-sort values.
- Pie charts will sort slices and merge any slice under 5% into “Others.”

## Database Configuration

Manages persistent storage for simulation data, agent states, decisions, and events.

**Find `database` in `config/config.json`**

```jsonc
"database": {
  "enabled": false,            // Whether to enable PostgreSQL database support
  "host": "localhost",         // Database host
  "port": 5432,                // Database port (default PostgreSQL port)
  "dbname": "onesim",          // Name of the PostgreSQL database
  "user": "postgres",          // Database username
  "password": "123456"         // Password for authentication
}
```

### Field Definitions

| Field      | Type     | Default       | Description                       |
|------------|----------|---------------|-----------------------------------|
| `enabled`  | `bool`   | `false`       | Toggle to enable database support |
| `host`     | `string` | `"localhost"` | Database server hostname or IP    |
| `port`     | `int`    | `5432`        | Port number for the database      |
| `dbname`   | `string` | `"onesim"`    | Name of the database              |
| `user`     | `string` | `"postgres"`  | Username for authentication       |
| `password` | `string` | `"postgres"`  | Password for authentication       |

## Simple Example

```jsonc
"database": {
  "enabled": true,
  "host": "db.example.com",
  "port": 5432,
  "dbname": "onesim_prod",
  "user": "onesim_user",
  "password": "secure_pass"
}
```
- Enables PostgreSQL support to persist simulation scenarios, trails, agent states, events, and decisions.
- Connects to database at db.example.com:5432, using the onesim_prod database and onesim_user credentials.
- **Make sure you have PostgreSQL installed and running before enabling this configuration.**