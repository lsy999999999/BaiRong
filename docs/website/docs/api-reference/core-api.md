---

sidebar\_position: 1
title: Core API
---

# Core API Reference for `onesim` Models Package

## Message

Represents a chat message for model interaction, supporting different roles and content types.

### Constructor

```python
class Message:
    def __init__(
        self,
        name: Optional[str] = None,
        content: Any = None,
        role: str = "user",
        images: Optional[List[str]] = None,
        **kwargs
    )
```

| Parameter  | Type                  | Description                                              |
| ---------- | --------------------- | -------------------------------------------------------- |
| `name`     | `Optional[str]`       | Optional name of the sender                              |
| `content`  | `Any`                 | Main content of the message                              |
| `role`     | `str`                 | Role of the sender (`"system"`, `"user"`, `"assistant"`) |
| `images`   | `Optional[List[str]]` | List of image file paths to include                      |
| `**kwargs` | `Any`                 | Additional metadata                                      |

### Methods

* `to_dict(self) -> Dict[str, Any]`
  Convert the message to a dictionary representation.
* `@classmethod from_dict(cls, data: Dict[str, Any]) -> Message`
  Create a message instance from a dictionary.

#### Factory Functions

* `SystemMessage(content: Any, **kwargs) -> Message`
  Create a system message.
* `UserMessage(content: Any, **kwargs) -> Message`
  Create a user message.
* `AssistantMessage(content: Any, **kwargs) -> Message`
  Create an assistant message.

---

## ModelAdapterBase

Abstract base class for all model adapters, defining the interface for model interactions.

### Constructor

```python
class ModelAdapterBase(ABC):
    def __init__(
        self,
        config_name: str,
        model_name: str = None,
        **kwargs
    )
```

| Parameter     | Type  | Description                                     |
| ------------- | ----- | ----------------------------------------------- |
| `config_name` | `str` | Identifier for this model configuration         |
| `model_name`  | `str` | Specific model name (defaults to `config_name`) |
| `**kwargs`    | `Any` | Additional model-specific parameters            |

### Methods

* `__call__(self, *args, **kwargs) -> ModelResponse`
  Process inputs and generate a model response synchronously.
* `async def acall(self, *args, **kwargs) -> ModelResponse`
  Process inputs and generate a model response asynchronously.
* `@abstractmethod format(self, *args: Union[Message, Sequence[Message]]) -> Any`
  Format input messages into the structure expected by the model.
* `@staticmethod format_for_common_chat_models(*args: Union[Message, Sequence[Message]]) -> List[Dict[str, str]]`
  Format messages for standard chat models following the common format.
* `get_info(self) -> Dict[str, Any]`
  Get information about this model instance.
* `@abstractmethod list_models(self) -> List[str]`
  Return the list of available model IDs from this adapter's backend.
* `@abstractmethod async def alist_models(self) -> List[str]`
  Asynchronously return the list of available model IDs.

---

## LoadBalancer

Load balancer for distributing requests across multiple model instances. Inherits from `ModelAdapterBase`.

### Constructor

```python
class LoadBalancer(ModelAdapterBase):
    def __init__(
        self,
        config_name: str = "chat_load_balancer",
        models: List[Union[str, dict, ModelAdapterBase]] = None,
        strategy: str = "round_robin",
        category: str = "chat",
        provider: str = None,
        model_type: str = None,
        model_name: str = None,
        max_retries: int = 3,
        **kwargs
    )
```

| Parameter     | Type                                       | Description                                             |
| ------------- | ------------------------------------------ | ------------------------------------------------------- |
| `config_name` | `str`                                      | Name for this load balancer configuration               |
| `models`      | `List[Union[str, dict, ModelAdapterBase]]` | Models to balance between                               |
| `strategy`    | `str`                                      | Load balancing strategy (`"round_robin"` or `"random"`) |
| `category`    | `str`                                      | Model category (`"chat"` or `"embedding"`)              |
| `provider`    | `Optional[str]`                            | Provider filter (e.g., `"openai"`)                      |
| `model_type`  | `Optional[str]`                            | Alias for category                                      |
| `model_name`  | `Optional[str]`                            | Specific model name to balance across providers         |
| `max_retries` | `int`                                      | Maximum retry attempts on model failure                 |
| `**kwargs`    | `Any`                                      | Additional parameters                                   |

### Methods

* `initialize_models(self, model_manager=None)`
  Initialize model instances from configuration names.

*Inherits **`__call__`**, **`acall`**, **`format`**, and **`get_info`** from **`ModelAdapterBase`**.*

---

## ModelResponse

Encapsulates data returned by a model, providing a standardized response structure.

### Constructor

```python
class ModelResponse:
    def __init__(
        self,
        text: str = None,
        embedding: Sequence = None,
        raw: Any = None,
        parsed: Any = None,
        stream: Optional[Generator[str, None, None]] = None,
        usage: Optional[Dict[str, Any]] = None,
        model_info: Optional[Dict[str, Any]] = None,
    )
```

| Parameter    | Type                                   | Description                       |
| ------------ | -------------------------------------- | --------------------------------- |
| `text`       | `Optional[str]`                        | Text response from the model      |
| `embedding`  | `Optional[Sequence]`                   | Vector embeddings from the model  |
| `raw`        | `Any`                                  | Raw unparsed response             |
| `parsed`     | `Any`                                  | Parsed response data              |
| `stream`     | `Optional[Generator[str, None, None]]` | Generator for streaming responses |
| `usage`      | `Optional[Dict[str, Any]]`             | Token usage information           |
| `model_info` | `Optional[Dict[str, Any]]`             | Model metadata                    |

### Properties

* `@property text`
  Get the text response, processing the stream if needed.
* `@property stream`
  Get the stream generator with status information.
* `@property is_stream_exhausted`
  Check if the stream has been fully processed.

---

## ModelManager

Singleton manager for model configurations and instances.

### Methods

* `@classmethod get_instance(cls) -> ModelManager`
  Get or create the singleton instance.
* `initialize(self, config_path: Optional[Union[str, Dict, List]] = None)`
  Initialize the manager with configurations.
* `load_model_configs(self, configs: Union[str, Dict, List], clear_existing: bool = False)`
  Load model configurations from various sources.
* `get_model(self, config_name: Optional[str] = None, model_type: Optional[str] = None, model_name: Optional[str] = None) -> ModelAdapterBase`
  Retrieve a model adapter by configuration name or selection criteria.
* `get_config(self, config_name: str) -> Optional[Dict[str, Any]]`
  Get a model configuration by name.
* `clear_configs(self)`
  Clear all loaded model configurations.
* `get_configs_by_type(self, model_type: str) -> List[Dict[str, Any]]`
  Get all configurations of a specific type.
* `get_model_names_by_type(self, model_type: str) -> List[str]`
  Get all configuration names of a specific type.
* `configure_load_balancer(self, model_configs=None, strategy: str = "round_robin", config_name: str = "chat_load_balancer", model_type: str = "chat", model_name: str = None)`
  Configure a load balancer for multiple models.
