<template>
	<div class="settings-panel" v-loading="loading">
		<!-- <h2>Simulation Settings Panel</h2> -->
		<div class="panel-content">
			<el-form :model="formData" label-width="180px" :disabled="!isPaused">
				<!-- Environment Settings -->
				<el-divider content-position="left">Environment Settings</el-divider>
				<el-form-item label="Scene Name">
					<el-input v-model="formData.environment.name" placeholder="Enter scene name"></el-input>
				</el-form-item>
				<el-form-item label="Run Mode">
					<el-select v-model="formData.environment.mode" placeholder="Select run mode">
						<el-option v-for="mode in formData.environment.modes" :key="mode" :label="mode" :value="mode">
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="Max Steps">
					<el-input-number v-model="formData.environment.max_steps" :min="1"></el-input-number>
				</el-form-item>

				<!-- Agent Settings -->
				<el-divider content-position="left">Agent Settings</el-divider>

				<!-- Planning Strategy -->
				<el-form-item label="Planning Strategy">
					<el-select v-model="formData.agent.planning" placeholder="Select planning strategy">
						<el-option v-for="plan in planning" :key="plan" :label="plan" :value="plan">
						</el-option>
					</el-select>
				</el-form-item>

				<!-- Memory Strategy -->
				<el-form-item label="Memory Strategy">
					<el-select v-model="formData.agent.memory" placeholder="Select memory strategy">
						<el-option v-for="memory in memory" :key="memory" :label="memory" :value="memory">
						</el-option>
					</el-select>
				</el-form-item>

				<!-- Agent Configuration -->
				<el-form-item label="Agent Configuration">
					<div class="agent-config-container">
						<div class="agent-config-header">
							<h3>Agent Types</h3>
							<el-input v-model="searchQuery" placeholder="Search agents..." prefix-icon="Search"
								clearable class="search-input" />
						</div>
						<div class="agent-grid">
							<div v-for="(profile, agentType) in filteredAgentProfiles" :key="agentType"
								class="agent-card" @click="handleAgentClick(agentType)">
								<div class="agent-card-content">
									<div class="agent-icon">
										<el-icon>
											<User />
										</el-icon>
									</div>
									<div class="agent-info">
										<h4>{{ agentType }}</h4>
										<p>Count: {{ profile.count }} / {{ profile.max_count }}</p>
									</div>
								</div>
							</div>
						</div>
					</div>
				</el-form-item>

				<!-- Agent Edit Dialog -->
				<div class="modal-overlay" v-if="editDialogVisible" @click.self="editDialogVisible = false">
					<div class="modal-content">
						<div class="modal-header">
							<h3>Edit {{ selectedAgent }}</h3>
							<button class="close-btn" @click="editDialogVisible = false">
								<el-icon>
									<Close />
								</el-icon>
							</button>
						</div>

						<div class="modal-form">
							<div class="agent-edit-info">
								<p class="max-count-info">
									Maximum number of agents: {{ editingProfile.max_count }}
								</p>
							</div>

							<el-form :model="editingProfile" label-width="50px">
								<div class="form-group">
									<el-form-item label="Count">
										<el-input-number v-model="editingProfile.count" :min="0"
											:max="editingProfile.max_count"
											@change="handleAgentCountChange(selectedAgent, $event)">
										</el-input-number>
									</el-form-item>
								</div>
							</el-form>

							<div class="form-actions">
								<el-button @click="editDialogVisible = false" class="cancel-btn">Cancel</el-button>
								<el-button type="primary" @click="handleSaveEdit" class="save-btn">Save</el-button>
							</div>
						</div>
					</div>
				</div>

				<!-- Agent Settings -->
				<el-divider content-position="left">Model</el-divider>
				<el-form-item label="LLM for Agent Behaviors">
					<el-select v-model="formData.model.chat" placeholder="Select run model">
						<el-option v-for="item in chat" :key="item" :label="item" :value="item">
						</el-option>
					</el-select>
				</el-form-item>
				<el-form-item label="Embedding Model">
					<el-select v-model="formData.model.embedding" placeholder="Select run model">
						<el-option v-for="item in embedding" :key="item" :label="item" :value="item">
						</el-option>
					</el-select>
				</el-form-item>
			</el-form>
		</div>

		<div class="settings-actions">
			<el-button type="primary" @click="handleSubmit" :disabled="!isPaused">Save Settings</el-button>
			<el-button @click="handleReset" :disabled="!isPaused">Reset</el-button>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, defineExpose, nextTick } from "vue";
import { User, Close } from "@element-plus/icons-vue";
import { useGameStore } from "../../../stores/gameStore";
import { ElMessageBox, ElMessage } from "element-plus";
import { useRoute } from "vue-router";

import axios from "axios";
const emit = defineEmits(["settings-updated", "form-submitted"]);
const gameStore = useGameStore();

const props = defineProps({
	newMap: Function
});
const route = useRoute();

const searchQuery = ref("");
const editDialogVisible = ref(false);
const selectedAgent = ref("");
const editingProfile = ref(null);

const chat = ref([]);
const embedding = ref([]);

const planning = ref(["None", "BDIPlanning", "COTPlanning", "TOMPlanning"]);
const memory = ref(["None", "ListStrategy", "ShortLongStrategy"]);
const loading = ref(false);
const isFormSubmitted = ref(false);

const formData = reactive({
	environment: {
		name: "",
		mode: "",
		max_steps: 3,
		modes: [],
	},
	agent: {
		planning: "",
		memory: "",
		profile: {
		},
	},
	model: {
		embedding: "",
		chat: "",
	},
});

const filteredAgentProfiles = computed(() => {
	if (!searchQuery.value) return formData.agent.profile;
	const query = searchQuery.value.toLowerCase();
	return Object.fromEntries(
		Object.entries(formData.agent.profile).filter(([key]) =>
			key.toLowerCase().includes(query)
		)
	);
});

const handleAgentClick = (agentType) => {
	selectedAgent.value = agentType;
	editingProfile.value = {
		...formData.agent.profile[agentType]
	};
	editDialogVisible.value = true;
};

const handleSaveEdit = () => {
	formData.agent.profile[selectedAgent.value] = {
		...editingProfile.value
	};
	editDialogVisible.value = false;
};

const handleAgentCountChange = (agentType, value) => {
	const profile = formData.agent.profile[agentType];
	if (value > profile.max_count) {
		profile.count = profile.max_count;
	}
};

const handleAgentMaxCountChange = (agentType, value) => {
	const profile = formData.agent.profile[agentType];
	if (profile.count > value) {
		profile.count = value;
	}
};
/**
 * 处理提交表单的逻辑
 */
const handleSubmit = () => {
	loading.value = true;
	// 验证所有必填参数
	if (!formData.environment.name) {
		ElMessage({
			type: "warning",
			message: "Please enter scene name",
		});
		loading.value = false;
		return;
	}

	if (!formData.environment.mode) {
		ElMessage({
			type: "warning",
			message: "Please select run mode",
		});
		loading.value = false;
		return;
	}

	if (!formData.agent.planning) {
		ElMessage({
			type: "warning",
			message: "Please select planning strategy",
		});
		loading.value = false;
		return;
	}

	if (!formData.agent.memory) {
		ElMessage({
			type: "warning",
			message: "Please select memory strategy",
		});
		loading.value = false;
		return;
	}

	if (!formData.model.chat) {
		ElMessage({
			type: "warning",
			message: "Please select chat model",
		});
		loading.value = false;
		return;
	}

	if (!formData.model.embedding) {
		ElMessage({
			type: "warning",
			message: "Please select embedding model",
		});
		loading.value = false;
		return;
	}

	// 验证场景名称是否存在于localStorage
	const scenarioName = localStorage.getItem('scenarioName');
	if (!scenarioName) {
		ElMessage({
			type: "warning",
			message: "Scene name not set, please create a scene first",
		});
		loading.value = false;
		return;
	}

	// Add form validation and submission logic here
	console.log("Form data submitted:", formData);

	ElMessageBox.confirm("Save Settings?", {
		confirmButtonText: "OK",
		cancelButtonText: "Cancel",
	}).then(() => {
		const isDevMode = gameStore.isDevMode;
		console.log("ok");

		let param = {
			env_name: scenarioName,
			config: formData,
		};
		axios.post(`/api/config/save`, param).then((res) => {
			emit("settings-updated", formData);
			isFormSubmitted.value = true;
			ElMessage({
				type: "success",
				message: "Settings saved successfully",
			});
			getAgents();
			// 通知父组件表单已提交
			emit("form-submitted");
		}).catch((err) => {
			if (err.response?.data?.detail) {
				ElMessage.error(err.response.data.detail);
			} else {
				ElMessage.error("Failed to save settings");
			}
		});
	})
		.catch(() => {
			console.log("cancel");
			loading.value = false;
		});
};

const getAgents = () => {
	axios.post("/api/simulation/initialize?env_name=" + localStorage.getItem('scenarioName') + "&model_name=" + formData.model.chat).then((res) => {
		gameStore.agentsData = res.data;
		console.log(gameStore.agentsData, "gameStore.agentsData");
		nextTick(() => {
			//获取数据成功之后关闭面板
			emit('close-panel');
			//生成新地图
			props.newMap(res.data.agent_count);
			//设置完成
			gameStore.setSettingComplete(true);
			loading.value = false;
		}, 1000)
	});
	axios.get(`/api/config/options?env_name=` + localStorage.getItem('scenarioName')).then((res) => {
		gameStore.systemConfig = res.data;
		console.log(gameStore.systemConfig, "gameStore.systemConfig");
	});
};
const handleReset = () => {
	// Reset form data
	Object.assign(formData, {
		environment: {
			name: "broken_window_theory",
			mode: "round",
			modes: ["round", "tick"],
			max_steps: 3,
		},
		agent: {
			profile: {
				Resident: {
					count: 1,
					max_count: 5,
				},
				LawEnforcementOfficer: {
					count: 1,
					max_count: 5,
				},
				UrbanEnvironment: {
					count: 1,
					max_count: 5,
				},
			},
			planning: ["None", "BDIPlanning", "COTPlanning", "TOMPlanning"],
			memory: ["None", "ListStrategy", "ShortLongStrategy"],
		},
	});
};

const getOptions = () => {
	const isDevMode = gameStore.isDevMode;
	const systemConfig = gameStore.systemConfig;
	if (isDevMode) {
		planning.value = systemConfig.agent.planning;
		memory.value = systemConfig.agent.memory;
		formData.environment = systemConfig.environment;
		formData.agent.profile = systemConfig.agent.profile;
		chat.value = systemConfig.model.chat;
		embedding.value = systemConfig.model.embedding;
	} else {
		axios.get(`/api/config/options?env_name=${localStorage.getItem('scenarioName')}`).then((res) => {
			planning.value = res.data.agent.planning;
			memory.value = res.data.agent.memory;
			formData.environment = res.data.environment;
			formData.agent.profile = res.data.agent.profile;
			chat.value = res.data.model.chat;
			embedding.value = res.data.model.embedding;
			
			formData.model.chat = chat.value[0]
			formData.model.embedding = embedding.value[0]
			formData.agent.memory = memory.value[0]
			formData.agent.planning = planning.value[0]
		});
	}
};

// 每次打开设置面板时刷新选项数据的方法
const refreshOptions = () => {
	console.log('SettingsPanel refreshOptions called');
	getOptions();
};

// onMounted(() => {
// 	console.log('agentsData',agentsData.agents);
// });

// 向父组件暴露refreshOptions方法和isFormSubmitted状态
defineExpose({
	refreshOptions,
	isFormSubmitted
});

const isPaused = computed(() => {
	return gameStore.isPaused;
});
</script>

<style scoped>
.settings-panel {
	/* padding: 20px; */
	height: 100%;
	background-color: var(--panel-bg, #ffffff);
	transition: all 0.3s ease;
	display: flex;
	flex-direction: column;
}

h2 {
	margin-bottom: 20px;
	font-size: 1.5rem;
	color: var(--text-color, #333333);
}

.panel-content {
	flex: 1;
	border: 1px solid var(--border-color, #e0e0e0);
	border-radius: 8px;
	padding: 15px;
	background-color: var(--panel-bg, #f8f8f8);
	transition: all 0.3s ease;
	overflow-y: auto;
	margin-bottom: 20px;
}

/* 外部按钮区域样式 */
.settings-actions {}

.agent-profile {
	margin-bottom: 20px;
	padding: 15px;
	border: 1px solid var(--border-color, #e0e0e0);
	border-radius: 4px;
	background-color: var(--card-bg, #ffffff);
	transition: all 0.3s ease;
}

.agent-profile h4 {
	margin: 0 0 15px 0;
	color: var(--text-color, #333333);
}

.el-divider {
	margin: 20px 0;
}

.el-divider__text {
	color: var(--text-color, #333333);
	background-color: var(--panel-bg, #f8f8f8);
}

/* Form elements styling */
:deep(.el-form-item__label) {
	color: var(--text-color, #333333);
}

:deep(.el-input__wrapper) {
	background-color: var(--input-bg, #ffffff);
	border-color: var(--border-color, #e0e0e0);
	box-shadow: 0 0 0 1px var(--border-color, #e0e0e0);
	transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
	box-shadow: 0 0 0 1px var(--primary-color, #409eff);
}

:deep(.el-input__wrapper.is-focus) {
	box-shadow: 0 0 0 1px var(--primary-color, #409eff);
}

:deep(.el-input__inner) {
	background-color: var(--input-bg, #ffffff);
	border-color: var(--border-color, #e0e0e0);
	color: var(--text-color, #333333);
}

:deep(.el-input__inner:hover) {
	border-color: var(--primary-color, #409eff);
}

:deep(.el-select .el-input__inner) {
	background-color: var(--input-bg, #ffffff);
}

:deep(.el-select-dropdown) {
	background-color: var(--dropdown-bg, #ffffff);
	border-color: var(--border-color, #e0e0e0);
}

:deep(.el-select-dropdown__item) {
	color: var(--text-color, #333333);
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
	background-color: var(--hover-bg, #f5f7fa);
	color: var(--primary-color, #409eff);
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
	background-color: var(--input-bg, #ffffff);
	border-color: var(--border-color, #e0e0e0);
	color: var(--text-color, #333333);
}

:deep(.el-input-number__decrease:hover),
:deep(.el-input-number__increase:hover) {
	color: var(--primary-color, #409eff);
	border-color: var(--primary-color, #409eff);
}

/* Dark theme styles */
.simulation-layout.dark-theme .settings-panel {
	background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme .settings-panel h2 {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .panel-content {
	background-color: var(--dark-panel-bg, #1a1a1a);
	border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .agent-profile {
	background-color: var(--dark-card-bg, #2a2a2a);
	border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .agent-profile h4 {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .el-divider__text {
	color: var(--dark-text-color, #ffffff);
	background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme :deep(.el-form-item__label) {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-input__wrapper) {
	background-color: var(--dark-input-bg, #2a2a2a);
	border-color: var(--dark-border-color, #333333);
	box-shadow: 0 0 0 1px var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-input__wrapper:hover) {
	box-shadow: 0 0 0 1px var(--primary-color, #409eff);
}

.simulation-layout.dark-theme :deep(.el-input__wrapper.is-focus) {
	box-shadow: 0 0 0 1px var(--primary-color, #409eff);
}

.simulation-layout.dark-theme :deep(.el-input__inner) {
	background-color: var(--dark-input-bg, #2a2a2a);
	border-color: var(--dark-border-color, #333333);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-select .el-input__inner) {
	background-color: var(--dark-input-bg, #2a2a2a);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown) {
	background-color: var(--dark-dropdown-bg, #2a2a2a);
	border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown__item) {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown__item.hover),
.simulation-layout.dark-theme :deep(.el-select-dropdown__item:hover) {
	background-color: var(--dark-hover-bg, #3a3a3a);
	color: var(--primary-color, #409eff);
}

.simulation-layout.dark-theme :deep(.el-input-number__decrease),
.simulation-layout.dark-theme :deep(.el-input-number__increase) {
	background-color: var(--dark-input-bg, #2a2a2a);
	border-color: var(--dark-border-color, #333333);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-input-number__decrease:hover),
.simulation-layout.dark-theme :deep(.el-input-number__increase:hover) {
	color: var(--primary-color, #409eff);
	border-color: var(--primary-color, #409eff);
}

.agent-config-container {
	border: 1px solid var(--border-color, #e0e0e0);
	border-radius: 8px;
	padding: 20px;
	background-color: var(--panel-bg, #ffffff);
	transition: all 0.3s ease;
	width: 100%;
}

.agent-config-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.agent-config-header h3 {
	margin: 0;
	font-size: 1.2rem;
	color: var(--text-color, #333333);
}

.search-input {
	width: 200px;
}

.agent-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 16px;
	margin-top: 16px;
}

.agent-card {
	background-color: var(--card-bg, #ffffff);
	border: 1px solid var(--border-color, #e0e0e0);
	border-radius: 8px;
	padding: 16px;
	cursor: pointer;
	transition: all 0.3s ease;
	position: relative;
	overflow: hidden;
	width: 100%;
	margin: 0 auto;
}

.agent-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.agent-card-content {
	display: flex;
	align-items: center;
	gap: 12px;
	width: 100%;
}

.agent-icon {
	width: 40px;
	height: 40px;
	border-radius: 50%;
	background-color: var(--primary-color-light, #ecf5ff);
	display: flex;
	align-items: center;
	justify-content: center;
	color: var(--primary-color, #409eff);
	font-size: 20px;
}

.agent-info {
	flex: 1;
	display: flex;
	justify-content: space-between;
	align-items: center;
	min-width: 0;
}

.agent-info h4 {
	margin: 0;
	font-size: 1rem;
	color: var(--text-color, #333333);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.agent-info p {
	margin: 0;
	font-size: 0.875rem;
	color: var(--text-secondary, #666666);
	white-space: nowrap;
}

/* Dark theme styles */
.simulation-layout.dark-theme .agent-config-container {
	background-color: var(--dark-panel-bg, #1a1a1a);
	border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .agent-config-header h3 {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .agent-card {
	background-color: var(--dark-card-bg, #2a2a2a);
	border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .agent-info h4 {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .agent-info p {
	color: var(--dark-text-secondary, #999999);
}

.simulation-layout.dark-theme .agent-icon {
	background-color: var(--dark-primary-color-light, #1a2b4c);
	color: var(--primary-color, #409eff);
}

/* Dialog styles */
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 10;
}

.modal-content {
	background-color: var(--panel-bg, #ffffff);
	padding: 20px;
	border-radius: 8px;
	width: 400px;
	max-height: 80vh;
	overflow-y: auto;
}

.modal-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.modal-header h3 {
	margin: 0;
	font-size: 1.2rem;
	color: var(--text-color, #333333);
}

.close-btn {
	background: none;
	border: none;
	font-size: 1.5rem;
	color: var(--text-color, #333333);
	cursor: pointer;
}

.modal-form {
	margin-bottom: 20px;
}

.agent-edit-info {
	padding: 12px 0px;
	border-radius: 4px;
}

.max-count-info {
	margin: 0;
	font-size: 14px;
	color: var(--info-color, #909399);
	line-height: 1.5;
}

/* Dark theme styles */
.simulation-layout.dark-theme .modal-overlay {
	background-color: rgba(0, 0, 0, 0.7);
}

.simulation-layout.dark-theme .modal-content {
	background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme .modal-header h3 {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .max-count-info {
	color: var(--dark-info-color, #a6a6a6);
}

/* El-Table Styles */
:deep(.el-table) {
	--el-table-border-color: var(--border-color, #e0e0e0);
	--el-table-header-bg-color: var(--panel-bg, #f8f8f8);
	--el-table-header-text-color: var(--text-color, #333333);
	--el-table-row-hover-bg-color: var(--hover-bg, #f5f7fa);
	--el-table-current-row-bg-color: var(--hover-bg, #f5f7fa);
	--el-table-bg-color: var(--panel-bg, #ffffff);
	--el-table-tr-bg-color: var(--panel-bg, #ffffff);
	--el-table-expanded-cell-bg-color: var(--panel-bg, #ffffff);
	--el-table-fixed-box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
	--el-table-text-color: var(--text-color, #333333);
	--el-table-footer-bg-color: var(--panel-bg, #f8f8f8);
	border-radius: 8px;
	overflow: hidden;
}

:deep(.el-table th) {
	font-weight: 500;
	background-color: var(--panel-bg, #f8f8f8);
	color: var(--text-color, #333333);
}

:deep(.el-table td) {
	color: var(--text-color, #333333);
}

:deep(.el-table--border th),
:deep(.el-table--border td) {
	border-color: var(--border-color, #e0e0e0);
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
	background-color: var(--hover-bg, #f5f7fa);
}

:deep(.el-table__body tr.hover-row > td),
:deep(.el-table__body tr:hover > td) {
	background-color: var(--hover-bg, #f5f7fa);
}

:deep(.el-table .cell) {
	word-break: break-word;
}

:deep(.el-table__row) {
	transition: background-color 0.3s ease;
}

:deep(.el-pagination) {
	margin-top: 16px;
	text-align: right;
}

:deep(.el-pagination .el-pagination__total),
:deep(.el-pagination .el-pagination__jump) {
	color: var(--text-color, #333333);
}

:deep(.el-pagination .el-input__inner) {
	background-color: var(--input-bg, #ffffff);
	color: var(--text-color, #333333);
}

:deep(.el-pagination button) {
	background-color: var(--input-bg, #ffffff);
	color: var(--text-color, #333333);
}

:deep(.el-pagination button:hover) {
	color: var(--primary-color, #409eff);
}

:deep(.el-pagination button:disabled) {
	background-color: var(--input-bg, #ffffff);
	color: var(--text-secondary, #c0c4cc);
}

:deep(.el-pagination .el-pager li) {
	background-color: var(--input-bg, #ffffff);
	color: var(--text-color, #333333);
}

:deep(.el-pagination .el-pager li:hover) {
	color: var(--primary-color, #409eff);
}

:deep(.el-pagination .el-pager li.active) {
	background-color: var(--primary-color, #409eff);
	color: #ffffff;
}

:deep(.el-select__wrapper) {
	box-shadow: 0 0 0 1px var(--el-border-color) inset !important;
}

/* Dark Theme El-Table Styles */
.simulation-layout.dark-theme :deep(.el-table) {
	--el-table-border-color: var(--dark-border-color, #333333);
	--el-table-header-bg-color: var(--dark-panel-bg, #2a2a2a);
	--el-table-header-text-color: var(--dark-text-color, #ffffff);
	--el-table-row-hover-bg-color: var(--dark-hover-bg, #3a3a3a);
	--el-table-current-row-bg-color: var(--dark-hover-bg, #3a3a3a);
	--el-table-bg-color: var(--dark-panel-bg, #1a1a1a);
	--el-table-tr-bg-color: var(--dark-panel-bg, #1a1a1a);
	--el-table-expanded-cell-bg-color: var(--dark-panel-bg, #1a1a1a);
	--el-table-fixed-box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
	--el-table-text-color: var(--dark-text-color, #ffffff);
	--el-table-footer-bg-color: var(--dark-panel-bg, #2a2a2a);
}

.simulation-layout.dark-theme :deep(.el-table) {
	background-color: var(--dark-panel-bg, #1a1a1a);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-table th) {
	background-color: var(--dark-panel-bg, #2a2a2a);
	color: var(--dark-text-color, #ffffff);
	border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-table td) {
	border-color: var(--dark-border-color, #333333);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
	background-color: var(--dark-hover-bg, #262626);
}

.simulation-layout.dark-theme :deep(.el-table__body tr.hover-row > td),
.simulation-layout.dark-theme :deep(.el-table__body tr:hover > td) {
	background-color: var(--dark-hover-bg, #3a3a3a);
}

.simulation-layout.dark-theme :deep(.el-table::before) {
	background-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-table__empty-block) {
	background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme :deep(.el-table__empty-text) {
	color: var(--dark-text-secondary, #999999);
}

.simulation-layout.dark-theme :deep(.el-pagination .el-pagination__total),
.simulation-layout.dark-theme :deep(.el-pagination .el-pagination__jump) {
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-pagination .el-input__inner) {
	background-color: var(--dark-input-bg, #2a2a2a);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-pagination button) {
	background-color: var(--dark-input-bg, #2a2a2a);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-pagination button:disabled) {
	background-color: var(--dark-input-bg, #2a2a2a);
	color: var(--dark-text-secondary, #666666);
}

.simulation-layout.dark-theme :deep(.el-pagination .el-pager li) {
	background-color: var(--dark-input-bg, #2a2a2a);
	color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-pagination .el-pager li.active) {
	background-color: var(--primary-color, #409eff);
	color: #ffffff;
}
</style>