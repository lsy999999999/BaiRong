<template>
  <div class="progress-layout">
    <div class="progress-container">
      <button 
        class="nav-btn prev" 
        @click="handlePrev"
        :disabled="isLoading || (currentStep === 4 && !hasWorkflowData)"
      >
        <i class="fa fa-arrow-left"></i> Back
      </button>
      
      <div class="progress-content">
        <div class="progress-bar">
          <div class="progress" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="step-nodes">
          <div 
            v-for="(step, index) in steps" 
            :key="index"
            class="step-node"
            :class="{ 
              'active': currentStep > index + 1,
              'completed': currentStep > index + 1,
              'current': currentStep === index + 1
            }"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-name">{{ step }}</div>
          </div>
        </div>
      </div>
      
      <div class="nav-right">
        <button 
          class="nav-btn next" 
          @click="$emit('call-proceed-next', currentStep)"
          :disabled="isLoading 
            || !canProceedToNext
            || (currentStep === totalSteps && currentStep !== 5) 
            || (currentStep === 4 && !hasWorkflowData)"
        >
          Next <i class="fa fa-arrow-right"></i>
        </button>
        <div class="theme-toggle-space"></div>
      </div>
    </div>
    
    <div class="content">
      <slot></slot>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus';

export default {
  name: 'ProgressLayout',
  props: {
    currentStep: {
      type: Number,
      required: true
    },
    canProceedToNext: {
      type: Boolean,
      default: false
    },
    totalSteps: {
      type: Number,
      required: true
    },
    generationComplete: Boolean,
    hasWorkflowData: {
      type: Boolean,
      default: false
    },
    stepConditionInfo: {
      type: Object,
      default: () => ({
        step1: "Need more conversation data to generate ODD protocol",
        step2: "Please add at least one agent type to proceed",
        step4: "Please wait for code generation to complete"
      })
    },
    isCodeModified: {
      type: Boolean,
      default: false
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    progress() {
      // 使用固定的百分比值
      const progressValues = [12, 36, 62, 87, 100];
      return progressValues[this.currentStep - 1];
    },
    steps() {
      return [
        'ODD Protocol Generation',
        'Agent Type Extraction',
        'Simulation Workflow Generation',
        'Code Generation',
        'Agent Profile Configuration'
      ];
    },
    isFirstStep() {
      return this.currentStep === 1;
    }
  },
  methods: {
    handlePrev() {
      if (this.currentStep === 1) {
        this.$confirm(
          'Returning to Dashboard will clear all current data. Are you sure you want to continue?',
          'Warning',
          {
            confirmButtonText: 'Confirm',
            cancelButtonText: 'Cancel',
            type: 'warning'
          }
        )
          .then(() => {
            // 清除所有数据
            // localStorage.removeItem('scenarioName');
            // localStorage.removeItem('sessionId');
            // window.summaryContent = null;
            // window.messages = null;
            // 清除所有数据，用来判断是从第二步返回的还是首页进入的
            window.query = null;
            this.$emit('go-dashboard');
          })
          .catch(() => {
            // User cancelled, do nothing
          });
      } else {
        window.query = null;
        this.$emit('prev');
      }
    },
  
  },
}
</script>

<style scoped>
.progress-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

.progress-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background-color: var(--bg-color);
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.progress-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.progress-bar {
  height: 4px;
  background-color: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  margin: 0 20px;
}

.progress {
  height: 100%;
  background-color: var(--accent-color);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.step-nodes {
  display: flex;
  justify-content: space-between;
  padding: 0 20px;
}

.step-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  position: relative;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--border-color);
  color: var(--text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.step-node.completed .step-number {
  background-color: var(--accent-color);
  color: white;
}

.step-name {
  font-size: 0.8rem;
  color: var(--secondary-color);
  transition: all 0.3s ease;
}

.step-node.active .step-number {
  background-color: var(--accent-color);
  color: white;
}

.step-node.active .step-name {
  color: var(--accent-color);
}

.step-node.current .step-number {
  background-color: var(--accent-color);
  color: white;
  transform: scale(1.2);
  box-shadow: 0 0 0 4px rgba(65, 112, 243, 0.2);
}

.step-node.current .step-name {
  color: var(--accent-color);
  font-weight: 500;
}

.nav-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: none;
  background-color: var(--accent-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  min-width: 80px;
  justify-content: center;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-btn:not(:disabled):hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

.nav-btn i {
  font-size: 0.8rem;
}

.content {
  flex: 1;
  margin-top: 90px; /* 为进度条和步骤节点预留空间 */
  padding: 20px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 32px;
}

.theme-toggle-space {
  width: 50px; /* 为ThemeToggle预留空间 */
  height: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-container {
    padding: 10px 15px;
  }
  
  .step-nodes {
    padding: 0 10px;
  }
  
  .step-name {
    font-size: 0.7rem;
  }
  
  .nav-btn {
    padding: 6px 12px;
    font-size: 0.8rem;
    min-width: 70px;
  }
}
</style>