<!-- start和terminate是内置的，不会体现在这里面，但是转换整理的时候需要加入，0是start,-1是terminate -->
<template>
  <div class="topology-editor-container">
    <div class="loading-overlay" v-if="loading">
      <div class="spinner"></div>
      <div class="loading-text">Generating simulation workflow...</div>
      <TipsCarousel />
    </div>

    <!-- JSON Data Overlay -->
    <div class="json-debug-overlay" v-if="showDebugOverlay">
      <div class="json-debug-panel">
        <div class="json-debug-header">
          <h3>Topology Data (JSON)</h3>
          <div class="json-debug-actions">
            <button @click="copyDebugJson" class="copy-btn">
              <i class="fa fa-copy"></i> Copy
            </button>
            <button @click="showDebugOverlay = false" class="close-btn">
              <i class="fa fa-times"></i>
            </button>
          </div>
        </div>
        <div class="json-debug-content">
          <div class="markdown-content">
            <h4>Nodes ({{ nodes.length }} total)</h4>
            <pre><code>{{ formattedNodesJson }}</code></pre>

            <h4>Links ({{ links.length }} total)</h4>
            <pre><code>{{ formattedLinksJson }}</code></pre>

            <div v-if="isolatedNodes.length > 0" class="warning-section">
              <h4>⚠️ Warning: Isolated Nodes ({{ isolatedNodes.length }})</h4>
              <ul>
                <li v-for="node in isolatedNodes" :key="node.id">
                  ID: {{ node.id }}, Name: {{ node.label }}, Type: {{ node.agentType }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="toolbar">
      <div class="tool-group">
        <button @click="addNode" class="tool-btn">
          <i class="fa fa-plus-circle"></i> Add Node
        </button>
        <button @click="startLinkCreation" class="tool-btn" :class="{ active: isAddingLink }">
          <i class="fa fa-link"></i> Connect Nodes
        </button>
        <button @click="restoreOriginalJson" class="tool-btn restore-btn">
          <i class="fa fa-undo"></i> Reset
        </button>
        <button @click="saveTopology" class="tool-btn save-btn" v-loading="nextLoading">
          <i class="fa fa-save"></i> Save & Continue
        </button>
      </div>
    </div>

    <div class="linking-status" v-if="isAddingLink">
      <span v-if="!linkSource">Please select source node</span>
      <span v-else>Please select target node</span>
      <button @click="cancelLinkCreation" class="cancel-btn">
        <i class="fa fa-times"></i> Cancel
      </button>
    </div>

    <div ref="chartContainer" class="chart-container"></div>

    <!-- 编辑器蒙版 -->
    <transition name="fade">
      <div class="editor-overlay" v-show="selectedNode || selectedLink" @click="closeAllEditors"></div>
    </transition>

    <!-- 节点编辑器 -->
    <div class="node-editor" v-show="selectedNode" :class="{ visible: selectedNode }">
      <div class="editor-header">
        <h3>Edit Node: {{ selectedNode ? selectedNode.label : "" }}</h3>
        <button @click="closeEditor" class="close-btn">
          <i class="fa fa-times"></i>
        </button>
      </div>

      <div class="editor-content">
        <div class="editor-tabs">
          <div class="tab" :class="{ active: activeNodeTab === 'form' }" @click="switchToNodeFormMode">
            Form Mode
          </div>
          <div class="tab" :class="{ active: activeNodeTab === 'json' }" @click="switchToNodeJsonMode">
            Code Mode
          </div>
        </div>

        <div v-if="activeNodeTab === 'form' && selectedNode">
          <div class="form-group" v-if="selectedNode && selectedNode.agentType !== 'EnvAgent'">
            <label for="node-id">ID</label>
            <input type="text" id="node-id" v-model="selectedNode.id" disabled />
          </div>

          <div class="form-group">
            <label for="node-label">Name</label>
            <input type="text" id="node-label" v-model="selectedNode.label"
              :disabled="selectedNode && selectedNode.agentType == 'EnvAgent'" />
          </div>

          <div class="form-group">
            <label for="node-agent">Agent Type</label>
            <input type="text" id="node-agent" v-model="selectedNode.agentType"
              :disabled="selectedNode && selectedNode.agentType == 'EnvAgent'" />
          </div>

          <div class="form-group">
            <label for="node-description">Description</label>
            <el-input type="textarea" id="node-description" v-model="selectedNode.description" :rows="3"
              placeholder="Enter node description" />
          </div>

          <div class="form-group">
            <label>Node Logic Type</label>
            <el-radio-group v-model="selectedNode.type">
              <el-radio :value="'AND'" border>AND</el-radio>
              <el-radio :value="'OR'" border>OR</el-radio>
            </el-radio-group>
          </div>

          <!-- Required Variables -->
          <div class="form-section" v-if="
            selectedNode &&
            selectedNode.required_variables &&
            selectedNode.required_variables.length > 0
          ">
            <div class="section-header">
              <h4>Required Variables</h4>
              <button @click="addVariable('required_variables')" class="add-field-btn">
                <i class="fa fa-plus"></i> Add Variable
              </button>
            </div>
            <div class="fields-grid">
              <div class="field-item" v-for="(variable, varIndex) in selectedNode.required_variables"
                :key="'req-' + varIndex">
                <div class="field-header">
                  <div class="field-header-left">
                    <label>Name</label>
                    <input type="text" class="field-name-input" v-model="variable.name" />
                  </div>
                  <div class="field-actions">
                    <button @click="removeVariable('required_variables', varIndex)" class="remove-field-btn"
                      title="Remove Variable">
                      <i class="fa fa-trash"></i>
                    </button>
                  </div>
                </div>
                <div class="field-content">
                  <div class="field-row">
                    <div class="field-column">
                      <label>Type</label>
                      <el-select v-model="variable.type" placeholder="Type" class="field-type-select">
                        <el-option label="string" value="string"></el-option>
                        <el-option label="float" value="float"></el-option>
                        <el-option label="datetime" value="datetime"></el-option>
                        <el-option label="list" value="list"></el-option>
                      </el-select>
                    </div>
                    <div class="field-column">
                      <label>Context</label>
                      <el-select v-model="variable.context" placeholder="Context" class="field-type-select">
                        <el-option label="agent" value="agent"></el-option>
                        <el-option label="env" value="env"></el-option>
                      </el-select>
                    </div>
                  </div>
                  <div class="field-row">
                    <label>Description</label>
                    <input type="text" v-model="variable.description" class="field-description-input" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Output Updates -->
          <div class="form-section" v-if="
            selectedNode &&
            selectedNode.output_updates &&
            selectedNode.output_updates.length > 0
          ">
            <div class="section-header">
              <h4>Output Updates</h4>
              <button @click="addVariable('output_updates')" class="add-field-btn">
                <i class="fa fa-plus"></i> Add Output
              </button>
            </div>

            <div class="fields-grid">
              <div class="field-item" v-for="(output, outputIndex) in selectedNode.output_updates"
                :key="'out-' + outputIndex">
                <div class="field-header">
                  <div class="field-header-left">
                    <label>Name</label>
                    <input type="text" class="field-name-input" v-model="output.name" />
                  </div>
                  <div class="field-actions">
                    <button @click="removeVariable('output_updates', outputIndex)" class="remove-field-btn"
                      title="Remove Output">
                      <i class="fa fa-trash"></i>
                    </button>
                  </div>
                </div>
                <div class="field-content">
                  <div class="field-row">
                    <div class="field-column">
                      <label>Type</label>
                      <el-select v-model="output.type" placeholder="Type" class="field-type-select">
                        <el-option label="string" value="string"></el-option>
                        <el-option label="float" value="float"></el-option>
                        <el-option label="datetime" value="datetime"></el-option>
                        <el-option label="list" value="list"></el-option>
                      </el-select>
                    </div>
                    <div class="field-column">
                      <label>Context</label>
                      <el-select v-model="output.context" placeholder="Context" class="field-type-select">
                        <el-option label="local" value="local"></el-option>
                        <el-option label="global" value="global"></el-option>
                      </el-select>
                    </div>
                  </div>
                  <div class="field-row">
                    <label>Description</label>
                    <input type="text" v-model="output.description" class="field-description-input" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="fields-section" v-if="selectedNodeFields.length">
            <h4>Event Fields</h4>
            <div class="field-item" v-for="(field, index) in selectedNodeFields" :key="index">
              <div class="field-header">
                <div class="field-header-left">
                  <label>Name</label>
                  <input type="text" class="field-name-input" v-model="field.name" disabled />
                </div>
                <div class="field-type">{{ field.type }}</div>
              </div>
              <div class="field-value">
                <label>Default Value</label>
                <input type="text" v-model="field.default_value" class="field-value-input" />
              </div>
              <div class="field-description">
                <label>Description</label>
                <input type="text" v-model="field.description" class="field-description-input" disabled />
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeNodeTab === 'json'" class="json-editor-section">
          <h4>Node Code</h4>
          <div class="json-editor">
            <!-- <textarea v-model="nodeJsonData" rows="15" placeholder="Edit node code in JSON format"
              class="json-textarea"></textarea> -->
            <Codemirror v-model="nodeJsonData"
              :extensions="isDarkMode_type ? codeMirrorExtensionsDark : codeMirrorExtensions"
              :style="{ height: '100%', border: '1px solid #ccc', fontSize: '14px' }" ref="codemirror"
              placeholder="Edit node code in JSON format" @change="onCodeChange" />
          </div>
          <div v-if="nodeJsonError" class="json-error">
            {{ nodeJsonError }}
          </div>
        </div>

        <div class="editor-actions">
          <div>
            <button @click="resetNodeChanges" class="reset-btn">
              <i class="fa fa-undo"></i> Reset
            </button>
            <button @click="applyChanges" class="primary-btn">
              <i class="fa fa-check"></i> Apply
            </button>
            <button @click="deleteNode" class="danger-btn">
              <i class="fa fa-trash"></i> Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 连线编辑器 -->
    <div class="link-editor" v-show="selectedLink" :class="{ visible: selectedLink }">
      <div class="editor-header">
        <h3>
          Edit Event:
          {{
            originalEvent
              ? originalEvent.event_name
              : selectedLink
                ? selectedLink.name
                : ""
          }}
        </h3>
        <button @click="closeLinkEditor" class="close-btn">
          <i class="fa fa-times"></i>
        </button>
      </div>

      <div class="editor-content">
        <div class="editor-tabs">
          <div class="tab" :class="{ active: activeTab === 'form' }" @click="switchToFormMode">
            Form Mode
          </div>
          <div class="tab" :class="{ active: activeTab === 'json' }" @click="switchToJsonMode">
            Code Mode
          </div>
        </div>

        <div class="connection-info" v-if="activeTab === 'form' && selectedLink">
          <div class="connection-label">
            <strong>From Action:</strong>
            <el-select v-model="selectedLink.source" placeholder="Select From Action" @change="updateSourceNode"
              style="width: 100%; margin-top: 5px">
              <el-option v-for="node in nodes" :key="node.id" :label="`${node.label || node.name} (${node.agentType})`"
                :value="node.id">
              </el-option>
            </el-select>
          </div>
          <div class="connection-label">
            <strong>To Action:</strong>
            <el-select v-model="selectedLink.target" placeholder="Select To Action" @change="updateTargetNode"
              style="width: 100%; margin-top: 5px">
              <el-option v-for="node in nodes" :key="node.id" :label="`${node.label || node.name} (${node.agentType})`"
                :value="node.id">
              </el-option>
            </el-select>
          </div>
        </div>

        <!-- 优化布局为每行一个字段 -->
        <div class="form-layout" v-if="activeTab === 'form' && selectedLink">
          <div class="form-group">
            <label for="link-name">Event Name</label>
            <input type="text" id="link-name" v-model="selectedLink.name" @input="updateJsonFromForm" />
          </div>
          <div class="form-group">
            <label for="link-info">Description</label>
            <textarea id="link-info" v-model="selectedLink.info" @input="updateJsonFromForm" rows="2"></textarea>
          </div>
        </div>

        <div v-if="activeTab === 'form' && selectedLink" class="fields-section">
          <div class="section-header">
            <h4>Event Fields</h4>
            <button @click="addNewField" class="add-field-btn">
              <i class="fa fa-plus"></i> Add Field
            </button>
          </div>
          <div v-if="!linkFields || linkFields.length === 0" class="no-fields">
            No editable fields available
          </div>
          <div v-else class="fields-grid">
            <div class="field-item" v-for="(field, index) in linkFields" :key="index">
              <div class="field-header">
                <div class="field-header-left">
                  <label>Name</label>
                  <input type="text" class="field-name-input" v-model="field.name" />
                </div>
                <div class="field-actions">
                  <button @click="removeField(index)" class="remove-field-btn" title="Remove Field">
                    <i class="fa fa-trash"></i>
                  </button>
                </div>
              </div>
              <div class="field-content">
                <div class="field-row">
                  <div class="field-column">
                    <label>Type</label>
                    <el-select v-model="field.type" placeholder="Type" class="field-type-select"
                      @change="updateJsonFromForm">
                      <el-option label="string" value="string"></el-option>
                      <el-option label="float" value="float"></el-option>
                      <el-option label="datetime" value="datetime"></el-option>
                      <el-option label="list" value="list"></el-option>
                    </el-select>
                  </div>
                  <div class="field-column">
                    <label>Default Value</label>
                    <input type="text" v-model="field.default_value" class="field-value-input"
                      @input="updateJsonFromForm" />
                  </div>
                </div>
                <div class="field-row">
                  <label>Description</label>
                  <input type="text" v-model="field.description" class="field-description-input"
                    @input="updateJsonFromForm" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'json' && selectedLink" class="json-editor-section">
          <h4>Event Code</h4>
          <div class="json-editor">
            <textarea v-model="linkJsonData" rows="15" placeholder="Edit event code in JSON format"
              class="json-textarea"></textarea>
          </div>
          <div v-if="jsonError" class="json-error">
            {{ jsonError }}
          </div>
        </div>

        <div class="editor-actions" v-if="selectedLink">
          <div>
            <button @click="resetLinkChanges" class="reset-btn">
              <i class="fa fa-undo"></i> Reset
            </button>
            <button @click="applyLinkChanges" class="primary-btn">
              <i class="fa fa-check"></i> Apply
            </button>
            <button @click="deleteLink" class="danger-btn">
              <i class="fa fa-trash"></i> Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// import workflow222 from '../assets/js/workflow_data.json'
import * as echarts from "echarts";
import axios from "axios";
import { Codemirror } from 'vue-codemirror'
import { json } from '@codemirror/lang-json'
import { oneDark } from '@codemirror/theme-one-dark'
import { githubLight } from "@uiw/codemirror-theme-github";
import { emitter } from '../layouts/ProgressLayoutWrapper.vue';
import TipsCarousel from './TipsCarousel.vue';
import { ElMessageBox } from "element-plus";

export default {
  name: "TopologyEditor",
  components: {
    Codemirror,
    TipsCarousel
  },
  props: {
    isDarkMode: {
      type: Boolean,
      default: true,
    },
    actionsData: {
      type: Object,
      default: () => ({}),
    },
    eventsData: {
      type: Object,
      default: () => ({}),
    },
    jsonFiles: {
      type: Array,
      default: () => [],
    },
    agentTypes: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      nextLoading: false,
      workflow: {},
      loading: true,
      chart: null,
      chartOption: null,
      selectedNode: null,
      selectedNodeFields: [],
      nodes: [],
      links: [],
      nextNodeId: 100, // Start from a high number to avoid conflicts with existing IDs
      isAddingLink: false,
      linkSource: null,
      echarts: null, // 存储CDN导入的echarts
      topologyData: null, // 移除重复的数据结构
      showDebugOverlay: false, // 添加显示调试弹窗的标志
      formattedNodesJson: "", // 格式化的节点JSON
      formattedLinksJson: "", // 格式化的连线JSON
      isolatedNodes: [], // 孤立节点
      selectedLink: null,
      linkFields: [],
      linkJsonData: "",
      jsonError: null,
      activeTab: "form",
      originalEventKey: null, // 保存找到的原始事件的键
      originalEvent: null, // 保存找到的原始事件对象
      backupLinkData: null, // 添加备份数据用于重置
      backupNodeData: null, // 添加备份数据用于重置
      nodeJsonData: "", // 节点的JSON数据
      nodeJsonError: null, // 节点JSON错误信息
      activeNodeTab: "form", // 节点编辑器的当前活动选项卡
      agentTypeColorCache: {}, // 添加颜色缓存对象，保存agentType到颜色的映射
      originalWorkflowData: null, // 用于存储原始工作流数据
      nodeStrData: '',  // JSON 编辑内容
      nodeJsonError: null,  // JSON 解析错误信息
      codeMirrorExtensionsDark: [json(), oneDark],
      codeMirrorExtensions: [json(), githubLight], // 高亮配置
      isDarkMode_type: localStorage.getItem('theme') === 'dark',
      isWorkflowChanged: false, // 添加标志，用于判断工作流是否发生变化
    };
  },
  watch: {
    loading(newValue) {
      this.$emit('update-loading', newValue);
    },
  },
  created() {
    // 初始化图表配置
    this.chartOption = {
      series: [
        {
          name: "拓扑网络",
          type: "graph",
          layout: "none", // 使用固定布局而不是力导向图
          data: [],
          links: [],
          categories: [],
          roam: true, // 保留缩放和平移功能
          label: {
            show: true,
            position: "right",
            formatter: "{b}",
            color: this.isDarkMode ? "#ddd" : "#333",
          },
          lineStyle: {
            color: "source",
            curveness: 0, // 设置为 0 表示直线
            width: 2, // 加粗线条，使其更明显
          },
          emphasis: {
            focus: "adjacency",
            lineStyle: {
              width: 4,
            },
          },
          draggable: false, // 禁止拖动节点
          edgeSymbol: ["none", "arrow"],
          edgeLabel: {
            show: true,
            formatter: "{c}",
            color: this.isDarkMode ? "#ddd" : "#333",
            fontSize: 12,
            distance: 10, // 设置标签与边的距离
          },
        },
      ],
    };

    // 检查是否有原始数据传入
    if (
      this.actionsData &&
      Object.keys(this.actionsData).length > 0 &&
      this.eventsData &&
      Object.keys(this.eventsData).length > 0
    ) {
      console.log("在created中检测到actions和events数据");
    }
  },
  mounted() {
    this.loading = true;
    console.log('load:' + this.loading);
    this.loadEchartsData();
    emitter.on('theme-changed', (isDarkMode) => {
      this.isDarkMode_type = isDarkMode;
    });
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.resizeChart);
    if (this.chart) {
      this.chart.dispose();
    }
  },
  methods: {
    updateChart() {
      // ... existing code ...
      //this.$emit('loading-change', false);
    },
    loadEchartsData() {
      const scenarioName = localStorage.getItem('scenarioName');
      // 检查是否存在场景名称
      if (!scenarioName) {
        this.loading = false;
        ElMessageBox.alert('未找到场景名称，请返回控制面板选择场景', '提示', {
          confirmButtonText: '确定',
          showClose: false,
          modal: true,
          closeOnClickModal: false,
          callback: () => {
            this.$router.push('/');
          }
        });
        return;
      }
      this.generateWorkflow(scenarioName);
    },
    generateWorkflow(scenarioName){
      axios.post("/api/pipeline/generate_workflow",{
        env_name: scenarioName
      }).then((response) => {
        let status = response.data.success;
        if(response.data.success && response.data.success != '0'){
          if(status == '2'){
            setTimeout(() => {
              this.generateWorkflow(scenarioName);
            },1000)
          }else if(status == '1'){
            this.workflow = response.data;
            // 保存原始工作流数据 - 使用深拷贝避免数据污染
            this.originalWorkflowData = JSON.parse(JSON.stringify(response.data));
            this.initEcharts();
          }else{
            this.loading = false;
            this.backToDashboard();
          }
        }else{
          this.loading = false;
          this.backToDashboard();
        }
      })
    },
    initEcharts() {
      // 动态加载echarts
      this.loadECharts()
        .then(() => {
          this.initializeChart();

          if (this.originalWorkflowData) {
            this.loadTopology();
          }
        })
        .catch((error) => {
          console.error("Echarts加载失败:", error);
          this.loading = false;
          this.backToDashboard();
        });

      // Handle window resize
      window.addEventListener("resize", this.resizeChart);
      console.log("TopologyEditor组件挂载完成");
    },
    // 通过CDN加载echarts
    loadECharts() {
      return new Promise((resolve, reject) => {
        console.log("开始加载Echarts库");
        try {
          // 使用npm引入的echarts库
          this.echarts = echarts;
          console.log("使用npm引入的Echarts库");
          resolve();
        } catch (error) {
          console.error("加载Echarts失败:", error);
          reject(error);
        }
      });
    },

    initializeChart() {
      // Initialize ECharts
      try {
        if (!this.$refs.chartContainer) {
          console.error("chartContainer ref不存在");
          this.loading = false;
          return;
        }

        this.chart = this.echarts.init(this.$refs.chartContainer);

        // 统一处理所有图表元素的点击事件
        this.chart.on("click", (params) => {
          console.log("点击元素数据:", params.data);

          // 根据data结构判断是节点还是连线
          if (
            params.data &&
            params.data.id !== undefined &&
            params.data.name !== undefined
          ) {
            // 是节点
            console.log("节点被点击:", params.data);

            // 清除选中的连线
            this.selectedLink = null;

            if (this.isAddingLink) {
              this.handleLinkTarget(params.data);
            } else {
              this.handleNodeClick(params.data);
            }
          } else {
            // 是连线
            console.log("连线被点击:", params.data);

            // 清除选中的节点
            this.selectedNode = null;

            this.handleLinkClick(params.data, params.event.event);
          }
        });

        // 给图表容器添加点击事件，用于在空白处点击时关闭编辑器
        this.$refs.chartContainer.addEventListener("click", (event) => {
          // 确认点击的是图表容器本身而不是其中的元素
          if (event.target === this.$refs.chartContainer) {
            this.closeEditor();
            this.closeLinkEditor();
          }
        });

        // 设置初始图表选项
        if (this.chartOption) {
          this.chart.setOption(this.chartOption);
        }
        this.$nextTick(() => {
          this.loading = false;
        });
        console.log(this.loading);
      } catch (error) {
        console.error("初始化ECharts失败:", error);
        this.loading = false;
      }
    },

    getColorForAgent(agentType) {
      // 首先检查缓存中是否已有该agentType的颜色
      if (this.agentTypeColorCache[agentType]) {
        return this.agentTypeColorCache[agentType];
      }

      // 默认的颜色映射
      const colorMap = {
        EnvAgent: "#29ebd7",
        CommunityCommittee: "#547bb8",
        Resident: "#e4a357",
        PropertyManagementCompany: "#1f274f",
        GovernmentRepresentative: "#4bca85",
        System: "#4bca85",
        Environment: "#29ebd7",
        Interface: "#e4a357",
      };

      let color;

      // 如果传入了自定义的agentTypes，为每种类型生成一个唯一的颜色
      if (this.agentTypes && this.agentTypes.length > 0) {
        // 查找匹配的代理类型
        const matchedAgent = this.agentTypes.find((agent) => agent.name === agentType);
        if (matchedAgent) {
          // 使用代理类型的ID来生成一个相对稳定的颜色
          const colors = [
            "#4e79a7",
            "#f28e2c",
            "#e15759",
            "#76b7b2",
            "#59a14f",
            "#edc949",
            "#af7aa1",
            "#ff9da7",
            "#9c755f",
            "#bab0ab",
          ];
          const colorIndex = matchedAgent.id % colors.length;
          color = colors[colorIndex];
        }
      }

      // 如果在映射中找到类型，返回对应颜色，否则生成随机颜色
      if (!color) {
        color = colorMap[agentType] || "#" + Math.floor(Math.random() * 16777215).toString(16);
      }

      // 将颜色保存到缓存
      this.agentTypeColorCache[agentType] = color;

      return color;
    },

    async loadTopology() {

      this.loading = true;
      const originalData = {
        nodes: [
          {
            id: 0,
            label: "start",
            agentType: "EnvAgent",
            color: "#29ebd7",
          },
          ...Object.entries(this.originalWorkflowData.actions).flatMap(([agentType, actions]) =>
            actions.map((action) => ({
              id: action.id,
              label: action.name,
              agentType: agentType,
              color: this.getColorForAgent(agentType),
              description: action.description,
              type: action.type,
              required_variables: action.required_variables,
              output_updates: action.output_updates,
            }))
          ),
        ],
        links: [
          ...Object.values(this.originalWorkflowData.events).map((event) => ({
            source: event.from_action_id,
            target: event.to_action_id,
            name: event.event_name,
            info: event.event_info,
          })),
        ],
      };
      // 修改-1为最后一个节点的ID
      originalData.links = originalData.links.map((link) => ({
        ...link,
        source: link.source === -1 ? originalData.nodes.length : link.source,
        target: link.target === -1 ? originalData.nodes.length : link.target,
      }));
      originalData.nodes.push({
        id: originalData.nodes.length,
        label: "terminate",
        agentType: "EnvAgent",
        color: "#29ebd7",
      });

      // 对演示数据进行预处理，确保所有ID是数字类型
      originalData.nodes = originalData.nodes.map((node) => ({
        ...node,
        id: typeof node.id === "string" ? parseInt(node.id) : node.id,
      }));

      originalData.links = originalData.links.map((link) => ({
        ...link,
        source: typeof link.source === "string" ? parseInt(link.source) : link.source,
        target: typeof link.target === "string" ? parseInt(link.target) : link.target,
      }));
      this.processTopologyData(originalData);
    },

    processTopologyData(data) {
      if (!data || !data.nodes || !data.links) {
        console.error("无效的拓扑数据格式", data);
        return;
      }

      // 确保所有节点ID是数字类型
      this.nodes = data.nodes.map((node) => ({
        ...node,
        symbolSize: 50,
        name: node.label,
        id: typeof node.id === "string" ? parseInt(node.id) : node.id,
      }));

      // 确保所有连线的source和target是数字类型
      this.links = data.links.map((link) => ({
        ...link,
        value: link.name,
        source: typeof link.source === "string" ? parseInt(link.source) : link.source,
        target: typeof link.target === "string" ? parseInt(link.target) : link.target,
      }));


      // 检查所有连线的节点是否存在
      const nodeIds = this.nodes.map((n) => n.id);
      const invalidLinks = this.links.filter(
        (link) => !nodeIds.includes(link.source) || !nodeIds.includes(link.target)
      );

      if (invalidLinks.length > 0) {
        console.warn("发现无效连线 (引用不存在的节点):", invalidLinks);
      }

      // 为start和terminate节点设置固定位置
      // 获取chart容器的宽度，如果还没有渲染则使用默认值
      const chartWidth = this.$refs.chartContainer ? this.$refs.chartContainer.clientWidth : 1200;
      const chartHeight = this.$refs.chartContainer ? this.$refs.chartContainer.clientHeight : 600;

      // 查找start和terminate节点
      const startNode = this.nodes.find(n => n.id === 0);
      const terminateNode = this.nodes.find(n => n.id === -1) || this.nodes.find(n => n.label === "terminate");

      // 如果找到start节点，设置固定位置在左侧
      if (startNode) {
        startNode.x = 100;
        startNode.y = chartHeight / 2;
        startNode.fixed = true; // 固定位置
      }

      // 如果找到terminate节点，设置固定位置在右侧
      if (terminateNode) {
        terminateNode.x = chartWidth - 100;
        terminateNode.y = chartHeight / 2;
        terminateNode.fixed = true; // 固定位置
      }

      // 确保在DOM更新后更新图表
      this.$nextTick(() => {
        this.updateChart();
        // this.loading = false;
      });

      // Update nextNodeId to be higher than any existing node ID
      const maxId = Math.max(...this.nodes.map((node) => parseInt(node.id) || 0), 0);
      this.nextNodeId = maxId + 1;
    },

    calculateNodePositions() {
      const nodeCount = this.nodes.length;
      if (nodeCount === 0) return;

      // 按照ID排序节点（从小到大）
      this.nodes.sort((a, b) => a.id - b.id);

      // 计算水平布局参数
      const canvasWidth = 1200; // 假设的画布宽度，可以根据实际情况调整
      const nodeWidth = 100; // 节点宽度
      const horizontalGap = 200; // 节点之间的水平间距

      // 特殊处理开始和结束节点
      const startNode = this.nodes.find((n) => n.id === 0);
      const endNode = this.nodes.find((n) => n.id === -1);

      // 分离普通节点（排除开始和结束节点）
      const regularNodes = this.nodes.filter((n) => n.id !== 0 && n.id !== -1);

      // 按ID排序普通节点
      regularNodes.sort((a, b) => a.id - b.id);

      // 设置节点的y坐标
      const baseY = 300;
      const rows = 2; // 最多分几行
      const rowHeight = 150; // 行高

      // 计算每个节点的位置
      if (startNode) {
        startNode.x = 100;
        startNode.y = baseY;
      }

      if (endNode) {
        endNode.x = canvasWidth - 100;
        endNode.y = baseY;
      }

      // 计算常规节点的位置
      const availableWidth = canvasWidth - 300; // 减去开始和结束节点的空间
      let currentX = 200; // 从左侧开始，留些空间

      regularNodes.forEach((node, index) => {
        // 将节点均匀分布在水平方向上
        const row = index % rows; // 确定节点在哪一行
        node.x = currentX;
        node.y = baseY - rowHeight + row * rowHeight; // 不同行的高度不同

        // 计算下一个节点的x坐标
        if ((index + 1) % rows === 0) {
          currentX += horizontalGap; // 下一列
        }
      });
    },

    updateChart() {
      if (!this.chart || !this.echarts) return;

      try {
        // 确保数据已经初始化
        if (!this.nodes || !this.links) {
          console.warn("无法更新图表 - 节点或连线数据尚未初始化");
          return;
        }

        // 提取所有分类
        const agentCategories = [
          ...new Set(this.nodes.map((node) => node.agentType)),
        ].map((type) => {
          return {
            name: type,
          };
        });

        // 更新图表数据
        const chartData = this.nodes.map((node) => {
          const categoryIndex = agentCategories.findIndex(
            (cat) => cat.name === node.agentType
          );

          return {
            id: node.id,
            name: node.label, // 使用label作为显示名称
            symbolSize: node.symbolSize || 50,
            itemStyle: {
              color: node.color || "#547bb8",
            },
            x: node.x,
            y: node.y,
            fixed: node.fixed || false, // 保留节点的fixed属性
            draggable: true, // 允许用户拖动调整
            value: node.id, // 确保每个节点有唯一的值
            agentType: node.agentType, // 确保agentType属性被传递到echarts数据中
            description: node.description, // 确保description被传递
            type: node.type, // 确保type属性被传递
            required_variables: node.required_variables, // 确保required_variables属性被传递
            output_updates: node.output_updates, // 确保output_updates属性被传递
            category: categoryIndex >= 0 ? categoryIndex : 0, // 通过索引绑定分类
            tooltip: {
              formatter: () => {
                return `<div style="font-weight:bold">${node.label}</div>
                        <div>ID: ${node.id}</div>
                        <div>类型: ${node.agentType}</div>
                        <div>${node.description || ""}</div>`;
              },
            },
          };
        });

        const chartLinks = this.links.map((link) => {
          // 确保source和target是数字类型
          const sourceId =
            typeof link.source === "string" ? parseInt(link.source) : link.source;
          const targetId =
            typeof link.target === "string" ? parseInt(link.target) : link.target;

          return {
            source: sourceId,
            target: targetId,
            value: link.name,
            lineStyle: {
              color: link.color || "source",
              width: 2,
              curveness: 0, // 更明显的曲线，避免重叠
            },
            label: {
              show: true,
              formatter: link.name,
              fontSize: 12,
              color: this.isDarkMode ? "#ddd" : "#333",
            },
            tooltip: {
              formatter: () => {
                return `<div style="font-weight:bold">${link.name}</div>
                        <div>从: ${this.getNodeName(sourceId)}</div>
                        <div>到: ${this.getNodeName(targetId)}</div>
                        <div>${link.info || ""}</div>`;
              },
            },
            emphasis: {
              lineStyle: {
                width: 4,
                shadowBlur: 5,
                shadowColor: "rgba(0, 0, 0, 0.3)",
              },
            },
            symbol: ["none", "arrow"], // 确保所有连接都有箭头
          };
        });

        // 确保所有连线的source和target节点都存在
        const validLinks = chartLinks.filter((link) => {
          const sourceExists = chartData.some((n) => n.id === link.source);
          const targetExists = chartData.some((n) => n.id === link.target);
          if (!sourceExists) console.warn(`连线错误: 源节点ID ${link.source} 不存在`);
          if (!targetExists) console.warn(`连线错误: 目标节点ID ${link.target} 不存在`);
          return sourceExists && targetExists;
        });

        // 更新图表选项
        this.chartOption.series[0].data = chartData;
        this.chartOption.series[0].links = validLinks;
        this.chartOption.series[0].layout = "force"; // 使用力导向布局
        this.chartOption.series[0].draggable = true; // 允许拖动节点
        this.chartOption.series[0].categories = agentCategories;

        // 增强力导向布局的参数，使节点分布更加分散
        this.chartOption.series[0].force = {
          repulsion: 1000, // 增大斥力，使节点之间距离更远
          gravity: 0.05,   // 减小引力，使整体更分散
          edgeLength: 250, // 增加边的长度
          layoutAnimation: true
        };

        // 增强分类的视觉效果
        this.chartOption.series[0].legendHoverLink = true; // 启用图例悬停时高亮相关节点
        this.chartOption.series[0].focus = "series"; // 默认聚焦整个系列
        this.chartOption.series[0].focusNodeAdjacency = "allEdges"; // 高亮关联节点和边
        this.chartOption.series[0].emphasis = {
          focus: "adjacency", // 高亮相邻节点和连接线
          scale: true, // 放大高亮项
          lineStyle: {
            width: 4,
            shadowBlur: 5,
            shadowColor: this.isDarkMode
              ? "rgba(255, 255, 255, 0.3)"
              : "rgba(0, 0, 0, 0.3)",
          },
          itemStyle: {
            borderWidth: 2,
            borderColor: this.isDarkMode ? "#fff" : "#000",
            shadowBlur: 10,
            shadowColor: this.isDarkMode
              ? "rgba(255, 255, 255, 0.5)"
              : "rgba(0, 0, 0, 0.5)",
          },
          label: {
            fontWeight: "bold",
          },
        };

        // 更新图表标题

        this.chartOption.tooltip = {
          trigger: "item",
          backgroundColor: this.isDarkMode
            ? "rgba(50, 50, 50, 0.9)"
            : "rgba(255, 255, 255, 0.9)",
          borderColor: this.isDarkMode ? "#555" : "#ddd",
          textStyle: {
            color: this.isDarkMode ? "#fff" : "#333",
          },
        };

        // 完全重新设置选项
        this.chart.setOption(this.chartOption, true);
      } catch (error) {
        console.error("图表更新失败:", error);
      }
    },

    handleNodeClick(nodeData) {
      console.log("Node clicked:", nodeData);

      // 清除选中的连线
      this.selectedLink = null;

      // 查找原始节点数据
      const originalNodeData = this.findOriginalNodeData(nodeData.id);

      // 确保先设置selectedNode为null，触发Vue的响应式更新
      this.selectedNode = null;

      // 使用nextTick确保DOM更新后再设置新值
      this.$nextTick(() => {
        this.selectedNode = {
          id: nodeData.id,
          label: nodeData.label || nodeData.name,
          agentType: nodeData.agentType,
          color: nodeData.color || "#547bb8",
          description: nodeData.description || "",
          type: nodeData.type || "OR",
          required_variables: nodeData.required_variables || [],
          output_updates: nodeData.output_updates || [],
          originalData: originalNodeData, // 保存原始数据引用
        };

        console.log("Selected node state updated:", this.selectedNode);

        // 如果找到原始节点数据，使用它的详细信息
        if (originalNodeData && originalNodeData.action) {
          console.log("Found original node data:", originalNodeData);

          // 使用原始数据覆盖节点属性
          this.selectedNode.type = originalNodeData.action.type || this.selectedNode.type;
          this.selectedNode.required_variables =
            originalNodeData.action.required_variables || [];
          this.selectedNode.output_updates = originalNodeData.action.output_updates || [];
        }

        // Get fields for this node from the events data
        this.selectedNodeFields = [];

        if (this.eventsData) {
          // Find related events that have this node as source or target
          Object.values(this.eventsData).forEach((event) => {
            if (
              event.from_action_id === nodeData.id ||
              event.to_action_id === nodeData.id
            ) {
              // Add fields from the event
              if (event.fields && event.fields.length) {
                event.fields.forEach((field) => {
                  this.selectedNodeFields.push({
                    ...field,
                  });
                });
              }
            }
          });
        }

        // 更新节点JSON数据
        this.updateNodeJsonData();

        // 保存原始数据的备份用于重置
        this.backupNodeData = JSON.parse(JSON.stringify(this.selectedNode));

        // 移除高亮效果，改用蒙版
        // this.highlightSelectedNode();

        // 强制更新DOM，确保编辑器显示
        this.$forceUpdate();

        console.log(
          "Node editor should be visible now, selectedNode state:",
          this.selectedNode
        );
      });
    },

    // 高亮选中的节点和相关连线
    highlightSelectedNode() {
      if (!this.selectedNode || !this.chart) return;

      try {
        // 查找与当前节点相关的所有连线和节点
        const relatedLinks = this.links.filter(
          (link) =>
            link.source === this.selectedNode.id || link.target === this.selectedNode.id
        );

        // 获取与选中节点相关联的所有节点ID
        const relatedNodeIds = new Set();
        relatedLinks.forEach((link) => {
          if (link.source === this.selectedNode.id) {
            relatedNodeIds.add(link.target);
          } else if (link.target === this.selectedNode.id) {
            relatedNodeIds.add(link.source);
          }
        });

        console.log("相关节点IDs:", [...relatedNodeIds]);

        // 创建高亮样式
        const highlightOption = {
          series: [
            {
              // 高亮节点
              data: this.chartOption.series[0].data.map((node) => {
                // 当前选中的节点
                if (node.id === this.selectedNode.id) {
                  return {
                    ...node,
                    itemStyle: {
                      ...node.itemStyle,
                      borderWidth: 4,
                      borderColor: "#ffcc00",
                      shadowBlur: 10,
                      shadowColor: "rgba(255, 204, 0, 0.5)",
                    },
                    symbolSize: (node.symbolSize || 50) * 1.1, // 放大节点
                    z: 10, // 确保显示在最上层
                  };
                }
                // 与选中节点相关联的节点
                else if (relatedNodeIds.has(node.id)) {
                  return {
                    ...node,
                    itemStyle: {
                      ...node.itemStyle,
                      borderWidth: 2,
                      borderColor: "#ffaa00",
                      shadowBlur: 5,
                      shadowColor: "rgba(255, 170, 0, 0.3)",
                    },
                    z: 5, // 比其他节点层级高
                  };
                }
                // 其他节点变暗
                return {
                  ...node,
                  itemStyle: {
                    ...node.itemStyle,
                    opacity: 0.4,
                  },
                };
              }),
              // 高亮相关连线
              links: this.chartOption.series[0].links.map((link) => {
                // 与选中节点相关的连线
                if (
                  link.source === this.selectedNode.id ||
                  link.target === this.selectedNode.id
                ) {
                  return {
                    ...link,
                    lineStyle: {
                      ...link.lineStyle,
                      width: 3,
                      color: "#ffcc00",
                      shadowBlur: 5,
                      shadowColor: "rgba(255, 204, 0, 0.5)",
                      opacity: 1,
                      curveness: 0,
                    },
                    label: {
                      ...link.label,
                      show: true,
                      fontWeight: "bold",
                      fontSize: 14,
                      formatter: link.name || "",
                    },
                    edgeSymbol: ["none", "arrow"],
                    edgeSymbolSize: [0, 12], // 增大箭头大小
                    z: 5, // 确保显示在其他连线之上
                  };
                }
                // 其他连线变暗
                return {
                  ...link,
                  lineStyle: {
                    ...link.lineStyle,
                    opacity: 0.2,
                    width: 1,
                  },
                  label: {
                    ...link.label,
                    show: false,
                  },
                };
              }),
            },
          ],
        };

        // 应用高亮样式
        this.chart.setOption(highlightOption, false);
        console.log("节点高亮样式已应用");
      } catch (error) {
        console.error("高亮节点失败:", error);
      }
    },

    startLinkCreation() {
      this.isAddingLink = true;
      this.linkSource = null;
      this.$el.classList.add("linking-mode");
    },

    handleLinkTarget(nodeData) {
      if (!this.linkSource) {
        // First click - select source
        this.linkSource = nodeData;
        this.$message({
          message: `Source node selected: ${nodeData.label || nodeData.name}. Please select the target node.`,
          type: "info",
          duration: 2000,
        });
      } else {
        // Second click - create link
        if (this.linkSource.id === nodeData.id) {
          // 提示不能连接到同一个节点
          this.$message({
            message: "You cannot connect to the same node.",
            type: "warning",
            duration: 2000,
          });
        } else {
          // 检查是否已经存在连接
          const linkExists = this.links.some(
            link =>
              (link.source === this.linkSource.id && link.target === nodeData.id)
          );

          if (linkExists) {
            this.$message({
              message: "这两个节点之间已经有相同方向的连线",
              type: "warning",
              duration: 2000,
            });
          } else {
            this.createLink(this.linkSource.id, nodeData.id);
            // 设置工作流已修改标志
            this.isWorkflowChanged = true;
            this.$message({
              message: `Link created successfully from ${this.linkSource.label || this.linkSource.name} to ${nodeData.label || nodeData.name}.`,
              type: "success",
              duration: 2000,
            });
          }
        }

        // Reset linking mode
        this.isAddingLink = false;
        this.linkSource = null;
        this.$el.classList.remove("linking-mode");
      }
    },

    createLink(sourceId, targetId) {
      const newLink = {
        source: sourceId,
        target: targetId,
        name: "NewEvent",
        info: "Description for the new event",
        value: "NewEvent",
      };

      this.links.push(newLink);
      this.updateChart();
    },

    cancelLinkCreation() {
      this.isAddingLink = false;
      this.linkSource = null;
      this.$el.classList.remove("linking-mode");
    },

    closeEditor() {
      console.log("Closing node editor");

      // 先添加淡出类，然后使用setTimeout确保动画完成后再真正关闭编辑器
      const nodeEditor = this.$el.querySelector(".node-editor");
      if (nodeEditor) {
        nodeEditor.classList.add("fade-out");
        setTimeout(() => {
          this.selectedNode = null;
          this.selectedNodeFields = [];
          this.nodeJsonData = "";
          this.nodeJsonError = null;
          this.activeNodeTab = "form";
          nodeEditor.classList.remove("fade-out");
        }, 300); // 动画持续时间
      } else {
        this.selectedNode = null;
        this.selectedNodeFields = [];
        this.nodeJsonData = "";
        this.nodeJsonError = null;
        this.activeNodeTab = "form";
      }

      console.log("Node editor closing with animation");
    },

    closeLinkEditor() {
      console.log("Closing link editor");

      // 先添加淡出类，然后使用setTimeout确保动画完成后再真正关闭编辑器
      const linkEditor = this.$el.querySelector(".link-editor");
      if (linkEditor) {
        linkEditor.classList.add("fade-out");
        setTimeout(() => {
          this.selectedLink = null;
          this.linkFields = [];
          this.linkJsonData = "";
          this.jsonError = null;
          this.activeTab = "form";
          linkEditor.classList.remove("fade-out");
        }, 300); // 动画持续时间
      } else {
        this.selectedLink = null;
        this.linkFields = [];
        this.linkJsonData = "";
        this.jsonError = null;
        this.activeTab = "form";
      }

      console.log("Link editor closing with animation");
    },

    applyChanges() {
      if (!this.selectedNode) return;

      try {
        // 如果当前是JSON模式，先更新表单数据
        if (this.activeNodeTab === "json") {
          this.updateNodeFormFromJson();
          if (this.nodeJsonError) {
            // 如果有JSON错误，不继续处理
            return;
          }
        }

        // Find and update the node in our nodes array
        const index = this.nodes.findIndex((node) => node.id === this.selectedNode.id);
        if (index !== -1) {
          this.nodes[index].label = this.selectedNode.label;
          this.nodes[index].name = this.selectedNode.label; // For display in chart
          this.nodes[index].agentType = this.selectedNode.agentType;
          this.nodes[index].color = this.selectedNode.color;
          this.nodes[index].description = this.selectedNode.description;
          this.nodes[index].type = this.selectedNode.type;
          this.nodes[index].required_variables = this.selectedNode.required_variables;
          this.nodes[index].output_updates = this.selectedNode.output_updates;
        }

        // 如果找到原始节点数据，更新workflow
        if (this.selectedNode.originalData && this.selectedNode.originalData.action) {
          const { agentType, action } = this.selectedNode.originalData;

          // 查找要更新的节点在原始数据中的索引
          const actionIndex = this.workflow.actions[agentType].findIndex(
            (a) => a.id === this.selectedNode.id
          );

          if (actionIndex !== -1) {
            // 更新原始数据
            this.workflow.actions[agentType][actionIndex] = {
              ...this.workflow.actions[agentType][actionIndex],
              name: this.selectedNode.label,
              description: this.selectedNode.description,
              type: this.selectedNode.type,
              required_variables: this.selectedNode.required_variables,
              output_updates: this.selectedNode.output_updates,
            };


            // 设置工作流已修改标志
            this.isWorkflowChanged = true;
            // 使用Element UI提示操作成功
            this.$message({
              message: "Node changes applied successfully",
              type: "success",
              duration: 2000,
            });
          }
        }

        // Update the chart
        this.updateChart();

        // 使用淡出效果关闭编辑器
        this.closeEditor();
      } catch (error) {
        console.error("应用节点修改失败:", error);

        // 使用Element UI提示错误
        this.$message({
          message: "Failed to apply changes: " + error.message,
          type: "error",
          duration: 3000,
        });
      }
    },

    onCodeChange() {
      try {
        JSON.parse(value)
        this.nodeJsonError = null
      } catch (err) {
        this.nodeJsonError = 'Invalid JSON: ' + err.message
      }
      this.isCodeModified = true; // 确保在输入时标记为已修改
    },

    addNode() {
      const newNode = {
        id: this.nextNodeId++,
        label: "New Node",
        name: "New Node",
        agentType: "Custom",
        color: this.isDarkMode ? "#4bca85" : "#2196F3",
        symbolSize: 50,
      };

      this.nodes.push(newNode);

      // 重新计算节点位置
      this.calculateNodePositions();
      this.updateChart();
      this.handleNodeClick(newNode);
    },

    deleteNode() {
      if (!this.selectedNode) return;

      // 检查节点是否有连接的线
      const connectedLinks = this.links.filter(
        (link) =>
          link.source === this.selectedNode.id || link.target === this.selectedNode.id
      );

      // 如果有连接的线，提示用户先删除连接
      if (connectedLinks.length > 0) {
        this.$message({
          message: `Cannot delete node. This node has ${connectedLinks.length} connections. Please delete all connections first before attempting to delete the node.`,
          type: "warning",
          duration: 3000,
        });
        return;
      }

      // 使用Element UI确认对话框
      this.$confirm(
        "Are you sure you want to delete this node? This will also remove all connected links. This action cannot be undone.",
        "Warning",
        {
          confirmButtonText: "Delete",
          cancelButtonText: "Cancel",
          type: "warning",
        }
      )
        .then(() => {
          try {
            // 记录将要删除的节点ID，用于日志
            const nodeId = this.selectedNode.id;
            const nodeName = this.selectedNode.label;

            // 删除原始workflow数据中的节点（如果存在）
            if (this.selectedNode.originalData && this.selectedNode.originalData.action) {
              const { agentType } = this.selectedNode.originalData;

              if (this.workflow.actions && this.workflow.actions[agentType]) {
                // 在原始数据中查找并删除节点
                const actionIndex = this.workflow.actions[agentType].findIndex(
                  (a) => a.id === nodeId
                );

                if (actionIndex !== -1) {
                  this.workflow.actions[agentType].splice(actionIndex, 1);
                  console.log(`从workflow中删除了节点: ${agentType}.${nodeId}`);
                }
              }
            }

            // 找出所有与该节点相连的连线
            const connectedLinks = this.links.filter(
              (link) => link.source === nodeId || link.target === nodeId
            );

            // 删除与该节点相连的所有事件数据
            if (this.workflow.events) {
              Object.keys(this.workflow.events).forEach((key) => {
                const event = this.workflow.events[key];
                if (event.from_action_id === nodeId || event.to_action_id === nodeId) {
                  delete this.workflow.events[key];
                  console.log(`从workflow中删除了事件: ${key}`);
                }
              });
            }

            // 同样从eventsData中删除相关事件
            if (this.eventsData) {
              // 创建一个新对象而不是直接修改原对象，避免proxy错误
              const updatedEventsData = {
                ...this.eventsData,
              };
              Object.keys(updatedEventsData).forEach((key) => {
                const event = updatedEventsData[key];
                if (event.from_action_id === nodeId || event.to_action_id === nodeId) {
                  delete updatedEventsData[key];
                }
              });
              // 通过事件通知父组件更新eventsData
              this.$emit("update:eventsData", updatedEventsData);
            }

            // 从nodes数组中移除节点
            this.nodes = this.nodes.filter((node) => node.id !== nodeId);

            // 从links数组中移除所有相关连线
            this.links = this.links.filter(
              (link) => link.source !== nodeId && link.target !== nodeId
            );

            // 更新其他连线的source和target索引
            this.links.forEach((link) => {
              // 如果source大于等于被删除的节点ID，则减1
              if (link.source > nodeId) {
                link.source -= 1;
              }
              // 如果target大于等于被删除的节点ID，则减1
              if (link.target > nodeId) {
                link.target -= 1;
              }
            });

            this.nodes.forEach((node) => {
              // 如果nodeId大于等于被删除的节点ID，则减1
              if (node.id > nodeId) {
                node.id -= 1;
              }
            });

            // 重新计算节点位置
            this.calculateNodePositions();

            // 更新图表
            this.updateChart();

            // 关闭编辑器
            this.closeEditor();

            // 显示成功消息
            this.$message({
              message: `Node "${nodeName}" deleted successfully with ${connectedLinks.length} connected links`,
              type: "success",
              duration: 2000,
            });
            // 设置工作流已修改标志
            this.isWorkflowChanged = true;
          } catch (error) {
            console.error("删除节点失败:", error);
            this.$message({
              message: "Failed to delete node: " + error.message,
              type: "error",
              duration: 3000,
            });
          }
        })
        .catch(() => {
          // 用户取消删除
          this.$message({
            type: "info",
            message: "Delete operation canceled",
          });
        });
    },

    saveTopology() {
      // 检查是否有孤立节点（没有任何连线的节点）
      const isolatedNodes = this.nodes.filter(node => {
        return !this.links.some(link =>
          link.source === node.id || link.target === node.id
        );
      });

      // 如果存在孤立节点，直接显示错误信息并阻止保存
      if (isolatedNodes.length > 0) {
        const nodeNames = isolatedNodes.map(node => node.label || node.name || node.id).join(', ');
        this.$message({
          message: `Isolated nodes detected: ${nodeNames}. These nodes don't have connections with other nodes. Please add connections before saving.`,
          type: "error",
          duration: 5000
        });
        return; // 阻止继续执行保存
      }

      // 没有孤立节点，确认保存
      ElMessageBox.confirm(
        "Are you sure you want to save and continue to the next step?",
        "Confirmation",
        {
          confirmButtonText: "Confirm",
          cancelButtonText: "Cancel",
        }
      ).then(() => {
        this.proceedToSave();
      });
    },

    proceedToSave() {
      // Create the topology object to be saved
      const topology = {
        nodes: this.nodes.map(({ id, name, label, agentType, color, description }) => ({
          id,
          label: label || name,
          agentType,
          color,
          description,
        })),
        links: this.links.map(({ source, target, name, info }) => ({
          source,
          target,
          name,
          info,
        })),
      };

      console.log("Topology to be saved:", topology);
      console.log("Workflow to be saved:", this.workflow);

      const scenarioName = localStorage.getItem('scenarioName');
      if (!scenarioName) {
        this.$message.error("无法获取场景名称，保存失败");
        return;
      }

      // 检查是否对工作流进行了修改
      const hasWorkflowChanged = this.isWorkflowChanged;

      if (hasWorkflowChanged) {
        // 有修改，调用update_workflow接口
        this.nextLoading = true;
        const updateData = {
          env_name: scenarioName,
          actions: this.workflow.actions || {},
          events: this.workflow.events || {}
        };

        axios.post("/api/pipeline/update_workflow", updateData)
          .then(response => {
            // 更新成功后继续操作
            this.$emit("save-topology", topology);
            this.$emit("save-workflow", this.workflow);
            // 同时触发继续下一步的事件
            this.$emit("proceed-next");
            this.nextLoading = false;
          })
          .catch(error => {
            this.$message.error("Failed to save the workflow, please try again.");

            this.nextLoading = false;
          });
      } else {
        // 没有修改，直接进入下一步
        console.log("工作流未发生变化，跳过更新");
        this.$emit("save-topology", topology);
        this.$emit("save-workflow", this.workflow);
        this.$emit("proceed-next");
      }
    },


    restoreOriginalJson() {
      ElMessageBox.confirm(
        "Are you sure you want to go back to the original state? All current changes are discarded.",
        "Warning",
        {
          confirmButtonText: "Confirm",
          cancelButtonText: "Cancel",
          type: "warning"
        }
      ).then(async () => {
        this.loading = true;
        try {
          // 尝试加载原始数据
          if (this.originalWorkflowData) {
            await this.loadTopology();
            // 重置修改标志
            this.isWorkflowChanged = false;
          }
        } finally {
          this.loading = false;
        }
      }).catch(() => {
        // 用户取消操作，不做任何处理
      });
    },
    initChart() {
      if (!this.$refs.chartContainer) return;

      // 初始化ECharts实例
      this.chart = echarts.init(this.$refs.chartContainer);

      // 设置配置项
      // this.chart.setOption(this.chartOption);
      // console.log(this.chartOption);
      this.chartOption && this.chart.setOption(this.chartOption);
    },
    resizeChart() {
      if (this.chart && this.echarts) {
        this.chart.resize();
      }
    },

    importTopology(data) {
      try {
        this.loading = true;

        // 验证数据格式
        if (
          !data.nodes ||
          !Array.isArray(data.nodes) ||
          !data.links ||
          !Array.isArray(data.links)
        ) {
          throw new Error("无效的拓扑图数据格式");
        }

        // 清除现有数据
        this.nodes = [];
        this.links = [];

        // 导入节点
        this.nodes = data.nodes.map((node) => ({
          id: node.id,
          label: node.name || `节点 ${node.id}`,
          agentType: node.type || "default",
          color: (node.itemStyle && node.itemStyle.color) || "#547bb8",
          symbolSize: node.symbolSize || 50,
          description: node.description || "",
          x: node.x,
          y: node.y,
        }));

        // 导入连线
        this.links = data.links.map((link) => ({
          source: link.source,
          target: link.target,
          name: link.value || "连接",
          info: link.info || "",
          color: (link.lineStyle && link.lineStyle.color) || "source",
        }));

        // 更新图表
        this.updateChart();

        // 显示成功消息
        this.$nextTick(() => {
          alert("拓扑图导入成功！");
        });
      } catch (error) {
        console.error("Import error:", error);
        alert(`导入失败: ${error.message}`);
      } finally {
        this.loading = false;
      }
    },

    // 辅助方法，根据节点ID获取节点名称
    getNodeName(nodeId) {
      const node = this.nodes.find((n) => n.id === nodeId);
      return node ? node.label || node.name : nodeId;
    },

    // 复制JSON数据到剪贴板
    copyDebugJson() {
      const fullJson = JSON.stringify(
        {
          nodes: JSON.parse(this.formattedNodesJson),
          links: JSON.parse(this.formattedLinksJson),
        },
        null,
        2
      );

      navigator.clipboard
        .writeText(fullJson)
        .then(() => {
          alert("JSON数据已复制到剪贴板");
        })
        .catch((err) => {
          console.error("复制失败:", err);
          alert("复制失败，请手动选择文本复制");
        });
    },



    // 处理actions和events数据转换为节点和连线
    processActionsEvents(actionsData, eventsData) {
      this.loading = true;

      try {
        console.log("开始处理actions和events数据");

        // 收集所有节点数据
        const allNodes = [];

        // 先将actions转换为节点
        Object.entries(actionsData).forEach(([agentType, actions]) => {
          console.log(`处理代理类型: ${agentType}, 动作数量: ${actions.length}`);
          actions.forEach((action) => {
            allNodes.push({
              id: action.id,
              name: action.name,
              label: action.name,
              agentType: agentType,
              symbolSize: 50,
              value: 20, // 默认值
              category: agentType, // 使用代理类型作为分类
              description: action.description || "",
            });
          });
        });

        // 添加特殊节点：开始和结束
        allNodes.push({
          id: 0,
          name: "start",
          label: "start",
          agentType: "EnvAgent",
          symbolSize: 50,
          value: 15,
          category: "EnvAgent",
        });

        allNodes.push({
          id: -1,
          name: "terminate",
          label: "terminate",
          agentType: "EnvAgent",
          symbolSize: 50,
          value: 15,
          category: "EnvAgent",
        });

        // 提取所有的代理类型，用于创建分类
        const categories = [...new Set(allNodes.map((node) => node.agentType))].map(
          (type) => {
            return {
              name: type,
            };
          }
        );

        // 从events创建连线
        const links = Object.values(eventsData).map((event) => {
          return {
            source: event.from_action_id.toString(),
            target: event.to_action_id.toString(),
            name: event.event_name,
            value: event.event_name, // 用于显示
            info: event.event_info || "",
          };
        });

        // 构建符合echarts格式的数据
        const echartsData = {
          nodes: allNodes,
          links: links,
          categories: categories,
        };

        // 处理为TopologyEditor需要的格式
        const topology = {
          nodes: echartsData.nodes.map((node) => ({
            id: node.id,
            label: node.name,
            agentType: node.category,
            color: this.getColorForAgent(node.category),
            description: node.description || "",
            x: node.x,
            y: node.y,
            symbolSize: node.symbolSize,
          })),
          links: echartsData.links.map((link) => ({
            source: parseInt(link.source),
            target: parseInt(link.target),
            name: link.name || link.value,
            info: link.info,
          })),
        };

        console.log("生成的拓扑数据:", topology);

        // 保存事件数据，用于字段编辑
        this.eventsData = eventsData; // 直接引用传入的eventsData

        // 处理拓扑数据
        this.processTopologyData(topology);
      } catch (error) {
        console.error("处理actions和events数据时出错:", error);
        alert(`数据处理失败: ${error.message}`);
        this.processTopologyData({
          nodes: [],
          links: [],
        });
      } finally {
        this.loading = false;
      }
    },

    editVariable(variable, type, index) {
      // Logic to edit a variable/output
      // This could open a dialog or inline edit
      console.log(`Editing ${type} at index ${index}:`, variable);
      // Implement dialog or inline editing
    },

    addVariable(type) {
      // Add a new variable/output to the selected node
      const newItem = {
        name: type === "required_variables" ? "New Variable" : "New Output",
        type: "string",
        context: "global",
        description: "Description here",
      };

      if (!this.selectedNode[type]) {
        this.selectedNode[type] = [];
      }

      this.selectedNode[type].push(newItem);
    },

    removeVariable(type, index) {
      if (
        this.selectedNode &&
        this.selectedNode[type] &&
        index >= 0 &&
        index < this.selectedNode[type].length
      ) {
        this.$confirm(
          "确定要删除这个" + (type === "required_variables" ? "变量" : "输出") + "吗?",
          "提示",
          {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
          }
        )
          .then(() => {
            this.selectedNode[type].splice(index, 1);
            // 更新节点JSON数据
            this.updateNodeJsonData();
          })
          .catch(() => {
            // 用户取消删除
          });
      }
    },

    // 添加处理连线点击事件的方法
    handleLinkClick(linkData, event) {
      // 不再需要阻止事件冒泡，已通过数据结构识别区分节点和连线

      // 查找原始连线数据
      const linkIndex = this.links.findIndex(
        (link) =>
          link.source === linkData.source &&
          link.target === linkData.target &&
          link.name === linkData.value
      );

      if (linkIndex !== -1) {
        // 保存选中的连线
        this.selectedLink = {
          ...this.links[linkIndex],
          oldSource: this.links[linkIndex].source, // 保存原始source用于后续比较
          oldTarget: this.links[linkIndex].target, // 保存原始target用于后续比较
        };
        console.log("Selected link:", this.selectedLink);

        // 处理特殊节点ID
        let sourceId = this.selectedLink.source;
        let targetId = this.selectedLink.target;

        // 查找关联的事件数据
        this.linkFields = [];
        this.originalEventKey = null;
        this.originalEvent = null;

        // 从workflow原始数据中查找事件
        if (this.workflow && this.workflow.events) {
          Object.entries(this.workflow.events).forEach(([key, event]) => {
            // 检查事件的源节点和目标节点是否匹配
            // 注意特殊处理start和terminate节点
            if (
              (event.from_action_id === sourceId ||
                (event.from_action_id === 0 && sourceId === 0) ||
                (event.from_action_id === -1 && sourceId === this.nodes.length - 1)) &&
              (event.to_action_id === targetId ||
                (event.to_action_id === 0 && targetId === 0) ||
                (event.to_action_id === -1 && targetId === this.nodes.length - 1))
            ) {
              console.log("Found matching event:", key, event);
              this.originalEventKey = key;
              this.originalEvent = {
                ...event,
              };

              // 如果有fields字段，添加到linkFields中
              if (event.fields && event.fields.length) {
                this.linkFields = event.fields.map((field) => ({
                  ...field,
                }));
              }

              // 更新JSON数据为原始事件数据
              this.updateLinkJsonData(event);
            }
          });
        }

        // 如果没有找到匹配的原始事件，作为后备，从eventsData中查找
        if (!this.originalEvent && this.eventsData) {
          Object.entries(this.eventsData).forEach(([key, event]) => {
            if (event.from_action_id === sourceId && event.to_action_id === targetId) {
              console.log("Found matching event in eventsData:", key, event);

              // 如果有fields字段，添加到linkFields中
              if (event.fields && event.fields.length) {
                this.linkFields = event.fields.map((field) => ({
                  ...field,
                }));
              }

              // 更新JSON数据
              this.updateLinkJsonData(event);
            }
          });
        }

        // 移除高亮效果，改用蒙版
        // this.highlightSelectedLink();

        // 在找到匹配事件后，添加备份
        if (this.originalEvent) {
          // 保存备份用于重置
          this.backupLinkData = {
            link: JSON.parse(JSON.stringify(this.selectedLink)),
            event: JSON.parse(JSON.stringify(this.originalEvent)),
            fields: JSON.parse(JSON.stringify(this.linkFields)),
          };
        }
      }
    },

    // 从workflow原始数据中查找事件数据
    findOriginalEventData(sourceId, targetId) {
      try {
        // 确保workflow数据存在
        if (this.workflow && this.workflow.events) {
          // 查找匹配的事件
          return Object.values(this.workflow.events).find(
            (event) =>
              event.from_action_id === sourceId && event.to_action_id === targetId
          );
        }
        return null;
      } catch (error) {
        console.error("查找原始事件数据失败:", error);
        return null;
      }
    },

    // 从workflow原始数据中查找节点数据
    findOriginalNodeData(nodeId) {
      try {
        // 确保workflow数据存在
        if (this.workflow && this.workflow.actions) {
          // 遍历所有代理类型
          for (const agentType in this.workflow.actions) {
            // 在每种代理类型中查找匹配的节点
            const foundAction = this.workflow.actions[agentType].find(
              (action) => action.id === nodeId
            );
            if (foundAction) {
              return {
                action: foundAction,
                agentType: agentType,
                originalKey: `${agentType}_${foundAction.id}`,
              };
            }
          }
        }
        return null;
      } catch (error) {
        console.error("查找原始节点数据失败:", error);
        return null;
      }
    },

    // 关闭连线编辑器
    closeLinkEditor() {
      // 先添加淡出类，然后使用setTimeout确保动画完成后再真正关闭编辑器
      const linkEditor = this.$el.querySelector(".link-editor");
      if (linkEditor) {
        linkEditor.classList.add("fade-out");
        setTimeout(() => {
          this.selectedLink = null;
          this.linkFields = [];
          this.linkJsonData = "";
          this.jsonError = null;
          this.activeTab = "form";
          this.originalEventKey = null;
          this.originalEvent = null;
          linkEditor.classList.remove("fade-out");
        }, 300); // 动画持续时间
      } else {
        this.selectedLink = null;
        this.linkFields = [];
        this.linkJsonData = "";
        this.jsonError = null;
        this.activeTab = "form";
        this.originalEventKey = null;
        this.originalEvent = null;
      }

      console.log("Link editor closing with animation");
    },

    // 关闭所有编辑器的方法
    closeAllEditors() {
      this.closeEditor();
      this.closeLinkEditor();
    },

    // 应用连线修改，使用Element UI组件
    applyLinkChanges() {
      if (!this.selectedLink) return;

      try {
        if (this.activeTab === "json") {
          // 从JSON数据更新
          try {
            const updatedData = JSON.parse(this.linkJsonData);

            // 找到原始连线（使用oldSource和oldTarget如果存在）
            const sourceToCheck = this.selectedLink.oldSource || this.selectedLink.source;
            const targetToCheck = this.selectedLink.oldTarget || this.selectedLink.target;

            const linkIndex = this.links.findIndex(
              (link) => link.source === sourceToCheck && link.target === targetToCheck
            );

            if (linkIndex !== -1) {
              // 更新连线数据
              this.links[linkIndex] = {
                ...this.links[linkIndex],
                source: updatedData.from_action_id,
                target: updatedData.to_action_id,
                name: updatedData.event_name,
                value: updatedData.event_name,
                info: updatedData.event_info || "",
              };

              // 如果找到原始事件数据，更新workflow
              if (this.originalEventKey && this.workflow.events) {
                this.workflow.events[this.originalEventKey] = {
                  ...updatedData,
                };
                console.log(
                  "Updated workflow event:",
                  this.originalEventKey,
                  this.workflow.events[this.originalEventKey]
                );
              }

              // 同时更新eventsData如果存在
              if (this.eventsData) {
                Object.keys(this.eventsData).forEach((key) => {
                  const event = this.eventsData[key];
                  if (
                    event.from_action_id === this.selectedLink.source &&
                    event.to_action_id === this.selectedLink.target
                  ) {
                    // 更新事件数据
                    this.eventsData[key] = {
                      ...updatedData,
                    };
                  }
                });
              }
            }
          } catch (error) {
            console.error("解析JSON失败:", error);
            this.jsonError = "Invalid JSON format: " + error.message;
            return;
          }
        } else {
          // 从表单数据更新
          // 找到原始连线（使用oldSource和oldTarget如果存在）
          const sourceToCheck = this.selectedLink.oldSource || this.selectedLink.source;
          const targetToCheck = this.selectedLink.oldTarget || this.selectedLink.target;

          const linkIndex = this.links.findIndex(
            (link) => link.source === sourceToCheck && link.target === targetToCheck
          );

          if (linkIndex !== -1) {
            // 更新连线数据
            this.links[linkIndex] = {
              ...this.links[linkIndex],
              name: this.selectedLink.name,
              value: this.selectedLink.name,
              info: this.selectedLink.info || "",
            };

            // 如果找到原始事件，更新workflow
            if (this.originalEventKey && this.workflow.events) {
              this.workflow.events[
                this.originalEventKey
              ].event_name = this.selectedLink.name;
              this.workflow.events[this.originalEventKey].event_info = this.selectedLink.info || "";

              // 更新字段
              if (this.linkFields && this.linkFields.length) {
                this.workflow.events[this.originalEventKey].fields = this.linkFields.map(
                  (field) => ({
                    name: field.name,
                    type: field.type,
                    default_value: field.default_value || "",
                    description: field.description || "",
                  })
                );
              }
              console.log(
                "Updated workflow event fields:",
                this.originalEventKey,
                this.workflow.events[this.originalEventKey]
              );
            }

            // 同时更新eventsData如果存在
            if (this.eventsData) {
              Object.keys(this.eventsData).forEach((key) => {
                const event = this.eventsData[key];
                if (
                  event.from_action_id === this.selectedLink.source &&
                  event.to_action_id === this.selectedLink.target
                ) {
                  // 更新事件数据
                  this.eventsData[key] = {
                    ...event,
                    event_name: this.selectedLink.name,
                    event_info: this.selectedLink.info || "",
                    fields: this.linkFields.map((field) => ({
                      name: field.name,
                      type: field.type,
                      default_value: field.default_value || "",
                      description: field.description || "",
                    })),
                  };
                }
              });
            }
          }
        }

        // 重新加载和渲染图表
        this.updateChart();
        // 设置工作流已修改标志
        this.isWorkflowChanged = true;
        // 使用Element UI提示操作成功
        this.$message({
          message: "Connection modification applied successfully",
          type: "success",
          duration: 2000,
        });

        // 使用淡出效果关闭编辑器
        this.closeLinkEditor();

        // 如果找到并更新了原始事件数据，尝试重新加载
        if (this.originalEventKey && this.workflow.events) {
          // 将通知定时器延迟，确保数据已经更新
          setTimeout(() => {
            this.$message({
              message: "Connection updated successfully, reloading data...",
              type: "success",
              duration: 2000,
            });



            // 优先使用原始workflow数据重新处理拓扑结构
            if (this.workflow) {
              const updatedTopology = {
                nodes: [
                  {
                    id: 0,
                    label: "start",
                    agentType: "EnvAgent",
                    color: "#29ebd7",
                  },
                  ...Object.entries(this.workflow.actions).flatMap(
                    ([agentType, actions]) =>
                      actions.map((action) => ({
                        id: action.id,
                        label: action.name,
                        agentType: agentType,
                        color: this.getColorForAgent(agentType),
                        description: action.description,
                        type: action.type,
                        required_variables: action.required_variables,
                        output_updates: action.output_updates,
                      }))
                  ),
                ],
                links: [
                  ...Object.values(this.workflow.events).map((event) => ({
                    source: event.from_action_id,
                    target: event.to_action_id,
                    name: event.event_name,
                    info: event.event_info,
                  })),
                ],
              };
              // 修改-1为最后一个节点的ID
              updatedTopology.links = updatedTopology.links.map((link) => ({
                ...link,
                source: link.source === -1 ? updatedTopology.nodes.length : link.source,
                target: link.target === -1 ? updatedTopology.nodes.length : link.target,
              }));
              // 添加终止节点
              updatedTopology.nodes.push({
                id: updatedTopology.nodes.length,
                label: "terminate",
                agentType: "EnvAgent",
                color: "#29ebd7",
              });
              // 确保所有ID是数字类型
              updatedTopology.nodes = updatedTopology.nodes.map((node) => ({
                ...node,
                id: typeof node.id === "string" ? parseInt(node.id) : node.id,
              }));

              updatedTopology.links = updatedTopology.links.map((link) => ({
                ...link,
                source:
                  typeof link.source === "string" ? parseInt(link.source) : link.source,
                target:
                  typeof link.target === "string" ? parseInt(link.target) : link.target,
              }));

              this.processTopologyData(updatedTopology);
            }
          }, 500);
        }
      } catch (error) {

        // 使用Element UI提示错误
        this.$message({
          message: "Failed to apply modifications: " + error.message,
          type: "error",
          duration: 3000,
        });
      }
    },

    // 删除连线，使用Element UI组件
    deleteLink() {
      if (!this.selectedLink) return;

      // 使用Element UI确认对话框
      this.$confirm(
        "Are you sure you want to delete this connection? This action cannot be undone.",
        "Warning",
        {
          confirmButtonText: "Delete",
          cancelButtonText: "Cancel",
          type: "warning",
        }
      )
        .then(() => {
          try {
            // 从links数组中移除连线
            this.links = this.links.filter(
              (link) =>
                !(
                  link.source === this.selectedLink.source &&
                  link.target === this.selectedLink.target &&
                  link.name === this.selectedLink.name
                )
            );

            // 如果找到原始事件，从workflow中删除
            if (this.originalEventKey && this.workflow.events) {
              delete this.workflow.events[this.originalEventKey];
              console.log("Deleted workflow event:", this.originalEventKey);
            }

            // 同时从eventsData中删除（如果存在）
            if (this.eventsData) {
              // 创建一个新对象而不是直接修改原对象，避免proxy错误
              const updatedEventsData = {
                ...this.eventsData,
              };
              Object.keys(updatedEventsData).forEach((key) => {
                const event = updatedEventsData[key];
                if (
                  event.from_action_id === this.selectedLink.source &&
                  event.to_action_id === this.selectedLink.target
                ) {
                  delete updatedEventsData[key];
                }
              });
              // 通过事件通知父组件更新eventsData
              this.$emit("update:eventsData", updatedEventsData);
            }

            // 重新加载和渲染图表
            this.updateChart();

            // 使用Element UI提示操作成功
            this.$message({
              message: "Connection deleted successfully",
              type: "success",
              duration: 2000,
            });

            // 关闭编辑器
            this.closeLinkEditor();
          } catch (error) {

            // 使用Element UI提示错误
            this.$message({
              message: "Failed to delete connection: " + error.message,
              type: "error",
              duration: 3000,
            });
          }
        })
        .catch(() => {
          // 用户取消删除操作
          this.$message({
            type: "info",
            message: "Delete operation canceled",
          });
        });
    },

    // 更新连线JSON数据
    updateLinkJsonData(eventData) {
      try {
        if (eventData) {
          // 格式化JSON数据
          this.linkJsonData = JSON.stringify(eventData, null, 2);

          // 同步更新表单数据
          if (this.selectedLink) {
            this.selectedLink.name = eventData.event_name || this.selectedLink.name;
            this.selectedLink.info = eventData.event_info || "";
          }

          // 同步更新字段数据
          if (eventData.fields && eventData.fields.length) {
            this.linkFields = eventData.fields.map((field) => ({
              ...field,
            }));
          }
        } else {
          // 如果没有找到事件数据，使用当前选中的连线数据
          this.linkJsonData = JSON.stringify(
            {
              from_action_id: this.selectedLink.source,
              to_action_id: this.selectedLink.target,
              event_name: this.selectedLink.name,
              event_info: this.selectedLink.info || "",
              fields: this.linkFields || [],
            },
            null,
            2
          );
        }
        this.jsonError = null;
      } catch (error) {
        this.jsonError = "Cannot parse JSON data: " + error.message;
      }
    },

    // 恢复高亮和取消高亮的方法
    // 高亮选中的连线和相关节点
    highlightSelectedLink() {
      if (!this.selectedLink || !this.chart) return;

      try {
        // 创建高亮样式
        const highlightOption = {
          series: [
            {
              // 高亮连线
              edges: this.chartOption.series[0].links.map((link) => {
                if (
                  link.source === this.selectedLink.source &&
                  link.target === this.selectedLink.target
                ) {
                  return {
                    ...link,
                    lineStyle: {
                      ...link.lineStyle,
                      width: 4,
                      color: "#ffcc00",
                      shadowBlur: 10,
                      shadowColor: "rgba(255, 204, 0, 0.5)",
                    },
                  };
                }
                // 其他连线变暗
                return {
                  ...link,
                  lineStyle: {
                    ...link.lineStyle,
                    opacity: 0.2,
                  },
                };
              }),
              // 高亮相关节点
              data: this.chartOption.series[0].data.map((node) => {
                if (
                  node.id === this.selectedLink.source ||
                  node.id === this.selectedLink.target
                ) {
                  return {
                    ...node,
                    itemStyle: {
                      ...node.itemStyle,
                      borderWidth: 4,
                      borderColor: "#ffcc00",
                      shadowBlur: 10,
                      shadowColor: "rgba(255, 204, 0, 0.5)",
                    },
                  };
                }
                // 其他节点变暗
                return {
                  ...node,
                  itemStyle: {
                    ...node.itemStyle,
                    opacity: 0.2,
                  },
                };
              }),
            },
          ],
        };

        // 应用高亮样式
        this.chart.setOption(highlightOption);
      } catch (error) {
      }
    },

    // 重置高亮
    resetHighlight() {
      if (!this.chart) return;

      try {
        // 恢复所有节点和连线的原始样式
        const resetOption = {
          series: [
            {
              data: this.chartOption.series[0].data.map((node) => ({
                ...node,
                itemStyle: {
                  ...node.itemStyle,
                  opacity: 1,
                  borderWidth: undefined,
                  borderColor: undefined,
                  shadowBlur: undefined,
                  shadowColor: undefined,
                },
                symbolSize: node.originSize || node.symbolSize || 50, // 恢复原始大小
                z: undefined,
              })),
              links: this.chartOption.series[0].links.map((link) => ({
                ...link,
                lineStyle: {
                  ...link.lineStyle,
                  opacity: 1,
                  width: 2,
                  color: link.originalColor || "source",
                  shadowBlur: undefined,
                  shadowColor: undefined,
                  curveness: 0,
                },
                label: {
                  ...link.label,
                  show: true,
                  fontWeight: "normal",
                  fontSize: 12,
                },
                edgeSymbol: ["none", "arrow"],
                edgeSymbolSize: [0, 8], // 恢复箭头默认大小
                z: undefined,
              })),
            },
          ],
        };

        // 应用重置样式
        this.chart.setOption(resetOption, false);
      } catch (error) {
        // 如果重置失败，尝试整体更新图表
        this.updateChart();
      }
    },

    addNewField() {
      // 验证是否已选择连线
      if (!this.selectedLink) {
        this.$message({
          message: "Please select a link first.",
          type: "warning",
          duration: 2000
        });
        return;
      }

      // 创建新字段名，确保不重复
      let fieldName = "new_field";
      let counter = 1;
      let newFieldName = `${fieldName}_${counter}`;

      // 检查字段名是否已存在
      while (this.linkFields.some(field => field.name === newFieldName)) {
        counter++;
        newFieldName = `${fieldName}_${counter}`;
      }

      // 添加新字段
      this.linkFields.push({
        name: newFieldName,
        type: "string",
        default_value: "",
        description: "",
      });

      // 添加字段后更新JSON
      this.updateJsonFromForm();

      this.$message({
        message: `New field added: ${newFieldName}`,
        type: "success",
        duration: 2000
      });
    },

    removeField(index) {
      if (index >= 0 && index < this.linkFields.length) {
        this.linkFields.splice(index, 1);
        // 删除字段后更新JSON
        this.updateJsonFromForm();
      }
    },

    // 重置连线更改
    resetLinkChanges() {
      if (!this.backupLinkData) return;

      this.$confirm(
        "Are you sure you want to reset all changes? Any unsaved changes will be lost.",
        "Warning",
        {
          confirmButtonText: "Reset",
          cancelButtonText: "Cancel",
          type: "warning",
        }
      )
        .then(() => {
          // 还原备份数据
          this.selectedLink = JSON.parse(JSON.stringify(this.backupLinkData.link));
          this.originalEvent = JSON.parse(JSON.stringify(this.backupLinkData.event));
          this.linkFields = JSON.parse(JSON.stringify(this.backupLinkData.fields));

          // 更新JSON数据
          this.updateLinkJsonData(this.originalEvent);

          this.$message({
            message: "Changes have been reset to original",
            type: "info",
            duration: 2000,
          });
        })
        .catch(() => {
          // 用户取消
        });
    },

    switchToFormMode() {
      // 从JSON模式切换到表单模式
      if (this.activeTab === "json") {
        try {
          const updatedData = JSON.parse(this.linkJsonData);

          // 更新表单数据
          if (this.selectedLink) {
            this.selectedLink.name = updatedData.event_name || this.selectedLink.name;
            this.selectedLink.info = updatedData.event_info || "";
          }

          // 更新字段数据
          if (updatedData.fields && updatedData.fields.length) {
            this.linkFields = updatedData.fields.map((field) => ({
              ...field,
            }));
          }
        } catch (e) {
          this.$message.error("Invalid JSON format, cannot switch to form mode.");
          return; // 阻止切换
        }
      }
      this.activeTab = "form";
    },

    switchToJsonMode() {
      // 从表单模式切换到JSON模式
      if (this.activeTab === "form") {
        // 使用updateJsonFromForm而不是updateLinkJsonData
        this.updateJsonFromForm();
      }
      this.activeTab = "json";
    },

    updateJsonFromForm() {
      // 当表单中的数据变更时，同步更新JSON数据
      if (this.activeTab === "form") {
        try {
          // 创建更新的事件数据对象
          let updatedEvent;

          if (this.originalEvent) {
            // 如果有原始事件数据，基于原始数据更新
            updatedEvent = {
              ...this.originalEvent,
              event_name: this.selectedLink.name,
              event_info: this.selectedLink.info || "",
              fields: this.linkFields.map((field) => ({
                name: field.name,
                type: field.type,
                default_value: field.default_value || "",
                description: field.description || "",
              })),
            };
          } else {
            // 否则基于当前的链接数据创建新的事件数据
            updatedEvent = {
              from_action_id: this.selectedLink.source,
              to_action_id: this.selectedLink.target,
              event_name: this.selectedLink.name,
              event_info: this.selectedLink.info || "",
              fields: this.linkFields.map((field) => ({
                name: field.name,
                type: field.type,
                default_value: field.default_value || "",
                description: field.description || "",
              })),
            };
          }

          // 更新JSON数据
          this.linkJsonData = JSON.stringify(updatedEvent, null, 2);
        } catch (error) {
          this.jsonError = "Cannot update JSON data: " + error.message;
        }
      }
    },

    updateSourceNode(nodeId) {
      if (this.selectedLink) {
        // 更新源节点ID
        this.selectedLink.source = nodeId;

        // 如果原始事件数据存在，更新from_action_id
        if (this.originalEvent) {
          this.originalEvent.from_action_id = nodeId;

          // 更新from_action_name
          const node = this.nodes.find((n) => n.id === nodeId);
          if (node) {
            this.originalEvent.from_action_name = node.label || node.name;
          }
        }

        // 查找并更新连接
        const linkIndex = this.links.findIndex(
          (link) =>
            (link.source === this.selectedLink.oldSource ||
              link.source === this.selectedLink.source) &&
            link.target === this.selectedLink.target
        );

        if (linkIndex !== -1) {
          // 保存旧的source值用于后续比较
          this.selectedLink.oldSource = this.selectedLink.source;
          // 更新连线数据
          this.links[linkIndex].source = nodeId;
        }
        // 更新JSON数据
        this.updateJsonFromForm();
      }
    },

    updateTargetNode(nodeId) {
      if (this.selectedLink) {
        // 更新目标节点ID
        this.selectedLink.target = nodeId;

        // 如果原始事件数据存在，更新to_action_id
        if (this.originalEvent) {
          this.originalEvent.to_action_id = nodeId;
          // 更新to_action_name
          const node = this.nodes.find((n) => n.id === nodeId);
          if (node) {
            this.originalEvent.to_action_name = node.label || node.name;
          }
        }

        // 查找并更新连接
        const linkIndex = this.links.findIndex(
          (link) =>
            link.source === this.selectedLink.source &&
            (link.target === this.selectedLink.oldTarget ||
              link.target === this.selectedLink.target)
        );

        if (linkIndex !== -1) {
          // 保存旧的target值用于后续比较
          this.selectedLink.oldTarget = this.selectedLink.target;
          // 更新连线数据
          this.links[linkIndex].target = nodeId;
        }

        // 更新JSON数据
        this.updateJsonFromForm();
      }
    },

    resetNodeChanges() {
      if (!this.backupNodeData) return;
      this.$confirm(
        "Are you sure you want to reset all changes? Any unsaved changes will be lost.",
        "Warning",
        {
          confirmButtonText: "Reset",
          cancelButtonText: "Cancel",
          type: "warning",
        }
      )
        .then(() => {
          // 还原备份数据
          this.selectedNode = JSON.parse(JSON.stringify(this.backupNodeData));

          // 如果原始数据中有originalData，则使用它的数据更新节点
          if (this.selectedNode.originalData) {
            const originalNodeData = this.selectedNode.originalData;

            // 将原始数据同步到当前节点
            if (originalNodeData.name) {
              this.selectedNode.label = originalNodeData.name;
            }

            if (originalNodeData.action) {
              this.selectedNode.type = originalNodeData.action.type || this.selectedNode.type;
              this.selectedNode.required_variables = originalNodeData.action.required_variables || [];
              this.selectedNode.output_updates = originalNodeData.action.output_updates || [];
            }
          }

          // 同时更新nodeJsonData
          this.updateNodeJsonData();

          this.$message({
            message: "Node changes have been reset to original",
            type: "info",
            duration: 2000,
          });
        })
        .catch(() => {
          // 用户取消
        });
    },

    // 更新节点JSON数据
    updateNodeJsonData() {
      try {
        if (this.selectedNode) {
          // 创建要显示在JSON编辑器中的数据对象
          const nodeJsonObj = {
            id: this.selectedNode.id,
            name: this.selectedNode.label,
            agentType: this.selectedNode.agentType,
            description: this.selectedNode.description,
            type: this.selectedNode.type,
            required_variables: this.selectedNode.required_variables || [],
            output_updates: this.selectedNode.output_updates || [],
          };

          // 格式化JSON数据
          this.nodeJsonData = JSON.stringify(nodeJsonObj, null, 2);
          this.nodeJsonError = null;
        }
      } catch (error) {
        this.nodeJsonError = "Cannot generate JSON data: " + error.message;
      }
    },

    // 从节点JSON更新表单
    updateNodeFormFromJson() {
      if (this.activeNodeTab !== "json" || !this.selectedNode) {
        return;
      }

      try {
        const updatedData = JSON.parse(this.nodeJsonData);

        // 更新表单数据
        this.selectedNode.label = updatedData.name || this.selectedNode.label;
        this.selectedNode.description = updatedData.description || "";
        this.selectedNode.agentType =
          updatedData.agentType || this.selectedNode.agentType;
        this.selectedNode.type = updatedData.type || this.selectedNode.type;
        this.selectedNode.required_variables = updatedData.required_variables || [];
        this.selectedNode.output_updates = updatedData.output_updates || [];

        this.nodeJsonError = null;
      } catch (e) {
        this.nodeJsonError = "Invalid JSON format: " + e.message;
      }
    },

    // 切换到节点表单模式
    switchToNodeFormMode() {
      if (this.activeNodeTab === "json") {
        this.updateNodeFormFromJson();
      }
      this.activeNodeTab = "form";
    },

    // 切换到节点JSON模式
    switchToNodeJsonMode() {
      if (this.activeNodeTab === "form") {
        this.updateNodeJsonData();
      }
      this.activeNodeTab = "json";
    },
    /**
     * 加载失败返回dashboard
     */
    backToDashboard(num) {
      ElMessageBox.confirm(
        "Fail to generate the workflow, you need more detailed scenario description.",
        "Notice",
        {
          confirmButtonText: "OK",
          type: "warning"
        }
      ).then(() => {
        // 因为这里也是返回的所以也需要清除一下window.query
        window.query = null;

        this.$emit('back-to-chat-mode');

        // this.$router.push({
        //   path: "/simulation",
        //   query: {
        //     model_name:this.$route.query.model_name,
        //     category: this.$route.query.category,
        //     step: 1,
        //   },
        // });
      })
    }
  },
};
</script>

<style scoped>
.topology-editor-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  color: var(--text-color);
  position: relative;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top: 3px solid var(--accent-color);
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 10px;
  font-size: 1rem;
  color: #fff;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(50px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }

  to {
    opacity: 0;
    transform: translateX(50px);
  }
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 0 15px;
  margin-top: 15px;
}

.tool-group {
  display: flex;
  gap: 8px;
}

.tool-btn {
  padding: 10px 15px;
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s ease;
  font-size: 0.85rem;
}

.tool-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.tool-btn.active {
  background-color: #f44336;
}

.tool-btn.restore-btn {
  background-color: #ffa000;
}

.tool-btn.restore-btn:hover {
  background-color: #ffb300;
}

.tool-btn.save-btn {
  background-color: #4caf50;
}

.tool-btn.save-btn:hover {
  background-color: #45a049;
}

.tool-btn i {
  position: relative;
  top: 2px;
}

.linking-status {
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px 12px;
  position: absolute;
  top: 50px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  border-radius: 4px;
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.cancel-btn {
  margin-left: 10px;
  background-color: transparent;
  border: 1px solid rgba(255, 255, 255, 0.5);
  color: white;
  border-radius: 3px;
  padding: 3px 6px;
  font-size: 0.8rem;
  cursor: pointer;
}

.cancel-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.linking-mode {
  cursor: crosshair;
}

.chart-container {
  height: 80vh;
  width: 100%;
}

.node-editor {
  position: absolute;
  top: 0;
  right: -50vw;
  width: 50vw;
  height: calc(100vh - 90px);
  background-color: var(--sidebar-bg);
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.2);
  transition: right 0.3s ease, opacity 0.3s ease, transform 0.3s ease;
  z-index: 900;
  display: flex;
  flex-direction: column;
  opacity: 0;
  transform: translateX(50px);
}

.node-editor.visible {
  right: 0;
  opacity: 1;
  transform: translateX(0);
  animation: fadeIn 0.3s ease-out forwards;
}

.node-editor.fade-out {
  animation: fadeOut 0.3s ease-in forwards;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
}

.editor-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-color);
  font-size: 1.2rem;
  cursor: pointer;
}

.editor-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 80px;
  /* 为底部按钮留出空间 */
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: flex;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.form-group textarea {
  resize: vertical;
}

.form-group input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.fields-section {
  margin-top: 30px;
}

.fields-section h4 {
  margin-bottom: 15px;
  font-size: 1.1rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.field-item {
  background-color: var(--bg-hover);
  padding: 12px;
  border-radius: 5px;
  margin-bottom: 15px;
  border: 1px solid var(--border-color);
}

.field-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.field-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.field-name {
  font-weight: 500;
}

.field-type {
  font-size: 0.9rem;
  opacity: 0.7;
}

.field-item input,
.field-item textarea {
  width: 100%;
  padding: 8px 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  resize: vertical;
}

.field-value,
.field-description {
  margin-top: 8px;
}

.field-value label,
.field-description label {
  display: block;
  font-size: 0.9rem;
  color: var(--text-secondary-color);
  margin-bottom: 4px;
}

.editor-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 15px 20px;
  background-color: var(--sidebar-bg);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  z-index: 10;
}

.reset-btn {
  background-color: #ffa000;
}

.reset-btn:hover {
  background-color: #ff8f00;
}

.primary-btn,
.danger-btn,
.reset-btn {
  padding: 10px 15px;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.primary-btn {
  background-color: var(--accent-color);
}

.danger-btn {
  background-color: #f44336;
}

/* Light theme adjustments */
.light-theme .loading-overlay {
  background-color: rgba(255, 255, 255, 0.7);
}

.light-theme .loading-text {
  color: #333;
}

.light-theme .linking-status {
  background-color: rgba(0, 0, 0, 0.15);
  color: #333;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.light-theme .cancel-btn {
  color: #333;
  border-color: rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {

  .node-editor,
  .link-editor {
    width: 100%;
    right: -100%;
    transform: translateX(100px);
  }

  .node-editor.visible,
  .link-editor.visible {
    right: 0;
    width: 100%;
    z-index: 1000;
    transform: translateX(0);
  }

  .toolbar {
    flex-direction: column;
    gap: 10px;
  }
}

.debug-btn {
  background-color: #795548;
}

.debug-btn:hover {
  background-color: #8d6e63;
}

.test-btn {
  background-color: #673ab7;
}

.test-btn:hover {
  background-color: #7e57c2;
}

/* JSON调试弹窗样式 */
.json-debug-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1100;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.json-debug-panel {
  width: 50%;
  max-width: 800px;
  height: 90vh;
  background-color: var(--bg-color);
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  margin-left: 2%;
  position: relative;
}

.json-debug-header {
  padding: 15px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.json-debug-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.json-debug-actions {
  display: flex;
  gap: 10px;
}

.copy-btn {
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 3px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 5px;
}

.json-debug-content {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.markdown-content h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  font-size: 1.1rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 5px;
}

.markdown-content pre {
  background-color: var(--sidebar-bg);
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0;
}

.markdown-content code {
  font-family: monospace;
  font-size: 0.9rem;
  line-height: 1.4;
  color: var(--text-color);
}

.warning-section {
  margin-top: 20px;
  padding: 10px;
  background-color: rgba(255, 87, 34, 0.1);
  border-left: 4px solid #ff5722;
  border-radius: 4px;
}

.warning-section h4 {
  color: #ff5722;
  margin-top: 0;
  border-bottom: none;
}

.warning-section ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.warning-section li {
  margin-bottom: 5px;
}

.form-section {
  margin-bottom: 25px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 15px;
  background-color: rgba(0, 0, 0, 0.05);
}

.form-section h4 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.1rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.action-details {
  margin-top: 10px;
}

.variable {
  background-color: var(--bg-color);
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  border-left: 3px solid var(--accent-color);
}

.variable-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.variable-name {
  font-weight: bold;
  color: var(--accent-color);
}

.variable-type {
  font-size: 0.9em;
  color: var(--text-secondary-color);
}

.variable-description {
  font-size: 0.9em;
  color: var(--text-color);
  margin: 5px 0;
}

.variable-actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.action-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  border-radius: 3px;
  padding: 3px 8px;
  font-size: 0.8em;
  cursor: pointer;
}

.action-btn:hover {
  background-color: var(--bg-hover);
}

.add-btn {
  display: block;
  width: 100%;
  background-color: var(--bg-color);
  border: 1px dashed var(--border-color);
  border-radius: 4px;
  padding: 8px;
  margin-top: 10px;
  text-align: center;
  cursor: pointer;
  color: var(--text-color);
}

.add-btn:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent-color);
  color: var(--accent-color);
}

.link-editor {
  position: absolute;
  top: 0;
  right: -50vw;
  width: 50vw;
  height: calc(100vh - 90px);
  background-color: var(--sidebar-bg);
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.2);
  transition: right 0.3s ease, opacity 0.3s ease, transform 0.3s ease;
  z-index: 900;
  display: flex;
  flex-direction: column;
  opacity: 0;
  transform: translateX(50px);
}

.link-editor.visible {
  right: 0;
  opacity: 1;
  transform: translateX(0);
  animation: fadeIn 0.3s ease-out forwards;
}

.link-editor.fade-out {
  animation: fadeOut 0.3s ease-in forwards;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
}

.editor-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-color);
  font-size: 1.2rem;
  cursor: pointer;
}

.editor-content {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.form-group textarea {
  resize: vertical;
}

.form-group input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.fields-section {
  margin-top: 30px;
}

.fields-section h4 {
  margin-bottom: 15px;
  font-size: 1.1rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.field-item {
  margin-bottom: 15px;
}

.field-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.field-name {
  font-weight: 500;
}

.field-type {
  font-size: 0.9rem;
  opacity: 0.7;
}

.field-item input,
.field-item textarea {
  width: 100%;
  padding: 8px 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  resize: vertical;
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
}

.primary-btn,
.danger-btn {
  padding: 10px 15px;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.primary-btn {
  background-color: var(--accent-color);
}

.danger-btn {
  background-color: #f44336;
}

.json-editor-section {
  margin-top: 15px;
  height: calc(100% - 130px);
  /* 减去顶部元素高度和边距 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 15px;
  background-color: rgba(0, 0, 0, 0.05);
}

.json-editor-section h4 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.1rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.json-editor {
  margin-top: 10px;
  height: calc(100% - 60px);
  /* 减去标题和边距的高度 */
  display: flex;
  flex-direction: column;
}

.json-textarea {
  width: 100%;
  height: 100%;
  min-height: 300px;
  font-family: monospace;
  font-size: 0.9rem;
  padding: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  resize: vertical;
  overflow: auto;
}

.json-error {
  margin-top: 10px;
  color: #f44336;
  font-size: 0.9rem;
}

/* 高亮模式 */
.chart-container.highlight-mode {
  position: relative;
}

.chart-container.highlight-mode::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

/* 连线编辑器样式 */
.link-editor {
  position: absolute;
  top: 0;
  right: -50vw;
  width: 50vw;
  height: calc(100vh - 90px);
  background-color: var(--sidebar-bg);
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.2);
  transition: right 0.3s ease, opacity 0.3s ease, transform 0.3s ease;
  z-index: 900;
  display: flex;
  flex-direction: column;
  opacity: 0;
  transform: translateX(50px);
}

.link-editor.visible {
  right: 0;
  opacity: 1;
  transform: translateX(0);
  animation: fadeIn 0.3s ease-out forwards;
}

.link-editor.fade-out {
  animation: fadeOut 0.3s ease-in forwards;
}

.editor-tabs {
  display: flex;
  margin-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--secondary-bg);
  padding: 0;
  width: 100%;
}

.tab {
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 500;
  text-align: center;
  flex: 1;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
}

.tab.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
  background-color: var(--sidebar-bg);
}

.tab:hover:not(.active) {
  background-color: rgba(0, 0, 0, 0.05);
}

.connection-info {
  background-color: var(--bg-hover);
  padding: 10px 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  border-left: 3px solid var(--accent-color);
}

.connection-label {
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.no-fields {
  color: var(--text-secondary-color);
  font-style: italic;
  padding: 10px;
  text-align: center;
  border: 1px dashed var(--border-color);
  border-radius: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h4 {
  margin: 0;
  font-size: 1.1rem;
}

.add-field-btn {
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 5px 10px;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.add-field-btn:hover {
  background-color: var(--accent-hover-color, #1565c0);
}

.remove-field-btn {
  background: none;
  border: none;
  color: var(--danger-color, #f44336);
  cursor: pointer;
  padding: 5px;
  border-radius: 3px;
}

.remove-field-btn:hover {
  background-color: rgba(244, 67, 54, 0.1);
}

.field-type-select {
  min-width: 120px;
}

.field-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.field-actions {
  display: flex;
  gap: 5px;
}

.field-name-input,
.field-value-input,
.field-description-input {
  width: 100%;
  padding: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.two-column-layout {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.two-column-layout .column {
  flex: 1;
}

.fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.field-content {
  padding: 8px;
}

.field-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.field-column {
  flex: 1;
  min-width: 120px;
}

/* 针对节点编辑器的样式 */
.node-editor .editor-actions {
  justify-content: flex-end;
  gap: 10px;
  display: flex;
}

/* 针对节点编辑器底部按钮的样式优化 */
.node-editor .editor-actions>div {
  display: flex;
  gap: 10px;
}

/* 针对链接编辑器底部按钮的样式优化 */
.link-editor .editor-actions>div {
  display: flex;
  gap: 10px;
}

.form-layout {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 覆盖Element UI样式 */
:deep(.el-select .el-input__inner) {
  background-color: var(--input-bg);
  border-color: var(--border-color);
  color: var(--text-color);
}

:deep(.el-select-dropdown) {
  background-color: var(--sidebar-bg);
  border-color: var(--border-color);
}

:deep(.el-select-dropdown__item) {
  color: var(--text-color);
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-select-dropdown__item.selected) {
  color: var(--primary-color);
  background-color: rgba(64, 158, 255, 0.15);
}

/* 编辑器蒙版样式 */
.editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 800;
  /* 比编辑器的z-index (900) 低，比chart-container高 */
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s ease;
  animation: fadeInOverlay 0.3s forwards;
}

@keyframes fadeInOverlay {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
