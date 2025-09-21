<template>
  <div class="data-transform-container">
    <div class="data-panel">
      <h2>Original Data</h2>
      <div class="data-content">
        <pre>{{ JSON.stringify(originalData, null, 2) }}</pre>
      </div>
    </div>
    <div class="data-panel">
      <h2>Transformed Data</h2>
      <div class="data-content">
        <pre>{{ JSON.stringify(transformedData, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import workflowData from '../assets/js/workflow_data.json'
import dataService from '../utils/dataService'

export default {
  name: 'DataTransformView',
  data() {
    return {
      originalData: {},
      transformedData: {
        nodes: [],
        links: []
      }
    }
  },
  created() {
    // 获取原始数据（优先使用缓存）
    const cachedOriginalData = dataService.getOriginalData()
    if (cachedOriginalData) {
      this.originalData = cachedOriginalData
    } else {
      // 没有缓存就使用模拟数据
      this.originalData = workflowData
      // 保存到数据服务
      dataService.setOriginalData(this.originalData)
    }
    
    // 获取转换后的数据（优先使用缓存）
    const cachedTransformedData = dataService.getTransformedData()
    if (cachedTransformedData) {
      this.transformedData = cachedTransformedData
    } else {
      // 如果没有缓存，执行转换
      this.transformData()
    }
  },
  methods: {
    transformData() {
      // 使用数据服务的转换方法
      this.transformedData = dataService.transformWorkflowData(this.originalData)
      
      // 保存转换后的数据到数据服务
      dataService.setTransformedData(this.transformedData)
    }
  }
}
</script>

<style scoped>
.data-transform-container {
  display: flex;
  width: 100%;
  height: 100vh;
}

.data-panel {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  border-right: 1px solid var(--border-color, #ccc);
  background-color: var(--bg-color, #ffffff);
}

.data-panel:last-child {
  border-right: none;
}

.data-content {
  height: calc(100vh - 80px);
  overflow-y: auto;
  background-color: var(--input-bg, #f5f5f5);
  border-radius: 6px;
  padding: 15px;
  font-family: monospace;
  font-size: 14px;
  color: var(--text-color, #333333);
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: var(--text-color, #333333);
}

pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style> 