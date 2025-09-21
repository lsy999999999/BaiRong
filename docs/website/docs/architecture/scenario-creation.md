# Scenario Creation Pipeline

YuLan-OneSim provides a systematic approach to creating simulation scenarios through an automated pipeline that transforms natural language descriptions into executable simulations using specialized AI agents.

## Overview

The scenario creation process consists of six main stages, each powered by dedicated AI agents that build upon the previous stage to create a complete simulation environment:

1. **ODD Protocol Generation** - Interactive dialogue using ODDAgent to capture scenario requirements
2. **Agent Type Extraction** - ProfileAgent identifies and defines participant types
3. **Workflow Generation** - WorkflowAgent creates agent interaction patterns and directed graphs
4. **Code Generation** - CodeAgent automatically synthesizes executable agent behaviors
5. **Data Generation** - ProfileAgent creates agent profiles, relationships, and environment data
6. **Metrics Generation** - MetricAgent defines monitoring and evaluation criteria

Let's explore each stage using a labor market simulation as our running example.

## Stage 1: ODD Protocol Generation

### Interactive Dialogue with ODDAgent

The `ODDAgent` class facilitates an interactive conversation that progressively builds a comprehensive ODD (Overview, Design concepts, Details) protocol document. Users provide natural language descriptions, and the agent asks clarifying questions until a complete specification is achieved.

#### ODDAgent Core Implementation

```python
class ODDAgent(AgentBase):
    def __init__(self, model_config_name: str, sys_prompt: str = ''):
        # Initialize with flexible ODD structure
        self.scene_info = {
            "domain": "",
            "scene_name": "",
            "odd_protocol": {
                "overview": {},
                "design_concepts": {},
                "details": {}
            }
        }
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        # Update scene_info based on user input
        response = self.update_scene_info(user_input)
        
        if response.get('end_conversation', False):
            return {
                "domain": self.scene_info.get("domain", ""),
                "scene_name": self.scene_info.get("scene_name", ""),
                "odd_protocol": self.scene_info.get("odd_protocol", {}),
                "clarification_question": '',
                "is_complete": True
            }
        
        # Generate clarification questions for missing information
        clarification_result = self.generate_clarification_questions()
        return {
            "domain": self.scene_info.get("domain", ""),
            "scene_name": self.scene_info.get("scene_name", ""),
            "odd_protocol": self.scene_info.get("odd_protocol", {}),
            "clarification_question": clarification_result.get('question', ''),
            "is_complete": clarification_result.get('is_complete', False)
        }
```

#### Example: Labor Market ODD Protocol

Starting with a user description: *"I want to simulate a job market where job seekers look for employment and employers recruit candidates through various channels"*

The ODDAgent progressively builds this into a comprehensive protocol:

```json
{
  "domain": "Economics",
  "scene_name": "labor_market_simulation",
  "odd_protocol": {
    "overview": {
      "system_goal": "Simulate the job seeking and recruitment process in the labor market to study information asymmetry, signaling, matching efficiency, bias, and the impact of different recruitment strategies",
      "agent_types": "Job_Seeker, Employer, Recruitment_Channel with specific attributes and behaviors for labor market interactions",
      "environment_description": "Labor market with varying tightness, economic conditions, regulatory environment, and skill demand trends"
    },
    "design_concepts": {
      "interaction_patterns": "Job seekers and employers interact through recruitment channels, with job seekers applying for jobs and employers screening candidates",
      "communication_protocols": "Information exchange through recruitment channels about job postings, applications, and negotiations",
      "decision_mechanisms": "Job seekers evaluate opportunities based on skill match and preferences; employers make hiring decisions based on candidate evaluations"
    },
    "details": {
      "agent_behaviors": "Job seekers set goals, evaluate applications, negotiate salaries; Employers post vacancies, screen candidates, conduct interviews",
      "decision_algorithms": "Matching algorithms based on skills, preferences, and market conditions",
      "specific_constraints": "Market tightness, economic conditions, bias in screening, social network effects"
    }
  }
}
```

## Stage 2: Agent Type Extraction

### ProfileAgent Identifies Participant Types

The `ProfileAgent` analyzes the completed ODD protocol to identify distinct agent types and their population distributions.

#### Agent Type Generation Process

```python
class ProfileAgent(AgentBase):
    def generate_agent_types(self, description):
        prompt = (
            f"Given the following description: {description}, identify or infer relevant agent types "
            "and return them as a JSON object where keys are PascalCase agent type names and values are short descriptions..."
        )
        
        response = self.model(formatted_prompt)
        res = parser.parse(response)
        agent_types = res.parsed
        return agent_types
    
    def assign_agent_portraits(self, agent_types_dict):
        # Assign social role portraits (1-5) to agent categories
        # 1=Government Official, 2=Researcher, 3=Worker, 4=Business, 5=Citizen
        ...
```

#### Example Output: Labor Market Agent Types

```json
{
  "agent_types": {
    "JobSeeker": "An agent representing individuals seeking employment, responsible for setting job goals, evaluating job applications, negotiating salaries, and deciding on job offers",
    "Employer": "An agent representing companies offering employment, responsible for posting job vacancies, screening candidates, conducting interviews, and making hiring decisions",
    "RecruitmentChannel": "An agent facilitating interactions between job seekers and employers, responsible for disseminating job postings, filtering applications, and matching candidates"
  },
  "portrait": {
    "JobSeeker": 3,
    "Employer": 4,
    "RecruitmentChannel": 1
  }
}
```

## Stage 3: Workflow Generation

### WorkflowAgent Creates Interaction Graphs

The `WorkflowAgent` transforms the ODD protocol and agent types into a directed graph of actions and events that defines how agents interact.

#### Workflow Extraction Process

```python
class WorkflowAgent(AgentBase):
    def extract_workflow(self, description: str, agent_types: list) -> dict:
        # Extract agents, actions, and events from description
        prompt = f"""
        Workflow Extraction Task
        Description: {description}
        Agent Types: {', '.join(agent_types)}
        
        Extract detailed workflow including:
        - Agent actions with conditions and types (OR/AND/XOR)
        - Events flowing between actions
        - StartEvents and terminal events
        """
        
        response = self.model(formatted_prompt)
        data = parser.parse(response).parsed
        
        # Process and validate workflow structure
        self.build_topology_graph()
        return data
    
    def generate_workflow(self, description: str, agent_types: list):
        # Complete workflow generation with validation and enhancement
        data = self.extract_workflow(description, agent_types)
        action_requirements = self.enhance_actions_with_requirements(...)
        system_data_model = self.derive_data_model_from_actions(...)
        G = self.build_topology_graph()
        return self.actions, self.events, system_data_model, G
```

#### Example: Labor Market Workflow Components

**Actions with Conditions and Types:**
```json
{
  "JobSeeker": [
    {
      "id": 1,
      "name": "enter_market",
      "condition": null,
      "type": "OR",
      "description": "Job seeker enters the labor market, setting initial parameters"
    },
    {
      "id": 2, 
      "name": "evaluate_job_applications",
      "condition": "Job postings received and job seeker is actively searching",
      "type": "OR",
      "description": "Evaluates job applications to determine best fit"
    },
    {
      "id": 3,
      "name": "negotiate_salaries", 
      "condition": "Job offer received",
      "type": "AND",
      "description": "Engages in salary negotiations with employers"
    }
  ]
}
```

**Events Connecting Actions:**
```json
{
  "1": {
    "event_name": "JobMarketEntryEvent",
    "from_agent_type": "JobSeeker",
    "from_action_name": "enter_market", 
    "to_agent_type": "RecruitmentChannel",
    "to_action_name": "distribute_job_postings",
    "fields": [
      {"name": "skills", "type": "list"},
      {"name": "experience", "type": "int"},
      {"name": "job_preferences", "type": "list"}
    ]
  }
}
```

**System Data Model:**
```json
{
  "environment": {
    "variables": [
      {"name": "application_cost", "type": "float"},
      {"name": "distributed_jobs", "type": "list"}
    ]
  },
  "agents": {
    "JobSeeker": {
      "variables": [
        {"name": "skills", "type": "list"},
        {"name": "market_status", "type": "str"},
        {"name": "applications_submitted", "type": "list"}
      ]
    }
  }
}
```

## Stage 4: Code Generation

### CodeAgent Synthesizes Executable Behaviors

The `CodeAgent` generates Python code for agent classes and event definitions based on the workflow specification.

#### Multi-Phase Code Generation

```python
class CodeAgent(AgentBase):
    def generate_code_phased(self, description: str, actions: Dict, events: Dict, 
                           env_path: str, status_dict: Dict, max_iterations: int = 3):
        # Phase 1: Generate initial code
        agent_code_dict, event_code = self.generate_initial_code(...)
        
        # Phase 2: Validate and fix code
        verification_results = self.check_code(...)
        if has_issues:
            agent_code_dict, event_code = self.fix_code(...)
            
        # Save and structure code
        self.save_phased_code(agent_code_dict, event_code, env_path, ...)
    
    def generate_handler_code(self, description: str, agent_type: str, 
                            action_info: Dict, incoming_events: List, 
                            outgoing_events: List) -> str:
        # Generate specific handler methods for each action
        thinking_prompt = f"""Analyze how to handle action '{action_info['name']}'..."""
        handler_prompt = f"""Generate handler method with decision-making logic..."""
        
        response = self.call_llm(handler_prompt)
        return extracted_handler_code
```

#### Example: Generated Agent Code

**JobSeeker Agent Class:**
```python
class JobSeeker(GeneralAgent):
    def __init__(self, sys_prompt=None, model_config_name=None, ...):
        super().__init__(...)
        self.register_event("StartEvent", "enter_market")
        self.register_event("JobPostingEvent", "evaluate_job_applications")
    
    async def enter_market(self, event: Event) -> List[Event]:
        # Extract agent profile information
        skills = self.profile.get_data("skills", [])
        education = self.profile.get_data("education", "")
        experience = self.profile.get_data("experience", 0)
        
        # Update market status
        self.profile.update_data("market_status", "active")
        
        # Generate reaction using LLM for decision making
        instruction = """Based on your profile, determine your job search strategy..."""
        observation = f"Skills: {skills}, Experience: {experience}"
        
        result = await self.generate_reaction(instruction, observation)
        target_ids = result.get('target_ids', [])
        
        # Create job market entry event
        events = []
        for target_id in target_ids:
            entry_event = JobMarketEntryEvent(
                self.profile_id, target_id, 
                skills=skills, education=education, experience=experience
            )
            events.append(entry_event)
        
        return events
```

**Event Classes:**
```python
class JobMarketEntryEvent(Event):
    def __init__(self, from_agent_id: str, to_agent_id: str, 
                 skills: List = [], education: str = "", experience: int = 0):
        super().__init__(from_agent_id, to_agent_id)
        self.skills = skills
        self.education = education  
        self.experience = experience
```

## Stage 5: Data Generation

### ProfileAgent Creates Agent Profiles and Relationships

The `ProfileAgent` generates individual agent profiles, relationship networks, and environment data based on customizable schemas.

#### Profile Schema Generation

```python
class ProfileAgent(AgentBase):
    def generate_profile_schema(self, scenario_description, agent_name, agent_data_model):
        prompt = f"""Generate Profile Schema for {agent_name} based on:
        - Scenario: {scenario_description}  
        - Data Model: {agent_data_model}
        
        Schema should include:
        - Static attributes (sampling: "llm" or "random")
        - Dynamic variables (sampling: "default")
        - Meaningful default values for simulation start
        """
        
        response = self.model(formatted_prompt)
        schema = parser.parse(response).parsed
        return schema
```

#### Example: JobSeeker Profile Schema

```json
{
  "name": {
    "type": "str",
    "default": "John Smith", 
    "private": false,
    "sampling": "llm",
    "description": "The agent's full name"
  },
  "skills": {
    "type": "list",
    "default": ["communication", "problem_solving"],
    "private": false, 
    "sampling": "llm",
    "description": "Professional skills possessed"
  },
  "experience": {
    "type": "int",
    "default": 3,
    "private": false,
    "sampling": "random", 
    "range": [0, 20]
  },
  "market_status": {
    "type": "str",
    "default": "seeking",
    "private": false,
    "sampling": "default"
  },
  "applications_submitted": {
    "type": "list", 
    "default": [{"job_id": "initial", "status": "pending"}],
    "private": true,
    "sampling": "default"
  }
}
```

#### Multi-Layer Data Generation

```python
# Generate agent profiles
profiles = AgentFactory.generate_profiles(
    agent_type="JobSeeker",
    schema=schema,
    model=model,
    num_profiles=60
)

# Generate relationship networks
relationships = profile_agent.generate_relationship_schema(agent_types, actions, events)

# Generate environment data  
env_data = profile_agent.generate_env_data(env_data_model, description)
```

#### Example: Generated Environment Data

```json
{
  "application_cost": 25.50,
  "market_tightness": 0.73,
  "economic_conditions": "stable_growth",
  "skill_demand_trends": ["ai_skills", "remote_work", "digital_literacy"]
}
```

## Stage 6: Metrics Generation

### MetricAgent Defines Monitoring Systems

The `MetricAgent` creates comprehensive monitoring systems for simulation evaluation and analysis.

#### Metrics Generation Process

```python
class MetricAgent(AgentBase):
    def generate_metrics(self, scenario_description: str, agent_types: List[str], 
                        system_data_model: Dict, num_metrics: int = 3) -> List[Dict]:
        prompt = f"""Generate monitoring metrics for:
        Scenario: {scenario_description}
        Agent Types: {agent_types}
        Data Model: {system_data_model}
        
        Focus on:
        - Behavioral patterns
        - System efficiency  
        - Emergent phenomena
        """
        
        response = self.model(formatted_prompt)
        metrics = parser.parse(response).parsed.get("metrics", [])
        return self.validate_metrics(metrics, system_data_model)
    
    def generate_calculation_function(self, metric_def: Dict) -> str:
        # Generate robust calculation functions with error handling
        prompt = f"""Generate calculation function for metric: {metric_def['name']}
        With safe handling of None values, empty lists, type errors..."""
        
        response = self.model(formatted_prompt)
        function_code = self.code_parser.parse(response).parsed
        return function_code
```

#### Example: Labor Market Metrics

**Average Job Seeker Experience:**
```json
{
  "name": "average_job_seeker_experience",
  "description": "Measures average years of experience among job seekers",
  "visualization_type": "bar",
  "variables": [
    {
      "name": "experience", 
      "source_type": "agent",
      "agent_type": "JobSeeker",
      "is_list": true
    }
  ]
}
```

**Generated Calculation Function:**
```python
def average_job_seeker_experience(data: Dict[str, Any]) -> Any:
    """Calculate average experience of job seekers with robust error handling"""
    try:
        experience_data = safe_list(safe_get(data, 'experience', []))
        if not experience_data:
            return {"No Data": 0}
            
        valid_experiences = [safe_number(exp) for exp in experience_data if exp is not None]
        average_exp = safe_avg(valid_experiences, 0)
        
        return {"Average Experience": round(average_exp, 1)}
    except Exception as e:
        log_metric_error('average_job_seeker_experience', e)
        return {"Error": 0}
```

## Best Practices

### Quality Assurance

Each stage includes validation mechanisms:

- **ODDAgent**: Completeness checking and clarification questions
- **WorkflowAgent**: Structural validation and connectivity verification  
- **CodeAgent**: Syntax checking, code review, and iterative fixing
- **ProfileAgent**: Schema validation and data consistency checks
- **MetricAgent**: Variable validation and calculation testing

### Scenario Design Guidelines

**Effective ODD Descriptions:**
- Provide specific, detailed scenarios rather than abstract concepts
- Include concrete examples of agent behaviors and interactions
- Specify measurable outcomes and success criteria

**Agent Modeling Best Practices:**
- Balance behavioral complexity with computational efficiency
- Design meaningful interactions that serve scenario objectives  
- Include realistic personality traits and decision factors

**Code Quality Assurance:**
- Review generated handlers for logical consistency
- Test action flows with representative inputs
- Verify event routing and data propagation

**Data Validation Standards:**
- Ensure profile schemas capture essential characteristics
- Validate relationship networks for realistic connectivity
- Check environment data for scenario consistency

The scenario creation pipeline in YuLan-OneSim transforms high-level scenario descriptions into complete, executable simulations through systematic application of specialized AI agents, ensuring consistency while reducing manual effort for complex agent-based modeling. 