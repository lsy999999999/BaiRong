---
sidebar_position: 1
title: System Overview
---

# System Overview

YuLan-OneSim is a next-generation social simulation platform powered by Large Language Models (LLMs) that enables researchers to create, execute, and analyze complex social simulations through natural language interactions.

## Core Architecture Components

YuLan-OneSim consists of four integrated subsystems:

### 1. Scenario Construction System
- **Purpose**: Transform natural language descriptions into executable simulation environments
- **Components**: Code generation, scenario validation, environment initialization
- **Key Feature**: Code-free scenario creation through conversational interface

### 2. Simulation Execution System  
- **Purpose**: Provide reactive agent framework and distributed execution capabilities
- **Components**: Agent runtime, event bus, environment management
- **Key Feature**: Real-time agent interactions with event-driven architecture

### 3. Feedback Evolution System
- **Purpose**: Automatically optimize LLM performance based on external feedback
- **Components**: Performance monitoring, model tuning, adaptive learning
- **Key Feature**: Self-improving simulation quality over time

### 4. AI Social Researcher System
- **Purpose**: End-to-end automated research from problem formulation to report generation
- **Components**: Research planning, experiment design, analysis automation
- **Key Feature**: Autonomous scientific research workflow


## Extensibility & Customization

YuLan-OneSim is designed for extensibility:

- **Plugin Architecture**: Custom components can be easily integrated
- **Configurable Models**: Support for different LLM providers and models
- **Custom Environments**: 50+ built-in scenarios with template for custom ones

## Deployment Modes

### Single Node Mode
- **Use Case**: Small-scale simulations (< 1,0000 agents)
- **Setup**: Single machine deployment
- **Benefits**: Simple configuration, easy debugging

### Distributed Mode  
- **Use Case**: Large-scale simulations (1,0000+ agents)
- **Setup**: Master-Worker cluster
- **Benefits**: High throughput, fault tolerance, horizontal scaling

This architecture enables researchers to focus on their research questions while YuLan-OneSim handles the complexity of multi-agent simulation, distributed computing, and LLM integration. 