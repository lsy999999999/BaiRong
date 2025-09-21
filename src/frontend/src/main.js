import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// 引入Pinia
import { createPinia } from 'pinia'
// 引入gameStore
import { useGameStore } from './stores/gameStore'

// 引入Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 引入Element Plus自定义主题
import './styles/element-theme.css'

// 引入Font Awesome
import '@fortawesome/fontawesome-free/css/all.min.css'

// 引入全局样式
import './style.css'

// 创建Vue应用实例
const app = createApp(App)

// 创建Pinia实例
const pinia = createPinia()

// 使用路由
app.use(router)
    // 使用Element Plus
app.use(ElementPlus)
    // 使用Pinia
app.use(pinia)

// 挂载应用
app.mount('#app')

// 获取gameStore实例并初始化
const gameStore = useGameStore()
    // 初始化开发者模式
gameStore.initDevMode()

// 初始化主题设置
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.classList.add(savedTheme === 'dark' ? 'dark-theme' : 'light-theme');
} else {
    // 如果没有保存的主题，根据系统主题设置
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.classList.add(prefersDark ? 'dark-theme' : 'light-theme');
}