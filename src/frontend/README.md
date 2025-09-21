# AI Behavior Simulation

An interactive tool for simulating AI agent behaviors and interactions in a virtual environment.

## Project Overview

AI Behavior Sim is a Vue.js-based application that allows users to:
- Configure and simulate AI agent behaviors
- Visualize agent interactions in a city map environment
- Generate and analyze agent workflows
- Create topology graphs for modeling agent relationships
- Monitor simulations with real-time data visualization

## Getting Started

### Prerequisites

- Node.js (latest LTS version recommended)
- npm or yarn package manager

### Installation

```bash 
cd src/frontend

# Install dependencies
npm install
# or 
yarn install
```

### Running the Application

```bash
# Development mode with hot-reload
npm run dev
# or
yarn dev

# Build for production
npm run build
# or
yarn build

# Preview production build
npm run preview
# or
yarn preview
```

## Project Structure

- **views/**: Main application views and pages
  - `ChatMode.vue`: Interactive chat interface
  - `Dashboard.vue`: Main application dashboard
  - `SimulationView.vue`: Simulation environment
  - `AgentConfigurationView.vue`: Agent setup and configuration
  - `AgentTypesView.vue`: Define different agent types
  - `CityMapView.vue`: City map visualization

- **components/**: Reusable UI components
  - `TopologyGraph.vue`: Agent relationship visualization
  - `TopologyEditor.vue`: Editor for creating topology graphs
  - `ProgressLayout.vue`: Step-by-step workflow interface
  - `ThemeToggle.vue`: Switch between light and dark themes

- **stores/**: State management with Pinia
  - `gameStore.js`: Central store for simulation state

- **router/**: Application routing with Vue Router

- **styles/**: Global CSS and theme definitions

## Key Features

1. **Agent Configuration**: Create and customize AI agents with different behaviors and properties

2. **Simulation Environment**: Run dynamic simulations with configurable parameters and visualization

3. **Topology Editor**: Create complex relationships and interaction models between agents

4. **Chat Interface**: Communicate with agents and analyze their responses

5. **Light/Dark Theme**: Support for both light and dark UI themes

6. **Development Mode**: Special tools and features for developers

## Technologies Used

- Vue 3 (Composition API)
- Vue Router for navigation
- Pinia for state management
- PixiJS for map rendering and visualization
- Element Plus for UI components
- CodeMirror/Monaco for code editing capabilities
- ECharts for data visualization
