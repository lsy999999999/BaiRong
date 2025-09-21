<template>
  <div class="map-camera-controls">
    <!-- 声音控制按钮已移至SimulationToolbar.vue -->
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useGameStore } from '../../stores/gameStore';
import * as PIXI from 'pixi.js';
import { sound } from '@pixi/sound';

export default {
  name: 'MapCamera',
  props: {
    padding: {
      type: Number,
      default: 100
    }
  },
  setup(props, { emit }) {
    const showCharacterList = ref(false);
    const activeTab = ref('outdoor');
    const router = useRouter();
    const route = useRoute();
    const gameStore = useGameStore();
    // 声音状态现在由SimulationToolbar.vue管理
    
    // 直接从gameStore获取viewport
    const viewport = computed(() => gameStore.getViewport);
    const app = computed(() => gameStore.getPixiApp);

    // 计算属性：获取室外角色列表
    const outdoorCharacters = computed(() => {
      return gameStore.getOutdoorCharacters || [];
    });

    // 计算属性：获取室内角色列表
    const indoorCharacters = computed(() => {
      return gameStore.getIndoorCharacters || [];
    });

    // 切换角色列表弹窗显示状态
    const toggleCharacterList = () => {
      showCharacterList.value = !showCharacterList.value;
    };

    // 获取角色世界坐标
    const getCharacterWorldPosition = (character) => {
      let worldX, worldY;

      // 防御性检查，确保character和sprite存在
      if (!character || !character.sprite) {
        console.warn('角色或精灵不存在', character);
        return { worldX: 0, worldY: 0 };
      }

      // 在函数开始时获取并存储isIndoor的值，确保状态一致性
      const isIndoor = character.isIndoor;

      // 判断是否有sprite引用
      if (isIndoor === false) {
        // 直接使用精灵的实际坐标
        worldX = character.sprite.x;
        worldY = character.sprite.y + props.padding;

      } else if (isIndoor === true) {
        character.sprite.zIndex = 9999;

        // 获取室内地板、楼层和建筑的引用
        const roomSprite = character.sprite.parent; // 室内地板
        const floorSprite = roomSprite?.parent; // 楼层精灵
        const buildingSprite = floorSprite?.parent; // 建筑精灵

        if (buildingSprite && floorSprite) {
          worldX = buildingSprite.x + (roomSprite.x + character.sprite.x);
          worldY = buildingSprite.y + floorSprite.y + roomSprite.y + character.sprite.y;
        } else {
          console.warn('无法正确获取室内人物的位置层级', character);
          worldX = character.x || 0;
          worldY = character.y || 0;
        }
      } else {
        console.warn('无法确定角色室内/室外状态，使用默认坐标处理', character);
        worldX = character.sprite.x || character.x || 0;
        worldY = (character.sprite.y || character.y || 0) + props.padding;
      }
      return { worldX, worldY };
    };

    // 移动相机到角色位置
    const moveCameraToCharacter = (worldX, worldY, options = {}) => {
      const {
        animate = false,
        scale = 2,
        duration = 500,
        ease = 'easeInOutQuad',
        offsetRatio = 0.2  // 默认右侧面板占比60%
      } = options;

      // 计算左侧可视区域宽度和中心位置
      const leftAreaWidth = viewport.value.screenWidth * (1 - offsetRatio); // 左侧区域宽度
      const offsetX = leftAreaWidth / 3; // 左侧区域中心点X坐标
      viewport.value.scale.set(scale);
      viewport.value.moveCenter(worldX, worldY);

      // 应用X偏移，向左移动视口
      viewport.value.position.x -= offsetX;

      // console.log(`摄像机已移动到位置: (${worldX}, ${worldY}), 视口位置: (${viewport.value.position.x}, ${viewport.value.position.y})`);
    };

    // 更新相机跟随功能
    const updateCameraFollow = () => {
      // 获取当前焦点角色ID
      const focusedCharacterId = gameStore.getFocusedCharacterId;

      // 如果没有焦点角色ID或视口未初始化，直接返回
      if (!focusedCharacterId || focusedCharacterId === null || !viewport.value) {
        return;
      }

      // 获取焦点角色对象
      const character = gameStore.getFocusedCharacter;
      if (!character) {
        console.log('镜头跟随取消: 找不到焦点角色对象');
        return;
      }

      // 设置焦点角色的zIndex确保可见
      if (character.sprite) {
        // console.log('角色:', character);
        character.sprite.zIndex = 9999;
        character.sprite.visible = true; // 确保角色可见
      }

      // 处理室内人物的可见性 - 持续保持可见性状态
      if (character.isIndoor && character.sprite) {
        // 获取室内地板、楼层精灵
        const roomSprite = character.sprite.parent; // 室内地板
        const floorSprite = roomSprite?.parent; // 楼层精灵

        // 确保室内地板可见
        if (roomSprite) {
          roomSprite.visible = true;

          // 将室内地板的所有子元素设为可见
          roomSprite.children.forEach(child => {
            if (child) {
              child.visible = true;
            }
          });
        }

        // 将楼层精灵设为半透明，以便看到内部
        if (floorSprite) {
          // 保存原始zIndex并提高楼层zIndex
          if (floorSprite.originalZIndex === undefined) {
            floorSprite.originalZIndex = floorSprite.zIndex;
          }
          floorSprite.zIndex = 9998; // 确保楼层在其他精灵之上，但在角色之下
        }
      }

      // 获取角色世界坐标
      const { worldX, worldY } = getCharacterWorldPosition(character);

      // 如果没有有效位置，直接返回
      if (worldX === undefined || worldY === undefined) {
        console.warn('无法获取角色位置，取消相机跟随');
        return;
      }

      // 移动相机到角色位置
      moveCameraToCharacter(worldX, worldY, {
        animate: false,
        scale: 0.5,
        duration: 500,
        ease: 'easeInOutQuad',
        offsetRatio: 0.2
      });
    };

    // 播放随机响应音效
    const playResponseSound = (agentId) => {
      // 检查全局声音状态
      const isSoundEnabled = typeof window !== 'undefined' ? window.isSoundEnabled : true;
      if (!isSoundEnabled) return;
      
      try {
        // 查找角色对象，获取性别信息
        const character = gameStore.characters.find(char => char.agentId === agentId);
        const gender = character ? character.gender : null;
        
        // 按性别播放声音
        if (gender && typeof window !== 'undefined' && window.playGenderSound) {
          window.playGenderSound(gender);
        }
      } catch (error) {
        console.error('播放声音时出错:', error);
      }
    };

    // 点击人物查看详情
    const viewCharacterDetail = (agentId, event) => {
      if (!agentId) return;

      // 阻止事件冒泡，防止触发地图点击事件
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }

      console.log('点击查看人物详情，agentId:', agentId);

      // 播放响应音效，传入agentId
      playResponseSound(agentId);

      // 设置为焦点角色ID
      gameStore.setFocusedCharacterId(agentId);
      // 打开角色详情面板
      router.replace({
        query: {
          panel: 'characterDetail',
          id: agentId,
          tab: 'info'
        }
      });
    };

    // 声音控制已移至SimulationToolbar.vue

    // 监听路由变化，当角色详情面板关闭时，解除锁定
    watch(() => route.query, (newQuery) => {
      // 如果当前没有panel=characterDetail查询参数，表示详情面板已关闭
      if (!newQuery.panel || newQuery.panel !== 'characterDetail') {
        // 清除焦点角色ID
        gameStore.clearFocusedCharacterId();
        console.log('角色详情面板已关闭，解除镜头锁定');
      }
    }, { deep: true });

    // 向父组件暴露方法，实现反向调用
    onMounted(() => {
      // 直接向gameStore注册相机控制器
      const controller = {
        updateCameraFollow,
        viewCharacterDetail,
        playResponseSound
      };

      // 设置控制器到gameStore
      gameStore.setCameraController(controller);
      console.log('已向gameStore注册相机控制器');

      // 初始执行一次更新相机跟随（如果有焦点角色）
      if (gameStore.getFocusedCharacterId) {
        updateCameraFollow();
      }
    });

    return {
      showCharacterList,
      activeTab,
      outdoorCharacters,
      indoorCharacters,
      toggleCharacterList,
      updateCameraFollow,
      viewCharacterDetail
    };
  }
};
</script>

<style scoped>
.map-camera-controls {
  position: absolute;
  left: 10px;
  top: 10px;
  z-index: 100;
}

.character-list-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid #dcdfe6;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  color: #409eff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.character-list-btn:hover {
  background-color: #f2f6fc;
}

/* 声音控制按钮样式已移至SimulationToolbar.vue */

.character-list-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 900px;
  max-height: 80vh;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.modal-header h3 {
  margin: 0;
  color: #303133;
}

.close-btn {
  background: none;
  border: none;
  font-size: 22px;
  color: #909399;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex-grow: 1;
}

.tabs {
  display: flex;
  margin-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.tab-btn {
  padding: 8px 15px;
  background: none;
  border: none;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
}

.tab-btn.active {
  color: #409eff;
  border-bottom: 2px solid #409eff;
}

.character-table-container {
  overflow-x: auto;
}

.character-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.character-table th,
.character-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.character-table th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 500;
}

.character-table tr:hover td {
  background-color: #f5f7fa;
}
</style>