<script>
import ProgressLayout from './components/ProgressLayout.vue'
import ChatMode from './views/ChatMode.vue'
import ThemeToggle from './components/ThemeToggle.vue'
// 后续会导入其他步骤组件

export default {
  name: 'App',
  components: {
    ProgressLayout,
    ChatMode,
    ThemeToggle
  },
  data() {
    return {
      currentStep: 1,
      totalSteps: 5,
      steps: [
        { name: 'Chat', component: 'ChatMode' },
        { name: 'Analysis', component: 'AnalysisMode' },
        { name: 'Behavior', component: 'BehaviorMode' },
        { name: 'Simulation', component: 'SimulationMode' },
        { name: 'Report', component: 'ReportMode' }
      ]
    }
  },
  computed: {
    currentComponent() {
      return this.steps[this.currentStep - 1].component
    }
  },
  methods: {
    prevStep() {
      if (this.currentStep > 1) {
        this.currentStep--
      }
    },
    nextStep() {
      if (this.currentStep < this.totalSteps) {
        this.currentStep++
      }
    },
    handleStepComplete() {
      if (this.currentStep < this.totalSteps) {
        this.nextStep()
      }
    }
  }
}
</script>

<template>
  <div class="app">
    <ThemeToggle class="global-theme-toggle" />
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style>
.app {
  min-height: 100vh;
  background-color: var(--bg-color);
  position: relative;
}

/* 全局滚动条样式 */
:root {
  --scrollbar-width: 4px;
  --scrollbar-track: transparent;
  --scrollbar-thumb: rgba(128, 128, 128, 0.3);
  --scrollbar-thumb-hover: rgba(128, 128, 128, 0.5);
}

/* WebKit/Blink (Chrome, Safari, Edge) */
::-webkit-scrollbar {
  width: var(--scrollbar-width);
  height: var(--scrollbar-width);
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: var(--scrollbar-thumb);
  border-radius: 4px;
  transition: background-color 0.3s;
}

::-webkit-scrollbar-thumb:hover {
  background-color: var(--scrollbar-thumb-hover);
}

/* 完全隐藏滚动条箭头 */
::-webkit-scrollbar-button {
  width: 0;
  height: 0;
  display: none;
}

::-webkit-scrollbar-corner {
  background: transparent;
}

/* 平滑滚动效果 */
html {
  scroll-behavior: smooth;
}

/* 亮色主题下的滚动条调整 */
.light-theme {
  --scrollbar-thumb: rgba(0, 0, 0, 0.2);
  --scrollbar-thumb-hover: rgba(0, 0, 0, 0.3);
}

.global-theme-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  gap: 10px;
  padding: 6px;
  background-color: rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(8px);
  border-radius: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.light-theme .global-btn {
  background-color: rgba(255, 255, 255, 0.6);
}

.button-area {
  display: flex;
  justify-content: flex-end;
  height: 100px;
  position: absolute;
  bottom: 25px;
  right: 25px;
}

.button-area button {
  padding: 10px 20px;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
}

.button-area button i {
  margin-right: 8px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
