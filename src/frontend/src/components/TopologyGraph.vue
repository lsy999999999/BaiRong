<template>
	<div ref="chartContainer" class="chart-container"></div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'
export default {
	name: 'TopologyGraph',
	props: {
		isDarkMode: {
			type: Boolean,
			default: true
		},
		subcategory: {
			type: String,
			default: ""
		},
	},
	data() {
		return {
			workflow: {},
			chart: null,
			agentTypeColorCache: {}, // 添加颜色缓存对象，保存agentType到颜色的映射
			chartOption: {
				tooltip: {
					trigger: 'item',
					formatter: (params) => {
						if (params.dataType === 'edge') {
							return `<div style="font-weight:bold">连接</div>
                      <div>从: ${params.data.source}</div>
                      <div>到: ${params.data.target}</div>
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
					layout: 'force',
					data: [],
					links: [],
					categories: [],
					roam: true,
					zoom: 1,
					force: { // 力引导布局的详细配置
						repulsion: 300, // 节点间的斥力，值越大节点越分散
						edgeLength: 100, // 边的理想长度，值越大边越长
						gravity: 0.2, // 向中心的引力，值越小节点越松散
						friction: 0.05, // 摩擦系数，值越小动画越平滑
						layoutAnimation: true // 开启动画
					},
					label: {
						show: true,
						position: 'right',
						formatter: '{b}',
						color: this.isDarkMode ? '#333' : '#fff'
					},
					lineStyle: {
						color: 'source',
						curveness: 0,
						width: 2,
					},
					emphasis: {
						focus: 'adjacency',
						lineStyle: {
							width: 1,
						},
						color: this.isDarkMode ? '#333' : '#fff',
					},
					draggable: false,
					edgeSymbol: ['none', 'arrow'],
					edgeLabel: {
						show: true,
						formatter: '{c}',
						color: this.isDarkMode ? '#333' : '#fff',
						fontSize: 12,
						distance: 10 // 设置标签与边的距离
					}
				}]
			}
		};
	},
	created() {

	},
	mounted() {
		this.loadEchartsData()
	},
	watch: {
		subcategory: {
			handler(newVal) {
				if (newVal) {
					this.loadEchartsData()
				}
			},
			immediate: true
		}
	},
	beforeUnmount() {
		// 移除事件监听
		window.removeEventListener('resize', this.resizeChart);
		// 销毁图表实例
		if (this.chart) {
			this.chart.dispose();
		}
	},
	methods: {
		loadEchartsData() {
			this.workflow = {}
			axios.get('/api/scene/' + this.subcategory).then(response => {
				console.log('response.data', response.data);
				if(JSON.stringify(response.data) != '{}'){
					// 处理workflow数据
					this.workflow = {
						events: response.data.events,
						actions: response.data.actions
					}
					this.processWorkflowData();
					// 初始化图表
					this.initChart();
					// 监听窗口大小变化
					window.addEventListener('resize', this.resizeChart);
					//传值给父组件
					this.$emit('odd_protocol', response.data.odd_protocol);
				}else{
					console.log('重置图表');
					//重置图表
					this.chart.dispose();
				}
				
			}).catch(error => {});
		},
		processWorkflowData() {
			// 生成演示数据
			const demoData = {
				nodes: [{
					id: 0,
					label: 'start',
					agentType: 'EnvAgent',
					color: '#29ebd7',
					fixed: true,
					x: '20%',
					y: '50%',
				},
				...Object.entries(this.workflow.actions).flatMap(([agentType, actions]) =>
					actions.map(action => ({
						id: action.id,
						label: action.name,
						agentType: agentType,
						color: this.getColorForAgent(agentType),
						description: action.description,
						type: action.type,
						required_variables: action.required_variables,
						output_updates: action.output_updates
					}))
				),
				],
				links: [
					...Object.values(this.workflow.events).map(event => ({
						source: event.from_action_id,
						target: event.to_action_id,
						name: event.event_name,
						info: event.event_info
					})),
				]
			};

			// 修改-1为最后一个节点的ID
			demoData.links = demoData.links.map(link => ({
				...link,
				source: link.source === -1 ? demoData.nodes.length : link.source,
				target: link.target === -1 ? demoData.nodes.length : link.target
			}));

			// 添加终止节点
			demoData.nodes.push({
				id: demoData.nodes.length,
				label: 'terminate',
				agentType: 'EnvAgent',
				color: '#29ebd7',
				fixed: true,
				x: '70%',
				y: '50%',
			});

			// 确保所有ID是数字类型
			demoData.nodes = demoData.nodes.map(node => ({
				...node,
				id: typeof node.id === 'string' ? parseInt(node.id) : node.id,
				// symbolSize: this.getNodeSize(node.agentType),
				symbolSize: 25,
				name: node.label,
				category: node.agentType
			}));

			// 确保所有连线的source和target是数字类型
			demoData.links = demoData.links.map(link => ({
				...link,
				source: typeof link.source === 'string' ? parseInt(link.source) : link.source,
				target: typeof link.target === 'string' ? parseInt(link.target) : link.target,
				value: link.name
			}));

			// 提取所有分类
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

		calculateNodePositions(nodes) {
			// 按ID排序节点
			nodes.sort((a, b) => a.id - b.id);

			// 布局参数
			const canvasWidth = 1200;
			const canvasHeight = 600;
			const paddingLeft = 100;
			const paddingRight = 100;
			const paddingTop = 100;
			const paddingBottom = 100;

			// 特殊节点
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

			const columns = Math.ceil(nodeCount / rows);
			const cellWidth = availableWidth / (columns + 1);
			const cellHeight = availableHeight / rows;

			// 分配常规节点位置
			regularNodes.forEach((node, index) => {
				const row = index % rows;
				const col = Math.floor(index / rows);

				node.x = paddingLeft + (col + 1) * cellWidth;
				node.y = paddingTop + (row + 0.5) * cellHeight;
			});
		},

		initChart() {
			if (!this.$refs.chartContainer) return;
			
			// 如果已存在实例，先销毁
			if (this.chart) {
				this.chart.dispose();
			}
			
			// 初始化ECharts实例
			this.chart = echarts.init(this.$refs.chartContainer);

			// 设置配置项
			this.chart.setOption(this.chartOption);
		},

		resizeChart() {
			if (this.chart) {
				this.chart.resize();
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

		getNodeSize(agentType) {
			// 根据节点类型设置不同大小
			const sizeMap = {
				'EnvAgent': 30,      // 环境节点
				'CommunityCommittee': 40,  // 社区委员会
				'Resident': 35,      // 居民
				'PropertyManagementCompany': 40,  // 物业公司
				'GovernmentRepresentative': 40,   // 政府代表
				'System': 35,        // 系统
				'Environment': 30,    // 环境
				'Interface': 35       // 接口
			};
			return sizeMap[agentType] || 35; // 默认大小
		}
	}
}
</script>

<style scoped>
.chart-container {
	width: 100%;
	height: 100%;
	border-radius: 15px;
	background-color: rgba(42, 42, 42, 0.1);
	box-shadow: var(--box-shadow);
}
</style>