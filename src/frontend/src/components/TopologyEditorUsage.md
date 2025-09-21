# TopologyEditor 组件使用指南

TopologyEditor 是一个功能强大的拓扑图编辑器组件，支持三种不同的工作模式：预览模式、工作流编辑模式和代码编辑模式。

## 组件特性

- **预览模式**：只能查看拓扑图，不能进行编辑操作
- **工作流模式**：可以添加/编辑节点和连线，支持JSON代码编辑
- **代码模式**：可以编辑节点中的code字段，支持JSON代码编辑

## 引入方式

```javascript
import TopologyEditor from '@/components/TopologyEditor.vue';
```

## 属性说明

| 属性名 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| editorType | String | 'workflow' | 编辑器模式，可选值: 'preview', 'workflow', 'code' |
| isDarkMode | Boolean | true | 是否使用暗色主题 |
| initialTopology | Object | null | 初始拓扑数据 |
| actionsData | Object | {} | 动作数据 |
| eventsData | Object | {} | 事件数据 |
| jsonFiles | Array | [] | JSON文件路径数组 |
| agentTypes | Array | [] | 代理类型数组 |
| codeData | Object | {} | code字段数据 |

## 使用示例

### 预览模式

适用于只需要展示工作流而不需要编辑的场景。

```vue
<template>
  <div class="preview-container">
    <TopologyEditor
      editorType="preview"
      :initialTopology="topologyData"
      :isDarkMode="isDarkTheme"
    />
  </div>
</template>

<script>
import TopologyEditor from '@/components/TopologyEditor.vue';

export default {
  components: {
    TopologyEditor
  },
  data() {
    return {
      isDarkTheme: true,
      topologyData: {
        nodes: [
          { id: 1, label: '节点1', agentType: 'Agent1', color: '#ff0000' },
          { id: 2, label: '节点2', agentType: 'Agent2', color: '#00ff00' }
        ],
        links: [
          { source: 1, target: 2, name: '连接', info: '节点1到节点2的连接' }
        ]
      }
    };
  }
}
</script>
```

### 工作流编辑模式

适用于需要编辑工作流结构的场景，可以添加/编辑节点和连线。

```vue
<template>
  <div class="workflow-editor">
    <TopologyEditor
      editorType="workflow"
      :initialTopology="topologyData"
      :agentTypes="agentTypes"
      :isDarkMode="isDarkTheme"
      @save="handleSave"
    />
  </div>
</template>

<script>
import TopologyEditor from '@/components/TopologyEditor.vue';

export default {
  components: {
    TopologyEditor
  },
  data() {
    return {
      isDarkTheme: true,
      agentTypes: [
        { id: 1, name: 'Agent1', description: '代理类型1' },
        { id: 2, name: 'Agent2', description: '代理类型2' }
      ],
      topologyData: {
        nodes: [],
        links: []
      }
    };
  },
  methods: {
    handleSave(data) {
      console.log('保存的拓扑数据:', data);
      // 处理保存逻辑
    }
  }
}
</script>
```

### 代码编辑模式

适用于需要编辑节点代码的场景，可以修改节点中的code字段。

```vue
<template>
  <div class="code-editor">
    <TopologyEditor
      editorType="code"
      :initialTopology="topologyData"
      :codeData="codeData"
      :isDarkMode="isDarkTheme"
      @save="handleSave"
    />
  </div>
</template>

<script>
import TopologyEditor from '@/components/TopologyEditor.vue';

export default {
  components: {
    TopologyEditor
  },
  data() {
    return {
      isDarkTheme: true,
      codeData: {
        // 代码数据
        "initFunction": "function init() { console.log('初始化'); }",
        "processData": "function process(data) { return data.map(item => item * 2); }"
      },
      topologyData: {
        nodes: [
          { 
            id: 1, 
            label: '节点1', 
            agentType: 'Agent1', 
            color: '#ff0000',
            code: {
              "initFunction": "function init() { console.log('初始化'); }",
              "processData": "function process(data) { return data.map(item => item * 2); }"
            }
          }
        ],
        links: []
      }
    };
  },
  methods: {
    handleSave(data) {
      console.log('保存的代码数据:', data);
      // 处理保存逻辑
    }
  }
}
</script>
```

## 注意事项

1. 组件使用了ECharts库，确保项目中已安装ECharts依赖
2. 预览模式下不允许任何编辑操作
3. 工作流模式下，可以添加/编辑节点和连线，也可以切换到JSON编辑模式
4. 代码模式下，可以编辑节点中的code字段，也可以切换到JSON编辑模式
5. 编辑错误的JSON不能提交，但可以使用还原按钮恢复原始数据 