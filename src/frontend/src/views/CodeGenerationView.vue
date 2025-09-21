<template>
	<div class="code-generation-container">
		<!-- Header progress area -->
		<div class="progress-header">
			<div class="stage-indicator">
				<div class="stage" :class="{ active: currentStage === 1 }">
					<div class="stage-number">1</div>
					<div class="stage-name">Code Programming</div>
				</div>
				<div class="stage-separator"></div>
				<div class="stage" :class="{ active: currentStage === 2 }">
					<div class="stage-number">2</div>
					<div class="stage-name">Code Refinement</div>
				</div>
				<div class="stage-separator"></div>
				<div class="stage" :class="{ active: currentStage === 3 }">
					<div class="stage-number">3</div>
					<div class="stage-name">Final Results</div>
				</div>
			</div>

			<!-- Stage 3 action buttons -->
			<div v-if="currentStage === 3" class="topology-actions">
				<button class="action-btn reset-btn" @click="resetProcess">
					<i class="fa fa-refresh"></i> Reset
				</button>
				<button class="action-btn confirm-btn" @click="confirmTopology" :disabled="!hasWorkflowData">
					<i class="fa fa-check"></i> Confirm
				</button>
			</div>
		</div>

		<!-- Middle code display area - fixed height -->
		<div class="code-content-wrapper" v-if="currentStage !== 3">
			<div class="code-editor-container">
				<div class="code-editor-header">
					<div class="stage-status">
						<div class="status-indicator" :class="{ 'pulse': !generationComplete }"></div>
						<div class="status-text">{{ currentStatusText }}</div>
					</div>
					<div class="stage-time" v-if="!generationComplete">
						<div class="time-icon"><i class="fa fa-clock-o"></i></div>
						<div class="time-estimate">{{ stageTimeEstimate }}</div>
					</div>
				</div>
				<div class="code-display-wrapper">
					<div class="processing-indicator" v-if="!displayedCode && !stageTitle.includes('Preparing')">
						<div class="processing-animation">
							<span></span>
							<span></span>
							<span></span>
						</div>
						<div class="processing-message">{{ processingMessage }}</div>
					</div>
					<div class="code-display" ref="codeDisplay">
						<div class="status-message" v-if="!displayedCode">{{ stageTitle }}</div>
						<pre ref="codeContainer"
							class="no-select"><code class="language-json" v-html="highlightedCode"></code></pre>
					</div>
				</div>
			</div>
		</div>

		<!-- Topology full-screen area (Stage 3) -->
		<div v-if="currentStage === 3" class="topology-fullscreen" >
			<div ref="chartContainer" class="chart-container"></div>
			
			<!-- 自定义加载层 -->
			<div v-if="toploading" class="custom-loading-mask">
				<div class="custom-loading-spinner"></div>
				<div class="custom-loading-text">Loading {{ Math.floor(loadingProgress) }}%</div>
			</div>
		</div>
		<!-- 编辑器蒙版 -->
		<transition>
			<div class="editor-overlay" v-show="selectedNode || selectedLink" @click="closeEditor"></div>
		</transition>

		<div class="node-editor" v-show="selectedNode || selectedLink"
			:class="{ 'visible': selectedNode || selectedLink }">
			<div class="editor-header">
				<h3>Edit Node: {{ selectedNode ? selectedNode.label : selectedLink ? selectedLink.name : '' }}
				</h3>
				<button @click="closeEditor" class="close-btn">
					<i class="fa fa-times"></i>
				</button>
			</div>

			<div class="editor-content">
				<div class="json-editor-section">
					<h4>Node Code{{ isDarkMode }}</h4>
					<div class="json-editor">
						<Codemirror 
							v-model="nodeStrData" 
							:extensions="isDarkMode_type ? codeMirrorExtensionsDark : codeMirrorExtensions" 
							:style="{ height: '100%', border: '1px solid #ccc', fontSize: '14px' }" 
							ref="codemirror" 
							placeholder="Edit node code in JSON format" 
							@change="onCodeChange" />
					</div>
					<div v-if="nodeJsonError" class="json-error">
						{{ nodeJsonError }}
					</div>
				</div>

				<div class="editor-actions">
					<div>
						<button @click="resetNodeChanges" class="action-btn reset-btn">
							<i class="fa fa-undo"></i> Reset
						</button>
						<button @click="applyChanges" class="action-btn primary-btn" :disabled="!isCodeModified"
							:class="{ 'disabled-btn': !isCodeModified }">
							<i class="fa fa-check"></i> Apply
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios';
// 移除Vue导入，因为在Vue组件中不需要显式导入Vue

import { ElMessageBox, ElMessage } from "element-plus";
import { fa } from 'element-plus/es/locale/index.mjs';
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { githubLight } from "@uiw/codemirror-theme-github";
// 从ProgressLayoutWrapper导入共享的emitter实例
import { emitter } from '../layouts/ProgressLayoutWrapper.vue';
import ProgressLayout from '../components/ProgressLayout.vue';

export default {
	name: 'CodeGenerationView',
	components: {
		Codemirror
	},
	data() {
		return {
			workflow: [], // 当前工作流数据
			originalWorkflowData: null, // 原始工作流数据
			saveData: null, // 保存修改后的数据
			nodeStrData: '', // 节点的str数据
			nodeJsonError: null, // 节点JSON错误信息
			isLoading: false, // 加载状态标志
			toploading: false, // 第三步加载状态标志
			loadingProgress: 0, // 加载进度百分比
			loadingProgressTimer: null, // 加载进度计时器
			isCodeScrollComplete: false, // 代码滚动是否完成
			chart: null, // echarts图表实例
			chartOption: {
				// 图表基本配置
				tooltip: {
					trigger: 'item',
					formatter: (params) => {
						// 不同数据类型的提示格式
						if (params.dataType === 'edge') {
							return `<div style="font-weight:bold">连接</div>
                      <div>从: ${params.data.sourceName}</div>
                      <div>到: ${params.data.targetName}</div>
                      <div>事件: ${params.data.value}</div>`;
						} else {
							return `<div style="font-weight:bold">${params.data.name}</div>
                      <div>类型: ${params.data.agentType}</div>
                      <div>${params.data.description || ''}</div>`;
						}
					}
				},
				animationDuration: 1500,
				animationEasingUpdate: 'quinticInOut',
				series: [{
					name: '拓扑网络',
					type: 'graph',
					layout: 'none',
					data: [], // 节点数据
					links: [], // 连接数据
					categories: [], // 分类数据
					roam: true, // 允许缩放平移
					label: {
						show: true,
						position: 'right',
						formatter: '{b}',
						color: this.isDarkMode ? '#ddd' : '#333'
					},
					lineStyle: {
						color: 'source',
						curveness: 0,
						width: 2
					},
					emphasis: {
						focus: 'adjacency',
						lineStyle: {
							width: 4
						}
					},
					draggable: false, // 禁止拖动
					edgeSymbol: ['none', 'arrow'], // 边的起点和终点样式
					edgeLabel: {
						show: true,
						formatter: '{c}',
						color: this.isDarkMode ? '#fff' : '#333',
						fontSize: 12,
						distance: 10 // 设置标签与边的距离
					}
				}]
			},

			currentStage: 0, // 当前阶段：0=初始化, 1=生成代码, 2=精炼代码, 3=最终确认
			stageCounter: {
				1: 0,
				2: 0,
				3: 0
			}, // 各阶段的计数器
			code: '', // 当前阶段的完整代码
			displayedCode: '', // 实际显示的代码（打字效果用）
			totalCodeLength: 0, // 代码总长度
			displayIndex: 0, // 当前显示到的位置
			typingSpeed: 40, // 每次迭代显示的字符数（可以调整打字速度）
			typingInterval: null, // 打字效果的定时器
			generationComplete: false, // 生成完成标志
			processingMessageInterval: null, // 处理消息轮换的定时器
			processingMessageIndex: 0, // 当前显示的处理消息索引
			cycleCount: 0, // 循环计数
			maxCycles: 3, // 最大循环次数
			showTopologyEditor: false, // 是否显示拓扑编辑器
			selectedNode: null, // 当前选中的节点
			selectedLink: null, // 当前选中的边连接
			editContent: '', // 编辑内容
			showEditModal: false, // 是否显示编辑模态框
			isCodeModified: false, // 代码是否被修改
			resetDialogVisible: false, // 重置对话框是否可见
			currentContent: '', // 当前从API获取的内容
			processingMessages: [
				// 处理过程中显示的消息列表
				"Initializing ...",
				"Analyzing agent interactions...",
				"Optimizing code patterns...",
				"Generating simulation logic...",
				"Mapping agent behaviors...",
				"Synthesizing communication protocols...",
				"Enhancing data structures...",
				"Validating code architecture...",
				"Refining algorithmic efficiency..."
			],
			stageActivityDetails: {
				// 各阶段的状态和时间估计
				1: {
					status: "Generating Code...",
					timeEstimate: "~30 seconds"
				},
				2: {
					status: "Refining Code...",
					timeEstimate: "~15 seconds"
				},
				3: {
					status: "Preparing Final Version...",
					timeEstimate: "~25 seconds"
				}
			},
			mockData: {
				// 模拟数据，用于演示生成过程
				stages: [{
					type: 1,
					code: ``
				},
				{
					type: 2,
					code: ``
				},
				{
					type: 3,
					code: `1`
				},
				]
			},
			// 以下是示例节点和连接数据
			topologyNodes: [{
				id: 1,
				name: 'CommunityCommittee',
				properties: {
					meeting_schedule: "datetime",
					collected_proposals: "list",
					review_status: "string",
					voting_results: "string"
				}
			},
			{
				id: 2,
				name: 'Resident',
				properties: {
					resident_interests: "list",
					alliance_id: "string"
				}
			},
			{
				id: 3,
				name: 'PropertyManagementCompany',
				properties: {
					feasibility_report: "string",
					assessment_id: "string"
				}
			},
			{
				id: 4,
				name: 'GovernmentRepresentative',
				properties: {
					policy_support_status: "string",
					policy_id: "string"
				}
			},
			{
				id: 5,
				name: 'EnvAgent',
				properties: {
					meeting_id: "string",
					agenda: "string"
				}
			}
			],
			topologyEdges: [{
				source: 1,
				sourceName: 'CommunityCommittee',
				target: 2,
				targetName: 'Resident',
				type: 'interacts'
			},
			{
				source: 1,
				sourceName: 'CommunityCommittee',
				target: 3,
				targetName: 'PropertyManagementCompany',
				type: 'requests'
			},
			{
				source: 2,
				sourceName: 'Resident',
				target: 3,
				targetName: 'PropertyManagementCompany',
				type: 'submits'
			},
			{
				source: 3,
				sourceName: 'PropertyManagementCompany',
				target: 4,
				targetName: 'CommunityCommittee',
				type: 'consults'
			},
			{
				source: 5,
				sourceName: 'EnvAgent',
				target: 1,
				targetName: 'CommunityCommittee',
				type: 'monitors'
			}],
			nodeStrData: '',  // JSON 编辑内容
			nodeJsonError: null,  // JSON 解析错误信息
			codeMirrorExtensionsDark: [python(), oneDark],
			codeMirrorExtensions: [python(), githubLight], // 高亮配置
			isDarkMode_type: localStorage.getItem('theme') === 'dark',
		};
	},
	created() {
		// 确保初始阶段为0
		this.currentStage = 0;
	},
	watch: {
		isLoading: {
			handler(newValue) {
				// 监听加载状态变化并向父组件发送
				this.$emit("update:loading", newValue);
			},
			immediate: true, // 组件创建时立即执行一次
		},
		// 监听loadingProgress变化
		loadingProgress: {
			handler(newValue) {
				// 当loadingProgress变化时，确保视图更新
				console.log("进度更新为: " + Math.floor(newValue) + "%");
			},
			immediate: false
		}
	},
	computed: {
		isDarkMode() {
			// 是否为暗色模式
			return document.documentElement.classList.contains('dark-theme');
		},
		// 判断是否有工作流数据
		hasWorkflowData() {
			return this.workflow &&
				this.workflow.actions &&
				this.workflow.events &&
				Object.keys(this.workflow.actions).length > 0 &&
				Object.keys(this.workflow.events).length > 0;
		},
		stageTitle() {
			// 根据当前阶段返回标题
			switch (this.currentStage) {
				case 1:
					return 'Generating Code...';
				case 2:
					return 'Refining Code...';
				case 3:
					return 'Preparing Final Confirmation...';
				default:
					return ' ';
				// Preparing...
			}
		},
		processingMessage() {
			return this.processingMessages[this.processingMessageIndex];
		},
		currentStatusText() {
			if (this.currentStage === 0) return 'Initializing...';
			if (this.generationComplete) return 'Process Complete';

			const stageInfo = this.stageActivityDetails[this.currentStage];
			return stageInfo ? stageInfo.status : 'Processing...';
		},
		stageTimeEstimate() {
			if (this.currentStage === 0) return '';
			const stageInfo = this.stageActivityDetails[this.currentStage];
			return stageInfo ? stageInfo.timeEstimate : '';
		},
		highlightedCode() {
			// Simple syntax highlighting for JSON
			if (!this.displayedCode) return '';

			return this.displayedCode
				.replace(/("[^"]*")\s*:/g, '<span class="json-key">$1</span>:') // Keys
				.replace(/:\s*("[^"]*")/g, ': <span class="json-string">$1</span>') // String values
				.replace(/:\s*([0-9]+)/g, ': <span class="json-number">$1</span>') // Number values
				.replace(/:\s*(true|false)/g, ': <span class="json-boolean">$1</span>') // Boolean values
				.replace(/\/\/(.*)/g, '<span class="json-comment">//$1</span>'); // Comments
		},
		canProceedToNext() {
			return this.generationComplete && !this.isCodeModified;
		},
		// 添加一个计算属性用于格式化显示的加载百分比
		formattedLoadingProgress() {
			return `已加载 ${Math.floor(this.loadingProgress)}%`;
		}
	},
	mounted() {
		// 组件挂载后执行
		// 开始加载代码数据
		this.loadCodeDataStart()

		// 监听窗口大小变化，以便调整图表尺寸
		window.addEventListener('resize', this.resizeChart);

		// 使用emitter代替
		emitter.on('call-proceed-next', (step) => {
			if (step === 3) { // step 3对应的是当前组件显示的第4阶段
				this.confirmTopology();
			}
		});
		emitter.on('theme-changed', (isDarkMode) => {
			this.isDarkMode_type = isDarkMode;
		});
	},
	beforeUnmount() {
		// 组件卸载前清理资源

		// 移除事件监听器
		window.removeEventListener('resize', this.resizeChart);
		// 销毁图表实例
		if (this.chart) {
			this.chart.dispose();
		}

		// 清除任何定时器
		if (this.typingInterval) {
			clearInterval(this.typingInterval);
		}
		if (this.processingMessageInterval) {
			clearInterval(this.processingMessageInterval);
		}
		if (this.loadingProgressTimer) {
			clearInterval(this.loadingProgressTimer);
			this.loadingProgressTimer = null;
		}

		// 使用emitter解绑事件
		emitter.off('call-proceed-next');
		emitter.off('theme-changed');
	},
	methods: {
		/**
		 * 初始化代码生成流程，向后端发送请求开始生成代码
		 */
		loadCodeDataStart() {
			// 初始化代码生成流程，向后端发送请求开始生成代码
			this.isLoading = true; // 显示加载状态
			this.currentStage = 0; // 确保从初始阶段开始
			
			axios.post('/api/pipeline/generate_code', {
				// session_id: localStorage.getItem('sessionId'),
				env_name: localStorage.getItem('scenarioName')
			}).then(response => {
				// 开始轮询代码生成状态
				this.loadCodeData(true)
			}).catch(error => {
				console.error('启动代码生成失败:', error);
				this.isLoading = false;
				this.$message({
					message: '启动代码生成失败，请重试',
					type: 'error'
				});
			})
		},
		/**
     	* 轮询获取代码生成状态
		* @param { boolean } isStart - 是否是首次调用，用于特殊处理初始状态
		*/
		loadCodeData(isStart) {
			// 轮询获取代码生成状态
			axios.get('/api/pipeline/code_generation_status?env_name=' + localStorage.getItem('scenarioName')).then(response => {
				console.log("API返回状态:", response.data.phase, 
					"内容长度:", response.data.content ? response.data.content.length : 0);
				
				// 如果是首次调用且状态为2(正在精炼代码)，开始模拟生成流程
				if (isStart && response.data.phase == 2) {
					isStart = false;
					this.simulateGeneration();
					this.isLoading = false;
				}
				if(response.data.phase == '-1'){
					ElMessageBox.confirm(response.data.content, 'error', {
						confirmButtonText: "Confirm",
						cancelButtonText: "Cancel",
					}).then(() => {
						this.$emit('prev');
					})
					return;
				}
				// 如果阶段不为0，表示代码生成尚未完成，继续轮询
				if (response.data.phase != 0) {
					// 更新当前阶段（如果阶段变化）
					if (this.currentStage !== response.data.phase) {
						console.log(`阶段变化: ${this.currentStage} -> ${response.data.phase}`);
						this.currentStage = response.data.phase;
					}
					
					// 使用content字段拼接内容，只对新增部分进行打字效果
					if (response.data.content) {
						const newContent = response.data.content;
						console.log("获取到新内容，长度:", newContent.length);
						
						// 拼接到当前代码后面
						this.code += newContent;
						const prevLength = this.totalCodeLength || 0;
						this.totalCodeLength = this.code.length;
						
						// 清除当前的打字效果并重新开始
						if (this.typingInterval) {
							clearInterval(this.typingInterval);
							this.typingInterval = null;
						}
						
						// 保留已显示内容，为新内容启动打字效果
						// 设置起始索引为上次显示的内容长度
						this.displayIndex = prevLength;
						
						// 启动打字效果，仅对新增部分
						console.log("启动新内容打字效果，当前总长度:", this.totalCodeLength, "从位置:", this.displayIndex);
						this.startTypingEffect();
					}
					
					// 1秒后再次轮询
					setTimeout(() => {
						this.loadCodeData(isStart);
					}, 1000);
				} else {
					// 当phase为0时，表示代码生成已完成，调用get_code接口获取最终代码
					console.log("阶段已完成，获取最终代码");
					
					axios.get('/api/pipeline/get_code?env_name=' + localStorage.getItem('scenarioName'))
						.then(codeResponse => {
							// 获取代码并设置到显示区域
							this.currentStage = 3; // 设置为最终阶段
							console.log("获取到最终代码，设置为阶段3");

							// 如果返回的是对象，格式化为JSON字符串
							if (typeof codeResponse.data === 'object') {
								this.displayedCode = JSON.stringify(codeResponse.data, null, 2);

								// 处理结构化数据，为拓扑图准备
								if (codeResponse.data.actions && codeResponse.data.events) {
									this.workflow = codeResponse.data;
									// 保存原始数据，用于重置
									this.originalWorkflowData = JSON.parse(JSON.stringify(codeResponse.data));

									// 确保进入第三阶段时始终有加载状态
									if (!this.toploading) {
										console.log("确保加载状态显示");
										this.toploading = true;
										if (!this.loadingProgressTimer) {
											this.startLoadingProgress();
										}
									}

									// 设置加载进度为100%
									console.log("设置加载进度为100%并准备关闭加载层");
									this.loadingProgress = 100;

									// 延迟一点时间初始化图表
									setTimeout(() => {
										// 关闭加载层
										this.toploading = false;
										// 清除进度计时器
										if (this.loadingProgressTimer) {
											clearInterval(this.loadingProgressTimer);
											this.loadingProgressTimer = null;
										}
										// 初始化图表
										this.initChart();
									}, 500);
								}
							} else {
								this.displayedCode = codeResponse.data.content || "";
							}

							// 标记生成完成状态
							this.generationComplete = true;
							this.isLoading = false;

							// 清除加载进度计时器
							if (this.loadingProgressTimer) {
								clearInterval(this.loadingProgressTimer);
								this.loadingProgressTimer = null;
							}

							// 向用户显示完成提示
							this.$message({
								message: '代码生成完成！',
								type: 'success',
								duration: 3000
							});
						})
						.catch(error => {
							console.error('获取最终代码失败:', error);
							this.$message({
								message: '获取生成的代码失败',
								type: 'error'
							});
							this.toploading = false;
							if (this.loadingProgressTimer) {
								clearInterval(this.loadingProgressTimer);
								this.loadingProgressTimer = null;
							}
						});
				}
			}).catch(error => {
				console.error('检查代码生成状态失败:', error);
				// 错误处理也要关闭加载状态
				this.toploading = false;
				if (this.loadingProgressTimer) {
					clearInterval(this.loadingProgressTimer);
					this.loadingProgressTimer = null;
				}
				
				// 3秒后重试
				setTimeout(() => {
					this.loadCodeData(isStart);
				}, 3000);
			});
		},
		/**
		 * 处理工作流数据，将JSON字符串转换为对象并进行处理
		 * 1. 解析JSON字符串
		 * 2. 生成节点和连接数据
		 * 3. 准备ECharts图表所需的数据结构
		 */
		processWorkflowData() {
			// 处理工作流数据，将JSON字符串转换为对象并进行处理
			if (typeof this.workflow === 'string') {
				try {
					this.workflow = JSON.parse(this.workflow);
				} catch (e) {
					console.error('解析工作流JSON失败:', e);
				}
			}

			// 确保workflow数据和actions存在
			if (!this.workflow || !this.workflow.actions || !this.workflow.events) {
				console.error('工作流数据不完整，无法处理');
				return;
			}

			// 生成演示数据
			const demoData = {
				// 节点数据，包括开始节点和从actions中提取的所有动作节点
				nodes: [{
					id: 0,
					label: 'start',
					agentType: 'EnvAgent',
					color: '#29ebd7'
				},
				// 展开所有代理类型的actions，并将每个action映射为一个节点
				...Object.entries(this.workflow.actions || {}).flatMap(([agentType, actions]) =>
					(actions || []).map(action => ({
						id: action.id,
						label: action.name,
						agentType: agentType,
						color: this.getColorForAgent(agentType),
							description: action.description,
							type: action.type,
							required_variables: action.required_variables,
							output_updates: action.output_updates,
							code: action.code || ''  // 添加code字段
					}))
				),
				],
				// 连接数据，从events中提取所有事件作为连接
				links: [
					...(Object.values(this.workflow.events || {}) || []).map(event => ({
						source: event.from_action_id,
						sourceName: event.from_action_name,
						target: event.to_action_id,
						targetName: event.to_action_name,
						name: event.event_name,
						info: event.event_info,
						code: event.code || ''  // 添加code字段
					})),
				]
			};

			// 修改-1为最后一个节点的ID (将终止事件指向终止节点)
			demoData.links = demoData.links.map(link => ({
				...link,
				source: link.source === -1 ? demoData.nodes.length : link.source,
				sourceName: link.sourceName === -1 ? demoData.nodes.length : link.sourceName,
				target: link.target === -1 ? demoData.nodes.length : link.target,
				targetName: link.targetName === -1 ? demoData.nodes.length : link.targetName
			}));

			// 添加终止节点
			demoData.nodes.push({
				id: demoData.nodes.length,
				label: 'terminate',
				agentType: 'EnvAgent',
				color: '#29ebd7'
			});

			// 确保所有ID是数字类型，并添加echarts所需的属性
			demoData.nodes = demoData.nodes.map(node => ({
				...node,
				id: typeof node.id === 'string' ? parseInt(node.id) : node.id,
				symbolSize: 50,
				name: node.label,
				category: node.agentType
			}));

			// 确保所有连线的source和target是数字类型，并添加echarts所需的属性
			demoData.links = demoData.links.map(link => ({
				...link,
				source: typeof link.source === 'string' ? parseInt(link.source) : link.source,
				sourceName: link.sourceName,
				target: typeof link.target === 'string' ? parseInt(link.target) : link.target,
				targetName: link.targetName,
				value: link.name
			}));

			// 提取所有分类，用于echarts的分类图例
			const categories = [...new Set(demoData.nodes.map(node => node.agentType))].map(type => ({
				name: type
			}));

			// 计算节点位置
			this.calculateNodePositions(demoData.nodes);

			// 更新图表配置
			this.chartOption.series[0].data = demoData.nodes;
			this.chartOption.series[0].links = demoData.links;
			this.chartOption.series[0].categories = categories;

		},
		/**
		 * 计算拓扑图中各节点的位置
		 * @param {Array} nodes - 节点数组
		 */
		calculateNodePositions(nodes) {
			// 计算拓扑图中各节点的位置
			// 按ID排序节点
			nodes.sort((a, b) => a.id - b.id);

			// 布局参数
			const canvasWidth = 1200;
			const canvasHeight = 600;
			const paddingLeft = 100;
			const paddingRight = 100;
			const paddingTop = 100;
			const paddingBottom = 100;

			// 特殊节点：开始节点和结束节点
			const startNode = nodes.find(n => n.id === 0);
			const endNode = nodes.find(n => n.id === -1);
			const regularNodes = nodes.filter(n => n.id !== 0 && n.id !== -1);

			// 设置开始和结束节点位置
			if (startNode) {
				startNode.x = paddingLeft;
				startNode.y = canvasHeight / 2;
			}

			if (endNode) {
				endNode.x = canvasWidth - paddingRight;
				endNode.y = canvasHeight / 2;
			}

			// 计算常规节点位置
			const availableWidth = canvasWidth - paddingLeft - paddingRight;
			const availableHeight = canvasHeight - paddingTop - paddingBottom;

			// 根据节点数量计算合适的行数
			const nodeCount = regularNodes.length;
			let rows = Math.ceil(Math.sqrt(nodeCount / 2));
			rows = Math.max(2, Math.min(4, rows));

			// 计算列数和单元格大小
			const columns = Math.ceil(nodeCount / rows);
			const cellWidth = availableWidth / (columns + 1);
			const cellHeight = availableHeight / rows;

			// 分配常规节点位置，按行列格式排列
			regularNodes.forEach((node, index) => {
				const row = index % rows;
				const col = Math.floor(index / rows);

				node.x = paddingLeft + (col + 1) * cellWidth;
				node.y = paddingTop + (row + 0.5) * cellHeight;
			});
		},
		closeEditor() {

			// 先添加淡出类，然后使用setTimeout确保动画完成后再真正关闭编辑器
			const nodeEditor = this.$el.querySelector('.node-editor');
			if (nodeEditor) {
				// 添加淡出动画
				nodeEditor.classList.add('fade-out');
				setTimeout(() => {
					// 动画结束后重置编辑器状态
					this.selectedNode = null;
					this.selectedLink = null;
					this.selectedNodeFields = [];
					this.nodeStrData = '';
					this.nodeJsonError = null;
					this.activeNodeTab = 'form';
					this.isCodeModified = false; // 重置修改状态
					nodeEditor.classList.remove('fade-out');
				}, 300); // 动画持续时间
			} else {
				// 如果找不到编辑器DOM，直接重置状态
				this.selectedNode = null;
				this.selectedLink = null;
				this.selectedNodeFields = [];
				this.nodeStrData = '';
				this.nodeJsonError = null;
				this.activeNodeTab = 'form';
				this.isCodeModified = false; // 重置修改状态
			}

		},
		initChart() {
			// 不要在这里重置toploading状态，让加载状态继续显示
			// this.toploading = false; // 移除这行代码
			
			// 如果还有进度计时器在运行，保持它继续运行
			// 不要清除计时器
			/*
			if (this.loadingProgressTimer) {
				clearInterval(this.loadingProgressTimer);
				this.loadingProgressTimer = null;
			}
			*/

			// 组件卸载前清理资源
			// 移除事件监听器
			window.removeEventListener('resize', this.resizeChart);
			// 销毁图表实例
			if (this.chart) {
				this.chart.dispose();
			}

			// 清除任何定时器
			if (this.typingInterval) {
				clearInterval(this.typingInterval);
			}
			if (this.processingMessageInterval) {
				clearInterval(this.processingMessageInterval);
			}

			// 使用emitter解绑事件
			emitter.off('call-proceed-next');

			// 处理工作流数据，准备节点和连接
			this.processWorkflowData();

			// 检查图表容器是否存在
			if (!this.$refs.chartContainer) return;


			// 初始化ECharts实例
			this.chart = echarts.init(this.$refs.chartContainer);
			// 添加节点点击事件监听
			this.chart.on('click', (params) => {
				if (params.data && params.data.id !== undefined && params.data.name !== undefined) {
					this.handleNodeClick(params.data);
				}
				// 添加连接线点击事件监听
				if (params.dataType === 'edge') {
					this.handleLinkClick(params.data);
				}
			})
			// 添加图表容器点击事件，用于关闭编辑器
			this.$refs.chartContainer.addEventListener('click', (event) => {
				// 确认点击的是图表容器本身而不是其中的元素
				if (event.target === this.$refs.chartContainer) {
					this.closeEditor();
				}
			});
			// 设置图表配置项并渲染
			this.chart.setOption(this.chartOption);
		},

		resizeChart() {
			// 调整图表大小以适应容器变化
			if (this.chart) {
				this.chart.resize();
			}
		},

		getColorForAgent(agentType) {
			// 根据代理类型获取对应的颜色
			// 默认的颜色映射
			const colorMap = {
				'EnvAgent': '#29ebd7',
				'CommunityCommittee': '#547bb8',
				'Resident': '#e4a357',
				'PropertyManagementCompany': '#1f274f',
				'GovernmentRepresentative': '#4bca85',
				'System': '#4bca85',
				'Environment': '#29ebd7',
				'Interface': '#e4a357'
			};

			// 返回预设颜色或随机生成一个颜色
			return colorMap[agentType] || '#' + Math.floor(Math.random() * 16777215).toString(16);
		},

	

		simulateGeneration() {
			// 模拟代码生成过程
			// 按顺序处理各个阶段的模拟数据
			this.processNextStage();
		},

		processNextStage() {
			// 处理下一个生成阶段
			// 检查是否还有待处理的阶段
			if (this.mockData.stages.length === 0) {
				this.generationComplete = true;
				return;
			}

			// 获取并移除队列中的第一个阶段
			const stage = this.mockData.stages.shift();

			// 如果已经在第3阶段，跳过第1和第2阶段
			if (this.currentStage === 3 && (stage.type === 1 || stage.type === 2)) {
				// 直接跳转到下一个阶段
				this.processNextStage();
				return;
			}
			// 设置当前阶段并增加该阶段的计数器
			this.currentStage = stage.type;
			this.stageCounter[stage.type]++;
			console.log(this.currentStage)

			// 如果是第3阶段(最终阶段)，初始化图表并确保加载状态
			if (this.currentStage === 3) {
				// 如果是从第2阶段完成后进入的第3阶段，启动加载进度动画
				this.toploading = true;
				if (!this.loadingProgressTimer) {
					this.startLoadingProgress();
				}
				
				setTimeout(() => {
					// 只初始化图表，不改变加载状态
					this.initChart();
				}, 1000)
			}

			// 检查是否需要在生成和精炼之间循环
			if ((this.currentStage === 1 || this.currentStage === 2) && this.cycleCount < this.maxCycles) {
				// 如果是生成或精炼阶段，且尚未完成3个循环
				if (this.stageCounter[1] + this.stageCounter[2] >= 2) {
					// 对于每个完成的生成+精炼轮次，增加循环计数器
					this.cycleCount++;
				}
			}
			// 重置代码显示为新阶段
			this.code = stage.code;
			this.totalCodeLength = this.code.length;
			this.displayedCode = '';
			this.displayIndex = 0;

			// 开始打字效果
			this.startTypingEffect();
		},

		startTypingEffect() {
			// 开始代码打字效果，模拟逐步生成代码的过程
			// 清除之前的打字效果定时器
			if (this.typingInterval) {
				clearInterval(this.typingInterval);
			}

			// 计算需要展示的字符总数
			const remainingChars = this.totalCodeLength - this.displayIndex;
			
			// 计算每个字符的显示间隔，确保一次content的内容在约12秒内展示完
			// 假设平均每次返回500字符，12秒完成，则每字符约需要24毫秒
			const charDelay = 6; // 毫秒/字符
			
			// 设置新的打字效果定时器，每次只显示1-2个字符，减慢速度
			this.typingInterval = setInterval(() => {
				// 每次只显示少量字符，降低显示速度
				const chunkSize = 1; // 每次只显示1个字符
				const nextIndex = Math.min(this.displayIndex + chunkSize, this.totalCodeLength);

				// 更新显示的代码内容
				this.displayedCode = this.code.substring(0, nextIndex);
				this.displayIndex = nextIndex;

				// 滚动代码容器到底部，保持新内容可见
				this.$nextTick(() => {
					if (this.$refs.codeDisplay) {
						this.$refs.codeDisplay.scrollTop = this.$refs.codeDisplay.scrollHeight;
					}
				});

				// 如果当前阶段的代码已全部显示完毕
				if (this.displayIndex >= this.totalCodeLength) {
					console.log("打字效果完成，清除打字计时器");
					clearInterval(this.typingInterval);
					this.typingInterval = null;
					
					// 标记代码滚动完成
					this.isCodeScrollComplete = true;
				}
			}, charDelay); // 调整时间以控制打字速度，改为更慢的速度
		},

		// 新增方法：开始加载进度动画
		startLoadingProgress() {
			// 设置初始加载状态
			this.toploading = true;
			this.loadingProgress = 0;
			
			// 清除可能存在的上一个计时器
			if (this.loadingProgressTimer) {
				clearInterval(this.loadingProgressTimer);
				this.loadingProgressTimer = null;
			}
			
			// 计算一分钟内从0%到99%所需的增量和间隔
			// 每秒更新5次，总共更新300次
			const totalSteps = 300;
			const interval = 200; // 200毫秒
			const incrementPerStep = 99 / totalSteps;
			
			console.log("开始加载进度动画，每" + interval + "ms增加" + incrementPerStep.toFixed(2) + "%");
			
			// 开始进度更新计时器
			this.loadingProgressTimer = setInterval(() => {
				// 确保进度不超过99%
				if (this.loadingProgress < 99) {
					// 不使用Vue.set，直接更新数据
					const newProgress = this.loadingProgress + incrementPerStep;
					// 限制最大值为99
					this.loadingProgress = Math.min(newProgress, 99);
					
					// 输出日志方便调试
					if (Math.floor(this.loadingProgress) % 10 === 0) {
						console.log("当前加载进度：" + Math.floor(this.loadingProgress) + "%");
					}
				}
			}, interval);
		},

		handleLinkClick(linkData) {

			this.selectedNode = null;
			const originalLinkData = this.findOriginalLinkData(linkData);

			const LinkData = this.workflow.events[originalLinkData.id];

			if (!LinkData) {
				this.$message({
					title: 'Warning',
					message: 'Current link cannot be modified',
					type: 'warning'
				});
				return;
			}

			this.selectedLink = {
				...LinkData,
				originalData: originalLinkData
			};

			// 确保 nodeStrData 被正确设置
			this.updateNodeLinkData();
			this.$forceUpdate();
		},

		handleNodeClick(nodeData) {
			this.selectedLink = null;
			const originalNodeData = this.findOriginalNodeData(nodeData.id);

			if (!originalNodeData) {
				this.$message({
					title: 'Warning',
					message: 'Current node cannot be modified',
					type: 'warning'
				});
				return;
			}

			this.selectedNode = {
				...nodeData,
				originalData: originalNodeData
			};

			this.updateNodeStrData();
			this.$forceUpdate();
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

		resetProcess() {
			this.$confirm('Are you sure you want to reset all data? Once reset, data cannot be recovered.',
				'Warning', {
				confirmButtonText: 'Confirm',
				cancelButtonText: 'Cancel',
				type: 'warning'
			}).then(() => {
				this.workflow = JSON.parse(JSON.stringify(this.originalWorkflowData));
				this.processWorkflowData();
				if (this.chart) {
					this.chart.setOption(this.chartOption);
				}

				this.isCodeModified = false;
				this.$message({
					message: 'Data has been reset to original state',
					type: 'success',
					duration: 3000
				});
			}).catch(() => {
				this.$message({
					type: 'info',
					message: 'Reset operation cancelled'
				});
			});
		},

		// 、重置方法专用
		findOriginalNodeData(nodeId) {
			const dataSource = this.originalWorkflowData;

			try {
				if (dataSource && dataSource.actions) {
					for (const agentType in dataSource.actions) {
						const foundAction = dataSource.actions[agentType].find(action =>
							action.id === nodeId || action.id === parseInt(nodeId)
						);
						if (foundAction) {
							return foundAction; // 返回找到的节点数据
						}
					}
				}
				return null;
			} catch (error) {
				console.error('查找原始节点数据失败:', error);
				return null;
			}
		},

		// 、重置方法专用link
		findOriginalLinkData(linkData) {
			console.log(linkData, 'linkData');
			const dataSource = this.originalWorkflowData.events;

			// 将对象转换为数组
			const dataSourceArray = Object.values(dataSource);

			// 使用 for...of 循环遍历数组
			for (const event of dataSourceArray) {

				if (event.from_action_id == linkData.source && event.to_action_id == linkData.target) {
					return event; // 返回找到的事件
				}
			}

			return null; // 如果没有找到匹配的事件，返回 null
		},


		confirmTopology() {
			// 确认拓扑结构并进入下一步
			if (!this.hasWorkflowData) {
				ElMessage.warning('没有可用的工作流数据，无法继续');
				return;
			}
			ElMessageBox.confirm(
				"Are you sure you want to proceed to the next step?",
				"Confirmation",
				{
					confirmButtonText: "OK",
					cancelButtonText: "Cancel",
				}
			).then(() => {
				// 更新代码
				this.updateWorkflowData().then(() => {
					// 生成代码
					return axios.post('/api/pipeline/generate_code', {
						env_name: localStorage.getItem('scenarioName')
					});
				}).then(() => {
					// 生成完成后进入下一步
					this.$emit('step-complete');
				}).catch(error => {
					console.error('生成代码失败:', error);
					this.$notify({
						title: 'Error',
						message: 'Failed to generate code',
						type: 'error'
					});
				});
			});
		},

		regenerateCode() {
			// 暂时先提示功能待开发，后续再开发
			this.$message({
				type: 'info',
				message: 'Regeneration cancelled'
			});
			return false
			// 重新生成代码，显示确认对话框
			this.$confirm('Regenerating code will take approximately 5-10 minutes. Do you want to proceed?',
				'Confirmation', {
				confirmButtonText: 'Proceed',
				cancelButtonText: 'Cancel',
				type: 'info'
			}).then(() => {
				// 用户确认重新生成
				this._doRegenerateCode();
			}).catch(() => {
				// 用户取消重新生成
				this.$message({
					type: 'info',
					message: 'Regeneration cancelled'
				});
			});
		},

		_doRegenerateCode() {
			// 执行重新生成代码的具体实现
			// 返回第一阶段，完全重新开始123阶段循环
			this.currentStage = 0; // 从0开始，而不是1，以确保正确初始化
			this.stageCounter = {
				1: 0,
				2: 0,
				3: 0
			};
			this.cycleCount = 0;
			this.generationComplete = false;
			this.displayedCode = '';

			// 重新初始化模拟数据以重新开始整个过程
			this.mockData.stages = [{
				type: 1,
				code: ``
			},
			{
				type: 2,
				code: ``
			},
			{
				type: 3,
				code: ``
			}
			];

			// 重新开始生成过程
			setTimeout(() => {
				this.simulateGeneration();
			}, 1000);
		},
		resetNodeChanges() {
			if (this.selectedNode) {
				// 如果选中的是节点，重置节点相关的数据
				const originalNodeData = this.selectedNode.originalData;
				if (originalNodeData) {
					this.nodeStrData = originalNodeData.code;
					this.nodeJsonError = null;
					this.$message({
						title: 'Success',
						message: 'Node data reset to original',
						type: 'success'
					});
					// 更新一下this.workflow.actions[this.selectedNode.agentType].find(node => node.id === this.selectedNode.id);
					this.workflow.actions[this.selectedNode.agentType].find(node => node.id === this.selectedNode.id).code = this.nodeStrData;
				}
			} else if (this.selectedLink) {
				// 如果选中的是线条，重置事件相关的数据
				const originalEventData = this.selectedLink.originalData;

				if (originalEventData) {
					this.nodeStrData = originalEventData.code;
					this.nodeJsonError = null;
					this.$message({
						title: 'Success',
						message: 'Event data reset to original',
						type: 'success'
					});
					// 更新一下this.workflow.events[this.selectedLink.id]
					this.workflow.events[this.selectedLink.id].code = this.nodeStrData;
				}
			}
			this.isCodeModified = false;
			// 延迟一点时间初始化图表
			setTimeout(() => {
				this.initChart();
			}, 500);

		},
		// 应用节点编辑
		applyChanges() {
			if (!this.isCodeModified) return; // 确保只有在修改后才应用更改

			try {
				if (this.selectedNode) {
					// 查找并更新节点的 code
					const node = this.workflow.actions[this.selectedNode.agentType].find(node => node.id === this.selectedNode.id);
					if (node) {
						node.code = this.nodeStrData;
					} else {
						throw new Error('Node not found');
					}
				} else if (this.selectedLink) {
					// 将 events 转换为数组并查找连接
					const eventsArray = Object.values(this.workflow.events);

					const link = eventsArray.find(event => event.id === this.selectedLink.id);
					if (link) {
						link.code = this.nodeStrData;
					} else {
						throw new Error('Link not found');
					}
				}


				this.$message({
					title: 'Success',
					message: 'Code updated',
					type: 'success'
				});
				this.closeEditor();
				// 延迟一点时间初始化图表
				setTimeout(() => {
					this.initChart();
				}, 500);


			} catch (error) {
				this.$message({
					title: 'Error',
					message: 'Failed to apply changes',
					type: 'error'
				});
			}
		},

		// 更新工作流数据到后端
		updateWorkflowData() {
			const updateData = {
				env_name: localStorage.getItem('scenarioName'),
				actions: this.workflow.actions || {},
				events: this.workflow.events || {}
			};


			return axios.post('/api/pipeline/update_code', updateData, {
				headers: {
					'Content-Type': 'application/json'
				}
			}).then(response => {
				console.log('代码更新成功:', response.data);
				this.$notify({
					title: 'Success',
					message: 'Code successfully saved to server',
					type: 'success',
					duration: 3000
				});
			}).catch(error => {
				console.error('更新代码失败:', error);
				this.$notify({
					title: 'Error',
					message: 'Failed to save code to server',
					type: 'error',
					duration: 3000
				});
			});
		},
		updateNodeStrData() {
			// 更新节点JSON数据，用于在JSON编辑器中显示
			try {
				if (this.selectedNode) {
					// 直接设置code内容到nodeStrData
					this.nodeStrData = this.selectedNode.code;
					this.nodeJsonError = null;
				}
			} catch (error) {
				console.error('更新节点JSON数据失败:', error);
				this.nodeJsonError = '无法生成JSON数据: ' + error.message;
			}
		},
		updateNodeLinkData() {
			if (this.selectedLink) {
				this.nodeStrData = this.selectedLink.code || ''; // 确保有默认值
				this.nodeJsonError = null;
			}
		}
	},

}

</script>

<style scoped>
.code-generation-container {
	display: flex;
	flex-direction: column;
	height: 100%;
	width: 100%;
	color: var(--text-color);
	animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
	from {
		opacity: 0;
	}

	to {
		opacity: 1;
	}
}

/* 顶部进度区域 */
.progress-header {
	padding: 15px 20px;
	border-bottom: 1px solid var(--border-color);
	height: 60px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	/* Ensure 100% width */
	box-sizing: border-box;
	/* Ensure padding doesn't increase width */
}

.stage-indicator {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 10px;
	flex: 1;
}

.stage {
	display: flex;
	align-items: center;
	gap: 10px;
	opacity: 0.5;
	transition: all 0.3s ease;
}

.stage.active {
	opacity: 1;
}

.stage-number {
	width: 30px;
	height: 30px;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: var(--accent-color);
	color: white;
	border-radius: 50%;
	font-weight: bold;
}

.stage-separator {
	width: 40px;
	height: 1px;
	background-color: var(--border-color);
}

/* 中间代码内容区域 */
.code-content-wrapper {
	flex: 1;
	display: flex;
	justify-content: center;
	align-items: center;
	padding: 20px;
	overflow: hidden;
}

.code-editor-container {
	width: 100%;
	height: 70vh;
	/* 使用vh单位 */
	max-height: calc(100vh - 140px);
	/* 确保在小屏幕上有足够空间给底部按钮 */
	display: flex;
	flex-direction: column;
	border-radius: 8px;
	border: 1px solid var(--border-color);
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
	overflow: hidden;
	position: relative;
}

.code-editor-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0 15px;
	background-color: var(--editor-header-bg, #2d2d2d);
	border-bottom: 1px solid var(--border-color);
	height: 40px;
}

.stage-status {
	display: flex;
	align-items: center;
	gap: 10px;
}

.status-indicator {
	width: 10px;
	height: 10px;
	border-radius: 50%;
	background-color: var(--accent-color);
}

.status-indicator.pulse {
	animation: pulse 1.5s infinite;
}

@keyframes pulse {
	0% {
		transform: scale(0.95);
		box-shadow: 0 0 0 0 rgba(var(--accent-color-rgb, 0, 120, 255), 0.7);
	}

	70% {
		transform: scale(1);
		box-shadow: 0 0 0 6px rgba(var(--accent-color-rgb, 0, 120, 255), 0);
	}

	100% {
		transform: scale(0.95);
		box-shadow: 0 0 0 0 rgba(var(--accent-color-rgb, 0, 120, 255), 0);
	}
}

.status-text {
	font-size: 14px;
	color: var(--editor-header-text, #e1e1e1);
}

.stage-time {
	display: flex;
	align-items: center;
	gap: 6px;
}

.time-icon {
	color: rgba(255, 255, 255, 0.6);
	font-size: 14px;
}

.time-estimate {
	font-size: 12px;
	color: rgba(255, 255, 255, 0.6);
	font-style: italic;
}

.code-display-wrapper {
	flex: 1;
	height: calc(100% - 40px);
	/* 容器高度减去header高度 */
	position: relative;
	overflow: hidden;
}

/* 处理中指示器 */
.processing-indicator {
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	z-index: 10;
}

.processing-animation {
	display: flex;
	gap: 6px;
	margin-bottom: 15px;
}

.processing-animation span {
	display: inline-block;
	width: 12px;
	height: 12px;
	background-color: var(--accent-color);
	border-radius: 50%;
	animation: bounce 1.4s infinite ease-in-out both;
}

.processing-animation span:nth-child(1) {
	animation-delay: -0.32s;
}

.processing-animation span:nth-child(2) {
	animation-delay: -0.16s;
}

@keyframes bounce {

	0%,
	80%,
	100% {
		transform: scale(0);
	}

	40% {
		transform: scale(1.0);
	}
}

.processing-message {
	color: rgba(255, 255, 255, 0.8);
	font-size: 1.1rem;
	text-align: center;
	max-width: 300px;
	animation: fadeInOut 1s ease-in-out infinite alternate;
}

@keyframes fadeInOut {
	from {
		opacity: 0.6;
	}

	to {
		opacity: 1;
	}
}

.code-display {
	height: 100%;
	width: 100%;
	overflow-y: auto;
	background-color: var(--code-bg, #1e1e1e);
	padding: 15px;
	font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
	line-height: 1.5;
	font-size: 14px;
	position: relative;
}

.status-message {
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	font-size: 1.2rem;
	color: rgba(255, 255, 255, 0.6);
	text-align: center;
	padding: 20px;
}

pre {
	margin: 0;
	white-space: pre-wrap;
	word-wrap: break-word;
}

/* 禁止选择和复制文本 */
.no-select {
	-webkit-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
	pointer-events: none;
}

/* 底部按钮区域 */
.actions-footer {
	display: none;
}

/* JSON Syntax Highlighting - Dark Theme (default) */
.json-key {
	color: #9CDCFE;
}

.json-string {
	color: #CE9178;
}

.json-number {
	color: #B5CEA8;
}

.json-boolean {
	color: #569CD6;
}

.json-comment {
	color: #6A9955;
	font-style: italic;
}

/* Light Theme Adjustments */
.light-theme .code-editor-header {
	background-color: #f0f0f0;
}

.light-theme .status-text {
	color: #333;
}

.light-theme .time-icon,
.light-theme .time-estimate {
	color: rgba(0, 0, 0, 0.6);
}

.light-theme .code-display {
	background-color: #fafafa;
	color: #333;
	border: 1px solid #e0e0e0;
}

.light-theme .code-editor-container {
	border-color: #e0e0e0;
	background-color: #ffffff;
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.light-theme .status-message {
	color: rgba(0, 0, 0, 0.6);
}

.light-theme .processing-message {
	color: rgba(0, 0, 0, 0.8);
}

.light-theme .json-key {
	color: #0451A5;
}

.light-theme .json-string {
	color: #A31515;
}

.light-theme .json-number {
	color: #098658;
}

.light-theme .json-boolean {
	color: #0000FF;
}

.light-theme .json-comment {
	color: #008000;
}

/* 拓扑图编辑器样式 */
.topology-editor-wrapper {
	height: 100%;
	width: 100%;
	position: relative;
	display: flex;
	justify-content: center;
	align-items: center;
}

.topology-container {
	height: 100%;
	width: 100%;
	position: relative;
	background-color: var(--code-bg, #1e1e1e);
	overflow: hidden;
}

.topology-graph {
	height: 100%;
	width: 100%;
	display: flex;
	flex-direction: column;
	position: relative;
	padding: 30px;
}

.topology-node {
	width: 120px;
	height: 120px;
	background-color: var(--accent-color, #0078ff);
	border-radius: 10px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	color: white;
	position: absolute;
	cursor: pointer;
	box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
	transition: all 0.3s ease;
}

.topology-node:nth-child(1) {
	top: 30%;
	left: 50%;
	transform: translate(-50%, -50%);
}

.topology-node:nth-child(2) {
	top: 60%;
	left: 20%;
}

.topology-node:nth-child(3) {
	top: 60%;
	left: 50%;
	transform: translateX(-50%);
}

.topology-node:nth-child(4) {
	top: 60%;
	left: 80%;
}

.topology-node:nth-child(5) {
	top: 20%;
	left: 80%;
}

.topology-node:hover {
	transform: scale(1.05);
	box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.topology-node:nth-child(1):hover {
	transform: translate(-50%, -50%) scale(1.05);
}

.topology-node:nth-child(3):hover {
	transform: translateX(-50%) scale(1.05);
}

.node-icon {
	font-size: 24px;
	margin-bottom: 8px;
}

.node-label {
	font-size: 12px;
	text-align: center;
	padding: 0 5px;
	font-weight: 500;
}

.topology-edge {
	position: absolute;
	cursor: pointer;
}

.topology-edge:nth-child(6) {
	top: 46%;
	left: 35%;
	width: 120px;
	transform: rotate(30deg);
}

.topology-edge:nth-child(7) {
	top: 47%;
	left: 48%;
	height: 80px;
}

.topology-edge:nth-child(8) {
	top: 60%;
	left: 30%;
	width: 100px;
}

.topology-edge:nth-child(9) {
	top: 60%;
	left: 65%;
	width: 80px;
}

.topology-edge:nth-child(10) {
	top: 30%;
	left: 65%;
	height: 60px;
	transform: rotate(-90deg);
}

.edge-line {
	width: 100px;
	height: 2px;
	background-color: rgba(255, 255, 255, 0.6);
	position: relative;
}

.edge-line::before,
.edge-line::after {
	content: '';
	position: absolute;
	width: 8px;
	height: 2px;
	background-color: rgba(255, 255, 255, 0.6);
}

.edge-line::after {
	right: 0;
	transform: rotate(30deg);
	transform-origin: right;
}

.edge-line::before {
	right: 0;
	transform: rotate(-30deg);
	transform-origin: right;
}

.edge-label {
	position: absolute;
	font-size: 11px;
	color: rgba(255, 255, 255, 0.8);
	background-color: rgba(0, 0, 0, 0.7);
	padding: 2px 6px;
	border-radius: 3px;
	top: -20px;
	left: 50%;
	transform: translateX(-50%);
	white-space: nowrap;
}

/* 编辑弹窗样式 */
.edit-modal {
	position: absolute;
	top: 0;
	right: 0;
	width: 330px;
	height: 100%;
	background-color: var(--bg-color, #1e1e1e);
	box-shadow: -5px 0 15px rgba(0, 0, 0, 0.2);
	z-index: 100;
	display: flex;
	flex-direction: column;
	animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
	from {
		transform: translateX(100%);
	}

	to {
		transform: translateX(0);
	}
}

.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s, transform 0.3s;
}

.fade-enter,
.fade-leave-to {
	opacity: 0;
	transform: translateX(30px);
}

.edit-modal-content {
	display: flex;
	flex-direction: column;
	height: 100%;
	overflow: hidden;
}

.edit-modal-header {
	padding: 15px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	border-bottom: 1px solid var(--border-color, #333);
}

.edit-modal-header h3 {
	margin: 0;
	font-size: 16px;
	color: var(--text-color, #fff);
}

.close-btn {
	background: none;
	border: none;
	color: var(--text-color, #fff);
	font-size: 16px;
	cursor: pointer;
}

.edit-modal-body {
	flex: 1;
	padding: 15px;
	overflow-y: auto;
	padding-bottom: 80px;
	/* 为底部按钮留出空间 */
}

.code-editor {
	width: 100%;
	height: 100%;
	min-height: 200px;
	background-color: var(--code-bg, #1e1e1e);
	color: var(--text-color, #fff);
	border: 1px solid var(--border-color, #333);
	border-radius: 4px;
	padding: 10px;
	font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
	resize: none;
	font-size: 14px;
	line-height: 1.5;
}

.edit-modal-footer {
	padding: 15px;
	display: flex;
	justify-content: flex-end;
	gap: 10px;
	border-top: 1px solid var(--border-color, #333);
}

.cancel-btn,
.save-btn {
	padding: 8px 16px;
	border-radius: 4px;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.2s ease;
}

.cancel-btn {
	background-color: transparent;
	border: 1px solid var(--border-color, #333);
	color: var(--text-color, #fff);
}

.save-btn {
	background-color: var(--accent-color, #0078ff);
	border: none;
	color: white;
}

.cancel-btn:hover {
	background-color: rgba(255, 255, 255, 0.1);
}

.save-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 明亮主题的调整 */
.light-theme .edit-modal {
	background-color: #f8f8f8;
	box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
}

.light-theme .code-editor {
	background-color: #fff;
	color: #333;
	border-color: #ddd;
}

.light-theme .cancel-btn {
	border-color: #ddd;
	color: #333;
}

.light-theme .topology-container {
	background-color: #f0f0f0;
}

.light-theme .topology-edge .edge-line,
.light-theme .topology-edge .edge-line::before,
.light-theme .topology-edge .edge-line::after {
	background-color: rgba(0, 0, 0, 0.5);
}

.light-theme .edge-label {
	background-color: rgba(255, 255, 255, 0.9);
	color: #333;
	border: 1px solid #ddd;
}

/* 拓扑图全屏样式 */
.topology-fullscreen {
	height: 80vh;
	position: absolute;
	top: 180px;
	/* 修改：确保在顶部进度区域下方 */
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 5;
	overflow: hidden;
}

.topology-fullscreen .topology-graph {
	width: 100%;
	height: 100%;
	padding: 40px;
}

/* Modify topology nodes size and position in full-screen mode */
.topology-fullscreen .topology-node {
	width: 150px;
	height: 150px;
}

.topology-fullscreen .topology-node:nth-child(1) {
	top: 25%;
	left: 50%;
	transform: translate(-50%, -50%);
}

.topology-fullscreen .topology-node:nth-child(2) {
	top: 65%;
	left: 25%;
}

.topology-fullscreen .topology-node:nth-child(3) {
	top: 65%;
	left: 50%;
	transform: translateX(-50%);
}

.topology-fullscreen .topology-node:nth-child(4) {
	top: 65%;
	left: 75%;
}

.topology-fullscreen .topology-node:nth-child(5) {
	top: 25%;
	left: 75%;
}

.topology-fullscreen .topology-edge:nth-child(6) {
	top: 42%;
	left: 38%;
	width: 150px;
	transform: rotate(30deg);
}

.topology-fullscreen .topology-edge:nth-child(7) {
	top: 44%;
	left: 50%;
	height: 120px;
}

.topology-fullscreen .topology-edge:nth-child(8) {
	top: 65%;
	left: 35%;
	width: 130px;
}

.topology-fullscreen .topology-edge:nth-child(9) {
	top: 65%;
	left: 62%;
	width: 110px;
}

.topology-fullscreen .topology-edge:nth-child(10) {
	top: 25%;
	left: 63%;
	height: 80px;
	transform: rotate(-90deg);
}

/* 修改底部按钮区域 - 移除，因为按钮已移至顶部 */
.actions-footer {
	display: none;
}

/* 阶段3操作按钮 */
.topology-actions {
	display: flex;
	gap: 10px;
	margin-left: 20px;
}

.action-btn {
	padding: 10px 15px;
	border-radius: 3px;
	font-weight: 500;
	cursor: pointer;
	display: flex;
	align-items: center;
	gap: 6px;
	transition: all 0.2s ease;
	font-size: 13px;
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
	border: none;
	color: white;
}

.reset-btn {
	background-color: #f44336;
}

.regenerate-btn {
	background-color: #ff9800;
}

.confirm-btn {
	background-color: #4caf50;
}

.action-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.chart-container {
	width: 100vw;
	height: 100%;
	box-shadow: var(--box-shadow);
}

/* 高亮模式 */
.chart-container.highlight-mode {
	position: relative;
}

.chart-container.highlight-mode::after {
	content: '';
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	pointer-events: none;
	z-index: 1;
}

/* 从 TopologyEditor.vue 复制的节点编辑器样式 */
.node-editor {
	position: absolute;
	top: 90px;
	right: -50vw;
	width: 50vw;
	height: calc(100vh - 90px);
	background-color: var(--sidebar-bg);
	box-shadow: -5px 0 15px rgba(0, 0, 0, 0.2);
	transition: right 0.3s ease, opacity 0.3s ease, transform 0.3s ease;
	z-index: 98;
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

.json-editor-section {
	margin-top: 15px;
	height: calc(100% - 30px);
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

.primary-btn {
	background-color: var(--accent-color);
}

.danger-btn {
	background-color: #f44336;
}

.reset-btn {
	background-color: #FFA000;
}

.reset-btn:hover {
	background-color: #FF8F00;
}

/* 针对节点编辑器的样式 */
.node-editor .editor-actions {
	gap: 10px;
	display: flex;
	justify-content: flex-end;
}

/* 针对节点编辑器底部按钮的样式优化 */
.node-editor .editor-actions>div {
	display: flex;
	gap: 10px;
}

/* 编辑器蒙版样式 */
.editor-overlay {
	position: fixed;
	top: 90px;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.5);
	z-index: 97;
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
		opacity: 0.5;
	}
}

/* 媒体查询 */
@media (max-width: 768px) {
	.node-editor {
		width: 100%;
		right: -100%;
		transform: translateX(100px);
	}

	.node-editor.visible {
		right: 0;
		width: 100%;
		z-index: 1000;
		transform: translateX(0);
	}
}

.loading-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(255, 255, 255, 0.5);
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
	color: #333;
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

.disabled-btn {
	background-color: #ccc;
	/* 灰色背景表示禁用 */
	cursor: not-allowed;
	/* 禁用时的鼠标样式 */
	opacity: 0.6;
	/* 透明度降低 */
}

/* 自定义加载层样式 */
.custom-loading-mask {
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
	z-index: 2000;
}

.custom-loading-spinner {
	width: 42px;
	height: 42px;
	border: 3px solid #fff;
	border-radius: 50%;
	border-top-color: #409EFF;
	animation: spin 1s linear infinite;
	margin-bottom: 15px;
}

.custom-loading-text {
	font-size: 16px;
	color: #fff;
	margin-top: 5px;
}

@keyframes spin {
	0% {
		transform: rotate(0deg);
	}
	100% {
		transform: rotate(360deg);
	}
}
</style>
