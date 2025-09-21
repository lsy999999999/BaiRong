<template>
  <div class="city-map-container">
    <div ref="mapContainer" class="map-view-container">
      <TilemapRenderer v-if="mapData" :map-data="mapData" @map-loaded="onMapLoaded" ref="tilemapRenderer" />
      <MapCamera v-if="mapLoaded" :padding="0" />
      <!-- 添加SoundManager组件用于加载声音 -->
      <SoundManager v-if="mapLoaded" />

      <!-- 添加事件阻断层 -->
      <div v-if="showEventBlocker" class="event-blocker" @click.stop.prevent @contextmenu.stop.prevent
        @mouseover.stop.prevent @mouseout.stop.prevent @mousemove.stop.prevent @mouseenter.stop.prevent
        @mouseleave.stop.prevent @mousedown.stop.prevent @mouseup.stop.prevent @wheel.stop.prevent
        @touchstart.stop.prevent @touchmove.stop.prevent @touchend.stop.prevent></div>
    </div>

    <!-- 添加SimulationToolbar组件 -->
    <SimulationToolbar @generate-map="generateNewMap" @generate-characters="generateCharacter"
      @control-clicked="handleControlClicked" />

    <!-- 返回首页按钮 -->
    <el-button @click="confirmBackToHome" class="home-btn control-btn">
      <el-icon>
        <HomeFilled />
      </el-icon>
    </el-button>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import TilemapRenderer from './TilemapRenderer.vue';
import MapCamera from './MapCamera.vue';
import MapGenerator from './MapGenerator';
import SimulationToolbar from '../simulation/SimulationToolbar.vue';
import { useGameStore } from '../../stores/gameStore';
import { HomeFilled } from '@element-plus/icons-vue';
import { ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import SoundManager from './SoundManager.vue';

export default {
  name: 'CityMapParent',
  components: {
    TilemapRenderer,
    MapCamera,
    SimulationToolbar,
    HomeFilled,
    SoundManager
  },
  setup() {
    const mapContainer = ref(null);
    const tilemapRenderer = ref(null);
    const mapData = ref(null);
    const mapLoaded = ref(false);
    const gameStore = useGameStore();
    const showEventBlocker = ref(false); // 添加事件阻断层状态
    const router = useRouter(); // 获取路由实例

    // 暂停由gameStore管理
    const paused = computed(() => gameStore.isPaused);

    // 使用gameStore中的人口相关状态
    const populationTotal = computed(() => gameStore.populationTotal);
    const populationCreated = computed(() => gameStore.populationCreated);

    // 使用gameStore管理isDevMode状态
    const isDevMode = computed(() => gameStore.isDevMode);

    // 添加事件阻断层
    const addEventBlocker = () => {
      showEventBlocker.value = true;

      // 只禁用PIXI的交互，不影响viewport功能
      if (gameStore.getPixiApp && gameStore.getPixiApp.stage) {
        // 禁用PIXI的交互
        gameStore.getPixiApp.stage.interactive = false;
        gameStore.getPixiApp.stage.interactiveChildren = false;
      }
    };

    // 移除事件阻断层
    const removeEventBlocker = () => {
      showEventBlocker.value = false;

      // 恢复PIXI的交互
      if (gameStore.getPixiApp && gameStore.getPixiApp.stage) {
        gameStore.getPixiApp.stage.interactive = true;
        gameStore.getPixiApp.stage.interactiveChildren = true;
      }
    };

    // 生成新地图
    const generateNewMap = () => {
      // 获取当前的人口总数
      const currentPopTotal = gameStore.agentsData?.agent_count || null; // 默认值100
      console.log('开始生成新地图，人口总数：', currentPopTotal);
      // 更新人口总数
      if (currentPopTotal) {
        gameStore.setPopulationTotal(currentPopTotal);
      } else {
        gameStore.setPopulationTotal(100);
      }

      mapLoaded.value = false;
      gameStore.resetPopulationCreated();

      try {
        const mapGenerator = new MapGenerator();
        const mapSize = 5 + 12 + 1 * Math.floor(populationTotal.value / 2000); // 根据人口规模调整地图尺寸
        // 修改后的尺寸，加上上下左右各12格的边缘区域，总共加24
        const totalMapSize = mapSize + 24;
        console.log('地图尺寸:', mapSize, '总地图尺寸(含边缘区域):', totalMapSize);

        // 生成地图数据
        const newMapData = mapGenerator.generate({
          width: totalMapSize,
          height: totalMapSize,
          tileWidth: 128, // 增加瓦片尺寸，让图块更加清晰
          tileHeight: 128,
          population: populationTotal.value
        });
        mapData.value = newMapData;
      } catch (error) {
        console.error('生成地图时发生错误:', error);
      }
    };

    // 地图加载完成回调
    const onMapLoaded = () => {
      console.log('地图加载完成');
      mapLoaded.value = true;
    };

    // 生成人物
    const generateCharacter = (num) => {
      if (!mapLoaded.value || !tilemapRenderer.value) {
        console.warn('地图尚未加载，无法生成人物');
        return;
      }

      console.log('生成人物，数量：', num);
      // 更新人物数量设置
      gameStore.setPopulationSize(num);

      // 调用TilemapRenderer的添加人物方法
      tilemapRenderer.value.addCharacter(num);
    };

    // 处理SimulationToolbar组件的control-clicked事件
    const handleControlClicked = (action) => {
      console.log('SimulationToolbar control-clicked event:', action);

      // 根据不同的action执行相应操作
      switch (action) {
        case 'add-blocker':
          addEventBlocker();
          break;
        case 'remove-blocker':
          removeEventBlocker();
          break;
        case 'finish':
          // 模拟结束处理
          console.log('处理模拟结束事件');
          // 可以添加额外的清理逻辑
          break;
        default:
          console.log('未知的控制事件:', action);
      }
    };

    // 返回首页按钮事件
    const confirmBackToHome = () => {
      // 记录当前暂停状态
      const wasPaused = paused.value;

      // 如果模拟正在运行且未暂停，先暂停模拟
      if (!paused.value) {
        gameStore.togglePause();
      }

      // 直接添加事件阻断层
      addEventBlocker();

      ElMessageBox.confirm(
        'Returning to the homepage will lose all progress',
        'Notice',
        {
          confirmButtonText: 'Confirm',
          cancelButtonText: 'Cancel',
          type: 'warning',
          // 点击蒙层关闭对话框时触发
          closeOnClickModal: true,
          beforeClose: (action, instance, done) => {
            if (action === 'confirm') {
              // 确认时，进行清理操作
              console.log('执行清理操作...');
              // 这里可以添加清理代码
              clearMapData();
              // 延迟执行跳转，确保清理操作完成
              setTimeout(() => {
                router.push('/');
              }, 100);
            } else {
              // 取消时，恢复原来的模拟状态
              if (!wasPaused) {
                gameStore.togglePause();
              }
              // 移除事件阻断层
              removeEventBlocker();
            }
            done();
          }
        }
      ).catch(() => {
        // 发生异常时，也要确保恢复模拟状态并移除阻断层
        if (!wasPaused) {
          gameStore.togglePause();
        }
        removeEventBlocker();
      });
    };
    const clearMapData = () => {
      mapData.value = null;
      mapLoaded.value = false;
      // 调用gameStore的resetState方法重置所有状态
      gameStore.resetState();
      console.log('地图数据已清除，游戏状态已重置');
    };
    onMounted(() => {
      // 初始化gameStore的开发者模式
      gameStore.initDevMode();

      // 显示开发者模式状态
      if (isDevMode.value) {
        console.log('已启用开发者模式');
      }
      // 初始化时自动生成地图并传入人口总数
      generateNewMap();
    });

    onBeforeUnmount(() => {
      // 清理资源
      if (tilemapRenderer.value) {
        tilemapRenderer.value.dispose && tilemapRenderer.value.dispose();
      }
      clearMapData();
    });

    return {
      mapContainer,
      tilemapRenderer,
      mapData,
      mapLoaded,
      isDevMode,
      paused,
      populationCreated,
      generateNewMap,
      generateCharacter,
      onMapLoaded,
      addEventBlocker, // 暴露添加事件阻断层方法
      removeEventBlocker, // 暴露移除事件阻断层方法
      showEventBlocker, // 暴露事件阻断层状态
      handleControlClicked, // 暴露handleControlClicked方法
      confirmBackToHome, // 暴露confirmBackToHome方法
    };
  }
}
</script>

<style scoped>
.city-map-container {
  width: 100vw;
  height: 100vh;
  position: absolute;
  top: 0;
  left: 0;
  overflow: hidden;
}

.map-view-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background-color: #252934;
  /* 深色背景 */
}

/* 事件阻断层样式 */
.event-blocker {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: transparent;
  z-index: 100;
  /* 确保在所有元素上方，但允许其他UI控件正常工作 */
  cursor: default;
  /* 使用默认光标样式 */
  pointer-events: all;
  /* 捕获所有指针事件 */
  touch-action: none;
  /* 阻止所有触摸操作 */
  user-select: none;
  /* 防止文本选择 */
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* 首页按钮样式 */
.home-btn {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 2005;
  border-radius: 4px;
  transition: all 0.2s ease;
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

.dark-theme .control-btn {
  background-color: #333;
  color: #ddd;
  border-color: #444;
}

.dark-theme .control-btn:hover:not(:disabled) {
  background-color: #444;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}
</style>