<template>
  <div class="character-detail-panel">
    <div v-if="!selectedCharacter" class="no-character-selected">
      <el-empty description="Please select a character from the list to view details"></el-empty>
    </div>

    <template v-else>
      <!-- Character Basic Info -->
      <div class="character-basic-info">
        <div class="character-avatar">
          <div ref="avatarContainer" class="avatar-pixi-container"></div>
        </div>
        <div class="character-info">
          <h3>{{ selectedCharacter.name }}</h3>
          <div class="info-row">
            <span class="info-label">ID:</span>
            <span class="info-value">{{ selectedCharacter.id }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Type:</span>
            <span class="info-value">{{ selectedCharacter.agent_type }}</span>
          </div>
        </div>
        <div class="character-controls">
          <el-button-group>
            <el-button type="primary" :icon="ArrowLeft" @click="loadPreviousCharacter">Previous</el-button>
            <el-button type="primary" @click="loadNextCharacter">Next<el-icon class="el-icon--right">
                <component :is="ArrowRight" />
              </el-icon></el-button>
          </el-button-group>
        </div>
      </div>

      <!-- Character Detailed Attributes -->
      <div class="character-tabs-container">
        <el-tabs class="character-tabs" v-model="activeTab">
          <!-- Dynamic Attributes Tab -->
          <el-tab-pane label="Detailed Attributes" name="info">
                          <!-- Button Area -->
                          <div class="attribute-actions">
                <el-button v-if="!isEditing" type="primary" @click="startEditing">Edit</el-button>
                <template v-else>
                  <el-button type="success" @click="confirmSave">Save</el-button>
                  <el-button @click="confirmReset">Reset</el-button>
                </template>
              </div>
            <div class="tab-content-wrapper">
              <el-descriptions border :column="1" class="attribute-list" label-width="200">
                <el-descriptions-item v-for="(value, key) in dynamicAttributes" :key="key" :label="formatLabel(key)">
                  <!-- Nested objects display as secondary tables -->
                  <template v-if="isNestedObject(value)">
                    <el-table :data="convertObjectToTableData(value)" border stripe size="small" class="nested-table"
                      :show-header="false">
                      <el-table-column prop="key" label="" width="180" />
                      <el-table-column prop="value" label="">
                        <template #default="scope">
                          <!-- For simple type values show input box -->
                          <el-input v-if="isEditing && isEditableType(scope.row.value)" 
                            v-model="scope.row.value" 
                            :disabled="!isEditing"></el-input>
                          <!-- For nested objects render recursively -->
                          <template v-else-if="isNestedObject(scope.row.value)">
                            <div class="nested-object-container">
                              <el-table 
                                :data="convertObjectToTableData(scope.row.value)" 
                                border stripe size="small" 
                                class="nested-table-second-level" 
                                :show-header="false">
                                <el-table-column prop="key" label="" width="160" />
                                <el-table-column prop="value" label="">
                                  <template #default="nestedScope">
                                    <el-input v-if="isEditing && isEditableType(nestedScope.row.value)" 
                                      v-model="nestedScope.row.value" 
                                      :disabled="!isEditing"></el-input>
                                    <span v-else>{{ formatValue(nestedScope.row.value) }}</span>
                                  </template>
                                </el-table-column>
                              </el-table>
                            </div>
                          </template>
                          <!-- For arrays display formatted content -->
                          <template v-else-if="Array.isArray(scope.row.value)">
                            <span>{{ formatArrayValue(scope.row.value) }}</span>
                          </template>
                          <!-- For other cases display formatted value -->
                          <span v-else>{{ formatValue(scope.row.value) }}</span>
                        </template>
                      </el-table-column>
                    </el-table>
                  </template>
                  <!-- Regular values display directly -->
                  <template v-else>
                    <el-input v-if="isEditing && isEditableType(value)" 
                      v-model="editableAttributes[key]" 
                      :disabled="!isEditing"></el-input>
                    <span v-else>{{ formatValue(value) }}</span>
                  </template>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>

          <!-- Event History Tab -->
          <el-tab-pane label="Event History" name="history">
            <div class="tab-content-wrapper">
              <div class="event-history">
                <div v-if="characterEvents.length > 0">
                  <el-timeline>
                    <el-timeline-item v-for="(event, index) in characterEvents" :key="index"
                      :timestamp="event.time || 'Unknown time'"
                      :type="event.eventType === 'InformationGeneratedEvent' ? 'primary' : 'info'">
                      <div class="event-header">
                        <h4>{{ event.title }}
                          <el-tag size="small" type="info" class="event-step">Step: {{ event.step }}</el-tag>
                        </h4>
                      </div>
                      <p class="event-description" v-if="!isNestedObject(event.description)">{{ event.description }}</p>
                      <!-- Nested objects display as tables -->
                      <div class="event-description-table" v-else>
                        <el-table :data="convertObjectToTableData(event.description)" border stripe size="small"
                          class="nested-table" :show-header="false">
                          <el-table-column prop="key" label="" width="180" />
                          <el-table-column prop="value" label="">
                            <template #default="scope">
                              <template v-if="scope.row.value && scope.row.value._isArray">
                                <div v-if="scope.row.value._tableData" class="nested-array-container">
                                  <el-table :data="scope.row.value._tableData" border stripe size="small"
                                    class="nested-table-second-level" :show-header="false">
                                    <el-table-column prop="key" label="" width="60" />
                                    <el-table-column prop="value" label="">
                                      <template #default="arrayScope">
                                        <div v-if="arrayScope.row.value && arrayScope.row._isNestedObject" class="nested-object-container">
                                          <el-table :data="arrayScope.row._tableData" border stripe size="small"
                                            class="nested-table-third-level" :show-header="false">
                                            <el-table-column prop="key" label="" width="120" />
                                            <el-table-column prop="value" label="">
                                              <template #default="nestedScope">
                                                <span>{{ formatValue(nestedScope.row.value) }}</span>
                                              </template>
                                            </el-table-column>
                                          </el-table>
                                        </div>
                                        <span v-else>{{ formatValue(arrayScope.row.value) }}</span>
                                      </template>
                                    </el-table-column>
                                  </el-table>
                                </div>
                                <span v-else>{{ scope.row.value._formattedValue }}</span>
                              </template>
                              <template v-else-if="isNestedObject(scope.row.value)">
                                <div class="nested-object-container">
                                  <el-table :data="convertObjectToTableData(scope.row.value)" border stripe size="small"
                                    class="nested-table-second-level" :show-header="false">
                                    <el-table-column prop="key" label="" width="160" />
                                    <el-table-column prop="value" label="">
                                      <template #default="nestedScope">
                                        <span>{{ formatValue(nestedScope.row.value) }}</span>
                                      </template>
                                    </el-table-column>
                                  </el-table>
                                </div>
                              </template>
                              <span v-else>{{ formatValue(scope.row.value) }}</span>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                      <div class="event-participants" v-if="event.participants">
                        <span class="participant-label">Participants: </span>
                        <el-tag v-for="participant in event.participants" :key="participant.id" class="participant-tag"
                          :type="participant.id === 'ENV' ? 'info' : 'primary'"
                          @click="participant.id !== 'ENV' && viewParticipant(participant.id)"
                          :class="{ 'env-tag': participant.id === 'ENV' }">
                          {{ participant.name }}
                        </el-tag>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                </div>
                <div v-else class="no-data">
                  <el-empty description="No related event records"></el-empty>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Chat List Tab -->
          <el-tab-pane label="Conversations" name="chat">
            <div class="tab-content-wrapper">
              <div class="dialog-list">
                <div class="dialog-history" ref="dialogHistoryRef">
                  <div v-if="dialogHistory.length > 0" class="dialog-messages">
                    <div v-for="(message, index) in dialogHistory"
                      :key="`message-${selectedCharacter.value?.id}-${message.role}-${index}-${message.timestamp}`"
                      :class="['message', message.role === 'user' ? 'message-user' : 'message-agent']">
                      <!-- <div class="message-avatar">
                        <el-avatar :size="40"
                          :src="message.from === 'user' ? '/user-avatar.png' : '/placeholder-avatar.png'" />
                      </div> -->
                      <div class="message-content">
                        <div class="message-name">{{ message.role === 'user' ? 'Me' : selectedCharacter.name }}</div>
                        <div class="message-text">{{ message.content }}</div>
                        <div class="message-time">{{ message.timestamp || formatTime(new Date()) }}</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="no-messages">
                    <el-empty description="No conversation records, send a message to start chatting"></el-empty>
                  </div>
                </div>

                <div class="dialog-input">
                  <el-input class="Character-dialogue-input" v-model="messageInput" type="textarea" :rows="2"
                    placeholder="Enter a message to chat with the character..." @keyup.enter.exact="sendMessage" />
                  <el-button type="primary" @click="sendMessage" :disabled="!messageInput.trim()">
                    Send
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Debug Data Tab - Only visible in developer mode -->
          <el-tab-pane v-if="isDevMode" label="Debug Data" name="debug">
            <div class="tab-content-wrapper">
              <div class="debug-data">
                <div v-if="characterRawData" class="markdown-container">
                  <pre class="markdown-content">{{ characterRawData }}</pre>
                </div>
                <div v-else class="no-data">
                  <el-empty description="Unable to get character raw data"></el-empty>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue';
import { useGameStore } from '../../../stores/gameStore';
import { useRoute, useRouter } from 'vue-router';
import axios from "axios";
import { ElMessage, ElMessageBox } from 'element-plus';
import * as PIXI from 'pixi.js';

export default {
  name: 'CharacterDetailPanel',
  props: {
    characterId: {
      type: String,
      default: ''
    },
    visible: {
      type: Boolean,
      default: true
    }
  },
  emits: ['panel-close'],
  setup(props, { emit }) {
    const route = useRoute();
    const router = useRouter();
    const gameStore = useGameStore();
    // 选中的人物数据
    const selectedCharacter = ref(null);
    const currentIndex = ref(-1);
    
    // 添加PIXI相关的引用
    const avatarContainer = ref(null);
    const pixiApp = ref(null);
    const avatarSprite = ref(null);
    const pixiInitialized = ref(false); // 添加初始化状态标志
    
    // 添加开发者模式状态
    const isDevMode = computed(() => gameStore.devModeEnabled);
    
    // 添加activeTab状态
    const activeTab = ref('info');
    
    // 添加人物原始数据，用于调试选项卡
    const characterRawData = computed(() => {
      if (!selectedCharacter.value || !selectedCharacter.value.id) return '';
      
      // 从gameStore获取完整的角色数据
      const fullCharacter = gameStore.getAllCharacters.find(
        char => char.agentId === selectedCharacter.value.id
      );
      
      if (!fullCharacter) return '';
      
      // 构建Markdown格式的字符串
      const fields = [
        `agentId: "${fullCharacter.agentId}"`,
        `agentType: "${fullCharacter.agentType || fullCharacter.type}"`,
        `avatarConfig: "${fullCharacter.avatarConfig}"`,
        `bounds: ${JSON.stringify(fullCharacter.bounds)}`,
        `buildingId: ${JSON.stringify(fullCharacter.buildingId)}`,
        `buildingInterval: ${fullCharacter.buildingInterval}`,
        `buildingStayTime: ${fullCharacter.buildingStayTime}`,
        `gridX: ${fullCharacter.gridX}`,
        `gridY: ${fullCharacter.gridY}`,
        `id: "${fullCharacter.id}"`,
        `isFocused: ${fullCharacter.isFocused}`,
        `isGoingToBuilding: ${fullCharacter.isGoingToBuilding}`,
        `isIndoor: ${fullCharacter.isIndoor}`,
        `isMoving: ${fullCharacter.isMoving}`,
        `isWorking: ${fullCharacter.isWorking}`,
        `lastBuildingTime: ${fullCharacter.lastBuildingTime}`,
        `lastUpdateTime: ${fullCharacter.lastUpdateTime}`,
        `moveInterval: ${fullCharacter.moveInterval}`,
        `moveTimer: ${fullCharacter.moveTimer}`,
        `speed: ${fullCharacter.speed}`,
        `targetGridX: ${fullCharacter.targetGridX}`,
        `targetGridY: ${fullCharacter.targetGridY}`,
        `targetX: ${fullCharacter.targetX}`,
        `targetY: ${fullCharacter.targetY}`,
        `type: "${fullCharacter.type}"`,
        `x: ${fullCharacter.x}`,
        `y: ${fullCharacter.y}`
      ].join('\n');
      
      return fields;
    });
    
    // 对话相关
    const dialogHistory = ref([]);
    const messageInput = ref('');
    const dialogHistoryRef = ref(null);
    
    // 事件历史
    const characterEvents = ref([]);
    
    // 添加编辑表单相关状态和方法
    const isEditing = ref(false);
    const editableAttributes = ref({});
    const originalAttributes = ref({});
    
    // 监听面板可见性变化
    watch(() => props.visible, (newVisible) => {
      if (!newVisible) {
        // 面板被关闭，清除URL参数
        clearUrlParams();
        
        // 重置编辑状态
        if (isEditing.value) {
          isEditing.value = false;
          editableAttributes.value = {};
        }
      }
    });
    
    // 清除URL参数方法
    const clearUrlParams = () => {
      // 仅保留不相关的查询参数，移除panel、id和tab参数
      const newQuery = { ...route.query };
      delete newQuery.panel;
      delete newQuery.id;
      delete newQuery.tab;
      
      // 使用replace避免增加浏览器历史记录
      router.replace({ query: newQuery });
      
      console.log('已清除URL参数');
    };
    
    // 组件销毁时也清除URL参数
    onUnmounted(() => {
      clearUrlParams();
    });
    
    // 获取agent列表并按ID排序
    const allAgents = computed(() => {
      const agents = gameStore.getAgentsData.agents || [];
      // 按ID排序（数字排序）
      return [...agents].sort((a, b) => {
        const idA = parseInt(a.id) || 0;
        const idB = parseInt(b.id) || 0;
        return idA - idB;
      });
    });
    
    // 获取所有事件
    const allEvents = computed(() => {
      return gameStore.getEventsData || [];
    });
    
    // 计算属性：动态属性（排除固定字段）
    const dynamicAttributes = computed(() => {
      if (!selectedCharacter.value || !selectedCharacter.value.profile) return {};
      
      // 排除已在基础信息中显示的字段
      const fixedFields = ['id', 'name', 'agent_type'];
      const result = {};
      
      Object.entries(selectedCharacter.value.profile).forEach(([key, value]) => {
        if (!fixedFields.includes(key)) {
          result[key] = value;
        }
      });
      
      return result;
    });
    
    // 格式化标签名
    const formatLabel = (key) => {
      // 驼峰转换为空格分隔的文本
      return key.replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/^\s+/, '')
        .replace(/^./, str => str.toUpperCase());
    };
    
    // 格式化属性值
    const formatValue = (value) => {
      if (value === null || value === undefined) return '无';
      if (isNestedObject(value)) return ''; // 嵌套对象由表格单独处理
      if (typeof value === 'object') return JSON.stringify(value);
      return value.toString();
    };
    
    // 检查是否为嵌套对象
    const isNestedObject = (value) => {
      if (value === null || value === undefined) return false;
      if (Array.isArray(value)) return false; // 数组不算嵌套对象
      if (typeof value !== 'object') return false;
      
      // 过滤掉内部使用的_tableData属性
      if (Object.keys(value).length === 1 && value._tableData) return false;
      
      return true;
    };
    
    // 格式化数组值
    const formatArrayValue = (arr) => {
      if (!Array.isArray(arr)) return '[]';
      
      // Check array length
      if (arr.length === 0) return '[]';
      
      // Truncate long arrays
      const maxDisplayItems = 3;
      let result = arr.slice(0, maxDisplayItems).map(item => {
        if (typeof item === 'object') return '[Object]';
        return String(item);
      }).join(', ');
      
      // If array length exceeds limit, add ellipsis
      if (arr.length > maxDisplayItems) {
        result += `, ...${arr.length - maxDisplayItems} more items`;
      }
      
      return `[${result}]`;
    };
    
    // 格式化时间
    const formatTime = (date) => {
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      return `${hours}:${minutes}`;
    };
    
    // 格式化时间戳
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return '未知时间';
      
      const date = new Date(timestamp * 1000);
      return date.toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    };
    
    // 加载上一个人物
    const loadPreviousCharacter = () => {
      if (currentIndex.value <= 0) {
        // Already at the first one, show a hint
        ElMessage({
          message: 'This is already the first character',
          type: 'warning'
        });
        return;
      }
      
      currentIndex.value--;
      const prevId = allAgents.value[currentIndex.value].id;
      
      // 保留当前tab
      const currentTab = route.query.tab || 'info';
      
      // 清除当前焦点角色状态
      const currentId = selectedCharacter.value?.id;
      if (currentId) {
        gameStore.clearFocusedCharacterId(currentId);
      }
      
      // 设置焦点角色ID以启用镜头跟随
      gameStore.setFocusedCharacterId(prevId);
      
      // 播放响应音效，传入角色ID
      if (gameStore.cameraController && gameStore.cameraController.playResponseSound) {
        gameStore.cameraController.playResponseSound(prevId);
      }
      
      // 使用渲染器的相机控制器查看角色详情（这会同时移动相机）
      if (gameStore.renderer && gameStore.renderer.cameraController) {
        gameStore.renderer.cameraController.viewCharacterDetail(prevId);
      }
      
      // 使用与CharacterPanel相同的导航逻辑
      router.replace({ 
        query: { 
          panel: 'characterDetail',
          id: prevId,
          tab: currentTab
        }
      });
    };
    
    // 加载下一个人物
    const loadNextCharacter = () => {
      if (currentIndex.value >= allAgents.value.length - 1) {
        // Already at the last one, show a hint
        ElMessage({
          message: 'This is already the last character',
          type: 'warning'
        });
        return;
      }
      
      currentIndex.value++;
      const nextId = allAgents.value[currentIndex.value].id;
      
      // 保留当前tab
      const currentTab = route.query.tab || 'info';
      
      // 清除当前焦点角色状态
      const currentId = selectedCharacter.value?.id;
      if (currentId) {
        gameStore.clearFocusedCharacterId(currentId);
      }
      
      // 设置焦点角色ID以启用镜头跟随
      gameStore.setFocusedCharacterId(nextId);
      
      // 播放响应音效，传入角色ID
      if (gameStore.cameraController && gameStore.cameraController.playResponseSound) {
        gameStore.cameraController.playResponseSound(nextId);
      }
      
      // 使用渲染器的相机控制器查看角色详情（这会同时移动相机）
      if (gameStore.renderer && gameStore.renderer.cameraController) {
        console.log('加载下一个人物:', nextId);
        gameStore.renderer.cameraController.viewCharacterDetail(nextId);
      }
      
      // 使用与CharacterPanel相同的导航逻辑
      router.replace({ 
        query: { 
          panel: 'characterDetail',
          id: nextId,
          tab: currentTab
        }
      });
    };
    // 查询对话历史
    const chatHistory = ()=>{
      axios.get("/api/agent/history/" + localStorage.getItem('scenarioName') + "/" + selectedCharacter.value?.id).then((response) => {
        dialogHistory.value = response.data.history;
      })
    }
    // 发送消息
    const sendMessage = () => {
      if (!messageInput.value.trim()) return;
      
      // 添加用户消息
      const param = {
        env_name: localStorage.getItem('scenarioName'),
        agent_id: selectedCharacter.value?.id,
        message: messageInput.value,
      }
      dialogHistory.value.push({
        role: 'user',
        content: messageInput.value,
        timestamp: formatTime(new Date())
      })
      messageInput.value = '';
      if (dialogHistoryRef.value) {
        dialogHistoryRef.value.scrollTop = dialogHistoryRef.value.scrollHeight;
      }
      axios.post("/api/agent/chat", param).then((response) => {
        console.log("response", response);
        dialogHistory.value = response.data.history;
        // 滚动到底部
        nextTick(() => {
          if (dialogHistoryRef.value) {
            dialogHistoryRef.value.scrollTop = dialogHistoryRef.value.scrollHeight;
          }
        });
      });
    };
    
    // 获取代理名称
    const getAgentName = (id) => {
      if (id === 'ENV') return 'System Environment';
      
      const agent = gameStore.getAgentsData.agents.find(a => a.id === id.toString());
      
      if (agent && agent.profile && agent.profile.name) {
        return agent.profile.name;
      } else {
        return `Unknown Agent(ID:${id})`;
      }
    };
    
    // 初始化PIXI应用
    const initPixiApp = async () => {
      if (pixiApp.value) {
        // 如果已存在，先销毁
        pixiApp.value.destroy(true);
        pixiInitialized.value = false;
      }
      
      try {
        // 创建新的PIXI应用 - 使用v8的API
        pixiApp.value = new PIXI.Application();
        
        // 异步初始化应用
        await pixiApp.value.init({
          width: 100,
          height: 100,
          background: 0xffffff,
          antialias: true,
          resolution: window.devicePixelRatio || 1,
          autoDensity: true,
        });
        
        // 添加到DOM
        if (avatarContainer.value) {
          avatarContainer.value.innerHTML = '';
          avatarContainer.value.appendChild(pixiApp.value.canvas);
        }
        
        // 创建精灵但不设置纹理，等待后续更新
        avatarSprite.value = new PIXI.Sprite();
        avatarSprite.value.width = 100;
        avatarSprite.value.height = 100;
        pixiApp.value.stage.addChild(avatarSprite.value);
        
        // 标记初始化完成
        pixiInitialized.value = true;
        console.log('PIXI应用初始化完成');
        
        // 如果有待处理的角色，更新头像
        if (selectedCharacter.value && selectedCharacter.value.avatarConfig) {
          updateAvatar(selectedCharacter.value.avatarConfig);
        }
      } catch (error) {
        console.error('PIXI初始化失败:', error);
      }
    };
    
    // 更新角色头像
    const updateAvatar = (avatarConfigOrPath) => {
      if (!pixiInitialized.value) {
        console.warn('PIXI尚未初始化，不能更新头像');
        return;
      }
      
      if (!pixiApp.value || !avatarSprite.value) {
        console.warn('PIXI应用或精灵对象不存在');
        return;
      }
      
      // 检查输入是否为头部配置对象
      if (typeof avatarConfigOrPath === 'object' && avatarConfigOrPath !== null) {
        // 使用配置对象生成头像
        try {
          // 导入CharacterFactory类
          import('../../../components/city-map/CharacterFactory').then(module => {
            const CharacterFactory = module.default;
            const factory = new CharacterFactory();
            
            // 获取角色性别（如果在selectedCharacter中）
            const gender = selectedCharacter.value?.gender;
            console.log('gender:', gender);
            
            // 使用工厂的generateHeadTexture方法生成头像纹理
            const headTexture = factory.generateHeadTexture(gender, avatarConfigOrPath, pixiApp.value);
            
            if (headTexture) {
              // 更新头像精灵的纹理
              avatarSprite.value.texture = headTexture;
              
              // // 调整尺寸并居中
              avatarSprite.value.width = 144;
              avatarSprite.value.height = 88;
              
              // 使精灵居中
              avatarSprite.value.x = (pixiApp.value.screen.width - avatarSprite.value.width) / 2;
              avatarSprite.value.y = (pixiApp.value.screen.height - avatarSprite.value.height) / 2;
              
              console.log('头像从配置生成成功');
            } else {
              console.warn('头像生成失败，无法获取纹理');
            }
          }).catch(error => {
            console.error('导入CharacterFactory失败:', error);
          });
        } catch (error) {
          console.error('生成头像时出错:', error);
        }
      } else if (typeof avatarConfigOrPath === 'string') {
        // 原有的通过纹理路径更新头像的逻辑
        // 从window.textures获取纹理
        const headTexture = window.textures[avatarConfigOrPath];
        if (headTexture) {
          avatarSprite.value.texture = headTexture;
          
          // 根据纹理调整尺寸（保持比例）
          avatarSprite.value.width = 144;
          avatarSprite.value.height = 88;
          
          // 使精灵居中
          avatarSprite.value.x = (pixiApp.value.screen.width - avatarSprite.value.width) / 2;
          avatarSprite.value.y = (pixiApp.value.screen.height - avatarSprite.value.height) / 2;
          
          console.log('头像通过路径更新成功:', avatarConfigOrPath);
        } else {
          console.warn('头像纹理未找到:', avatarConfigOrPath);
        }
      } else {
        console.warn('无效的头像配置或路径:', avatarConfigOrPath);
      }
    };
    
    // 通过ID加载人物详情
    const loadCharacterById = (id = null) => {
      const allCharacters = gameStore.getAllCharacters || [];
      // console.log('所有角色数据:', allCharacters);
      
      // 在角色数组中查找指定agentId的角色
      const character = allCharacters.find(agent => agent.agentId === id.toString());
      // console.log('找到的角色数据:', character.avatarConfig);
      
      if (character) {
        // 保存raw头像路径，不添加/img/前缀
        const avatarTexturePath = character.avatarConfig;
        
        // 设置角色数据
        selectedCharacter.value = {
          avatarConfig: avatarTexturePath, // 保存原始路径用于获取纹理
          id: character.agentId,
          name: character.profile?.name || 'Unknown',
          agent_type: character.profile?.agent_type || character.type,
          profile: character.profile || {},
          gender: character.gender || 'f' // 添加性别信息，默认为女性
        };
        
        console.log('角色性别:', selectedCharacter.value.gender);
        
        // 只有在PIXI已经初始化后才更新头像，否则等待初始化完成
        if (pixiInitialized.value) {
          updateAvatar(avatarTexturePath);
        } else {
          console.log('等待PIXI初始化完成后再更新头像');
          // 注意：initPixiApp完成后会自动检查并更新头像
        }
        
        // 获取在排序后数组中的索引
        currentIndex.value = allAgents.value.findIndex(agent => agent.id === id.toString());
        console.log('已加载人物:', selectedCharacter.value.name, '索引:', currentIndex.value);
        
        // 加载真实事件历史
        loadCharacterEvents(id);
        
        // 清空对话历史
        dialogHistory.value = [];
      } else {
        selectedCharacter.value = null;
        characterEvents.value = [];
        dialogHistory.value = [];
        console.log('未找到ID为', id, '的人物');
      }
    };
    
    // 加载与角色相关的事件
    const loadCharacterEvents = (characterId) => {
      // 清空现有事件
      characterEvents.value = [];
      
      // 过滤出与该角色相关的事件（作为source或target）
      const relevantEvents = allEvents.value.filter(event => 
        event.source_id === characterId.toString() || 
        event.target_id === characterId.toString() ||
        (event.data && event.data.target_opinion_leaders && 
          Array.isArray(event.data.target_opinion_leaders) && 
          event.data.target_opinion_leaders.some(id => id.toString() === characterId.toString()))
      );
      
      // 对事件按时间戳排序（最新的在前）
      const sortedEvents = [...relevantEvents].sort((a, b) => b.timestamp - a.timestamp);
      
      // 转换为所需格式
      characterEvents.value = sortedEvents.map(event => {
        // 确定另一方的ID（如果角色是source，则另一方是target，反之亦然）
        const otherPartyId = event.source_id === characterId.toString() ? event.target_id : event.source_id;
        

        let eventTitle = event.event_type;
        
        // 处理InformationGeneratedEvent类型
        if (event.event_type === 'InformationGeneratedEvent') {
          // 尝试解析content字段，如果是JSON字符串则转换为对象
          let content = event.data.content || 'No content';
          try {
            if (typeof content === 'string' && (content.startsWith('{') || content.startsWith('['))) {
              const parsedContent = JSON.parse(content);
              if (typeof parsedContent === 'object' && parsedContent !== null) {
                content = parsedContent;
              }
            }
          } catch (e) {
            // 解析失败，保持原始内容
            console.log('事件内容解析失败:', e);
          }
          
          return {
            title: eventTitle,
            description: content,
            time: formatTimestamp(event.timestamp),
            eventType: event.event_type,
            step: event.step,
            participants: [
              { id: characterId, name: selectedCharacter.value.name },
              { id: otherPartyId, name: getAgentName(otherPartyId) }
            ],
            rawEvent: event
          };
        } 
        // 处理StartEvent类型
        else if (event.event_type === 'StartEvent') {
          return {
            title: eventTitle,
            description: 'System startup event',
            time: formatTimestamp(event.timestamp),
            eventType: event.event_type,
            step: event.step,
            participants: [
              { id: characterId, name: selectedCharacter.value.name },
              { id: 'ENV', name: 'System Environment' }
            ],
            rawEvent: event
          };
        }
        // 处理通用事件 - 保持data作为对象
        else {
          return {
            title: eventTitle,
            description: event.data || {}, // 直接使用data对象而不是转为字符串
            time: formatTimestamp(event.timestamp),
            eventType: event.event_type,
            step: event.step,
            participants: [
              { id: characterId, name: selectedCharacter.value.name },
              { id: otherPartyId || 'ENV', name: otherPartyId ? getAgentName(otherPartyId) : 'System Environment' }
            ],
            rawEvent: event
          };
        }
      });
    };
        
    // 点击参与者，跳转到其详情页
    const viewParticipant = (participantId) => {
      if (participantId === 'ENV') return; // 系统环境不能点击
      
      // 保留当前tab
      const currentTab = route.query.tab || 'info';
      
      // 清除当前焦点角色状态
      const currentId = selectedCharacter.value?.id;
      if (currentId) {
        gameStore.clearFocusedCharacterId(currentId);
      }
      
      // 设置焦点角色ID以启用镜头跟随
      gameStore.setFocusedCharacterId(participantId);
      
      // 使用渲染器的相机控制器查看角色详情（这会同时移动相机）
      if (gameStore.renderer && gameStore.renderer.cameraController) {
        gameStore.renderer.cameraController.viewCharacterDetail(participantId);
      }
      
      // 使用与CharacterPanel相同的导航逻辑
      router.replace({ 
        query: { 
          panel: 'characterDetail',
          id: participantId,
          tab: currentTab
        }
      });
    };
    
    // 监听URL参数和props变化
    watch(
      [() => route.query.id, () => props.characterId],
      ([routeId, propsId]) => {
        const id = routeId || propsId;
        if (id) {
          console.log('URL或props ID变化，加载人物:', id);
          
          // 清除当前焦点角色状态
          const currentId = selectedCharacter.value?.id;
          if (currentId && currentId !== id) {
            gameStore.clearFocusedCharacterId(currentId);
          }
          
          loadCharacterById(id);
          // 设置焦点角色ID以启用镜头跟随
          gameStore.setFocusedCharacterId(id);
        } else if (allAgents.value.length > 0) {
          const firstCharacter = allAgents.value[0];
          console.log('无ID参数，加载第一个人物:', firstCharacter.id);
          
          // 清除当前焦点角色状态
          const currentId = selectedCharacter.value?.id;
          if (currentId && currentId !== firstCharacter.id) {
            gameStore.clearFocusedCharacterId(currentId);
          }
          
          loadCharacterById(firstCharacter.id);
          // 设置焦点角色ID以启用镜头跟随
          gameStore.setFocusedCharacterId(firstCharacter.id);
        }
      },
      { immediate: true }
    );
    
    // 监听事件数据变化，实时更新角色相关事件
    watch(() => allEvents.value, (newEvents) => {
      if (selectedCharacter.value && selectedCharacter.value.id) {
        // console.log('事件数据变化，重新加载角色相关事件');
        loadCharacterEvents(selectedCharacter.value.id);
      }
    }, { deep: true });
    
    watch(() => activeTab.value,(newTabs) => {
      if (newTabs == 'chat'){
        chatHistory();
      }
    })

    // 监听路由参数变化，切换到对应选项卡
    watch(() => route.query.tab, (newTab) => {
      if (newTab && ['info', 'history', 'chat'].includes(newTab)) {
        activeTab.value = newTab;
        console.log('切换到选项卡:', newTab);
      }
    }, { immediate: true });
    
    // 监听动态属性变化，初始化editableAttributes
    watch(() => dynamicAttributes.value, (newAttributes) => {
      if (!isEditing.value && newAttributes) {
        // 只有在非编辑模式下才更新可编辑属性
        editableAttributes.value = JSON.parse(JSON.stringify(newAttributes));
      }
    }, { deep: true, immediate: true });
    
    // 保存更改
    const saveChanges = async () => {
      try {
        // 构建要保存的数据结构
        const profileData = {
          ...selectedCharacter.value.profile
        };

        // 处理编辑的属性值
        Object.entries(editableAttributes.value).forEach(([key, value]) => {
          if (isNestedObject(value)) {
            // 处理嵌套对象
            profileData[key] = processNestedObjectForSave(value);
          } else {
            // 处理普通值
            profileData[key] = value;
          }
        });
        console.log(profileData, "profileData");

        // API请求保存数据
        await axios.post('/api/agent/update_profile', {
          env_name: localStorage.getItem('scenarioName'),
          agent_id: selectedCharacter.value.id,
          profile_data: profileData
        });
        
        console.log('人物属性保存成功');
        
        // 保存成功后，立即更新本地数据
        selectedCharacter.value.profile = { ...profileData };
        
        // 退出编辑模式
        isEditing.value = false;
        
        // 同时更新gameStore中的数据，保持数据一致性
        const allCharacters = gameStore.getAllCharacters || [];
        const characterIndex = allCharacters.findIndex(char => char.agentId === selectedCharacter.value.id);
        if (characterIndex !== -1) {
          allCharacters[characterIndex].profile = { ...profileData };
        }
        
      } catch (error) {
        console.error('保存角色数据失败:', error);
        ElMessage.error('保存失败，请重试');
      }
    };
    
    // 递归处理嵌套对象用于保存
    const processNestedObjectForSave = (obj) => {
      // 如果是null或非对象，直接返回值
      if (obj === null || typeof obj !== 'object') return obj;
      
      // 处理数组
      if (Array.isArray(obj)) {
        return obj.map(item => processNestedObjectForSave(item));
      }
      
      // 处理标记为数组的对象
      if (obj._isArray && obj._arrayValue) {
        return obj._arrayValue.map(item => processNestedObjectForSave(item));
      }
      
      const result = {};
      
      // 处理表格数据
      if (obj._tableData && Array.isArray(obj._tableData)) {
        obj._tableData.forEach(row => {
          // 处理标记为数组的值
          if (row.value && row.value._isArray) {
            result[row.originalKey] = processNestedObjectForSave(row.value);
          }
          // 处理嵌套对象
          else if (isNestedObject(row.value)) {
            result[row.originalKey] = processNestedObjectForSave(row.value);
          } 
          // 处理普通值
          else {
            result[row.originalKey] = row.value;
          }
        });
        return result;
      }
      
      // 处理普通对象
      Object.entries(obj).forEach(([key, value]) => {
        // 跳过内部使用的特殊属性
        if (key.startsWith('_')) return;
        
        if (isNestedObject(value)) {
          // 递归处理嵌套对象
          result[key] = processNestedObjectForSave(value);
        } else {
          // 处理普通值
          result[key] = value;
        }
      });
      
      return result;
    };
    
    // 修改convertObjectToTableData函数，确保正确处理嵌套对象
    // 将对象转换为表格数据
    const convertObjectToTableData = (obj) => {
      if (!obj || typeof obj !== 'object') return [];
      
      // 过滤掉_tableData属性
      const filteredEntries = Object.entries(obj).filter(([key]) => key !== '_tableData');
      const result = filteredEntries.map(([key, value]) => {
        let processedValue = value;
        
        // 特殊处理嵌套对象和数组
        if (Array.isArray(value)) {
          // 如果数组中的元素是对象，则转换为嵌套表格数据
          if (value.length > 0 && typeof value[0] === 'object' && value[0] !== null) {
            // 创建一个表格数据数组
            processedValue = {
              _isArray: true,
              _arrayValue: value,
              _tableData: value.map((item, index) => {
                if (typeof item === 'object' && item !== null) {
                  // 将对象项转换为内部表格数据
                  return {
                    key: `[${index}]`,
                    value: item,
                    _isNestedObject: true,
                    _tableData: convertObjectToTableData(item)
                  };
                } else {
                  // 简单类型直接显示
                  return {
                    key: `[${index}]`,
                    value: item
                  };
                }
              })
            };
          } else {
            // 简单类型数组使用格式化字符串
            processedValue = {
              _isArray: true,
              _arrayValue: value,
              _formattedValue: formatArrayValue(value)
            };
          }
        } else if (isNestedObject(value)) {
          // 保持对象引用，以便编辑状态下能够同步更新
          processedValue._isNestedObject = true;
        }
        
        return {
          key: formatLabel(key),
          originalKey: key, // 添加原始键名，用于保存时恢复
          value: processedValue
        };
      });
      
      // 如果在编辑模式，将convertObjectToTableData的结果保存到对象的_tableData属性中
      if (isEditing.value) {
        obj._tableData = result;
      }
      
      return result;
    };
    
    // 开始编辑
    const startEditing = () => {
      // 保存原始数据用于重置
      originalAttributes.value = JSON.parse(JSON.stringify(dynamicAttributes.value));
      
      // 创建可编辑的副本
      editableAttributes.value = JSON.parse(JSON.stringify(dynamicAttributes.value));
      
      // 切换到编辑模式
      isEditing.value = true;
    };
    
    // 确认保存修改
    const confirmSave = () => {
      ElMessageBox.confirm(
        'Are you sure you want to save these changes?',
        'Save Confirmation',
        {
          confirmButtonText: 'Confirm',
          cancelButtonText: 'Cancel',
          type: 'warning',
        }
      )
        .then(() => {
          // Save logic
          saveChanges();
          ElMessage({
            type: 'success',
            message: 'Saved successfully',
          });
        })
        .catch(() => {
          ElMessage({
            type: 'info',
            message: 'Save cancelled',
          });
        });
    };
    
    // 确认重置
    const confirmReset = () => {
      ElMessageBox.confirm(
        'Are you sure you want to reset all changes?',
        'Reset Confirmation',
        {
          confirmButtonText: 'Confirm',
          cancelButtonText: 'Cancel',
          type: 'warning',
        }
      )
        .then(() => {
          // Reset logic
          resetChanges();
          ElMessage({
            type: 'success',
            message: 'Reset completed',
          });
        })
        .catch(() => {
          ElMessage({
            type: 'info',
            message: 'Reset cancelled',
          });
        });
    };
    
    // 重置更改
    const resetChanges = () => {
      // 重置为原始数据
      editableAttributes.value = JSON.parse(JSON.stringify(originalAttributes.value));
      
      // 退出编辑模式
      isEditing.value = false;
    };
    
    // 检查值是否为可编辑类型（字符串、浮点数或整数）
    const isEditableType = (value) => {
      // 检查是否为字符串
      if (typeof value === 'string') return true;
      
      // 检查是否为数字（浮点或整数）
      if (typeof value === 'number') return true;
      
      // 若是其他类型，则不可编辑
      return false;
    };
    
    onMounted(() => {
      console.log('角色详情面板已挂载');
      console.log('查看事件信息:', gameStore.eventsOriginalData);
      // 在组件挂载后立即初始化PIXI应用
      nextTick(async () => {
        try {
          await initPixiApp();
          // 初始化完成后如果已有角色数据，更新头像
          if (selectedCharacter.value && selectedCharacter.value.avatarConfig) {
            updateAvatar(selectedCharacter.value.avatarConfig);
          }
        } catch (error) {
          console.error('初始化PIXI时出错:', error);
        }
      });
    });
    
    onUnmounted(() => {
      clearUrlParams();
      // 组件卸载时销毁PIXI应用
      if (pixiApp.value) {
        pixiApp.value.destroy(true);
        pixiInitialized.value = false;
      }
    });
    
    return {
      selectedCharacter,
      dynamicAttributes,
      characterEvents,
      dialogHistory,
      messageInput,
      dialogHistoryRef,
      activeTab,
      ArrowLeft,
      ArrowRight,
      isDevMode,
      characterRawData,
      avatarContainer, // 导出引用
      formatLabel,
      formatValue,
      isNestedObject,
      isEditableType,
      convertObjectToTableData,
      formatTime,
      formatTimestamp,
      loadPreviousCharacter,
      loadNextCharacter,
      sendMessage,
      loadCharacterById,
      viewParticipant,
      clearUrlParams,
      // 新增
      isEditing,
      editableAttributes,
      startEditing,
      confirmSave,
      confirmReset,
      processNestedObjectForSave,
      formatArrayValue
    };
  }
};
</script>

<style scoped>
.character-detail-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.no-character-selected {
  margin-top: 80px;
  flex-grow: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.character-basic-info {
  display: flex;
  align-items: center;
  background-color: var(--bg-color-light);
  padding: 0 20px;
  position: relative;
  flex-shrink: 0;
}

.character-avatar {
  margin-right: 30px;
  width: 100px;
  height: 100px;
}

/* PIXI容器样式 */
.avatar-pixi-container {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.character-info {
  flex: 1;
}

.character-info h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 24px;
}

.character-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  margin-bottom: 5px;
  display: flex;
}

.info-label {
  width: 70px;
  color: var(--text-color-light);
}

.info-value {
  font-weight: 500;
}

.character-tabs-container {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  overflow: hidden;
}

.character-tabs {
  height: 100%;
  display: flex;
  flex-direction: column-reverse;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__nav-wrap) {
  padding: 0 5px;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding-top: 15px;
}

:deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
}

.tab-content-wrapper {
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

/* 事件历史样式 */
.event-history {
  padding-top: 20px;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.event-header h4 {
  margin: 0;
}

.event-step {
  margin-left: 8px;
}

.event-description {
  margin-bottom: 8px;
  white-space: pre-wrap;
}

.event-participants {
  margin-top: 8px;
}

.participant-label {
  margin-right: 8px;
  color: var(--text-color-light);
}

.participant-tag {
  margin-right: 5px;
  cursor: pointer;
}

.env-tag {
  cursor: default;
}

/* 对话列表样式 */
.dialog-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.dialog-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--bg-color-light);
  border-radius: 8px;
  margin-bottom: 15px;
}

.dialog-messages {
  display: flex;
  flex-direction: column;
}

.message {
  display: flex;
  margin-bottom: 15px;
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 10px;
  animation: fadeIn-0e73115f 0.3s ease;
}

.message-user {
    align-self: flex-end;
    background-color: var(--accent-color);
    color: white;
    max-width: 70%;
  /* flex-direction: row-reverse; */
}

.message-avatar {
  margin: 0 10px;
}

.message-content {
  padding: 10px;
  border-radius: 8px;
  position: relative;
}

.message-user .message-content {
  background-color: var(--primary-color);
  color: white;
  display: flex;
  flex-direction: column;
}

.message-agent .message-content {
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
}

.message-name {
  font-size: 12px;
  margin-bottom: 5px;
  color: var(--text-color-light);
}

.message-user .message-name,
.message-user .message-time {
  text-align: right;
}

.message-text {
  line-height: 1.5;
  word-break: break-word;
}

.message-time {
  font-size: 11px;
  color: var(--text-color-light);
  margin-top: 5px;
}

.dialog-input {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 15px;
}

.dialog-input .el-textarea {
  flex: 1;
}

.no-data, .no-messages {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 200px;
}

.debug-data {
  padding: 20px 0;
}

.markdown-container {
  background-color: var(--bg-color-light);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
  overflow-x: auto;
}

.markdown-content {
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  margin: 0;
}

/* 嵌套表格样式 */
.nested-table {
  width: 100%;
  margin: 8px 0;
  font-size: 14px;
}

:deep(.el-table__header) {
  font-weight: bold;
  background-color: var(--bg-color-light);
}

:deep(.el-table--small) {
  font-size: 13px;
}

/* 事件历史表格样式 */
.event-description-table {
  margin: 10px 0;
}

.event-description-table .nested-table {
  font-size: 13px;
}
:deep(.el-textarea__inner){
  box-shadow: 0 0 0 1px var(--el-input-border-color, var(--el-border-color)) inset !important;
}

.attribute-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

:deep(.el-input.is-disabled .el-input__inner) {
  color: var(--text-color);
}

:deep(.el-descriptions__body) {
  width: 100%;
}

:deep(.nested-table .el-input) {
  width: 100%;
}

.nested-table-second-level {
  margin-top: 5px;
  margin-bottom: 5px;
  width: 100%;
  border: 1px solid var(--border-color-light) !important;
  font-size: 12px;
}

:deep(.nested-table-second-level .el-table__row) {
  background-color: #f9f9fc;
}

:deep(.nested-table-second-level .el-input) {
  width: 100%;
  font-size: 12px;
}

.nested-array-container {
  margin: 5px 0;
  width: 100%;
}

.nested-table-third-level {
  width: 100%;
  border: 1px solid #ebeef5 !important;
  font-size: 11px;
}

:deep(.nested-table-third-level .el-table__row) {
  background-color: #f0f2f5;
}

:deep(.el-table--small) {
  font-size: 13px;
}

/* 嵌套表格行高 */
:deep(.el-table--small .el-table__cell) {
  padding: 4px 0;
}

/* 表格边框样式 */
:deep(.nested-table, .nested-table-second-level, .nested-table-third-level) {
  --el-table-border-color: #ebeef5;
  --el-table-border: 1px solid var(--el-table-border-color);
  border-collapse: collapse;
}
</style> 