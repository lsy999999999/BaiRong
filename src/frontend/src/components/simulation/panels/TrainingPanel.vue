<template>
  <div class="training-panel">
    <h2>Model Training Panel</h2>
    <div class="panel-content">
      <!-- 顶部按钮区域 -->
      <div class="button-group">
        <el-button type="primary" @click="showModelSelectDialog">
          Select Model
        </el-button>
        <el-button type="primary" @click="showTrainingMethodDialog">
          Training Method
        </el-button>
        <el-button type="primary" @click="showDataSelectDialog">
          Select Data
        </el-button>
        <el-button type="primary" @click="showConfigDialog">
          Model Config
        </el-button>
        <el-button type="success" @click="startTraining">
          Start Training
        </el-button>
      </div>
      
      <!-- 训练过程内容区域 -->
      <div class="training-content">
        <!-- 第一行：训练日志区域 -->
        <div class="training-logs-row">
          <div class="training-block">
            <h3>Model Parameters</h3>
            <div class="log-container">
              <div v-for="(log, index) in modelParamLogs" :key="'param-'+index" class="log-item">
                {{ log }}
              </div>
            </div>
          </div>
          <div class="training-block">
            <h3>Training Progress</h3>
            <div class="log-container">
              <div v-for="(log, index) in trainingProgressLogs" :key="'progress-'+index" class="log-item">
                {{ log }}
              </div>
            </div>
          </div>
          <div class="training-block">
            <h3>Performance Metrics</h3>
            <div class="log-container">
              <div v-for="(log, index) in performanceLogs" :key="'perf-'+index" class="log-item">
                {{ log }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 第二行：图表区域 -->
        <div class="charts-row">
          <div class="chart-block">
            <h3>Loss Function</h3>
            <div ref="lossChart" class="chart-container"></div>
          </div>
          <div class="chart-block">
            <h3>Accuracy</h3>
            <div ref="accuracyChart" class="chart-container"></div>
          </div>
          <div class="chart-block">
            <h3>Learning Rate</h3>
            <div ref="learningRateChart" class="chart-container"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 模型选择对话框 -->
    <div class="modal-overlay" v-if="modelDialogVisible" @click.self="modelDialogVisible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Select Training Model</h3>
          <button class="close-btn" @click="modelDialogVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        
        <el-form :model="trainingConfig" label-width="120px" class="modal-form">
          <div class="form-group">
            <el-form-item label="Model Type">
              <el-select v-model="trainingConfig.modelType" placeholder="Please select model type">
                <el-option label="Convolutional Neural Network" value="cnn" />
                <el-option label="Recurrent Neural Network" value="rnn" />
                <el-option label="Transformer" value="transformer" />
                <el-option label="LSTM" value="lstm" />
                <el-option label="GRU" value="gru" />
              </el-select>
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button @click="modelDialogVisible = false" class="cancel-btn">Cancel</el-button>
            <el-button type="primary" @click="saveModelConfig" class="save-btn">Confirm</el-button>
          </div>
        </el-form>
      </div>
    </div>
    
    <!-- 训练方式对话框 -->
    <div class="modal-overlay" v-if="methodDialogVisible" @click.self="methodDialogVisible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Select Training Method</h3>
          <button class="close-btn" @click="methodDialogVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        
        <el-form :model="trainingConfig" label-width="120px" class="modal-form">
          <div class="form-group">
            <el-form-item label="Training Method">
              <el-select v-model="trainingConfig.trainingMethod" placeholder="Please select training method">
                <el-option label="Supervised Learning" value="supervised" />
                <el-option label="Unsupervised Learning" value="unsupervised" />
                <el-option label="Semi-supervised Learning" value="semi-supervised" />
                <el-option label="Transfer Learning" value="transfer" />
                <el-option label="Reinforcement Learning" value="reinforcement" />
              </el-select>
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button @click="methodDialogVisible = false" class="cancel-btn">Cancel</el-button>
            <el-button type="primary" @click="saveMethodConfig" class="save-btn">Confirm</el-button>
          </div>
        </el-form>
      </div>
    </div>
    
    <!-- 数据选择对话框 -->
    <div class="modal-overlay" v-if="dataDialogVisible" @click.self="dataDialogVisible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Select Training Data</h3>
          <button class="close-btn" @click="dataDialogVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        
        <el-form :model="trainingConfig" label-width="120px" class="modal-form">
          <div class="form-group">
            <el-form-item label="Dataset">
              <el-select v-model="trainingConfig.dataset" placeholder="Please select dataset">
                <el-option label="MNIST" value="mnist" />
                <el-option label="CIFAR-10" value="cifar10" />
                <el-option label="ImageNet" value="imagenet" />
                <el-option label="Custom Dataset" value="custom" />
              </el-select>
            </el-form-item>
          </div>
          
          <div class="form-group">
            <el-form-item label="Train/Test Split">
              <el-slider v-model="trainingConfig.trainTestSplit" :format-tooltip="formatSplitTooltip" />
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button @click="dataDialogVisible = false" class="cancel-btn">Cancel</el-button>
            <el-button type="primary" @click="saveDataConfig" class="save-btn">Confirm</el-button>
          </div>
        </el-form>
      </div>
    </div>
    
    <!-- 模型配置对话框 -->
    <div class="modal-overlay" v-if="configDialogVisible" @click.self="configDialogVisible = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Model Configuration</h3>
          <button class="close-btn" @click="configDialogVisible = false">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        
        <el-form :model="trainingConfig" label-width="120px" class="modal-form">
          <div class="form-group">
            <el-form-item label="Batch Size">
              <el-input-number v-model="trainingConfig.batchSize" :min="1" :max="1024" />
            </el-form-item>
          </div>
          
          <div class="form-group">
            <el-form-item label="Learning Rate">
              <el-input-number v-model="trainingConfig.learningRate" :precision="4" :step="0.001" :min="0.0001" :max="1" />
            </el-form-item>
          </div>
          
          <div class="form-group">
            <el-form-item label="Epochs">
              <el-input-number v-model="trainingConfig.epochs" :min="1" :max="1000" />
            </el-form-item>
          </div>
          
          <div class="form-group">
            <el-form-item label="Optimizer">
              <el-select v-model="trainingConfig.optimizer" placeholder="Please select optimizer">
                <el-option label="Adam" value="adam" />
                <el-option label="SGD" value="sgd" />
                <el-option label="RMSprop" value="rmsprop" />
                <el-option label="AdaGrad" value="adagrad" />
              </el-select>
            </el-form-item>
          </div>
          
          <div class="form-actions">
            <el-button @click="configDialogVisible = false" class="cancel-btn">Cancel</el-button>
            <el-button type="primary" @click="saveTrainingConfig" class="save-btn">Confirm</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { Close } from '@element-plus/icons-vue';

export default {
  name: 'TrainingPanel',
  components: {
    Close
  },
  data() {
    return {
      // 对话框显示控制
      modelDialogVisible: false,
      methodDialogVisible: false,
      dataDialogVisible: false,
      configDialogVisible: false,
      
      // 训练配置
      trainingConfig: {
        modelType: 'cnn',
        trainingMethod: 'supervised',
        dataset: 'mnist',
        trainTestSplit: 80,
        batchSize: 32,
        learningRate: 0.001,
        epochs: 10,
        optimizer: 'adam'
      },
      
      // 日志数据
      modelParamLogs: [
        'Model Type: Convolutional Neural Network (CNN)',
        'Parameter Count: 1,254,322',
        'Layer Count: 15',
        'Input Dimensions: [224, 224, 3]',
        'Output Dimensions: [1000]',
        'Activation Function: ReLU',
        'Regularization: L2(0.001)',
        'Initialization: Kaiming',
      ],
      
      trainingProgressLogs: [
        'Initializing training environment...',
        'Loading dataset: MNIST...',
        'Data preprocessing complete',
        'Starting training: Epoch 1/10',
        'Progress: 100/500 batches (20%)',
        'Progress: 200/500 batches (40%)',
        'Progress: 300/500 batches (60%)',
        'Progress: 400/500 batches (80%)',
      ],
      
      performanceLogs: [
        'GPU Utilization: 87%',
        'Memory Usage: 4.2GB/8GB',
        'Time per batch: 0.25 seconds',
        'Estimated time remaining: 15 minutes',
        'Current loss: 0.342',
        'Current accuracy: 91.7%',
        'Validation loss: 0.415',
        'Validation accuracy: 89.2%',
      ],
      
      // 图表实例
      lossChart: null,
      accuracyChart: null,
      learningRateChart: null,
      
      // 模拟数据
      epochData: [1, 2, 3, 4, 5, 6, 7, 8],
      lossData: [2.5, 1.8, 1.4, 1.0, 0.85, 0.7, 0.6, 0.55],
      accuracyData: [0.4, 0.55, 0.65, 0.75, 0.8, 0.84, 0.86, 0.87],
      learningRateData: [0.001, 0.001, 0.0009, 0.0008, 0.0007, 0.0005, 0.0003, 0.0001]
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initCharts();
    });
  },
  methods: {
    // 初始化图表
    initCharts() {
      // 损失函数图表
      this.lossChart = echarts.init(this.$refs.lossChart);
      this.renderLossChart();
      
      // 准确率图表
      this.accuracyChart = echarts.init(this.$refs.accuracyChart);
      this.renderAccuracyChart();
      
      // 学习率图表
      this.learningRateChart = echarts.init(this.$refs.learningRateChart);
      this.renderLearningRateChart();
      
      // 响应窗口大小变化
      window.addEventListener('resize', this.resizeCharts);
    },
    
    // 渲染损失函数图表
    renderLossChart() {
      const option = {
        title: {
          text: 'Training Loss'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: this.epochData,
          name: 'Epoch'
        },
        yAxis: {
          type: 'value',
          name: 'Loss'
        },
        series: [{
          data: this.lossData,
          type: 'line',
          smooth: true,
          name: 'Training Loss'
        }]
      };
      this.lossChart.setOption(option);
    },
    
    // 渲染准确率图表
    renderAccuracyChart() {
      const option = {
        title: {
          text: 'Training Accuracy'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: this.epochData,
          name: 'Epoch'
        },
        yAxis: {
          type: 'value',
          name: 'Accuracy',
          axisLabel: {
            formatter: '{value}%'
          },
          max: 1,
          min: 0
        },
        series: [{
          data: this.accuracyData,
          type: 'line',
          smooth: true,
          name: 'Training Accuracy'
        }]
      };
      this.accuracyChart.setOption(option);
    },
    
    // 渲染学习率图表
    renderLearningRateChart() {
      const option = {
        title: {
          text: 'Learning Rate'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: this.epochData,
          name: 'Epoch'
        },
        yAxis: {
          type: 'value',
          name: 'Learning Rate'
        },
        series: [{
          data: this.learningRateData,
          type: 'line',
          step: 'end',
          name: 'Learning Rate'
        }]
      };
      this.learningRateChart.setOption(option);
    },
    
    // 重新调整图表大小
    resizeCharts() {
      this.lossChart && this.lossChart.resize();
      this.accuracyChart && this.accuracyChart.resize();
      this.learningRateChart && this.learningRateChart.resize();
    },
    
    // 显示模型选择对话框
    showModelSelectDialog() {
      this.modelDialogVisible = true;
    },
    
    // 显示训练方式对话框
    showTrainingMethodDialog() {
      this.methodDialogVisible = true;
    },
    
    // 显示数据选择对话框
    showDataSelectDialog() {
      this.dataDialogVisible = true;
    },
    
    // 显示配置对话框
    showConfigDialog() {
      this.configDialogVisible = true;
    },
    
    // 开始训练
    startTraining() {
      this.$message.success('Model training started');
      // 这里可以添加实际训练逻辑
      this.simulateTraining();
    },
    
    // 保存模型配置
    saveModelConfig() {
      this.modelDialogVisible = false;
      this.$message.success('Model selection updated');
    },
    
    // 保存训练方式配置
    saveMethodConfig() {
      this.methodDialogVisible = false;
      this.$message.success('Training method updated');
    },
    
    // 保存数据配置
    saveDataConfig() {
      this.dataDialogVisible = false;
      this.$message.success('Training data updated');
    },
    
    // 保存训练配置
    saveTrainingConfig() {
      this.configDialogVisible = false;
      this.$message.success('Training configuration updated');
    },
    
    // 格式化分割比例提示
    formatSplitTooltip(val) {
      return `Training:${val}% / Validation:${100-val}%`;
    },
    
    // 模拟训练过程
    simulateTraining() {
      // 清空现有日志
      this.trainingProgressLogs = ['Initializing training environment...'];
      this.performanceLogs = ['Preparing evaluation metrics...'];
      
      // 模拟训练进度更新
      setTimeout(() => {
        this.trainingProgressLogs.push('Loading dataset: ' + this.trainingConfig.dataset + '...');
        this.performanceLogs.push('GPU Utilization: 45%');
      }, 1000);
      
      setTimeout(() => {
        this.trainingProgressLogs.push('Data preprocessing complete');
        this.trainingProgressLogs.push('Starting training: Epoch 1/' + this.trainingConfig.epochs);
        this.performanceLogs.push('Memory Usage: 2.8GB/8GB');
        this.performanceLogs.push('Initial loss: 2.54');
      }, 2000);
      
      // 模拟更多训练日志和指标更新...
      let epochCounter = 1;
      let batchCounter = 0;
      
      const trainInterval = setInterval(() => {
        batchCounter += 100;
        const totalBatches = 500;
        
        if (batchCounter <= totalBatches) {
          this.trainingProgressLogs.push(`Progress: ${batchCounter}/${totalBatches} batches (${Math.floor(batchCounter/totalBatches*100)}%)`);
          this.performanceLogs.push(`Current loss: ${(2.5 - (batchCounter/totalBatches)*0.7).toFixed(3)}`);
          this.performanceLogs.push(`Current accuracy: ${(40 + (batchCounter/totalBatches)*30).toFixed(1)}%`);
        } else {
          epochCounter++;
          batchCounter = 0;
          
          if (epochCounter <= this.trainingConfig.epochs) {
            this.trainingProgressLogs.push(`Completed Epoch ${epochCounter-1}/${this.trainingConfig.epochs}`);
            this.trainingProgressLogs.push(`Starting training: Epoch ${epochCounter}/${this.trainingConfig.epochs}`);
            
            // 更新图表数据
            this.updateChartData(epochCounter);
          } else {
            this.trainingProgressLogs.push('Training complete!');
            this.performanceLogs.push('Final loss: 0.48');
            this.performanceLogs.push('Final accuracy: 92.4%');
            clearInterval(trainInterval);
          }
        }
        
        // 保持日志不超过8条
        if (this.trainingProgressLogs.length > 8) {
          this.trainingProgressLogs.shift();
        }
        if (this.performanceLogs.length > 8) {
          this.performanceLogs.shift();
        }
      }, 1000);
    },
    
    // 更新图表数据
    updateChartData(epoch) {
      if (epoch > this.epochData.length) {
        this.epochData.push(epoch);
        const newLoss = Math.max(0.4, this.lossData[this.lossData.length-1] * 0.9);
        this.lossData.push(newLoss);
        
        const newAccuracy = Math.min(0.95, this.accuracyData[this.accuracyData.length-1] * 1.05);
        this.accuracyData.push(newAccuracy);
        
        const newLearningRate = Math.max(0.0001, this.learningRateData[this.learningRateData.length-1] * 0.85);
        this.learningRateData.push(newLearningRate);
        
        // 更新图表
        this.renderLossChart();
        this.renderAccuracyChart();
        this.renderLearningRateChart();
      }
    }
  },
  computed: {
    isDarkMode() {
      // 假设通过父组件或Vuex传递了暗色主题状态
      return document.querySelector('.simulation-layout')?.classList.contains('dark-theme') || false;
    }
  },
  beforeUnmount() {
    // 清理图表实例和事件监听
    window.removeEventListener('resize', this.resizeCharts);
    this.lossChart && this.lossChart.dispose();
    this.accuracyChart && this.accuracyChart.dispose();
    this.learningRateChart && this.learningRateChart.dispose();
  }
}
</script>

<style scoped>
/* 基础样式 */
.training-panel {
  padding: 20px;
  height: 100%;
  background-color: var(--panel-bg, #ffffff);
  transition: all 0.3s ease;
}

h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  color: var(--text-color, #333333);
}

h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.1rem;
  color: var(--text-color, #333333);
}

.panel-content {
  height: calc(100% - 60px);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 15px;
  background-color: var(--panel-bg, #f8f8f8);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

/* 按钮组样式 */
.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

/* 训练内容区域样式 */
.training-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

/* 训练日志区域 */
.training-logs-row {
  display: flex;
  gap: 15px;
  min-height: 200px;
  max-height: 40%;
}

.training-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  padding: 12px;
  overflow: hidden;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background-color: var(--input-bg, #f5f5f5);
  border-radius: 4px;
  font-family: monospace;
}

.log-item {
  padding: 3px 0;
  line-height: 1.5;
  font-size: 0.9rem;
  color: var(--text-color, #333333);
}

/* 图表区域 */
.charts-row {
  display: flex;
  gap: 15px;
  flex: 1;
  min-height: 300px;
}

.chart-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  padding: 12px;
  overflow: hidden;
}

.chart-container {
  flex: 1;
  min-height: 100px;
}

/* Element UI 组件样式 */
:deep(.el-dialog) {
  --el-dialog-bg-color: var(--card-bg, #ffffff);
  --el-dialog-border-color: var(--border-color, #e0e0e0);
}

:deep(.el-form-item__label),
:deep(.el-dialog__title) {
  color: var(--text-color, #333333);
}

:deep(.el-input__wrapper),
:deep(.el-textarea__wrapper) {
  background-color: var(--input-bg, #ffffff);
  box-shadow: 0 0 0 1px var(--border-color, #e0e0e0);
}

/* 暗色主题样式 */
.simulation-layout.dark-theme .training-panel {
  background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme h2,
.simulation-layout.dark-theme h3 {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .panel-content {
  background-color: var(--dark-panel-bg, #1a1a1a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .training-block,
.simulation-layout.dark-theme .chart-block {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .log-container {
  background-color: var(--dark-input-bg, #1e1e1e);
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .log-item {
  color: var(--dark-text-color, #dddddd);
}

.simulation-layout.dark-theme :deep(.el-dialog) {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-dialog__title),
.simulation-layout.dark-theme :deep(.el-form-item__label) {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-input__wrapper),
.simulation-layout.dark-theme :deep(.el-textarea__wrapper) {
  background-color: var(--dark-input-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
  box-shadow: 0 0 0 1px var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-input__inner),
.simulation-layout.dark-theme :deep(.el-textarea__inner) {
  background-color: var(--dark-input-bg, #2a2a2a);
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown) {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown__item) {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning):not(.el-button--danger)) {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
  color: var(--dark-text-color, #ffffff);
}

/* 响应式样式 */
@media (max-width: 768px) {
  .button-group {
    flex-direction: column;
  }
  
  .training-logs-row,
  .charts-row {
    flex-direction: column;
  }
}

/* 添加模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  width: 500px;
  max-width: 90%;
  background-color: var(--panel-bg, #ffffff);
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  color: var(--text-color, #333);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--text-color, #333);
}

.close-btn {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 18px;
  color: var(--text-secondary, #666);
  transition: color 0.3s;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  color: var(--primary-color, #409EFF);
  background-color: var(--hover-bg, rgba(64, 158, 255, 0.1));
}

.modal-form {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn {
  background-color: var(--button-bg, #f5f7fa);
  color: var(--text-color, #333);
  border: 1px solid var(--border-color, #dcdfe6);
}

.save-btn {
  background-color: var(--primary-color, #409EFF);
  color: white;
  border: none;
}

/* 暗色模式适配 */
.simulation-layout.dark-theme .modal-content {
  background-color: var(--dark-panel-bg, #1a1a1a);
  color: var(--dark-text-color, #fff);
}

.simulation-layout.dark-theme .modal-header {
  border-bottom-color: var(--dark-border-color, #333);
}

.simulation-layout.dark-theme .modal-header h3 {
  color: var(--dark-text-color, #fff);
}

.simulation-layout.dark-theme .close-btn {
  color: var(--dark-text-secondary, #aaa);
}

.simulation-layout.dark-theme .close-btn:hover {
  background-color: var(--dark-hover-bg, rgba(64, 158, 255, 0.2));
}

.simulation-layout.dark-theme .cancel-btn {
  background-color: var(--dark-button-bg, #2a2a2a);
  color: var(--dark-text-color, #fff);
  border-color: var(--dark-border-color, #444);
}
</style> 