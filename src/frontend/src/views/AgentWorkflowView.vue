<template>
	<div class="agent-workflow-container">
		<div class="topology-wrapper">
			<TopologyEditor :isDarkMode="isDarkMode" :agentTypes="agentTypes" :loadingshow="true"
				@save-topology="handleSaveTopology" @save-workflow="handleSaveWorkflow" @proceed-next="goToNextStep"
				@update-loading="handleLoadingUpdate" @back-to-chat-mode="backToChatMode" ref="topologyEditor" />
		</div>

		<div v-if="showEmptyWarning" class="empty-warning">
			<i class="fa fa-exclamation-triangle"></i> Please create at least one connection in the workflow to proceed
		</div>
	</div>
</template>

<script>
	import TopologyEditor from '../components/TopologyEditor.vue';

	export default {
		name: 'AgentWorkflowView',
		components: {
			TopologyEditor
		},
		data() {
			return {
				workflowData: null,
				showEmptyWarning: false,
				agentTypes: [],
				loading: true, // 用于控制加载状态
			}
		},
		created() {
			// 尝试从localStorage获取保存的Agent Types
			const savedAgentTypes = localStorage.getItem('agentTypes');
			if (savedAgentTypes) {
				try {
					const parsedAgentTypes = JSON.parse(savedAgentTypes);
					if (Array.isArray(parsedAgentTypes) && parsedAgentTypes.length > 0) {
						this.agentTypes = parsedAgentTypes;
					}
				} catch (error) {
					console.error('Error parsing saved agent types:', error);
				}
			}

			// 尝试从localStorage获取保存的Workflow数据
			const savedWorkflow = localStorage.getItem('workflowData');
			if (savedWorkflow) {
				try {
					this.workflowData = JSON.parse(savedWorkflow);
				} catch (error) {
					console.error('Error parsing saved workflow data:', error);
				}
			}
		},
		watch: {
			loading: {
				handler(newValue) {
					console.log(newValue);
					// 监听加载状态变化并向父组件发送
					this.$emit("update:loading", newValue);
				},
				immediate: true, // 组件创建时立即执行一次
			},
		},
		mounted() {
			// 在组件挂载后，如果有保存的Workflow数据，初始化拓扑图
			if (this.workflowData && this.$refs.topologyEditor) {
				this.$nextTick(() => {
					this.$refs.topologyEditor.processTopologyData(this.workflowData);
				});
			}
		},
		computed: {
			isDarkMode() {
				return document.documentElement.classList.contains('dark-theme');
			},
			canProceed() {
				// 检查是否有足够的节点和连接
				return this.workflowData &&
					this.workflowData.links &&
					this.workflowData.links.length > 0;
			}
		},
		methods: {
			backToChatMode() {
				this.$emit('back-to-chat-mode');
				// this.$router.push({
				// 	path: '/simulation',
				// 	query: {
				// 		model_name:this.$route.query.model_name,
				// 		category: this.$route.query.category,
				// 		step: 1, 
				// 	}
				// });
			},
			handleLoadingUpdate(loading) {
				this.loading = loading;
			},
			handleSaveWorkflow(workflow) {
				// 保存到localStorage
				localStorage.setItem('workflow', JSON.stringify(workflow));
			},
			handleSaveTopology(topology) {
				this.workflowData = topology;

				// 保存到localStorage
				localStorage.setItem('workflowData', JSON.stringify(topology));

				// 显示保存成功提示
				this.$message({
					message: 'Workflow saved successfully!',
					type: 'success',
					duration: 2000
				});
			},

			goToNextStep() {
				if (!this.canProceed) {
					this.showEmptyWarning = true;
					setTimeout(() => {
						this.showEmptyWarning = false;
					}, 3000);
					return;
				}

				// 保存workflow数据到localStorage
				localStorage.setItem('workflowData', JSON.stringify(this.workflowData));

				// 触发事件移动到下一步
				this.$emit('step-complete');
			}
		}
	}
</script>

<style scoped>
	.agent-workflow-container {
		padding: 0;
		margin: -20px;
		width: 100vw;
		height: calc(100vh - 60px);
		/* 减去顶部导航栏的高度 */
		animation: fadeIn 0.5s ease;
		position: relative;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}

		to {
			opacity: 1;
		}
	}

	.topology-wrapper {
		flex: 1;
		width: 100%;
		height: 100%;
		background-color: rgba(255, 255, 255, 0.05);
		border-radius: 0;
		box-shadow: none;
		animation: slideInUp 0.5s ease both;
		overflow: hidden;
	}

	@keyframes slideInUp {
		from {
			transform: translateY(30px);
			opacity: 0;
		}

		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.empty-warning {
		position: fixed;
		bottom: 20px;
		left: 50%;
		transform: translateX(-50%);
		background-color: rgba(255, 87, 34, 0.9);
		color: white;
		padding: 10px 20px;
		border-radius: 4px;
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		gap: 10px;
		z-index: 1000;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
		animation: fadeInUp 0.3s ease;
	}

	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translate(-50%, 20px);
		}

		to {
			opacity: 1;
			transform: translate(-50%, 0);
		}
	}

	@media (max-width: 768px) {
		.empty-warning {
			width: 90%;
			text-align: center;
			font-size: 0.8rem;
		}
	}
</style>