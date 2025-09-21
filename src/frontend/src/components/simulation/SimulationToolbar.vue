<template>
  <div class="simulation-toolbar">

    <!-- Game Control Buttons Area -->
    <div class="game-controls">
      <!-- Pause/Resume Button -->
      <el-button @click="togglePause" class="control-btn" v-if="!isEnd">
        {{ getButtonText() }}
      </el-button>
      <!-- Map Generation Control -->
      <!-- <el-button @click="hideAllStatusImages()" class="control-btn" v-else> -->
      <el-button @click="togglePause_Restart()" class="control-btn" v-else>
        Restart
      </el-button>
      <!-- Game Speed Control -->
      <el-button :type="getSpeedButtonType()" @click="toggleGameSpeed" class="control-btn">
        {{ Math.ceil(gameSpeed) }}x Speed
      </el-button>
      <el-button class="control-btn" @click="handleEndSimulation" type="danger" :loading="isLoading" v-if="isRunning">
        End
      </el-button>
    </div>

    <div class="toolbar-section">
      <div class="toolbar-controls">
        <!-- Add sound control switch -->
        <el-switch v-model="isSoundEnabled" active-text="Sound On" inactive-text="Sound Off" @change="toggleSound"
          class="sound-switch" />
      </div>
    </div>
  </div>

  <!-- Status Image Display Area -->
  <div class="simulation-status-image" :class="{ 'fade-in': showStatusImage, 'fade-out': fadeOutStatusImage }">
    <img v-if="showStartImage" src="/img/1.png" alt="Start Simulation" />
    <img v-if="showPauseImage" src="/img/2.png" alt="Pause Simulation" />
    <img v-if="showEndImage" src="/img/3.png" alt="End Simulation" />
  </div>
</template>

<script>
// Import required libraries and components
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from "vue";
import { useGameStore } from "../../stores/gameStore";
import { ElMessage, ElMessageBox } from "element-plus";
import axios from "axios";
import { useRoute, useRouter } from "vue-router";
import { sound } from '@pixi/sound';

export default {
  name: "SimulationToolbar",
  // Add emits option, declare events that the component can emit
  emits: ['control-clicked', 'generate-map', 'generate-characters'],
  components: {
  },

  setup(props, { emit }) {
    const route = useRoute();
    const router = useRouter();

    // 使用Pinia游戏状态存储  
    const gameStore = useGameStore();
    // 添加模拟状态变量以跟踪第一次点击
    const isFirstStart = ref(true);
    // 添加模拟结束状态变量
    const isEnd = ref(false);
    // 添加加载状态变量
    const isLoading = ref(false);
    // 计算属性：游戏是否暂停
    const isPaused = computed(() => gameStore.isPaused);

    // 计算属性：游戏是否运行
    const isRunning = computed(() => gameStore.isRunning);

    // 计算属性：当前游戏速度
    const gameSpeed = computed(() => gameStore.gameSpeed);

    // 使用ref而不是计算属性来管理开发者模式状态
    const isDevMode = ref(gameStore.isDevMode);

    // 添加声音控制状态
    const isSoundEnabled = ref(true);

    // 获取设置完成状态
    const isSettingComplete = computed(() => gameStore.isSettingComplete);

    // 检查当前路由是否为仪表板
    const isDashboardRoute = computed(() => {
      return route.path.includes('/');
    });

    // 添加状态图像显示控制变量
    const showStatusImage = ref(false);
    const fadeOutStatusImage = ref(false);
    const showStartImage = ref(false);
    const showPauseImage = ref(false);
    const showEndImage = ref(false);

    // 监听本地isDevMode状态变化，同步到gameStore
    watch(isDevMode, (newValue) => {
      gameStore.setDevMode(newValue);
      console.log("Developer mode switched to:", newValue);
    });

    // 监听gameStore isDevMode状态变化，同步到本地
    watch(
      () => gameStore.isDevMode,
      (newValue) => {
        isDevMode.value = newValue;
      }
    );

    // 监听暂停状态变化，控制暂停图像显示
    watch(isPaused, (newValue) => {
      if (!isFirstStart.value && !showStartImage.value && !showEndImage.value) {
        showPauseImage.value = newValue;
        showStatusImage.value = newValue;
        fadeOutStatusImage.value = false;
      }
    });

    // 切换声音状态
    const toggleSound = () => {
      sound.toggleMuteAll();
      console.log(`Sound ${isSoundEnabled.value ? 'enabled' : 'disabled'}`);

      // 保存声音状态，供其他组件使用
      if (typeof window !== 'undefined') {
        window.isSoundEnabled = isSoundEnabled.value;
      }
    };

    // 地图和角色生成相关状态 - 直接使用gameStore
    const populationTotal = computed({
      get: () => gameStore.agentsData.agent_count,
      set: (value) => gameStore.setPopulationTotal(value),
    });

    const populationSize = computed({
      get: () => gameStore.populationSize,
      set: (value) => gameStore.setPopulationSize(value),
    });

    // 验证人口总数 - 直接调用gameStore方法
    const validatePopulationTotal = (value) => {
      gameStore.setPopulationTotal(value);
    };

    // 验证角色数量 - 直接调用gameStore方法
    const validatePopulationSize = (value) => {
      gameStore.setPopulationSize(value);
    };

    // 显示启动状态图像，2秒后隐藏
    const showStartStatusImage = () => {
      showStartImage.value = true;
      showPauseImage.value = false;
      showEndImage.value = false;
      showStatusImage.value = true;
      fadeOutStatusImage.value = false;

      setTimeout(() => {
        fadeOutStatusImage.value = true;
        setTimeout(() => {
          showStartImage.value = false;
          showStatusImage.value = false;
          fadeOutStatusImage.value = false;
        }, 500); // Fade out animation duration
      }, 2000); // Show for 2 seconds then start fade out
    };

    // 显示结束状态图像
    const showEndStatusImage = () => {
      showStartImage.value = false;
      showPauseImage.value = false;
      showEndImage.value = true;
      showStatusImage.value = true;
      fadeOutStatusImage.value = false;
    };

    // 隐藏所有状态图像
    const hideAllStatusImages = () => {
      ElMessageBox.confirm("Are you sure you want to restart the simulation?", "Confirmation", {
        confirmButtonText: "Yes",
        cancelButtonText: "No",
        type: "info",
      }).then(() => {
        showStartImage.value = false;
        showPauseImage.value = false;
        showEndImage.value = false;
        showStatusImage.value = false;
        fadeOutStatusImage.value = false;
        isEnd.value = false;
        gameStore.isPaused = false;
        emit('generate-map', populationTotal);
      }).catch(() => {
        // User cancelled, do nothing
      });
    };

    // 获取按钮文本方法
    const getButtonText = () => {
      if (isFirstStart.value) {
        return "Start";
      } else {
        return isPaused.value ? "Resume" : "Pause";
      }
    };

    // 获取速度按钮类型方法
    const getSpeedButtonType = () => {
      const speed = Math.ceil(gameSpeed.value);
      switch (speed) {
        case 1:
          return "info";
        case 2:
          return "success";
        case 3:
          return "warning";
        case 4:
          return "danger";
        case 5:
          return "danger";
        default:
          return "info";
      }
    };

    // 处理结束模拟点击
    const handleEndSimulation = (data = '') => {
      if (isEnd.value) {
        ElMessage.warning("The simulation has ended, please click Restart to begin again.");
        return;
      }
      
      if (data == 'stop') {
        isLoading.value = true;
        axios
          .post("/api/simulation/stop", {
            env_name: localStorage.getItem('scenarioName'),
          })
          .then((res) => {
            console.log(res, "end");
            emit('control-clicked', 'finish');
            gameStore.isPaused = true;
            isEnd.value = true;
            console.log(gameStore.isPaused);
            showEndStatusImage();
          })
          .catch(err => {
            ElMessage.error("停止模拟失败");
          })
          .finally(() => {
            isLoading.value = false;
          });
      } else {
        ElMessageBox.confirm("Are you sure you want to end the simulation?", "Warning", {
          confirmButtonText: "Confirm",
          cancelButtonText: "Cancel",
          type: "warning",
        }).then(() => {
          // 显示加载状态
          isLoading.value = true;
          // 首先调用stop API停止模拟
          axios
            .post("/api/simulation/stop", {
              env_name: localStorage.getItem('scenarioName'),
            })
            .then((res) => {
              console.log(res, "end");
              emit('control-clicked', 'finish');
              gameStore.isPaused = true;
              isEnd.value = true;
              showEndStatusImage();
            })
            .catch(err => {
              ElMessage.error("停止模拟失败");
            })
            .finally(() => {
              isLoading.value = false;
            });
        }).catch(() => {
          // User clicked cancel
        })
      }
    };
    const togglePause_Restart = () => {
      isFirstStart.value = true;
      isEnd.value = false;
      nextTick(() => {
        togglePause();
      });
    }
    // 切换游戏暂停/恢复状态
    const togglePause = () => {
      // 如果是第一次启动，需要检查条件
      if (isFirstStart.value) {
        // 检查是否在开发者模式下
        if (!isDevMode.value) {
          // 如果不在开发者模式下，检查是否完成模拟设置
          if (!isSettingComplete.value) {
            ElMessage({
              message: "请先完成模拟设置再开始！",
              type: "warning",
              duration: 3000,
            });
            return; // 阻止游戏启动
          }
        }

        // 通过检查，设置第一次启动标志为false
        isFirstStart.value = false;
        gameStore.isStart = true;
        // 首先显示启动状态图像，然后处理暂停状态
        showStartStatusImage(); // 显示启动状态图像

        // 确保游戏在启动时没有暂停
        if (isPaused.value) {
          // 延迟执行togglePause以避免干扰启动图像显示
          setTimeout(() => {
            gameStore.togglePause();
          }, 100);
        }

        getEvents();
      } else {
        // 如果当前是暂停状态且显示了结束图片，需要在恢复时隐藏结束图片
        if (isPaused.value && showEndImage.value) {
          showEndImage.value = false;
          showStatusImage.value = false;
        }

        // 切换暂停状态
        gameStore.togglePause();
        ResumeOrPause();
      }
    };
    const getEvents = () => {
      // 只在非开发者模式下调用API
      if (!isDevMode.value) {
        // 首先调用start API启动模拟
        axios
          .post("/api/simulation/start", {
            env_name: localStorage.getItem('scenarioName'),
          })
          .then((res) => {
            console.log(res, "start");

            // 成功启动后，建立WebSocket连接以接收事件数据
            initWebSocket();
          })
          .catch(err => {
            console.error("Failed to start simulation", err);
            ElMessage.error("Failed to start simulation");
          });
      } else {
        console.log("In developer mode, skipping API call");
        // 在开发者模式下可以使用模拟数据
        gameStore.isStart = true;
      }
    };
    // 暂停或恢复游戏
    const ResumeOrPause = () => {
      // 如果游戏暂停，则恢复游戏
      if (isPaused.value) {
        axios
          .post("/api/simulation/pause", {
            env_name: localStorage.getItem('scenarioName'),
          })
          .then((res) => {
            console.log(res, "start");
          })
          .catch(err => {
            console.error("Failed to start simulation", err);
            ElMessage.error("Failed to start simulation");
          });
      } else {
        // 如果游戏运行，则暂停游戏
        axios
          .post("/api/simulation/resume", {
            env_name: localStorage.getItem('scenarioName'),
          })
          .then((res) => {
            console.log(res, "start");
          })
          .catch(err => {
            console.error("Failed to start simulation", err);
            ElMessage.error("Failed to start simulation");
          });
      }
    }

    // Initialize WebSocket connection
    const initWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.host;
      // 过滤掉http/https前缀
      const cleanBaseUrl = apiBaseUrl.replace(/^https?:\/\//, '');
      const wsUrl = `${protocol}//${cleanBaseUrl}simulation/ws/${localStorage.getItem('scenarioName')}`;
      
      console.log("Establishing WebSocket connection:", wsUrl);

      const socket = new WebSocket(wsUrl);

      // Connection established handler
      socket.onopen = () => {
        console.log("WebSocket connection established");
        ElMessage.success("Real-time event connection established");
      };

      // Message receiving handler
      socket.onmessage = (event) => {
        console.log(event, "event")
        try {
          const data = JSON.parse(event.data);
          // Handle EndEvent
          if (data.event_type === "EndEvent") {
            handleEndSimulation('stop');
          }
          // Handle regular events
          if (data.event_id && data.event_type) {
            // First get existing event data
            let eventData = gameStore.eventsOriginalData || [];
            // Check for duplicates
            const isDuplicate = eventData.some(existingEvent =>
              existingEvent.event_id === data.event_id
            );
            if (!isDuplicate) {
              eventData.push(data);
              console.log("eventData",eventData)
              gameStore.eventsOriginalData = eventData;
            }
          }
        } catch (error) {
          console.error("Error processing WebSocket message:", error);
        }
      };

      // Connection error handler
      socket.onerror = (error) => {
        console.error("WebSocket connection error:", error);
        ElMessage.error("Event connection error");
      };

      // Connection close handler
      socket.onclose = () => {
        console.log("WebSocket connection closed");
        axios.post("/api/simulation/stop", {
          env_name: localStorage.getItem('scenarioName'),
        })
        .then((res) => {
          console.log(res, "end");
          emit('control-clicked', 'finish');
          gameStore.isPaused = true;
          isEnd.value = true;
          showEndStatusImage();
        })
      };

      // // Save socket reference to gameStore for access elsewhere
      // gameStore.socket = socket;
    };
    // Toggle game speed
    const toggleGameSpeed = () => {
      gameStore.toggleGameSpeed();
    };

    // New: set specific game speed
    const setGameSpeed = (speed) => {
      if (speed >= 1 && speed <= 5) {
        gameStore.setGameSpeed(speed);
      }
    };

    // New: keyboard event handler
    const handleKeyDown = (event) => {
      // Number keys 1-5 control game speed
      if (event.code >= 'Digit1' && event.code <= 'Digit5') {
        const speed = parseInt(event.code.replace('Digit', ''));
        setGameSpeed(speed);
        event.preventDefault();
      }
    };

    // Toggle developer mode
    const toggleDevMode = () => {
      isDevMode.value = !isDevMode.value;
    };

    // On component mount, sync gameStore isDevMode state and add keyboard event listener
    onMounted(() => {
      isDevMode.value = gameStore.isDevMode;

      // Get sound state from window object (if exists)
      if (typeof window !== 'undefined' && window.isSoundEnabled !== undefined) {
        isSoundEnabled.value = window.isSoundEnabled;
        if (!isSoundEnabled.value) {
          sound.muteAll();
        }
      } else {
        // Default sound to on
        window.isSoundEnabled = true;
      }

      // Add keyboard event listener
      // window.addEventListener('keydown', handleKeyDown);
    });

    // Remove keyboard event listener on component unmount
    onUnmounted(() => {
      //window.removeEventListener('keydown', handleKeyDown);
    });

    // Return required states and methods
    return {
      isPaused,
      isRunning,
      gameSpeed,
      togglePause_Restart,
      togglePause,
      toggleGameSpeed,
      populationTotal,
      populationSize,
      validatePopulationTotal,
      validatePopulationSize,
      toggleDevMode,
      isDevMode,
      isFirstStart,
      isEnd,
      isLoading,
      getButtonText,
      getSpeedButtonType,
      isSettingComplete,
      isDashboardRoute,
      // Status image related
      showStatusImage,
      fadeOutStatusImage,
      showStartImage,
      showPauseImage,
      showEndImage,
      handleEndSimulation,
      setGameSpeed,
      isSoundEnabled,
      toggleSound,
      hideAllStatusImages
    };
  },
};
</script>

<style scoped>
.simulation-toolbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2004;
  background-color: var(--bg-color);
  padding: 15px 0;
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.game-controls {
  display: flex;
  align-items: center;
  margin-right: 20px;
  gap: 10px;
}

.map-controls,
.character-controls {
  display: flex;
  align-items: center;
  gap: 5px;
}

.control-input {
  width: 80px;
}

.control-btn {
  margin: 0 5px;
}

.control-buttons {
  display: flex;
  gap: 15px;
}

.control-btn {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.control-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* Status image styles */
.simulation-status-image {
  position: fixed;
  top: 250px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.5s ease, visibility 0.5s ease;
}

.simulation-status-image img {
  width: 200px;
  height: auto;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
}

.simulation-status-image.fade-in {
  opacity: 1;
  visibility: visible;
}

.simulation-status-image.fade-out {
  opacity: 0;
}

/* Dark mode styles */
.simulation-layout.dark-theme .simulation-toolbar {
  background-color: #232323;
  border-color: #383838;
}

.simulation-layout.dark-theme .simulation-toolbar .control-btn {
  background-color: #333;
  color: #ddd;
  border-color: #444;
}

.simulation-layout.dark-theme .simulation-toolbar .control-btn:hover:not(:disabled) {
  background-color: #444;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .simulation-toolbar {
    height: 60px;
    padding: 0 5px;
  }

  .control-buttons {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
    gap: 5px;
  }

  .control-btn {
    padding: 5px 8px;
    font-size: 12px;
  }

  .game-controls {
    flex-wrap: wrap;
  }

  .control-input {
    width: 60px;
  }

  .simulation-status-image {
    top: 80px;
  }

  .simulation-status-image img {
    width: 150px;
  }
}

/* Add sound switch styles */
.sound-switch {
  margin-left: 15px;
}
</style>
