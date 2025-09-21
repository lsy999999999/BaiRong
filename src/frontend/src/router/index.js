import { createRouter, createWebHistory } from 'vue-router'
import { h } from 'vue'

// 路由组件
import WelcomePage from '../views/WelcomePage.vue'
import Dashboard from '../views/Dashboard.vue'
import CategoryView from '../views/CategoryView.vue'
import ChatMode from '../views/ChatMode.vue'
import ProgressLayoutWrapper from '../layouts/ProgressLayoutWrapper.vue'
import AgentTypesView from '../views/AgentTypesView.vue'
import AgentConfigurationView from '../views/AgentConfigurationView.vue'
import DataTransformView from '../views/DataTransformView.vue'
import SimulationLayout from '../layouts/SimulationLayout.vue'
import CityMapView from '../views/CityMapView.vue'

const routes = [
  // {
  //   path: '/',
  //   name: 'welcome',
  //   component: WelcomePage
  // },
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard
  },
  {
    path: '/category/:category/:subcategory',
    name: 'category',
    component: CategoryView,
    props: true
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatMode
  },
  {
    path: '/simulation',
    name: 'Simulation',
    component: ProgressLayoutWrapper
  },
  {
    path: '/agent-types',
    name: 'agent-types',
    component: AgentTypesView
  },
  {
    path: '/agent-configuration',
    name: 'agent-configuration',
    component: AgentConfigurationView
  },
  {
    path: '/data-transform',
    name: 'data-transform',
    component: DataTransformView
  },
  {
    path: '/simulation-system',
    name: 'simulation-system',
    component: SimulationLayout
  },
  {
    path: '/city-map',
    name: 'city-map',
    component: CityMapView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 