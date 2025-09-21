---
sidebar_position: 1
---

# Scenarios Overview

In YuLan-OneSim, a **Scenario** is the core of any simulation. It defines the fundamental rules, the environment, the agents, and the ways they interact within a simulated world. All scenarios are located in the `src/envs` directory of the project.

## What is a Scenario?

Essentially, a scenario is a self-contained Python package that includes all the necessary components to run a specific simulation:

- **Environment**: The virtual space and rules where the simulation takes place.
- **Agents**: The participants in the simulation, each with its own behaviors and objectives.
- **Actions**: The operations that agents can perform.
- **Events**: Specific occurrences that drive the simulation forward.
- **Configuration**: Parameters that define various aspects of the simulation, such as the number of agents and the simulation's duration.

YuLan-OneSim provides a rich set of built-in scenarios covering 8 different fields including economics, sociology, etc. You can use these scenarios directly, modify them to fit your research needs, or create entirely new ones from scratch.

