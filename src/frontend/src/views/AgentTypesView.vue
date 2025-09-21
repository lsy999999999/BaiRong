<template>
  <div class="agent-types-container">
    <h2 class="page-title">Confirm Agent Types</h2>
    <p class="page-description">
      Define the types of agents that will participate in your simulation. Each agent type
      represents a role or profession in the system being modeled.
    </p>

    <div class="agent-types-content">
      <div class="agent-list-panel">
        <div class="panel-header">
          <div class="title-with-button">
            <h3>Agent Types</h3>
            <button class="add-btn" @click="showForm = true">
              <i class="fa fa-plus"></i> Add
            </button>
          </div>
          <div class="search-box">
            <input type="text" v-model="searchQuery" placeholder="Search agent types..." @input="filterAgentTypes" />
            <i class="fa fa-search"></i>
          </div>
        </div>

        <div class="agent-grid">
          <div v-for="(agent, index) in filteredAgentTypes" :key="index" class="agent-card" @click="editAgent(agent)">
            <div class="agent-name">{{ agent.name }}</div>
            <div class="agent-actions">
              <button class="action-btn edit" @click.stop="editAgent(agent)">
                <i class="fa fa-edit"></i>
              </button>
              <button class="action-btn delete" @click.stop="confirmDelete(agent)">
                <i class="fa fa-trash"></i>
              </button>
            </div>
          </div>

          <div v-if="filteredAgentTypes.length === 0" class="no-results">
            No agent types found. Try a different search or add a new agent type.
          </div>
        </div>
      </div>
    </div>

    <div class="action-buttons">
      <button class="next-btn" @click="goToNextStep" :disabled="!canProceed">
        Proceed to Next Step <i class="fa fa-arrow-right"></i>
      </button>
    </div>

    <div v-if="showEmptyWarning" class="empty-warning">
      <i class="fa fa-exclamation-triangle"></i> Please add at least one Agent type to
      proceed
    </div>

    <!-- 弹窗表单 -->
    <div class="modal-overlay" v-if="showForm" @click.self="cancelForm">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ isEditing ? "Edit Agent Type" : "Add New Agent Type" }}</h3>
          <button class="close-btn" @click="cancelForm">
            <i class="fa fa-times"></i>
          </button>
        </div>

        <form @submit.prevent="saveAgent">
          <div class="form-group">
            <label for="agentName">Agent Type Name (Role/Profession)</label>
            <input id="agentName" type="text" v-model="currentAgent.name"
              placeholder="E.g., Software Engineer, Doctor, Teacher" required @blur="ClearSpaces" />
          </div>

          <div class="form-group">
            <label for="agentDescription">Description</label>
            <textarea id="agentDescription" v-model="currentAgent.description"
              placeholder="Brief description of this agent type's role and responsibilities" rows="4"></textarea>
          </div>

          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="cancelForm">Cancel</button>
            <button type="submit" class="save-btn">
              {{ isEditing ? "Update Agent" : "Add Agent" }}
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- 全局加载层 -->
    <div class="loading-overlay" v-if="loadingData">
      <div class="spinner"></div>
      <div class="loading-text">Loading agent types...</div>
      <TipsCarousel />
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { ElMessageBox, ElMessage } from "element-plus";
import { nextTick } from "vue";
import TipsCarousel from "../components/TipsCarousel.vue";
export default {
  name: "AgentTypesView",
  components: {
    TipsCarousel,
  },
  data() {
    return {
      loadingData: false,
      agentTypes: [],
      searchQuery: "",
      filteredAgentTypes: [],
      currentAgent: {
        id: null,
        name: "",
        description: "",
      },
      isEditing: false,
      nextId: 6, // For generating new IDs
      showEmptyWarning: false,
      showForm: false,
    };
  },
  created() {
    // 尝试从localStorage获取保存的agentTypes数据
    // const savedAgentTypes = localStorage.getItem('agentTypes');
    // if (savedAgentTypes) {
    // 	try {
    // 		const parsedData = JSON.parse(savedAgentTypes);
    // 		if (Array.isArray(parsedData) && parsedData.length > 0) {
    // 			this.agentTypes = parsedData;
    // 			// 获取数组中最大的ID，设置nextId为最大ID+1
    // 			const maxId = Math.max(...this.agentTypes.map(agent => agent.id));
    // 			this.nextId = maxId + 1;
    // 		}
    // 	} catch (error) {
    // 		console.error('Error parsing saved agent types:', error);
    // 	}
    // }
  },
  mounted() {
    setTimeout(() => {
      this.subSession();
    }, 500);
  },
  computed: {
    canProceed() {
      return this.agentTypes.length > 0;
    },
  },
  methods: {
    //初始化场景
    subSession() {
      axios
        .post("/api/pipeline/initialize", {
          // "session_id": localStorage.getItem('sessionId'),
          env_name: localStorage.getItem('scenarioName'),
          model_name: this.$route.query.model_name,
          category: this.$route.query.category,
        })
        .then((response) => {
          this.loadAgentTypes();
        });
    },
    //加载AgentTypes
    loadAgentTypes() {
      this.loadingData = true;
      this.filteredAgentTypes = [];
      this.agentTypes = [];
      axios
        .post("/api/pipeline/generate_agent_types", {
          // "session_id": localStorage.getItem('sessionId'),
          env_name: localStorage.getItem('scenarioName'),
        })
        .then((response) => {
          let index = 1;
          for (let i in response.data.agent_types) {
            this.agentTypes.push({
              id: index,
              name: i,
              description: response.data.agent_types[i],
            });
            index++;
          }
          this.loadingData = false;
          this.filterAgentTypes();
        });
    },
    filterAgentTypes() {
      if (!this.searchQuery) {
        this.filteredAgentTypes = [...this.agentTypes];
        return;
      }

      const query = this.searchQuery.toLowerCase();
      this.filteredAgentTypes = this.agentTypes.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query)
      );
    },

    editAgent(agent) {
      this.currentAgent = {
        id: agent.id,
        name: agent.name,
        description: agent.description,
      };
      this.isEditing = true;
      this.showForm = true;
    },

    confirmDelete(agent) {
      this.$confirm(
        `Are you sure you want to delete the agent type "${agent.name}"?`,
        "Warning",
        {
          confirmButtonText: "Confirm",
          cancelButtonText: "Cancel",
          type: "warning",
        }
      )
        .then(() => {
          this.confirmDel(agent.id);
        })
        .catch(() => {
          // User cancelled, do nothing
        });
    },
    ClearSpaces() {
      if (this.currentAgent.name.includes(" ")) {
        this.currentAgent.name = this.currentAgent.name.replace(/\s+/g, '');
      }
    },
    confirmDel(id) {
      this.loadingData = true;
      let agentTypes_new = {};
      for (let i in this.agentTypes) {
        if (this.agentTypes[i].id != id) {
          agentTypes_new[this.agentTypes[i].name] = this.agentTypes[i].description;
        }
      }
      this.filteredAgentTypes = [];
      this.agentTypes = [];

      axios
        .post("/api/pipeline/update_agent_types", {
          env_name: localStorage.getItem('scenarioName'),
          // session_id: localStorage.getItem("sessionId"),
          agent_types: agentTypes_new,
        })
        .then((response) => {
          let index = 1;
          for (let i in response.data.agent_types) {
            this.agentTypes.push({
              id: index,
              name: i,
              description: response.data.agent_types[i],
            });
            index++;
          }
          this.loadingData = false;
          this.filterAgentTypes();
        });
    },
    saveAgent() {
      this.loadingData = true;
      let agentTypes_new = {};
      if (this.isEditing) {
        for (let i in this.agentTypes) {
          if (this.agentTypes[i].id != this.currentAgent.id) {
            agentTypes_new[this.agentTypes[i].name] = this.agentTypes[i].description;
          }
        }
      } else {
        for (let i in this.agentTypes) {
          agentTypes_new[this.agentTypes[i].name] = this.agentTypes[i].description;
        }
      }

      agentTypes_new[this.currentAgent.name] = this.currentAgent.description;
      this.filteredAgentTypes = [];
      this.agentTypes = [];
      axios
        .post("/api/pipeline/update_agent_types", {
          env_name: localStorage.getItem('scenarioName'), 
          agent_types: agentTypes_new,
        })
        .then((response) => {
          let index = 1;
          for (let i in response.data.agent_types) {
            this.agentTypes.push({
              id: index,
              name: i,
              description: response.data.agent_types[i],
            });
            index++;
          }
          this.filterAgentTypes();
          this.cancelForm();
          this.$nextTick(() => {
            this.loadingData = false;
          });
        });
    },

    resetForm() {
      this.currentAgent = {
        id: null,
        name: "",
        description: "",
      };
      this.isEditing = false;
    },

    cancelForm() {
      this.resetForm();
      this.showForm = false;
    },

    goToNextStep() {
      ElMessageBox.confirm(
        "Are you sure you want to proceed to the next step?",
        "Confirmation",
        {
          confirmButtonText: "OK",
          cancelButtonText: "Cancel",
        }
      ).then(() => {
        console.log("ok");
        if (!this.canProceed) {
          this.showEmptyWarning = true;
          setTimeout(() => {
            this.showEmptyWarning = false;
          }, 3000);
          return;
        }

        // 将agent数据保存到本地存储或状态管理系统
        localStorage.setItem("agentTypes", JSON.stringify(this.agentTypes));

        // 触发事件移动到下一步
        this.$emit("step-complete");
      });
    },
  },
  watch: {
    canProceed: {
      handler(newValue) {
        // 向父组件发送状态更新
        this.$emit("update:canProceed", newValue);
      },
      immediate: true,
    },
    loadingData: {
      handler(newValue) {
        // 监听加载状态变化并向父组件发送
        this.$emit("update:loading", newValue);
      },
      immediate: true, // 组件创建时立即执行一次
    },
  },
};
</script>

<style scoped>
.agent-types-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease;
}

/* 定义动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }

  to {
    opacity: 0;
  }
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

.page-title {
  color: var(--text-color);
  font-size: 1.8rem;
  margin-bottom: 10px;
}

.page-description {
  color: var(--secondary-color);
  font-size: 1.1rem;
  margin-bottom: 30px;
}

.agent-types-content {
  margin-bottom: 30px;
  height: 55vh;
}

.agent-list-panel {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  animation-name: slideInUp;
  animation-duration: 0.5s;
  animation-fill-mode: both;
  animation-timing-function: ease;
  will-change: transform, opacity;
  animation-delay: 0.1s;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.title-with-button {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header h3 {
  color: var(--text-color);
  margin: 0;
}

.search-box {
  position: relative;
  width: 200px;
}

.search-box input {
  width: 100%;
  padding: 8px 30px 8px 10px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.search-box .fa-search {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--secondary-color);
}

.add-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color, rgba(200, 200, 200, 0.3));
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--button-bg-color, rgba(255, 255, 255, 0.08));
  color: var(--text-color);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.06);
}

.add-btn:hover {
  background-color: var(--button-hover-bg-color, rgba(255, 255, 255, 0.15));
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.agent-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 10px;
  scrollbar-gutter: stable;
  align-content: flex-start;
}

.agent-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: var(--card-bg-color, rgba(255, 255, 255, 0.05));
  border-radius: 8px;
  transition: all 0.2s ease;
  animation: fadeIn 0.4s ease;
  width: calc(33% - 15px);
  min-width: 250px;
  cursor: pointer;
  height: fit-content;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
}

.agent-card:hover {
  background-color: var(--card-hover-bg-color, rgba(255, 255, 255, 0.1));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: var(--border-hover-color, rgba(255, 255, 255, 0.2));
}

.agent-card.fade-out {
  animation: fadeOut 0.3s ease forwards;
}

.agent-name {
  font-weight: 500;
  color: var(--text-color);
}

.agent-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.edit {
  background-color: rgba(65, 105, 225, 0.2);
  color: #4169e1;
}

.action-btn.delete {
  background-color: rgba(220, 53, 69, 0.2);
  color: #dc3545;
}

.action-btn:hover {
  transform: scale(1.1);
}

.no-results {
  padding: 20px;
  text-align: center;
  color: var(--secondary-color);
  font-style: italic;
  animation: fadeIn 0.5s ease;
  width: 100%;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
  animation: fadeIn 0.6s ease both;
}

.next-btn {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--accent-color);
  color: white;
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: rgba(65, 112, 243, 0.5);
}

.next-btn:not(:disabled):hover {
  transform: translateY(-2px);
}

.empty-warning {
  margin-top: 15px;
  color: #e74c3c;
  text-align: center;
  padding: 10px;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: 8px;
  animation: fadeIn 0.3s ease;
}

/* 弹窗样式 */
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
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  width: 500px;
  max-width: 90%;
  background-color: var(--bg-color);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  animation: slideInUp 0.3s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-color);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-color);
  font-size: 1.2rem;
  cursor: pointer;
}

form {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
  animation: fadeIn 0.5s ease both;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-color);
  font-weight: 500;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
  font-size: 1rem;
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn,
.save-btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.cancel-btn {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.save-btn {
  background-color: var(--accent-color);
  color: white;
}

.cancel-btn:hover,
.save-btn:hover {
  transform: translateY(-2px);
}

/* Responsive design */
@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .title-with-button {
    width: 100%;
    justify-content: space-between;
  }

  .search-box {
    width: 100%;
  }

  .add-btn {
    white-space: nowrap;
  }

  .agent-card {
    width: 100%;
  }

  .action-buttons {
    flex-direction: column;
    gap: 15px;
  }

  .next-btn {
    width: 100%;
    justify-content: center;
  }
}

/* 自定义加载动画样式 */
.agent-list-panel .el-loading-mask {
  background-color: rgba(0, 0, 0, 0.1);
}

.agent-list-panel .el-loading-spinner .circular {
  width: 30px;
  height: 30px;
}

.agent-list-panel .el-loading-spinner .path {
  stroke: var(--accent-color);
  stroke-width: 3;
}

.agent-list-panel .el-loading-text {
  color: var(--accent-color);
  margin-top: 10px;
  font-size: 14px;
}

.loading-overlay {
  position: fixed;
  top: 120px;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-color, rgba(255, 255, 255, 0.8));
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  opacity: 0.9;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color, rgba(255, 255, 255, 0.1));
  border-radius: 50%;
  border-top: 3px solid var(--accent-color);
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 10px;
  font-size: 1rem;
  color: var(--text-color, #333);
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

</style>
