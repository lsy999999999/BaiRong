<template>
  <div class="simulation-layout" :class="{ 'dark-theme': isDarkMode }">
    <!-- 主要内容区域 -->
    <div class="simulation-content">
      <!-- 城市地图画布 -->
      <CityMapParent ref="cityMap" />

      <!-- 右侧侧边菜单栏 -->
      <div class="side-menu">
        <el-button class="control-btn" @click="openPanel('character')"
          :class="{ 'active': activePanel === 'character' }">
          Characters
        </el-button>

        <el-button class="control-btn" @click="openPanel('event')" :class="{ 'active': activePanel === 'event' }">
          Events
        </el-button>

        <el-button class="control-btn" @click="openPanel('monitor')" :class="{ 'active': activePanel === 'monitor' }">
          Monitor
        </el-button>

        <el-button class="control-btn" @click="openPanel('feedback')" :class="{ 'active': activePanel === 'feedback' }">
          Feedback
        </el-button>

        <!-- <el-button class="control-btn" @click="openPanel('training')" :class="{ 'active': activePanel === 'training' }">
          Training
        </el-button>

        <el-button class="control-btn" @click="openPanel('modelLibrary')"
          :class="{ 'active': activePanel === 'modelLibrary' }">
          Models
        </el-button> -->

        <el-button class="control-btn" @click="openPanel('Broadcast')"
          :class="{ 'active': activePanel === 'Broadcast' }">
          Broadcast
        </el-button>

        <el-button class="control-btn" @click="openPanel('settings')" :class="{ 'active': activePanel === 'settings' }">
          Settings
        </el-button>
      </div>

      <!-- 底部工具栏 -->
      <SimulationToolbar @control-clicked="handleControlClick" @generate-map="handleGenerateMap"
        @generate-characters="handleGenerateCharacters">
      </SimulationToolbar>
    </div>

    <!-- 面板弹窗组件 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" direction="rtl" :size="drawerSize"
      :before-close="closePanel" class="nndrawer" @open="handleDrawerOpen" @close-panel="closePanel" :z-index="2000">
      <component :is="currentPanelComponent" :character-id="selectedCharacterId" @close-panel="closePanel"
        :newMap="handleGenerateMap" @view-character="handleViewCharacter" @form-submitted="hasSubmittedForm = true" 
        @show-message="handleShowMessage" ref="panelComponentRef"></component>
    </el-drawer>
    <!-- Broadcast弹窗 -->
    <el-dialog v-model="BroadcastWin" title="Add Broadcast" width="800">
      <el-input v-model="BroadcastName" type="textarea" placeholder="Enter the broadcast content here"></el-input>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="BroadcastWin = false">Cancel</el-button>
          <el-button type="primary" @click="SendBroadcast">
            Confirm
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from "axios";
import CityMapParent from '../components/city-map/CityMapParent.vue';
import SimulationToolbar from '../components/simulation/SimulationToolbar.vue';
import MonitorPanel from '../components/simulation/panels/MonitorPanel.vue';
import FeedbackPanel from '../components/simulation/panels/FeedbackPanel.vue';
import TrainingPanel from '../components/simulation/panels/TrainingPanel.vue';
import ModelLibraryPanel from '../components/simulation/panels/ModelLibraryPanel.vue';
import SettingsPanel from '../components/simulation/panels/SettingsPanel.vue';
import CharacterPanel from '../components/simulation/panels/CharacterPanel.vue';
import EventPanel from '../components/simulation/panels/EventPanel.vue';
import CharacterDetailPanel from '../components/simulation/panels/CharacterDetailPanel.vue';
import { useGameStore } from '../stores/gameStore'; // 导入gameStore
//模拟数据
// import agentsData from '../assets/js/s2/agents.json';
// import configData from '../assets/js/s2/config.json'
// import eventsOriginalData from '../assets/js/s2/events.json'


export default {
  name: 'SimulationLayout',
  components: {
    CityMapParent,
    SimulationToolbar,
    MonitorPanel,
    FeedbackPanel,
    TrainingPanel,
    ModelLibraryPanel,
    SettingsPanel,
    CharacterPanel,
    EventPanel,
    CharacterDetailPanel
  },
  data() {
    return {
      activePanel: '',
      BroadcastWin:false,
      BroadcastName:'',
      drawerVisible: false,
      drawerTitle: '',
      drawerDirection: 'rtl', // 默认为右侧弹出
      currentPanelComponent: null,
      isDarkMode: false, // 初始设为false，在mounted中更新
      selectedCharacterId: '', // 添加选中人物ID状态
      hasSubmittedForm: false, // 添加表单提交状态
      // 面板尺寸配置
      panelSizes: {
        // 左侧面板
        'character': '90%',
        'event': '60%',
        'settings': '80%',
        // 右侧面板
        'monitor': '70%',
        'feedback': '90%',
        'training': '80%',
        'modelLibrary': '70%',
        'characterDetail': '60%'
      },
    }
  },
  computed: {
    // 根据当前激活的面板动态计算抽屉尺寸
    drawerSize() {
      return this.panelSizes[this.activePanel] || '60%'; // 如果没有配置则使用默认尺寸
    }
  },
  mounted() {
    // 获取游戏存储
    const gameStore = useGameStore();
    
    // 检查设置是否完成和开发者模式状态
    if (!gameStore.isSettingComplete && !gameStore.isDevMode) {
      // 如果设置未完成且不是开发者模式，自动打开设置面板
      this.openPanel('settings');
    }
    // if(gameStore.isDevMode){
    //   gameStore.agentsData = agentsData;
    //   gameStore.systemConfig = configData;
    //   gameStore.eventsOriginalData = eventsOriginalData;
    // }
    
    // 初始化时检查主题
    this.checkThemeChange();

    // 添加主题变化的监听器 - 使用MutationObserver监听document.documentElement的class变化
    this.themeObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.attributeName === 'class') {
          this.checkThemeChange();
        }
      }
    });

    this.themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    // 添加storage事件监听
    window.addEventListener('storage', this.checkThemeChange);

    // 检查URL参数，如果有指定面板和人物ID则打开
    this.checkRouteParams();

    // 监听路由变化
    this.$router.afterEach(() => {
      this.checkRouteParams();
    });
  },
  beforeUnmount() {
    // 清除所有监听器
    window.removeEventListener('storage', this.checkThemeChange);
    if (this.themeObserver) {
      this.themeObserver.disconnect();
    }
    if (this.themeCheckInterval) {
      clearInterval(this.themeCheckInterval);
    }
  },
  methods: {
    /**
     * 发送广播
     */
    SendBroadcast(){
      axios.post('/api/simulation/broadcast', {
        env_name: localStorage.getItem('scenarioName'),
        message:this.BroadcastName,
      }).then(response => {
        this.$message({
          message: 'Broadcast sent successfully!',
          type:'success',
          duration: 2000
        });
        this.BroadcastWin = false;
        // 移除事件阻断层
        const cityMapComponent = this.$refs.cityMap;
        if (cityMapComponent && cityMapComponent.removeEventBlocker) {
          cityMapComponent.removeEventBlocker();
        }
      }).catch(error => {
        console.error('Error sending broadcast:', error);
        this.$message({
          message: 'Failed to send broadcast!',
          type:'error',
          duration: 2000
        });
      });
    },
    openPanel(panelName) {
      // 获取游戏存储
      const gameStore = useGameStore();
      this.activePanel = panelName;
      if(panelName != 'Broadcast'){
        this.drawerVisible = true;
      }

      // 所有面板统一从右侧弹出
      this.drawerDirection = 'rtl';

      // 添加事件阻断层，防止点击穿透
      const cityMapComponent = this.$refs.cityMap;
      if (cityMapComponent && cityMapComponent.addEventBlocker) {
        console.log('添加事件阻断层');
        cityMapComponent.addEventBlocker();
      }

      // 设置面板标题和组件
      switch (panelName) {
        case 'monitor':
          this.drawerTitle = 'Simulation Monitor';
          this.currentPanelComponent = 'MonitorPanel';
          break;
        case 'Broadcast':
          this.BroadcastWin = true;
          break;
        case 'feedback':
          this.drawerTitle = 'Simulation Feedback';
          this.currentPanelComponent = 'FeedbackPanel';
          break;
        case 'training':
          this.drawerTitle = 'Model Training';
          this.currentPanelComponent = 'TrainingPanel';
          break;
        case 'modelLibrary':
          this.drawerTitle = 'Model Library';
          this.currentPanelComponent = 'ModelLibraryPanel';
          break;
        case 'settings':
          this.drawerTitle = 'Settings';
          this.currentPanelComponent = 'SettingsPanel';
          break;
        case 'character':
          this.drawerTitle = 'Character Management';
          this.currentPanelComponent = 'CharacterPanel';
          break;
        case 'event':
          this.drawerTitle = 'Event Management';
          this.currentPanelComponent = 'EventPanel';
          break;
        case 'characterDetail':
          this.drawerTitle = 'Character Profile';
          this.currentPanelComponent = 'CharacterDetailPanel';
          break;
      }
    },
    closePanel() {
      // 获取当前面板类型
      const currentPanel = this.activePanel;
      
      // 如果关闭的是characterDetail面板
      if (currentPanel === 'characterDetail') {
        try {
          // 清除URL中的查询参数
          const newQuery = { ...this.$route.query };
          delete newQuery.panel;
          delete newQuery.id;
          delete newQuery.tab;
          
          // 使用replace避免增加浏览器历史记录
          this.$router.replace({ query: newQuery });
          
          // 获取游戏存储
          const gameStore = useGameStore();
          
          // 清除焦点角色ID
          gameStore.clearFocusedCharacterId();
          
          // 确认焦点角色ID已被清空
          setTimeout(() => {
            // 再次获取焦点角色ID检查是否真的被清空
            if (gameStore.getFocusedCharacterId) {
              console.warn('警告: 焦点角色ID未能成功清空，再次尝试清空');
              gameStore.clearFocusedCharacterId();
            }
          }, 0);
        } catch (error) {
          console.error('清除焦点角色ID时出错:', error);
        }
      }
      
      // 如果关闭的是SettingsPanel面板且表单未提交
      if (currentPanel === 'settings' && this.$refs.panelComponentRef) {
        if (!this.hasSubmittedForm && !this.$refs.panelComponentRef.isFormSubmitted) {
          this.$message({
            message: 'Please complete the setting information first！',
            type: 'warning',
            duration: 2000
          });
          return;
        }
      }
      
      // 更新面板状态
      this.drawerVisible = false;
      this.activePanel = '';
      
      // 移除事件阻断层
      const cityMapComponent = this.$refs.cityMap;
      if (cityMapComponent && cityMapComponent.removeEventBlocker) {
        cityMapComponent.removeEventBlocker();
      }
    },
    handleDrawerOpen() {
      // 每次打开抽屉时执行，如果是设置面板则调用refreshOptions方法
      if (this.activePanel === 'settings' && this.$refs.panelComponentRef) {
        // 使用nextTick确保组件已经渲染完成
        this.$nextTick(() => {
          // 如果当前面板是设置面板且有refreshOptions方法
          if (this.$refs.panelComponentRef.refreshOptions) {
            console.log('刷新设置选项');
            this.$refs.panelComponentRef.refreshOptions();
          }
          // 如果已经提交过表单，更新hasSubmittedForm状态
          if (this.$refs.panelComponentRef.isFormSubmitted) {
            this.hasSubmittedForm = true;
          }
        });
      }
      
      // 如果是反馈面板，则调用getFeedBack方法
      if (this.activePanel === 'feedback' && this.$refs.panelComponentRef) {
        this.$nextTick(() => {
          if (this.$refs.panelComponentRef.getFeedBack) {
            console.log('获取反馈数据');
            this.$refs.panelComponentRef.getFeedBack();
          }
        });
      }
    },
    handleControlClick(action) {
      // 处理底部工具栏的控制按钮点击事件
      console.log('Control action:', action);
      // 这里可以添加具体的控制逻辑
    },
    handleGenerateMap(populationTotal) {
      // 处理生成地图事件
      console.log('Generating map with population:', populationTotal);
      // 转发事件给CityMapParent组件
      const cityMapComponent = this.$refs.cityMap;
      if (cityMapComponent) {
        cityMapComponent.generateNewMap(populationTotal);
      } else {
        console.warn('CityMapParent组件引用不可用，无法生成地图');
      }
    },
    handleGenerateCharacters(count) {
      // 处理生成人物事件
      console.log('Generating characters:', count);
      // 转发事件给CityMapParent组件
      const cityMapComponent = this.$refs.cityMap;
      if (cityMapComponent) {
        cityMapComponent.generateCharacter(count);
      } else {
        console.warn('CityMapParent组件引用不可用，无法生成人物');
      }
    },
    checkThemeChange() {
      // 检查主题是否变化 - 多种方式检测
      // 1. 检查document元素上的class
      const hasDarkClass = document.documentElement.classList.contains('dark-theme');

      // 2. 检查localStorage
      const theme = localStorage.getItem('theme');
      const prefersDark = theme === 'dark' ||
        (theme === null && window.matchMedia('(prefers-color-scheme: dark)').matches);

      // 综合判断并更新
      this.isDarkMode = hasDarkClass || prefersDark;

      console.log('主题检测 - isDarkMode:', this.isDarkMode,
        '| HTML类:', hasDarkClass,
        '| localStorage:', theme,
        '| 系统偏好:', window.matchMedia('(prefers-color-scheme: dark)').matches);
    },
    handleViewCharacter(characterId) {
      this.selectedCharacterId = characterId;
      
      // 如果当前已经打开了人物列表面板，先关闭再打开人物详情面板
      if (this.activePanel === 'character') {
        this.closePanel();
        setTimeout(() => {
          this.openPanel('characterDetail');
        }, 300); // 等待关闭动画完成
      } else {
        // 直接打开人物详情面板
        this.openPanel('characterDetail');
      }
    },
    checkRouteParams() {
      // 获取URL参数
      const query = this.$route?.query;
      if (!query) return;

      // 处理面板参数
      if (query.panel) {
        const panelName = query.panel;

        // 检查是否是有效的面板名称
        const validPanels = ['monitor', 'feedback', 'training', 'modelLibrary',
          'settings', 'character', 'event', 'characterDetail'];

        if (validPanels.includes(panelName)) {
          // 如果是人物详情面板且有ID参数，先设置ID
          if (panelName === 'characterDetail' && query.id) {
            this.selectedCharacterId = query.id;
          }

          // 判断是否从人物列表切换到人物详情
          if (panelName === 'characterDetail' && this.activePanel === 'character') {
            // 先关闭当前面板，然后打开新面板，实现切换效果
            this.closePanel();
            setTimeout(() => {
              this.openPanel(panelName);
            }, 300); // 等待关闭动画完成
          } else {
            // 直接打开指定面板
            this.openPanel(panelName);
          }
        }
      }
    },
    /**
     * 处理消息通知
     * @param {Object} options - 消息配置对象
     * @param {string} options.message - 消息内容
     * @param {string} options.type - 消息类型 (success/warning/error/info)
     * @param {number} options.duration - 显示时长(ms)
     */
    handleShowMessage(options) {
      this.$message({
        message: options.message,
        type: options.type || 'info',
        duration: options.duration || 2000
      });
    },
  },
  watch: {
    BroadcastWin(newVal, oldVal) {
      // When the broadcast dialog is closed
      if (oldVal === true && newVal === false) {
        // 移除事件阻断层
        const cityMapComponent = this.$refs.cityMap;
        if (cityMapComponent && cityMapComponent.removeEventBlocker) {
          cityMapComponent.removeEventBlocker();
        }
      }
    }
  }
}
</script>

<style scoped>
.simulation-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow: hidden;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

.simulation-content {
  flex: 1;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  overflow: hidden;
}

/* 右侧侧边菜单栏 */
.side-menu {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px;
  background: rgba(240, 240, 240, 0.7);
  border-radius: 8px 0 0 8px;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.side-menu .el-button+.el-button {
  margin: 0;
}

.control-btn {
  width: 100px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #ddd;
  color: var(--control-btn-color);
  margin: 0;
  transition: all 0.3s ease;
  font-size: 14px;
  cursor: pointer;
}

.control-btn:hover {
  background-color: var(--accent-color);
  color: white;
}

.control-btn.active {
  background-color: var(--accent-color);
  color: white;
}

/* 暗色模式样式 */
.simulation-layout.dark-theme .side-menu {
  background: rgba(50, 50, 50, 0.7);
}

.simulation-layout.dark-theme .side-menu .control-btn {
  background-color: #333;
  color: #ddd;
  border-color: #444;
}

.simulation-layout.dark-theme .side-menu .control-btn:hover {
  background-color: var(--accent-color);
  color: white;
}

.simulation-layout.dark-theme .side-menu .control-btn.active {
  background-color: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .side-menu {
    bottom: 60px;
    top: auto;
    left: 0;
    right: 0;
    height: auto;
    width: 100%;
    flex-direction: row;
    justify-content: space-around;
    background: rgba(240, 240, 240, 0.9);
    border-radius: 8px 8px 0 0;
  }

  .control-btn {
    flex: 1;
    height: 40px;
    width: auto;
    font-size: 12px;
  }
  
  .simulation-layout.dark-theme .side-menu {
    background: rgba(50, 50, 50, 0.9);
  }
}

.el-drawer {
  transition: opacity 0.3s, transform 0.3s !important;
}

.el-drawer.rtl {
  transform-origin: right;
}

.el-drawer__body {
  overflow-y: auto;
}
:deep(.el-textarea__inner){
  box-shadow: 0 0 0 1px var(--el-input-border-color, var(--el-border-color)) inset !important;
}
</style>