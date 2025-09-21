<template>
  <div class="theme-toggle-container">
    <div class="theme-switch" @click="toggleTheme" :title="isDarkMode ? '切换到明亮模式' : '切换到暗黑模式'">
      <div class="theme-switch-track" :class="{ 'dark': isDarkMode }">
        <div class="icons">
          <div class="icon-moon">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          </div>
          <div class="icon-sun">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
          </div>
        </div>
        <div class="theme-switch-thumb" :class="{ 'dark': isDarkMode }"></div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { emitter } from '../layouts/ProgressLayoutWrapper.vue';

export default {
  name: 'ThemeToggle',
  data() {
    return {
      isDarkMode: true
    }
  },
  created() {
    // 从本地存储获取主题设置
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      this.isDarkMode = savedTheme === 'dark';
      this.applyTheme();
    } else {
      // 如果没有保存，则使用系统主题
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.isDarkMode = prefersDark;
      this.applyTheme();
    }
  },
  methods: {
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode;
      this.applyTheme();
      // 保存到本地存储
      localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light');
      // 触发事件通知其他组件
      emitter.emit('theme-changed', this.isDarkMode);
    },
    applyTheme() {
      if (this.isDarkMode) {
        document.documentElement.classList.remove('light-theme');
        document.documentElement.classList.add('dark-theme');
        document.querySelector('html').classList.remove('light-theme');
        document.querySelector('html').classList.add('dark-theme');
      } else {
        document.documentElement.classList.remove('dark-theme');
        document.documentElement.classList.add('light-theme');
        document.querySelector('html').classList.remove('dark-theme');
        document.querySelector('html').classList.add('light-theme');
      }
    }
  }
}
</script>

<style scoped>
.theme-toggle-container {
  /* 移除定位，由App.vue处理 */
}

.theme-switch {
  position: relative;
  cursor: pointer;
  user-select: none;
}

.theme-switch-track {
  width: 50px;
  height: 24px;
  background-color: #f3f3f3;
  border-radius: 50px;
  position: relative;
  transition: background-color 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.theme-switch-track.dark {
  background-color: #2a2a2a;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.theme-switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background-color: #fff;
  border-radius: 50%;
  transition: transform 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease;
  z-index: 2;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.theme-switch-thumb.dark {
  transform: translateX(24px);
  background-color: #383838;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.icons {
  display: flex;
  justify-content: space-between;
  width: 100%;
  height: 100%;
  padding: 4px 6px;
  box-sizing: border-box;
}

.icon-sun, .icon-moon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 16px;
}

.icon-sun {
  color: #f1c40f;
}

.icon-moon {
  color: #9b59b6;
}

.theme-switch-track:hover .theme-switch-thumb {
  box-shadow: 0 0 0 2px var(--accent-color);
}
</style> 