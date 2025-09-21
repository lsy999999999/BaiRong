---

sidebar_position: 2
title: Agent API
---

# Agent API

onesim agent module API

## AgentBase

### Description

Base class for all agents. Handles identity, model loading, and common utilities.

### Constructor

```python
class AgentBase:
    def __init__(
        self,
        sys_prompt: Optional[str] = None,
        model_config_name: str = None,
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter           | Type            | Description                         |
| ------------------- | --------------- | ----------------------------------- |
| sys\_prompt         | `Optional[str]` | Optional system prompt for LLM      |
| model\_config\_name | `str`           | Name of model configuration to load |

### Main Interfaces

* `generate_agent_id() -> str`
  Generate a unique identifier for this agent instance.

* `agent_id` (property / setter)
  Get or set the unique agent ID.

* `__str__() -> str`
  Serialize agent metadata (type, prompt, ID, model info) as JSON.

## GeneralAgent

### Description

Default asynchronous agent implementation with event queue, hooks, and data handling.

### Constructor

```python
class GeneralAgent(AgentBase):
    def __init__(
        self,
        sys_prompt: Optional[str] = None,
        model_config_name: str = None,
        event_bus_queue: asyncio.Queue = None,
        profile: AgentProfile = None,
        memory: MemoryStrategy = None,
        planning: PlanningBase = None,
        relationship_manager: RelationshipManager = None,
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter             | Type                  | Description                         |
| --------------------- | --------------------- | ----------------------------------- |
| sys\_prompt           | `Optional[str]`       | Optional system prompt for LLM      |
| model\_config\_name   | `str`                 | Name of model configuration to load |
| event\_bus\_queue     | `asyncio.Queue`       | Queue for event dispatching         |
| profile               | `AgentProfile`        | Agent profile manager               |
| memory                | `MemoryStrategy`      | Memory strategy implementation      |
| planning              | `PlanningBase`        | Planning strategy handler           |
| relationship\_manager | `RelationshipManager` | Manager for agent relationships     |

### Event Handling Interfaces

* `register_event(event_kind: str, ability_name: str) -> None`
  Register a handler method for incoming events of given kind.

* `add_event(event: Event) -> None`
  Enqueue an event for processing.

* `run() -> None` (async)
  Main loop: dispatch queued events to registered handlers with hooks.

* `register_hook(hook_name: str, hook_function: Callable) -> None`
  Register a hook function for lifecycle events.

### Core Agent Interfaces

* `generate_reaction(instruction: str, observation: str = None) -> dict` (async)
  Call LLM to decide next action; returns parsed JSON.

* `generate_memory(instruction: str, observation: str, reaction: dict) -> str` (async)
  Generate and store a memory entry based on recent interaction.

* `interact(message: str, chat_history: List[Dict[str, Any]] = None) -> dict` (async)
  Process a chat message and return an in-character response.

### Data Access Interfaces

* `get_data(key: str, default: Optional[Any] = None) -> Any` (async)
  Get data from agent profile.

* `update_data(key: str, value: Any) -> bool` (async)
  Update data in agent profile.

* `get_env_data(key: str, default: Optional[Any] = None, parent_event_id: Optional[str] = None) -> Any` (async)
  Get data from the environment.

* `update_env_data(key: str, value: Any, parent_event_id: Optional[str] = None) -> bool` (async)
  Update data in the environment with distributed locking.

* `get_agent_data(agent_id: str, key: str, default: Optional[Any] = None, parent_event_id: Optional[str] = None) -> Any` (async)
  Get data from another agent.

* `update_agent_data(agent_id: str, key: str, value: Any, parent_event_id: Optional[str] = None) -> bool` (async)
  Update data in another agent with distributed locking.

### Relationship Management Interfaces

* `add_relationship(target_id: str, description: str, target_info: Optional[Dict] = None) -> None`
  Add a new relationship with another agent.

* `remove_relationship(target_id: str) -> None`
  Remove a relationship with another agent.

* `update_relationship(target_id: str, description: str) -> None`
  Update an existing relationship description.

* `get_relationship(target_id: str) -> Optional[Relationship]`
  Get a specific relationship by target ID.

* `get_all_relationships() -> List[Relationship]`
  Get all relationships for this agent.

### Profile and Memory Interfaces

* `profile_id` (property)
  Get the agent's profile ID.

* `get_profile_str(include_private: bool = None) -> str`
  Get profile as a formatted string.

* `get_profile(include_private: bool = None) -> dict`
  Get profile as a dictionary.

* `get_memory() -> List` (async)
  Get all memory items.

* `add_memory(memory: str) -> None` (async)
  Add a memory item to the agent's memory.

### Utility Interfaces

* `is_stopped() -> bool`
  Check if the agent has been stopped.

* `set_env(env) -> None`
  Set the simulation environment associated with this agent.

* `create_context() -> AgentContext`
  Create an agent context object.

## CodeAgent

### Description

Agent specialized in generating and refining Python code for multi-agent systems.

### Constructor

```python
class CodeAgent(AgentBase):
    def __init__(
        self,
        model_config_name: str,
        sys_prompt: str = '',
        **kwargs: Any,
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter           | Type  | Description                                    |
| ------------------- | ----- | ---------------------------------------------- |
| model\_config\_name | `str` | Name of model configuration to load            |
| sys\_prompt         | `str` | System prompt for code generation              |
| \*\*kwargs          | `Any` | Additional parameters for agent initialization |

### Main Interfaces

* `generate_code(description: str, actions: Dict[str, List[Dict]], events: Dict[int, Dict], env_path: str, max_iterations: int = 3) -> Dict[str, Any]`
  Orchestrate phased code generation, validation, and fixes.

* `generate_code_phased(description: str, actions: Dict[str, List[Dict]], events: Dict[int, Dict], env_path: str, status_dict: Dict[str, Any], max_iterations: int = 3) -> None`
  Multi-phase code generation with status tracking.

* `generate_initial_code(description: str, actions: Dict[str, List[Dict]], events: Dict[int, Dict], env_path: str, status_dict: Dict[str, Any]) -> Tuple[Dict[str, str], str]`
  Produce initial agent and event class code blocks.

* `check_code(agent_code_dict: Dict[str, str], event_code: str, description: str, actions: Dict[str, List[Dict]], events: Dict[int, Dict]) -> Dict[str, List[Dict[str, Any]]>`
  Validate generated code via LLM; return per-class issues.

* `fix_code(agent_code_dict: Dict[str, str], event_code: str, verification_results: Dict[str, List[Dict[str, Any]]], actions: Dict[str, List[Dict]], events: Dict[int, Dict]) -> Tuple[Dict[str, str], str]`
  Iteratively correct code based on validation feedback.

### Code Generation Interfaces

* `generate_event_class(event_info: dict) -> str`
  Generate Python code for an Event subclass.

* `generate_handler_code(description: str, agent_type: str, action_info: Dict, incoming_events: List[Dict], outgoing_events: List[Dict], event_data_info: List[Dict]) -> str`
  Generate handler method code for an action.

* `generate_simenv_subclass_code(description: str, start_event_code: str) -> str`
  Generate SimEnv subclass code with `_create_start_event` method.

* `generate_event_code() -> str`
  Generate complete event code with imports and classes.

### Utility Interfaces

* `initialize_agent_class(agent_type: str, action_list: List[dict], events: Dict[int, Dict]) -> str`
  Initialize agent class code with event registrations.

* `build_action_graph(actions: Dict[str, List[Dict]], events: Dict[int, Dict]) -> Dict[Tuple[str, str], List[Tuple[str, str]]]`
  Build action topology graph from workflow definitions.

* `restructure_code(agent_code_dict: Dict[str, str], event_code: str, actions: Dict[str, List[Dict]], events: Dict[int, Dict]) -> Dict`
  Restructure code into ID-mapped format.

* `save_code_to_files(agent_code_dict: Dict[str, str], event_code: str, env_path: str, actions: Dict[str, List[Dict]], events: Dict[int, Dict]) -> None`
  Save generated code to filesystem.

## ODDAgent

### Description

Agent for extracting and updating ODD (Overview, Design, Details) protocols from natural language.

### Constructor

```python
class ODDAgent(AgentBase):
    def __init__(
        self,
        model_config_name: str,
        sys_prompt: str = '',
        **kwargs: Any,
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter           | Type  | Description                                    |
| ------------------- | ----- | ---------------------------------------------- |
| model\_config\_name | `str` | Name of model configuration to load            |
| sys\_prompt         | `str` | System prompt for ODD processing               |
| \*\*kwargs          | `Any` | Additional parameters for agent initialization |

### Main Interfaces

* `odd_to_markdown(scene_info: Dict) -> str` (static)
  Convert scene\_info ODD protocol into Markdown.

* `markdown_to_scene_info(markdown: str) -> Dict`
  Parse Markdown back into scene\_info structure.

* `update_scene_info(user_input: str) -> dict`
  LLM-driven update of ODD protocol; returns updated info and status.

* `generate_clarification_questions() -> dict`
  Identify missing info and propose clarification questions.

* `process_user_input(user_input: str) -> Dict[str, Any]`
  Wrapper to update protocol and obtain clarification question.

* `get_final_odd_protocol() -> Dict`
  Retrieve the ODD protocol part of scene\_info.

### Persistence Interfaces

* `save_scene_info(env_path: str) -> None`
  Save the scene\_info (including ODD protocol) to `scene_info.json` file.

* `load_scene_info(env_path: str) -> bool`
  Load the scene\_info (including ODD protocol) from `scene_info.json` file.

* `reset() -> None`
  Reset the scene\_info to its initial state.

## ProfileAgent

### Description

Simple dialogue agent for extracting agent types, portraits, and profile schemas.

### Constructor

```python
class ProfileAgent(AgentBase):
    def __init__(
        self,
        model_config_name: str,
        sys_prompt: str = '',
        **kwargs: Any,
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter           | Type  | Description                                    |
| ------------------- | ----- | ---------------------------------------------- |
| model\_config\_name | `str` | Name of model configuration to load            |
| sys\_prompt         | `str` | System prompt for profile extraction           |
| \*\*kwargs          | `Any` | Additional parameters for agent initialization |

### Main Interfaces

* `assign_agent_portraits(agent_types_dict: Dict[str, str]) -> Dict[str, int]`
  Map each agent type to a portrait ID (1–5).

* `generate_agent_types(description: str) -> Dict[str, str]`
  Infer agent types from a description.

* `merge_relationships(relationships: List[Dict]) -> List[Dict]`
  Deduplicate and merge reciprocal relationships.

* `generate_relationship_schema(agent_types: list, actions: dict, events: dict) -> List[Dict]`
  Generate relationship schema based on events graph.

* `generate_profile_schema(scenario_description: str, agent_name: str, agent_data_model) -> Dict`
  Generate a JSON schema for an agent profile.

* `generate_env_data(env_data_schema: dict, description: str) -> Dict`
  Transform environment data schema into realistic JSON with contextually appropriate values.

## MetricAgent

### Description

Agent for generating and validating monitoring metrics for multi-agent systems.

### Constructor

```python
class MetricAgent(AgentBase):
    def __init__(
        self,
        model_config_name: str,
        sys_prompt: str = '',
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter           | Type  | Description                         |
| ------------------- | ----- | ----------------------------------- |
| model\_config\_name | `str` | Name of model configuration to load |
| sys\_prompt         | `str` | System prompt for metric generation |

### Main Interfaces

* `generate_metrics(scenario_description: str, agent_types: List[str], system_data_model: Dict = None, num_metrics: int = 3) -> List[Dict]`
  Produce metric definitions via LLM.

* `validate_metrics(metrics: List[Dict], system_data_model: Dict = None) -> List[Dict]`
  Filter and correct metrics based on data model.

* `generate_calculation_function(metric_def: Dict, system_data_model: Dict = None) -> str`
  LLM-driven code for computing a metric.

* `generate_metrics_module(metrics: List[Dict], output_dir: str, system_data_model: Dict = None) -> str`
  Write a Python module containing all metric functions.

* `generate_metrics_code_file(metrics: List[Dict], output_dir: str) -> Dict[str, str]`
  Generate individual metric calculation code files.

* `format_metrics_for_export(metrics: List[Dict]) -> List[Dict]`
  Format generated metrics for export to `scene_info.json`.

## WorkflowAgent

### Description

Agent for extracting, validating, and visualizing multi-agent workflow topologies.

### Constructor

```python
class WorkflowAgent(AgentBase):
    def __init__(
        self,
        model_config_name: str,
        sys_prompt: str = '',
        **kwargs: Any,
    ) -> None:
        ...
```

### Constructor Arguments

| Parameter           | Type  | Description                                    |
| ------------------- | ----- | ---------------------------------------------- |
| model\_config\_name | `str` | Name of model configuration to load            |
| sys\_prompt         | `str` | System prompt for workflow extraction          |
| \*\*kwargs          | `Any` | Additional parameters for agent initialization |

### Main Interfaces

* `extract_workflow(description: str, agent_types: list, last_workflow: str = None, issues: Optional[list] = None, suggestions: Optional[list] = None) -> dict`
  LLM-based extraction of workflow structure.

* `validate_workflow_structural(data: dict) -> Tuple[bool, List[str], List[str]]`
  Structural checks: connectivity, reachability, naming.

* `validate_workflow_extraction(description: str, agent_types: list, extracted_info: dict) -> dict`
  Validate extracted information against the description.

* `generate_workflow(description: str, agent_types: list) -> Tuple[Dict, Dict, Dict, nx.DiGraph]`
  End-to-end extraction, validation, and graph build.

* `build_topology_graph() -> nx.DiGraph`
  Construct directed graph of actions and events.

* `visualize_interactive_graph(G: nx.DiGraph, filename: str = "workflow.html") -> None`
  Generate interactive HTML visualization of the workflow.

* `extract_event_data_requirements(description: str, events: dict) -> dict`
  Extract data field requirements for each event.

* `enhance_actions_with_requirements(description: str, agent_types: list, actions: dict, events: dict) -> dict`
  Generate enhanced action information including requirements.

* `derive_data_model_from_actions(actions: dict) -> dict`
  Derive environment and agent data models from action requirements.

* `get_incoming_event(G: nx.DiGraph, action_id: int) -> Optional[Event]`
  Find incoming event(s) for an action.
