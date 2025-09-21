/**
 * 数据服务 - 用于在组件间共享数据
 */

// 缓存数据对象
const cache = {
  originalData: null,
  transformedData: null
}

/**
 * 设置原始数据
 * @param {Object} data 原始数据对象
 */
export function setOriginalData(data) {
  cache.originalData = data
  // 同时保存到localStorage作为持久化存储
  localStorage.setItem('original_workflow_data', JSON.stringify(data))
}

/**
 * 获取原始数据
 * @returns {Object} 原始数据对象
 */
export function getOriginalData() {
  // 如果内存中没有，尝试从localStorage获取
  if (!cache.originalData) {
    const storedData = localStorage.getItem('original_workflow_data')
    if (storedData) {
      try {
        cache.originalData = JSON.parse(storedData)
      } catch (e) {
        console.error('解析缓存数据失败:', e)
      }
    }
  }
  return cache.originalData
}

/**
 * 设置转换后的数据
 * @param {Object} data 转换后的数据对象
 */
export function setTransformedData(data) {
  cache.transformedData = data
  // 同时保存到localStorage作为持久化存储
  localStorage.setItem('transformed_workflow_data', JSON.stringify(data))
}

/**
 * 获取转换后的数据
 * @returns {Object} 转换后的数据对象
 */
export function getTransformedData() {
  // 如果内存中没有，尝试从localStorage获取
  if (!cache.transformedData) {
    const storedData = localStorage.getItem('transformed_workflow_data')
    if (storedData) {
      try {
        cache.transformedData = JSON.parse(storedData)
      } catch (e) {
        console.error('解析缓存数据失败:', e)
      }
    }
  }
  return cache.transformedData
}

/**
 * 将原始工作流数据转换为echarts图表格式
 * @param {Object} originalData 原始数据
 * @returns {Object} 转换后的数据，包含nodes、links和categories
 */
export function transformWorkflowData(originalData) {
  if (!originalData || !originalData.actions || !originalData.events) {
    return { nodes: [], links: [], categories: [] }
  }

  const nodes = []
  const links = []
  const categories = []
  
  // 创建分类
  const agentTypes = Object.keys(originalData.actions)
  agentTypes.forEach((agentType, index) => {
    categories.push({
      name: agentType
    })
  })
  
  // 至少保证有一个默认分类
  if (categories.length === 0) {
    categories.push({ name: "Default" })
  }
  
  // 处理actions，将其转换为节点
  const nodePositions = {}
  let posX = -400
  let posY = -300
  let maxNodesPerRow = 5
  let nodeCount = 0
  
  agentTypes.forEach((agentType, agentIndex) => {
    originalData.actions[agentType].forEach(action => {
      // 计算节点位置，均匀分布
      const rowIndex = Math.floor(nodeCount / maxNodesPerRow)
      const colIndex = nodeCount % maxNodesPerRow
      const x = posX + colIndex * 200
      const y = posY + rowIndex * 150 + (agentIndex * 50)
      
      // 存储节点位置用于后续连线
      nodePositions[action.id.toString()] = { x, y }
      
      // 添加节点
      nodes.push({
        id: action.id.toString(),
        name: action.name,
        symbolSize: 40 + (action.description?.length || 0) / 10,
        x: x,
        y: y,
        value: 10 + (action.required_variables?.length || 0) * 5,
        category: agentIndex,
        agentType: agentType,
        description: action.description
      })
      
      nodeCount++
    })
  })
  
  // 处理events，将其转换为边
  Object.keys(originalData.events).forEach(eventId => {
    const event = originalData.events[eventId]
    links.push({
      source: event.from_action_id.toString(),
      target: event.to_action_id.toString(),
      name: event.event_name,
      value: event.event_info
    })
  })
  
  return { nodes, links, categories }
}

export default {
  setOriginalData,
  getOriginalData,
  setTransformedData,
  getTransformedData,
  transformWorkflowData
} 