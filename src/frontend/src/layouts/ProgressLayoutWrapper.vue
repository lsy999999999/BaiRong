<template>
	<ProgressLayout :current-step="currentStep" :total-steps="totalSteps" :can-proceed-to-next="canProceedToNext"
		:step-condition-info="stepConditionInfo" :has-workflow-data="hasWorkflowData" :is-loading="isLoading" @prev="prevStep" @next="nextStep" @go-dashboard="goToDashboard"
		@call-proceed-next="handleCallProceedNext">
		<component :is="currentComponent" @step-complete="handleStepComplete" @update:canProceed="updateCanProceed"
			 @update:loading="updateLoading" @back-to-chat-mode="backToChatMode" @prev="prevStep" ref="currentStepComponent"></component>
	</ProgressLayout>
</template>

<script>
import { ElMessageBox, ElMessage } from "element-plus";
	import ProgressLayout from '../components/ProgressLayout.vue'
	import ChatMode from '../views/ChatMode.vue'
	import AgentTypesView from '../views/AgentTypesView.vue'
	import AgentWorkflowView from '../views/AgentWorkflowView.vue'
	import CodeGenerationView from '../views/CodeGenerationView.vue'
	import AgentConfigurationView from '../views/AgentConfigurationView.vue'
	// 导入mitt事件总线
	import mitt from 'mitt'

	// 创建事件总线实例并导出，使其在组件间共享
	export const emitter = mitt()

	export default {
		name: 'ProgressLayoutWrapper',
		components: {
			ProgressLayout,
			ChatMode,
			AgentTypesView,
			AgentWorkflowView,
			CodeGenerationView,
			AgentConfigurationView
		},
		data() {
			return {
				currentStep: 1,
				totalSteps: 5,
				hasWorkflowData: false,
				checkInterval: null,
				isLoading: false,
				steps: [{
						name: 'ODD Protocol',
						component: 'ChatMode'
					},
					{
						name: 'Agent Types',
						component: 'AgentTypesView'
					},
					{
						name: 'Agent Workflow',
						component: 'AgentWorkflowView'
					},
					{
						name: 'Generate Code',
						component: 'CodeGenerationView'
					},
					{
						name: 'Agent Configuration',
						component: 'AgentConfigurationView'
					}
				],
				stepConditionInfo: {
					step1: "You need to complete more conversation to generate ODD protocol data",
					step2: "Please add at least one agent type to proceed",
					step4: "Please wait for code generation to complete",
					step5: "Please configure at least one agent population"
				},
				canProceedToNext: false
			}
		},
		created() {
			// 从URL获取step参数初始化当前步骤
			const stepParam = this.$route.query.step;
			if (stepParam) {
				const step = parseInt(stepParam);
				if (!isNaN(step) && step >= 1 && step <= this.totalSteps) {
					this.currentStep = step;
				}
			}
		},
		computed: {
			currentComponent() {
				return this.steps[this.currentStep - 1].component
			}
		},
		watch: {
			currentStep: {
				handler() {
					// 切换步骤时重置状态
					this.canProceedToNext = false;
					
					// 如果切换到步骤4，初始化hasWorkflowData为false
					if (this.currentStep === 4) {
						this.hasWorkflowData = false;
						
						// 清除之前的定时器
						if (this.checkInterval) {
							clearInterval(this.checkInterval);
						}
						
						// 对于第4步，设置定期检查，每2秒检查一次状态
						this.checkInterval = setInterval(() => {
							this.checkComponentCanProceed();
						}, 2000);
					} else {
						// 不是第4步时清除定时器
						if (this.checkInterval) {
							clearInterval(this.checkInterval);
							this.checkInterval = null;
						}
					}

					// 如果是第5步，直接设置为可点击
					if (this.currentStep === 5) {
						this.canProceedToNext = true;
						return;
					}

					// 给组件一些时间加载，然后查询状态
					this.$nextTick(() => {
						this.checkComponentCanProceed();
					});
				},
				immediate: true
			}
		},
		beforeUnmount() {
			// 组件卸载前清除定时器
			if (this.checkInterval) {
				clearInterval(this.checkInterval);
			}
		},
		methods: {
			backToChatMode() {
				this.currentStep = 1;
				this.updateUrlStep();
			},
			updateCanProceed(value) {
				// 从子组件接收状态更新
				this.canProceedToNext = value;
			},
			
			updateLoading(value) {
				// 从子组件接收加载状态更新
				this.isLoading = value;
			},

			checkComponentCanProceed() {
				const currentStepComponent = this.$refs.currentStepComponent;
				if (!currentStepComponent) return;
				// 检查特定组件状态
				switch (this.currentStep) {
					// case 1: // ChatMode
					// 	this.canProceedToNext = true;
					// 	break;

					case 2: // AgentTypesView
						this.canProceedToNext = currentStepComponent.canProceed === true;
						break;

					case 3: // AgentWorkflowView
						this.canProceedToNext = true; // 默认可以进行下一步
						break;

					case 4: // CodeGenerationView
						this.canProceedToNext = currentStepComponent.generationComplete === true;
						// 更新hasWorkflowData状态
						this.hasWorkflowData = currentStepComponent.hasWorkflowData === true;
						break;

					case 5: // AgentConfigurationView
						// 修改为只要有任何数据就可以点击下一步
						this.canProceedToNext = true;
						break;
				}
			},

			updateUrlStep(param) {
				// 保留现有查询参数，只更新step
				const query = {
					...this.$route.query,
					step: this.currentStep,
					...param
				};

				// 使用replace而不是push，避免在历史记录中创建多个条目
				this.$router.replace({
					path: this.$route.path,
					query: query
				});
			},
			prevStep() {
				if (this.currentStep > 1) {
					this.currentStep--;
					this.updateUrlStep();
				}
			},
			nextStep(param) {
				console.log(this.currentStep , 'this.currentStep')
				if (this.currentStep < this.totalSteps) {
					this.currentStep++;
					this.updateUrlStep(param);
				} else if (this.currentStep === this.totalSteps) {
					// 如果是最后一步，则跳转到模拟系统页面
					ElMessageBox.confirm(
						"Are you sure you want to proceed to the next step?",
						"Confirmation",
						{
							confirmButtonText: "OK",
							cancelButtonText: "Cancel",
						}
					).then(() => {
						this.$router.push({
						  path: '/simulation-system'
						});
					}).catch(() => {
						// 取消操作
					});
				}
			},
			handleStepComplete(param) {
				
				if (this.currentStep < this.totalSteps) {
					this.nextStep(param);
				} else {
				
					this.$router.push({
					  path: '/simulation-system'
					});
				}
			},
			goToDashboard() {
				this.$router.push('/');
			},
			
			handleCallProceedNext() {
				// 获取当前步骤组件的引用
				const currentStepComponent = this.$refs.currentStepComponent;
				// 如果当前步骤是ChatMode并且可以进行下一步，调用其proceedToNextStep方法
				if (this.currentStep === 1 && currentStepComponent && this.canProceedToNext) {
					console.log('调用ChatMode的proceedToNextStep方法');
					currentStepComponent.proceedToNextStepVerification();
				} else if (this.currentStep === 2 && currentStepComponent && this.canProceedToNext) {
					// 如果是第二步(AgentTypesView)，调用其goToNextStep方法
					console.log('调用AgentTypesView的goToNextStep方法');
					currentStepComponent.goToNextStep();
				} else if (this.currentStep === 3 && currentStepComponent && this.canProceedToNext) {
					// 如果是第三步(AgentWorkflowView)，调用其TopologyEditor组件的saveTopology方法
					console.log('调用TopologyEditor的saveTopology方法');
					if (currentStepComponent.$refs.topologyEditor) {
						currentStepComponent.$refs.topologyEditor.saveTopology();
					} else {
						console.error('找不到TopologyEditor组件引用');
						// 仍然继续下一步
						this.nextStep();
					}
				} else if (this.currentStep === 4 && currentStepComponent && this.canProceedToNext) {
					// 如果是第四步(CodeGenerationView)，调用其confirmTopology方法
					console.log('调用CodeGenerationView的confirmTopology方法');
					currentStepComponent.confirmTopology();
				} else if(this.currentStep === 5 && currentStepComponent && this.canProceedToNext){
					console.log('调用AgentConfigurationView的goToNextStep方法');
					currentStepComponent.goToNextStep();
				} else if (this.currentStep !== 1 && this.currentStep !== 2 && this.currentStep !== 3 && this.currentStep !== 4) {
					// 如果不是第一步、第二步、第三步和第四步，使用原来的nextStep方法
					this.nextStep();
				}
				
				// 使用emitter替代$root.$emit
				emitter.emit('call-proceed-next', this.currentStep);
			}
		}
	}
</script>