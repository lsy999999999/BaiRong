<template>
  <div class="simulation-view">
    <!-- 主画布区域 -->
    <div class="canvas-container">
      <!-- 顶部工具栏 -->
      <div class="simulation-toolbar">
        <div class="toolbar-section">
          <span class="current-stage">Stage: {{ stageNames[currentStage] }}</span>
        </div>
        <div class="toolbar-section">
          <button class="control-btn" 
                  :class="{'active': isSimulationRunning}" 
                  @click="toggleSimulation">
            <i class="fa" :class="isSimulationRunning ? 'fa-pause' : 'fa-play'"></i>
            {{ isSimulationRunning ? 'Pause' : 'Start' }}
          </button>
          <button class="control-btn reset-btn" @click="resetSimulation">
            <i class="fa fa-refresh"></i> Reset
          </button>
        </div>
        <div class="toolbar-section">
          <span class="rounds-info">Round: {{ currentRound }}/{{ totalRounds }}</span>
          <!-- 为昼夜切换按钮预留空间 -->
          <button class="toggle-day-night">
            <i class="fa fa-moon-o"></i>
          </button>
        </div>
      </div>
      
      <canvas ref="simulationCanvas" class="simulation-canvas"></canvas>
      
      <!-- 添加调试信息 -->
      <div v-if="simulationAgents.length > 0" class="debug-info">
        Agents ready. Click on an agent circle to view details.
      </div>
    </div>
    
    <!-- 右侧Agent信息面板 -->
    <div class="agent-detail-panel" v-if="selectedAgent" :class="{'show': isAgentPanelVisible}">
      <div class="panel-header">
        <h2>Agent Information</h2>
        <button class="close-btn" @click="closeAgentPanel">
          <i class="fa fa-times"></i>
        </button>
      </div>
      
      <div class="panel-body">
        <div class="agent-header">
          <div class="agent-color" :style="{ backgroundColor: selectedAgent.color }"></div>
          <h3>{{ selectedAgent.name }} #{{ selectedAgent.id }}</h3>
        </div>
        
        <div class="agent-stats">
          <div class="stat-item">
            <span class="stat-label">Type:</span>
            <span class="stat-value">{{ selectedAgent.type }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Status:</span>
            <span class="stat-value">{{ selectedAgent.status }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Position:</span>
            <span class="stat-value">{{ selectedAgent.position.x }}, {{ selectedAgent.position.y }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Current Action:</span>
            <span class="stat-value">{{ selectedAgent.currentAction }}</span>
          </div>
        </div>
        
        <div class="agent-interaction">
          <h4>Interaction History</h4>
          <div class="interaction-list">
            <div v-for="(interaction, index) in selectedAgent.interactions" :key="index" class="interaction-item">
              <div class="interaction-time">Round {{ interaction.round }}</div>
              <div class="interaction-content">
                <strong>Query:</strong> {{ interaction.query }}
              </div>
              <div class="interaction-content">
                <strong>Response:</strong> {{ interaction.response }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 左侧配置面板 -->
    <div class="config-panel" :class="{'show': isPanelVisible}">
      <div class="panel-header">
        <h2>Simulation Configuration</h2>
        <button class="close-btn" @click="togglePanel">
          <i class="fa fa-times"></i>
        </button>
      </div>
      
      <div class="panel-body">
        <div class="config-section">
          <h3>Simulation Parameters</h3>
          
          <div class="form-group vertical">
            <label for="rounds">Simulation Rounds:</label>
            <div class="input-control">
              <input type="number" id="rounds" v-model.number="totalRounds" min="1" max="1000">
            </div>
          </div>
          
          <div class="form-group vertical">
            <label>Map Generation:</label>
            <div class="map-options">
              <button class="map-btn" @click="generateRandomMap">
                <i class="fa fa-random"></i> Generate Random Map
              </button>
              <div class="map-status" v-if="!hasGeneratedMap">
                <i class="fa fa-exclamation-circle"></i> You need to generate a map before starting
              </div>
              <div class="map-status success" v-else>
                <i class="fa fa-check-circle"></i> Map generated
              </div>
            </div>
          </div>
        </div>
        
        <div class="config-section">
          <h3>Agent Configuration</h3>
          <div v-if="agents.length === 0" class="no-agents">
            No agents configured. Return to previous steps to configure agents.
          </div>
          
          <div v-else class="agent-list">
            <div v-for="(agent, index) in agents" :key="index" class="agent-item">
              <div class="agent-info">
                <div class="agent-color" :style="{ backgroundColor: agent.color }"></div>
                <div class="agent-name">{{ agent.name }}</div>
              </div>
              
              <div class="agent-quantity vertical">
                <label :for="'agent-' + index">Quantity:</label>
                <div class="quantity-control">
                  <input type="number" 
                         :id="'agent-' + index" 
                         v-model.number="agent.simulationQuantity" 
                         :min="1" 
                         :max="agent.generatedQuantity">
                  <span class="max-info">/ {{ agent.generatedQuantity }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="panel-footer">
        <button class="primary-btn" @click="startSimulation" :disabled="!canStartSimulation">
          Start Simulation
        </button>
        <button class="secondary-btn" @click="togglePanel">
          Cancel
        </button>
      </div>
    </div>
    
    <!-- 悬浮的配置按钮 -->
    <button class="floating-btn" @click="togglePanel" v-if="!isPanelVisible">
      <i class="fa fa-cog"></i>
      Configuration
    </button>
    
    <!-- 底部操作按钮 -->
    <div class="simulation-footer" v-if="simulationComplete">
      <button class="complete-btn" @click="finishSimulation">
        <i class="fa fa-check"></i> 完成模拟并返回仪表板
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SimulationView',
  data() {
    return {
      isPanelVisible: true,
      isSimulationRunning: false,
      isAgentPanelVisible: false,
      canvas: null,
      ctx: null,
      agents: [],
      simulationAgents: [],
      selectedAgent: null,
      totalRounds: 100,
      currentRound: 0,
      currentStage: 0,
      hasGeneratedMap: false,
      simulationInterval: null,
      stageNames: [
        'Initial Configuration',
        'Simulation Running',
        'Results Analysis'
      ],
      agentConfigurations: []
    }
  },
  computed: {
    canStartSimulation() {
      return this.agents.length > 0 && this.totalRounds > 0 && this.hasGeneratedMap;
    },
    simulationComplete() {
      return this.currentStage === 2 && this.currentRound >= this.totalRounds;
    }
  },
  mounted() {
    // 初始化画布
    this.initCanvas();
    
    // 从localStorage或Vuex获取之前步骤的数据
    this.loadAgentConfigurations();
    
    // 监听窗口大小变化，调整画布大小
    window.addEventListener('resize', this.handleResize);
    
    // 添加滚动条样式
    document.body.style.overflow = 'hidden';
    
    // 修复点击事件，确保在组件完全加载后绑定
    this.$nextTick(() => {
      this.canvas = this.$refs.simulationCanvas;
      if (this.canvas) {
        console.log('Canvas found, adding click event listener');
        this.canvas.addEventListener('click', this.handleCanvasClick);
        
        // 测试绘制一个可点击的Agent
        if (this.simulationAgents.length === 0) {
          this.testDrawAgent();
        }
      } else {
        console.error('Canvas reference not found in mounted hook');
      }
    });
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    if (this.canvas) {
      this.canvas.removeEventListener('click', this.handleCanvasClick);
    }
    document.body.style.overflow = '';
    
    // 清除模拟计时器
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
    }
  },
  methods: {
    initCanvas() {
      const canvas = this.$refs.simulationCanvas;
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      
      // 设置画布大小为容器大小
      this.handleResize();
      
      // 绘制初始空白画布
      this.drawEmptyCanvas();
    },
    
    handleResize() {
      const container = this.canvas.parentElement;
      this.canvas.width = container.clientWidth;
      this.canvas.height = container.clientHeight;
      
      // 如果已经生成了地图，则重新绘制
      if (this.currentStage > 0) {
        this.redrawMap();
        this.drawAgents(); // 重新绘制Agent
      } else {
        this.drawEmptyCanvas();
      }
    },
    
    drawEmptyCanvas() {
      if (!this.ctx) return;
      
      // 清空画布
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      
      // 绘制提示文本
      this.ctx.fillStyle = '#555';
      this.ctx.font = '18px Arial';
      this.ctx.textAlign = 'center';
      this.ctx.fillText('Configure simulation parameters and generate a map', 
                        this.canvas.width / 2, 
                        this.canvas.height / 2 - 20);
      
      this.ctx.font = '14px Arial';
      this.ctx.fillText('Use the configuration panel to set parameters', 
                        this.canvas.width / 2, 
                        this.canvas.height / 2 + 10);
    },
    
    generateRandomMap() {
      if (!this.ctx) return;
      
      // 清空画布
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      
      // 简单示例：绘制随机地形
      // 在实际应用中，这里会有更复杂的地图生成逻辑
      
      // 绘制背景
      this.ctx.fillStyle = '#f0f0f0';
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      // 绘制网格
      this.ctx.strokeStyle = '#ddd';
      this.ctx.lineWidth = 1;
      
      const gridSize = 50;
      for (let x = 0; x < this.canvas.width; x += gridSize) {
        this.ctx.beginPath();
        this.ctx.moveTo(x, 0);
        this.ctx.lineTo(x, this.canvas.height);
        this.ctx.stroke();
      }
      
      for (let y = 0; y < this.canvas.height; y += gridSize) {
        this.ctx.beginPath();
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(this.canvas.width, y);
        this.ctx.stroke();
      }
      
      // 绘制随机障碍物
      this.ctx.fillStyle = '#999';
      for (let i = 0; i < 30; i++) {
        const x = Math.random() * this.canvas.width;
        const y = Math.random() * this.canvas.height;
        const size = 20 + Math.random() * 40;
        
        this.ctx.beginPath();
        this.ctx.arc(x, y, size, 0, Math.PI * 2);
        this.ctx.fill();
      }
      
      // 更新状态
      this.currentStage = 0;
      this.hasGeneratedMap = true;
    },
    
    redrawMap() {
      // 重新绘制当前地图（用于窗口大小变化时）
      this.generateRandomMap();
    },
    
    loadAgentConfigurations() {
      try {
        // 从localStorage获取代理数据
        const agentData = JSON.parse(localStorage.getItem('agentData') || '[]');
        const agentPopulation = JSON.parse(localStorage.getItem('agentPopulation') || '{}');
        
        if (!agentData.length) {
          console.warn('No agent data found in localStorage');
          // 如果没有找到数据，保留示例数据用于演示
          this.agentConfigurations = [
            { id: 1, name: 'Resident', color: '#4CAF50', generatedQuantity: 50 },
            { id: 2, name: 'Worker', color: '#2196F3', generatedQuantity: 30 },
            { id: 3, name: 'Tourist', color: '#FFC107', generatedQuantity: 20 }
          ];
        } else {
          // 转换从localStorage获取的数据
          this.agentConfigurations = agentData.map(agent => ({
            id: agent.id,
            name: agent.name,
            color: agent.color || this.getRandomColor(),
            generatedQuantity: agentPopulation[agent.id] || 10
          }));
        }
        
        // 复制到本地状态，并添加simulationQuantity（默认使用全部生成的数量）
        this.agents = this.agentConfigurations.map(agent => ({
          ...agent,
          simulationQuantity: agent.generatedQuantity
        }));
      } catch (error) {
        console.error('Error loading agent configurations:', error);
        // 使用后备数据
        this.agents = [
          { id: 1, name: 'Resident', color: '#4CAF50', generatedQuantity: 50, simulationQuantity: 50 },
          { id: 2, name: 'Worker', color: '#2196F3', generatedQuantity: 30, simulationQuantity: 30 },
          { id: 3, name: 'Tourist', color: '#FFC107', generatedQuantity: 20, simulationQuantity: 20 }
        ];
      }
    },
    
    getRandomColor() {
      const colors = ['#4CAF50', '#2196F3', '#FFC107', '#FF5722', '#9C27B0', '#673AB7', '#3F51B5'];
      return colors[Math.floor(Math.random() * colors.length)];
    },
    
    generateSimulationAgents() {
      // 根据配置生成实际的Agent实例
      this.simulationAgents = [];
      
      this.agents.forEach(agentConfig => {
        // 根据数量生成对应数量的Agent实例
        for (let i = 0; i < agentConfig.simulationQuantity; i++) {
          const x = Math.random() * this.canvas.width;
          const y = Math.random() * this.canvas.height;
          
          this.simulationAgents.push({
            id: `${agentConfig.id}-${i+1}`,
            name: agentConfig.name,
            type: agentConfig.name,
            color: agentConfig.color,
            position: { x, y },
            radius: 12,
            status: 'Active',
            currentAction: ['Moving', 'Searching', 'Interacting'][Math.floor(Math.random() * 3)],
            interactions: [
              {
                round: 1,
                query: 'Where is the nearest shop?',
                response: 'There is a convenience store two blocks north.'
              },
              {
                round: 3,
                query: 'Is there any public transport nearby?',
                response: 'Yes, there is a bus stop just across the street.'
              }
            ]
          });
        }
      });
      
      // 绘制Agent
      this.drawAgents();
    },
    
    drawAgents() {
      if (!this.ctx || this.simulationAgents.length === 0) return;
      
      // 首先重新绘制地图
      this.redrawMap();
      
      // 然后绘制每个Agent
      this.simulationAgents.forEach(agent => {
        this.ctx.beginPath();
        this.ctx.arc(agent.position.x, agent.position.y, agent.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = agent.color;
        this.ctx.fill();
        
        // 绘制边框
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // 如果是选中的Agent，绘制高亮边框
        if (this.selectedAgent && agent.id === this.selectedAgent.id) {
          this.ctx.beginPath();
          this.ctx.arc(agent.position.x, agent.position.y, agent.radius + 4, 0, Math.PI * 2);
          this.ctx.strokeStyle = '#ff0';
          this.ctx.lineWidth = 2;
          this.ctx.stroke();
        }
      });
    },
    
    handleCanvasClick(event) {
      console.log('Canvas clicked!', event);
      
      // 检查是否有Agent可点击
      if (this.simulationAgents.length === 0) {
        console.log('No agents to click');
        return;
      }
      
      // 获取点击位置相对于画布的坐标
      const rect = this.canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      console.log('Click coordinates:', { x, y });
      
      // 检查是否点击到了Agent
      let clickedAgent = null;
      for (const agent of this.simulationAgents) {
        const dx = x - agent.position.x;
        const dy = y - agent.position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        console.log(`Agent ${agent.id} distance: ${distance}, radius: ${agent.radius}`);
        if (distance <= agent.radius) {
          clickedAgent = agent;
          break;
        }
      }
      
      if (clickedAgent) {
        console.log('Agent clicked:', clickedAgent);
        this.selectedAgent = clickedAgent;
        this.isAgentPanelVisible = true;
        
        // 绘制高亮
        this.drawAgents();
      } else {
        console.log('No agent found at click position');
      }
    },
    
    closeAgentPanel() {
      this.isAgentPanelVisible = false;
      this.selectedAgent = null;
      this.drawAgents(); // 重新绘制以移除选中状态
    },
    
    togglePanel() {
      this.isPanelVisible = !this.isPanelVisible;
    },
    
    startSimulation() {
      // 验证配置
      if (!this.canStartSimulation) return;
      
      // 关闭配置面板
      this.isPanelVisible = false;
      
      // 设置初始状态
      this.currentRound = 1;
      this.currentStage = 1;
      this.isSimulationRunning = true;
      
      // 生成Agent实例
      this.generateSimulationAgents();
      
      // 打印调试信息
      console.log(`Generated ${this.simulationAgents.length} agents for simulation`);
      
      // 设置模拟计时器，每2秒更新一轮
      this.simulationInterval = setInterval(() => {
        if (this.isSimulationRunning) {
          this.updateSimulation();
        }
      }, 2000);
      
      console.log('Starting simulation with:', {
        agents: this.agents,
        rounds: this.totalRounds
      });
    },
    
    updateSimulation() {
      // 更新轮数
      this.currentRound++;
      
      // 随机移动Agent
      this.simulationAgents.forEach(agent => {
        // 生成随机移动方向和距离
        const angle = Math.random() * Math.PI * 2;
        const distance = Math.random() * 30;
        
        // 更新位置
        agent.position.x += Math.cos(angle) * distance;
        agent.position.y += Math.sin(angle) * distance;
        
        // 确保不超出画布边界
        agent.position.x = Math.max(agent.radius, Math.min(this.canvas.width - agent.radius, agent.position.x));
        agent.position.y = Math.max(agent.radius, Math.min(this.canvas.height - agent.radius, agent.position.y));
        
        // 随机更新当前动作
        if (Math.random() > 0.7) {
          agent.currentAction = ['Moving', 'Searching', 'Interacting'][Math.floor(Math.random() * 3)];
        }
      });
      
      // 重新绘制
      this.drawAgents();
      
      // 如果已经达到最大轮数，结束模拟
      if (this.currentRound >= this.totalRounds) {
        this.isSimulationRunning = false;
        this.currentStage = 2; // 切换到结果分析阶段
        clearInterval(this.simulationInterval);
        this.simulationInterval = null;
      }
    },
    
    toggleSimulation() {
      this.isSimulationRunning = !this.isSimulationRunning;
      
      if (this.isSimulationRunning) {
        console.log('Resuming simulation');
      } else {
        console.log('Pausing simulation');
      }
    },
    
    resetSimulation() {
      // 重置模拟状态
      this.currentRound = 0;
      this.currentStage = 0;
      this.isSimulationRunning = false;
      this.hasGeneratedMap = false;
      this.simulationAgents = [];
      this.selectedAgent = null;
      this.isAgentPanelVisible = false;
      
      // 清除模拟计时器
      if (this.simulationInterval) {
        clearInterval(this.simulationInterval);
        this.simulationInterval = null;
      }
      
      // 重新绘制空白画布
      this.drawEmptyCanvas();
      
      // 显示配置面板
      this.isPanelVisible = true;
    },
    
    // 添加一个测试方法，绘制一个示例Agent
    testDrawAgent() {
      if (!this.ctx) return;
      
      console.log('Drawing test agent');
      // 创建一个测试Agent
      const testAgent = {
        id: 'test-1',
        name: 'Test Agent',
        type: 'Test',
        color: '#FF5722',
        position: { x: this.canvas.width / 2, y: this.canvas.height / 2 },
        radius: 20,
        status: 'Active',
        currentAction: 'Testing',
        interactions: [
          {
            round: 1,
            query: 'Test query?',
            response: 'Test response'
          }
        ]
      };
      
      // 添加到Agent列表
      this.simulationAgents.push(testAgent);
      
      // 绘制Agent
      this.ctx.beginPath();
      this.ctx.arc(testAgent.position.x, testAgent.position.y, testAgent.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = testAgent.color;
      this.ctx.fill();
      
      // 绘制边框
      this.ctx.strokeStyle = '#fff';
      this.ctx.lineWidth = 2;
      this.ctx.stroke();
      
      console.log('Test agent drawn at', testAgent.position);
    },
    // 添加方法，在模拟完成时导航回仪表板
    finishSimulation() {
      if (this.simulationComplete) {
        this.$router.push('/');
      }
    }
  }
}
</script>

<style scoped>
/* 修复滚动条问题 */
.simulation-view {
  display: flex;
  height: calc(100vh - 60px); /* 减去顶部导航栏的高度 */
  width: 100vw;
  overflow: hidden;
  position: relative;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
  max-height: 100vh;
  box-sizing: border-box;
}

.simulation-canvas {
  flex: 1;
  width: 100%;
  display: block;
}

.simulation-toolbar {
  position: relative;
  top: 0;
  left: 0;
  right: 0;
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 10;
  height: auto;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 24px;
}

.control-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: none;
  background-color: var(--accent-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.control-btn.active {
  background-color: #f44336;
}

.reset-btn {
  background-color: var(--secondary-color);
}

.reset-btn:hover {
  opacity: 0.9;
}

.control-btn:hover {
  opacity: 0.9;
}

.toggle-day-night {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  color: var(--text-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.toggle-day-night:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.current-stage, .rounds-info {
  font-size: 14px;
  color: var(--text-color);
}

/* 表单样式修改为垂直布局 */
.form-group.vertical {
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 20px;
}

.form-group.vertical label {
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group.vertical .input-control {
  width: 100%;
}

.agent-quantity.vertical {
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.quantity-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Agent详情面板 */
.agent-detail-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background-color: white;
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease, opacity 0.3s ease;
  display: flex;
  flex-direction: column;
  z-index: 1000; /* 确保在最上层 */
  opacity: 0;
}

.agent-detail-panel.show {
  transform: translateX(0);
  opacity: 1;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.agent-header .agent-color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.agent-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.agent-stats {
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.stat-label {
  font-weight: 500;
  color: #666;
}

.stat-value {
  color: #333;
}

.agent-interaction h4 {
  margin: 20px 0 15px;
  font-size: 16px;
  color: #333;
}

.interaction-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.interaction-item {
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 12px;
}

.interaction-time {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.interaction-content {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 5px;
}

.dark-theme .agent-detail-panel {
  background-color: #1e1e1e;
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.3);
}

.dark-theme .agent-header {
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.dark-theme .agent-header h3 {
  color: #eee;
}

.dark-theme .stat-item {
  border-bottom-color: rgba(255, 255, 255, 0.05);
}

.dark-theme .stat-label {
  color: #aaa;
}

.dark-theme .stat-value {
  color: #ddd;
}

.dark-theme .agent-interaction h4 {
  color: #eee;
}

.dark-theme .interaction-item {
  background-color: #2a2a2a;
}

.dark-theme .interaction-time {
  color: #aaa;
}

/* 其他现有样式保持不变 */
.config-panel {
  position: absolute;
  top: 0;
  left: 0;
  width: 380px;
  height: 100%;
  background-color: white;
  box-shadow: 5px 0 15px rgba(0, 0, 0, 0.1);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.config-panel.show {
  transform: translateX(0);
}

.panel-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.panel-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.primary-btn, .secondary-btn {
  padding: 10px 20px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.primary-btn {
  background-color: #4170F3;
  color: white;
  flex: 3;
}

.primary-btn:hover {
  background-color: #3461e0;
}

.primary-btn:disabled {
  background-color: #b1c4f7;
  cursor: not-allowed;
}

.secondary-btn {
  background-color: #e0e0e0;
  color: #333;
  flex: 2;
}

.secondary-btn:hover {
  background-color: #d5d5d5;
}

.config-section {
  margin-bottom: 25px;
}

.config-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.form-group {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.form-group label {
  flex: 1;
  font-size: 14px;
  color: #555;
}

.input-control {
  flex: 2;
}

.input-control input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.map-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}

.map-btn {
  padding: 8px 16px;
  border-radius: 4px;
  background-color: var(--accent-color);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  align-self: flex-start;
}

.map-btn:hover {
  opacity: 0.9;
}

.map-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #f44336;
  margin-top: 5px;
}

.map-status.success {
  color: #4CAF50;
}

.map-status i {
  font-size: 14px;
}

.agent-list {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f9f9f9;
  padding: 12px 15px;
  border-radius: 8px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.agent-name {
  font-size: 14px;
  color: #333;
}

.agent-quantity {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-quantity label {
  font-size: 13px;
  color: #666;
}

.agent-quantity input {
  width: 60px;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
}

.max-info {
  font-size: 13px;
  color: #888;
}

.no-agents {
  color: #888;
  font-style: italic;
  padding: 15px 0;
}

.floating-btn {
  position: absolute;
  bottom: 80px;
  left: 20px;
  padding: 10px 20px;
  border-radius: 30px;
  background-color: #4170F3;
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  z-index: 90;
}

.floating-btn:hover {
  background-color: #3461e0;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

/* Dark theme support */
.dark-theme .config-panel {
  background-color: #1e1e1e;
  box-shadow: 5px 0 15px rgba(0, 0, 0, 0.3);
}

.dark-theme .panel-header {
  border-bottom-color: #333;
}

.dark-theme .panel-footer {
  border-top-color: #333;
}

.dark-theme .panel-header h2 {
  color: #eee;
}

.dark-theme .close-btn {
  color: #aaa;
}

.dark-theme .close-btn:hover {
  color: #eee;
}

.dark-theme .config-section h3 {
  color: #eee;
  border-bottom-color: #444;
}

.dark-theme .form-group label {
  color: #ddd;
}

.dark-theme .input-control input {
  background-color: #333;
  border-color: #444;
  color: #eee;
}

.dark-theme .agent-item {
  background-color: #2a2a2a;
}

.dark-theme .agent-name {
  color: #eee;
}

.dark-theme .agent-quantity label {
  color: #bbb;
}

.dark-theme .max-info {
  color: #aaa;
}

.dark-theme .current-stage, 
.dark-theme .rounds-info {
  color: #eee;
}

.dark-theme .secondary-btn {
  background-color: #444;
  color: #eee;
}

.dark-theme .secondary-btn:hover {
  background-color: #555;
}

.dark-theme .no-agents {
  color: #aaa;
}

@media (max-width: 768px) {
  .config-panel, .agent-detail-panel {
    width: 300px;
  }
  
  .panel-footer {
    flex-direction: column;
  }
  
  .primary-btn, .secondary-btn {
    width: 100%;
  }
}

/* 添加调试信息样式 */
.debug-info {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  z-index: 10;
}

.simulation-footer {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.complete-btn {
  padding: 12px 24px;
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.complete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}
</style> 