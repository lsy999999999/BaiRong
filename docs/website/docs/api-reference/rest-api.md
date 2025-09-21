---
sidebar_position: 4
title: REST API
---

# REST API

## Simulation
Handles simulation environment initialization, control, and management.

### POST `/simulation/initialize`
**Description:** Initialize simulation environment and related components.

**Parameters:**
- `env_name` _str_: Environment name
- `model_name` _Optional[str]_: Optional model name (defaults to config)

**Response:**
```json
{
  "env_name": "string",
  "config_applied": true,
  "agents": [...],
  "agent_count": 0,
  "is_distributed": false,
  "trail_id": "string",
  "components_initialized": {},
  "workflow": {},
  "ready_for_simulation": true
}
```

### POST `/simulation/get_agents`

**Description:** Get agent information for an environment.

**Parameters:**

* `env_name` *str*: Environment name
* `agent_type` *Optional\[str]*: Filter by agent type

**Response:** `GetAgentsResponse`

### POST `/simulation/start`

**Description:** Start a simulation.

**Parameters:**

* `env_name` *str*: Environment name to start

**Response:** `StartSimulationResponse`

### POST `/simulation/stop`

**Description:** Stop a running simulation.

**Parameters:**

* `env_name` *str*: Environment name to stop

**Response:** `StopSimulationResponse`

### POST `/simulation/pause`

**Description:** Pause a running simulation.

**Parameters:**

* `env_name` *str*: Environment name to pause

**Response:** `PauseSimulationResponse`

### POST `/simulation/resume`

**Description:** Resume a paused simulation.

**Parameters:**

* `env_name` *str*: Environment name to resume

**Response:** `ResumeSimulationResponse`

### POST `/simulation/broadcast`

**Description:** Broadcast a message to all agents in the environment.

**Parameters:**

* `env_name` *str*: Environment name
* `message` *str*: Message to broadcast

**Response:**

```json
{
  "success": true,
  "message": "string",
  "broadcast_count": 0
}
```

### GET `/simulation/{env_name}/available_metrics`

**Description:** Get available metrics for an environment.

**Response:**

```json
{
  "agent_metrics": ["activity_level", "social_connections", "resource_usage"],
  "env_metrics": ["population", "resource_level", "social_stability"]
}
```

### GET `/simulation/{env_name}/events`

**Description:** Get simulation events.

**Response:** `GetEventsResponse`

### GET `/simulation/list_environments`

**Description:** List all initialized environments.

**Response:**

```json
{
  "success": true,
  "environments": ["env1", "env2"]
}
```

### GET `/simulation/registry/{env_name}`

**Description:** Get simulation registry information.

**Response:**

```json
{
  "success": true,
  "message": "string",
  "registry": {}
}
```

### WebSocket `/simulation/ws/{env_name}`

WebSocket endpoint for real-time simulation updates.

---

## Pipeline

Manages the pipeline for creating simulation scenarios including agent types, workflows, and code generation.

### POST `/pipeline/initialize`

**Description:** Initialize the pipeline for a new environment.

**Parameters:**

* `env_name` *str*: Environment name
* `description` *str*: Environment description
* `model_name` *Optional\[str]*: Model to use
* `category` *Optional\[str]*: Model category

**Response:**

```json
{
  "env_name": "string",
  "env_path": "string",
  "message": "Pipeline initialization successful"
}
```

### POST `/pipeline/generate_agent_types`

**Description:** Generate agent types based on the environment description.

**Parameters:**

* `env_name` *str*: Environment name

**Response:** `AgentTypesResponse`

### POST `/pipeline/update_agent_types`

**Description:** Update agent types with user modifications.

**Parameters:**

* `env_name` *str*: Environment name
* `agent_types` *Dict\[str, str]*: Updated agent types
* `portrait` *Optional\[Dict\[str, int]]*: Agent portrait assignments

**Response:** `AgentTypesResponse`

### POST `/pipeline/generate_workflow`

**Description:** Generate workflow (actions and events) for the environment.

**Parameters:**

* `env_name` *str*: Environment name

**Response:** `WorkflowResponse`

### POST `/pipeline/update_workflow`

**Description:** Update workflow with user modifications.

**Parameters:**

* `env_name` *str*: Environment name
* `actions` *Dict\[str, Any]*: Updated actions
* `events` *Dict\[str, Any]*: Updated events

**Response:**

```json
{
  "message": "Workflow successfully updated"
}
```

### POST `/pipeline/generate_code`

**Description:** Start code generation process.

**Parameters:**

* `env_name` *str*: Environment name

**Response:**

```json
{
  "message": "Code generation started",
  "env_name": "string"
}
```

### GET `/pipeline/code_generation_status`

**Description:** Get current status of code generation.

**Parameters:**

* `env_name` *str*: Environment name

**Response:** `CodeGenerationStatus`

### GET `/pipeline/get_code`

**Description:** Get generated code including mapping between actions/events and their code.

**Parameters:**

* `env_name` *str*: Environment name

**Response:**

```json
{
  "actions": {},
  "events": {}
}
```

### POST `/pipeline/update_code`

**Description:** Update generated code.

**Parameters:**

* `env_name` *str*: Environment name
* `actions` *Dict\[str, Any]*: Updated action code
* `events` *Dict\[str, Any]*: Updated event code

**Response:**

```json
{
  "message": "Code updated successfully",
  "updated_agents": "string",
  "events_updated": "Yes/No"
}
```

### GET `/pipeline/profile_schemas`

**Description:** Get agent profile schemas.

**Parameters:**

* `env_name` *str*: Environment name

**Response:**

```json
{
  "schemas": {},
  "profile_counts": {}
}
```

### POST `/pipeline/profile_schema`

**Description:** Save agent profile schema.

**Parameters:**

* `env_name` *str*: Environment name
* `agent_schemas` *Dict\[str, Any]*: Agent schemas to save

**Response:** `ProfileSchemaResponse`

### POST `/pipeline/generate_profiles`

**Description:** Generate agent profile data.

**Parameters:**

* `env_name` *str*: Environment name
* `agent_types` *Dict\[str, int]*: Agent type counts
* `model_name` *Optional\[str]*: Model to use
* `category` *Optional\[str]*: Model category

**Response:** `ProfileGenerationResponse`

### GET `/pipeline/tips`

**Description:** Get helpful tips about the simulation system.

**Response:** `TipsResponse`

---

## ODD

Handles ODD (Overview, Design concepts, Details) protocol generation and dialogue.

### POST `/odd/start` 

**Description:** Start a new ODD conversation with an initial prompt.

**Parameters:**

* `prompt` *str*: Initial user prompt
* `model_name` *Optional\[str]*: Model to use
* `category` *Optional\[str]*: Model category

**Response:** `ODDResponse`

### POST `/odd/chat`

**Description:** Process messages in the ODD conversation.

**Parameters:**

* `session_id` *str*: Session identifier
* `message` *str*: User message

**Response:** `ODDResponse`

### POST `/odd/confirm_scene`

**Description:** Confirm scene creation with the provided scene name.

**Parameters:**

* `session_id` *str*: Session identifier
* `scene_name` *str*: Scene name to create

**Response:** `SceneConfirmationResponse`

### GET `/odd/history/{session_id}`

**Description:** Get the conversation history for an ODD session.

**Parameters:**

* `env_name` *Optional\[str]*: Environment name

**Response:** `HistoryResponse`

### GET `/odd/protocol/{session_id}`

**Description:** Get the ODD protocol.

**Parameters:**

* `env_name` *Optional\[str]*:\* Environment name

**Response:** `ProtocolResponse`

### POST `/odd/check_scene_name`

**Description:** Check if a scene name already exists.

**Parameters:**

* `scene_name` *str*:\* Scene name to check

**Response:** `SceneNameCheckResponse`

### GET `/odd/domains`

**Description:** Get list of all domains.

**Response:** `List[str]`

### GET `/odd/examples`

**Description:** Get example descriptions for social simulation scenarios.

**Response:** `List[str]`

---

## Monitor

Provides real-time monitoring of simulation metrics and performance.

### GET `/monitor/{env_name}/metrics`

**Description:** Get all available metrics for an environment.

**Response:**

```json
{
  "success": true,
  "metrics": {}
}
```

### GET `/monitor/{env_name}/metrics/{metric_name}`

**Description:** Get a specific metric for an environment.

**Response:**

```json
{
  "success": true,
  "metric": {}
}
```

### POST `/monitor/{env_name}/metrics/{metric_name}/update`

**Description:** Manually trigger an update for a specific metric.

**Response:**

```json
{
  "success": true,
  "message": "Metric updated successfully"
}
```

### WebSocket `/monitor/ws/{env_name}`

WebSocket endpoint for real-time metric updates.

---

## Feedback

Manages decision data feedback, rating, and refinement for simulation improvement.

### GET `/feedback/decisions`

**Description:** Get decision data from the environment.

**Parameters:**

* `env_name` *str*:\* Environment name

**Response:** `FeedbackResponse`

### POST `/feedback/update`

**Description:** Update decision data.

**Parameters:**

* `env_name` *str*:\* Environment name
* `updated_data` *List\[Dict\[str, Any]]*:\* Updated decision data

**Response:** `FeedbackResponse`

### POST `/feedback/rate`

**Description:** Rate decision data quality.

**Parameters:**

* `env_name` *str*:\* Environment name
* `selected_data` *List\[Dict\[str, Any]]*:\* Data to rate
* `model_name` *str*:\* Model to use for rating

**Response:** `FeedbackResponse`

### POST `/feedback/refine`

**Description:** Refine decision data based on quality analysis.

**Parameters:**

* `env_name` *str*:\* Environment name
* `selected_data` *List\[Dict\[str, Any]]*:\* Data to refine
* `model_name` *str*:\* Model to use for refinement

**Response:** `FeedbackResponse`

### POST `/feedback/save`

**Description:** Save decision data to file.

**Parameters:**

* `env_name` *str*:\* Environment name

**Response:** `SaveResponse`

---

## Domains

Provides access to available domains and existing scenes.

### GET `/domains`

**Description:** Get all available domains.

**Response:** `List[str]`

### GET `/scenes`

**Description:** Get scenes grouped by domain.

**Response:**

```json
{
  "Economics": [...],
  "Sociology": [...],
  ...
}
```

### GET `/scenes/{domain}`

**Description:** Get scenes for a specific domain.

**Response:** `List[Dict[str, str]]`

### GET `/scene/{scene_name}`

**Description:** Get detailed information for a specific scene.

**Response:**

```json
{
  "scene_name": "string",
  "description": "string",
  "odd_protocol": {},
  "actions": {},
  "events": {},
  ...
}
```

### POST `/check_scene_name`

**Description:** Check if a scene name already exists.

**Parameters:**

* `scene_name` *str*:\* Scene name to check

**Response:** `SceneNameCheckResponse`

---

## Config

Manages system configuration, model settings, and environment options.

### GET `/config/options`

**Description:** Get configuration options for a scene.

**Parameters:**

* `env_name` *str*:\* Environment name

**Response:** `ConfigOptions`

### POST `/config/save`

**Description:** Save configuration for a scene.

**Parameters:**

* `env_name` *str*:\* Environment name
* `config` *Dict\[str, Any]*:\* Configuration to save

**Response:** `SaveConfigResponse`

### GET `/config/get`

**Description:** Get configuration for a specific environment.

**Parameters:**

* `env_name` *str*:\* Environment name

**Response:** `Dict[str, Any]`

### GET `/config/models`

**Description:** Get available models by category.

**Parameters:**

* `category` *Optional\[str]*:\* Filter by category ('chat' or 'embedding')

**Response:**

```json
{
  "models": {
    "chat": [...],
    "embedding": [...]
  }
}
```

---

## Agent

Handles direct interaction with agents including chat and profile updates.

### POST `/agent/chat`

**Description:** Chat with a specific agent.

**Parameters:**

* `env_name` *str*:\* Environment name
* `agent_id` *str*:\* Agent identifier
* `message` *str*:\* Message to send

**Response:** `AgentChatResponse`

### GET `/agent/history/{env_name}/{agent_id}`

**Description:** Get chat history with a specific agent.

**Response:** `AgentChatHistoryResponse`

### POST `/agent/update_profile`

**Description:** Update an agent's profile data.

**Parameters:**

* `env_name` *str*:\* Environment name
* `agent_id` *str*:\* Agent identifier
* `profile_data` *Dict\[str, Any]*:\* Profile fields to update

**Response:** `UpdateAgentProfileResponse`

```
```


*Documentation for YuLan-OneSim - A Next Generation Social Simulator with LLMs*
