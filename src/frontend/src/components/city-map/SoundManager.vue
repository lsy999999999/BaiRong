<template>
  <!-- 该组件仅处理声音加载，不包含UI元素 -->
</template>

<script>
import { onMounted, onBeforeUnmount, watch } from 'vue';
import { useGameStore } from '../../stores/gameStore';
import { sound } from '@pixi/sound';

export default {
  name: 'SoundManager',
  setup() {
    const gameStore = useGameStore();

    // 加载声音
    const loadSounds = () => {
        console.log('loadSounds',gameStore.pixiApp);
      // 确保PIXI应用已初始化
      if (!gameStore.pixiApp) {
        console.warn('PIXI应用尚未初始化，无法加载声音');
        return;
      }

      try {
        // 添加背景音乐并设置循环播放
        sound.add('bgm', {
          url: '/sounds/bgm.mp3',
          loop: true,
          volume: 0.5
        });
        
        // 加载女性声音 (1-50)
        for (let i = 1; i <= 50; i++) {
          sound.add(`f_${i}`, `/sounds/f/${i}.mp3`);
        }

        // 加载男性声音 (1-50)
        for (let i = 1; i <= 50; i++) {
          sound.add(`m_${i}`, `/sounds/m/${i}.mp3`);
        }

        console.log('声音加载成功',sound);
        
        // 开始播放背景音乐
        sound.play('bgm');
        
        // 根据初始游戏状态设置音量
        updateBgmVolume(gameStore.isPaused);
      } catch (error) {
        console.error('加载声音时出错:', error);
      }
    };

    // 更新背景音乐音量
    const updateBgmVolume = (isPaused) => {
      try {
        if (isPaused) {
          sound.volume('bgm', 0); // 暂停时静音
        } else {
          sound.volume('bgm', 0.5); // 播放时音量为0.5
        }
      } catch (error) {
        console.error('更新背景音乐音量时出错:', error);
      }
    };

    // 监听游戏暂停状态变化
    watch(() => gameStore.isPaused, (newValue) => {
      updateBgmVolume(newValue);
    });

    // 清理声音资源
    const cleanupSounds = () => {
      try {
        sound.removeAll();
        console.log('声音资源已清理');
      } catch (error) {
        console.error('清理声音资源时出错:', error);
      }
    };

    // 根据性别获取随机声音
    const getRandomGenderSound = (gender) => {
      // 随机选择1-50之间的一个数字
      const randomIndex = Math.floor(Math.random() * 50) + 1;
      console.log('soundId1',randomIndex);
      return `${gender}_${randomIndex}`;
    };

    // 暴露按性别播放声音的方法给全局window对象
    if (typeof window !== 'undefined') {
      // 添加按性别播放声音的方法
      window.playGenderSound = (gender) => {
        const soundId = getRandomGenderSound(gender);
        console.log('soundId',soundId,gender);
        sound.play(soundId);
      };
    }

    onMounted(() => {
      loadSounds();
    });

    onBeforeUnmount(() => {
      cleanupSounds();
    });

    return {
      // 这里可以暴露一些方法给模板，但当前模板为空
    };
  }
};
</script> 