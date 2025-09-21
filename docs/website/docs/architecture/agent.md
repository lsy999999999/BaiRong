# Agent System

YuLan-OneSim implements a sophisticated multi-agent system where each agent is an autonomous entity powered by LLMs. The agent system is built on a modular architecture with four core components working together to create intelligent, reactive behaviors.

## Agent Architecture Overview

Each agent in YuLan-OneSim consists of four fundamental modules:

- **Profile Module**: Defines agent identity, attributes, and characteristics
- **Memory Module**: Manages memory with retrieval and storage
- **Planning Module**: Implements decision-making strategies and goal planning
- **Action Module**: Executes planned behaviors and triggers simulation events


## Profile Module

The Profile module defines agent identity and characteristics through a structured attribute system.

### Attribute Structure
```json
{
  "public_attributes": {
    "name": "Alice Johnson",
    "age": 28,
    "occupation": "Data Scientist",
    "location": "San Francisco"
  },
  "private_attributes": {
    "personality": "analytical, introverted",
    "risk_tolerance": "moderate",
    "political_leaning": "liberal",
    "income_level": "high"
  }
}
```

### Key Features
- **Public Attributes**: Visible to other agents for social interaction
- **Private Attributes**: Hidden characteristics that influence decision-making
- **Dynamic Evolution**: Attributes can change based on experiences and interactions
- **Relationship Tracking**: Maintains connections and relationship states with other agents

## Memory Module

The Memory module implements a sophisticated memory management system that mimics human memory processes.

### Memory Architecture
```json
{
  "strategy": "ShortLongStrategy",
  "storages": {
      "short_term_storage": {
          "class": "ListMemoryStorage",
          "capacity": 100
      },
      "long_term_storage": {
          "class": "VectorMemoryStorage",
          "capacity": 100,
          "model_config_name": "openai_embedding-bert"
      }
  },
  "operations": {
      "add": {
          "class": "AddMemoryOperation"
      },
      "retrieve": {
          "class": "RetrieveMemoryOperation"
      },
      "remove": {
          "class": "RemoveMemoryOperation"
      }
  },
  "metrics": {
      "recency": {
          "class": "RecencyMetric",
          "weight": 0.5
      },
      "relevance": {
          "class": "RelevanceMetric",
          "model_config_name": "openai_embedding-bert",
          "weight": 0.5
      }
  }
}
```

### Memory Strategies

#### ShortLongStrategy
- **Short-term Memory**: Recent experiences stored in chronological order
- **Long-term Memory**: Important experiences stored with vector embeddings
- **Transfer Mechanism**: Automatic promotion from short-term to long-term based on metrics

#### Storage Types

**ListMemoryStorage**
- Simple chronological storage
- Fast insertion and retrieval
- Suitable for recent memory access

**VectorMemoryStorage**  
- Semantic similarity-based storage
- Uses embedding models for content representation
- Enables contextual memory retrieval

### Memory Retrieval
Memory retrieval considers three factors:
- **Recency**: How recently the memory was formed
- **Importance**: Significance of the memory content
- **Relevance**: Semantic similarity to current context

## Planning Module

The Planning module implements different cognitive architectures for agent decision-making.

### Planning Algorithms

#### COT (Chain-of-Thought) Planning
```python
class COTPlanning(PlanningBase):
    """Single-step reasoning for immediate decisions"""

    async def plan(self,**kwargs) -> str:
        prompt=f"""
        ### Agent Profile
        {kwargs["profile"]}

        ### Memory
        {kwargs["memory"]}

        
        ### Observation
        {kwargs["observation"]}
        
        ### Instruction
        {kwargs["instruction"]}

        Please think step by step based on the above concisely.
        """
        prompt=self.model.format(
            Message("system", self.sys_prompt, role="system"),
            Message("user", prompt, role="user")
        )
        response = await self.model.acall(prompt)
        return response.text

```

- **Use Case**: Simple, reactive decisions
- **Characteristics**: Fast, direct reasoning
- **Best For**: Immediate responses, simple interactions

#### BDI (Belief-Desire-Intention) Planning
```python
class BDIPlanning(PlanningBase):
    """Goal-oriented planning with beliefs and intentions"""
    
    async def plan(self, **kwargs) -> str:
        prompt = f"""
        ### Agent Profile
        {kwargs["profile"]}

        ### Memory (Beliefs)
        {kwargs["memory"]}
        
        ### Observation (New Beliefs)
        {kwargs["observation"]}
        
        ### Instruction (Task)
        {kwargs["instruction"]}

        Please analyze the situation using the BDI (Belief-Desire-Intention) framework:
        
        1. Beliefs: Based on the agent's memory and current observations, what does the agent believe about the current state of the world?
        
        2. Desires: Given these beliefs and the agent's profile, what goals should the agent prioritize?
        
        3. Intentions: What specific actions should the agent commit to in order to achieve these goals?
        
        Please think based on the above concisely.
        """
        
        prompt = self.model.format(
            Message("system", self.sys_prompt, role="system"),
            Message("user", prompt, role="user")
        )
        response = await self.model.acall(prompt)
        return response.text
```

- **Use Case**: Long-term goal pursuit
- **Characteristics**: Maintains persistent goals and plans
- **Best For**: Strategic behavior, complex objectives

#### TOM (Theory-of-Mind) Planning
```python
class TOMPlanning(PlanningBase):
    """Social reasoning considering others' perspectives"""
    
    async def plan(self, **kwargs) -> str:
        prompt = f"""
        ### Observation
        {kwargs["observation"]}
        
        ### Instruction
        {kwargs["instruction"]}
        
        ### Relationship
        {kwargs["relationship"]}

        Analyze the mental states of other agents in this scenario:
        
        1. What are other agents likely thinking or believing?
        
        2. What might be their intentions and goals?
        
        3. How might they react to different actions?
        
        Please think based on the above concisely.
        """
        
        prompt = self.model.format(
            Message("system", self.sys_prompt, role="system"),
            Message("user", prompt, role="user")
        )
        response = await self.model.acall(prompt)
        return response.text
```

- **Use Case**: Social interactions and negotiations
- **Characteristics**: Models other agents' mental states
- **Best For**: Competitive scenarios, cooperation, social dynamics

## Action Module

The Action module translates planning decisions into concrete simulation behaviors.

### Action Execution Flow
1. **Action Generation**: Planning module produces action specification
2. **State Update**: Update agent internal state
3. **Event Creation**: Convert action into simulation events
4. **Event Dispatch**: Send events through the event bus


## Agent Configuration

Agents are configured through JSON specifications:

```json5
{
    "profile": { // schema_path and profile_path could be omitted if you want to use the default schema and profile
        "ProductionManager": {
              "count": 10,
              "schema_path": "ProductionManager.json",
              "profile_path": "ProductionManager.json"
        },
        "QualityInspector": {
            "count": 10,
            "schema_path": "QualityInspector.json",
            "profile_path": "QualityInspector.json"
        },
        "Worker": {
            "count": 10,
            "schema_path": "Worker.json",
            "profile_path": "Worker.json"
        }
    },
    "planning": "COTPlanning",
    "memory": {
        "strategy": "ShortLongStrategy",
        "storages": {
            "short_term_storage": {
                "class": "ListMemoryStorage",
                "capacity": 100
            },
            "long_term_storage": {
                "class": "VectorMemoryStorage",
                "capacity": 100,
                "model_config_name": "openai_embedding-bert"
            }
        },
        "metric_weights": {
            "recency": 0.7
        },
        "operations": {
            "add": {
                "class": "AddMemoryOperation"
            },
            "retrieve": {
                "class": "RetrieveMemoryOperation"
            },
            "remove": {
                "class": "RemoveMemoryOperation"
            }
        },
        "metrics": {
            "recency": {
                "class": "RecencyMetric",
                "weight": 0.5
            },
            "relevance": {
                "class": "RelevanceMetric",
                "model_config_name": "openai_embedding-bert",
                "weight": 0.5
            }
        }
    }
}
```

## Agent Lifecycle

### Initialization
1. Load configuration and create agent instance
2. Initialize profile with attributes
3. Set up memory system with specified strategy
4. Configure planning algorithm
5. Register with simulation environment

### Runtime
1. **Perception**: Receive events from environment or other agents
2. **Planning**: Decide on actions based on goals and context
3. **Execution**: Perform actions and generate events
4. **Memory Update**: Store new experiences

### Termination
1. **Graceful Shutdown**: Complete ongoing actions
2. **State Persistence**: Save important memory contents
3. **Resource Cleanup**: Release model and memory resources

The agent system provides a flexible, powerful foundation for creating diverse social simulations while maintaining consistency and interoperability across different agent types and scenarios. 