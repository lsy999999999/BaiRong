<template>
  <div class="sidebar">
    <div class="logo">
      <router-link to="/">
        <h2>YuLan-OneSim</h2>
      </router-link>
    </div>

    <nav class="menu">
      <ul class="main-menu">
        <li
          v-for="(item, index) in menuItems"
          :key="index"
          class="menu-item"
          :class="{ active: activeCategory === item.id }"
        >
          <div class="menu-title" @click="toggleItem(item)">
            <i :class="item.icon"></i>
            <span>{{ item.category }}</span>
            <i class="fa fa-chevron-down"></i>
          </div>
          <ul class="submenu" v-if="item.subcategories && item.subcategories.length">
            <li
              v-for="(sub, subIndex) in item.subcategories"
              :key="subIndex"
              :class="{
                active: activeCategory === item.id && activeSubcategory === sub.id,
              }"
              @click="selectSubcategory(item.id, sub.id)"
            >
              {{ sub.name }}
            </li>
          </ul>
        </li>
      </ul>
    </nav>

    <div class="customize-btn" v-if="route.name !== 'dashboard'">
      <el-button
        id="customize-button"
        @click="navigateToDashboard"
      >
        <i class="fas fa-sliders-h"></i><span>Customize</span>
      </el-button>
<!--      <el-button class="data-transform-btn" @click="navigateToDataTransform">
        <i class="fas fa-exchange-alt"></i>
        <span>Data Transform</span>
      </el-button> -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from "axios"
import { useGameStore } from '../stores/gameStore'

const router = useRouter()
const route = useRoute()
const gameStore = useGameStore()
const activeCategory = ref('')
const activeSubcategory = ref('')
const menuItems = ref([])

// 初始化路由参数
const { category, subcategory } = route.params
if (category && subcategory) {
  activeCategory.value = category
  activeSubcategory.value = subcategory
}

const loadData = async () => {
  menuItems.value = []
  try {
    const response = await axios.get("/api/scenes")
    for (let i in response.data) {
      let item = response.data[i]
      let icon = "fa fa-chart-line" // 默认图标
      
      // 为不同分类配置不同图标
      if (i === "Economics") icon = "fa fa-chart-line"
      else if (i === "Sociology") icon = "fa fa-users"
      else if (i === "Politics") icon = "fa fa-landmark"
      else if (i === "Psychology") icon = "fa fa-brain"
      else if (i === "Communication") icon = "fa fa-comments"
      else if (i === "Organization") icon = "fa fa-building"
      else if (i === "Demographics") icon = "fa fa-chart-pie"
      else if (i === "Law") icon = "fa fa-gavel"
      
      let menuItemData = {
        id: i,
        category: i,
        icon: icon,
        subcategories: [],
      }
      for (let j in item) {
        menuItemData.subcategories.push({
          id: item[j].name,
          name: item[j].name.replace(/_/g, " "),
        })
      }
      menuItems.value.push(menuItemData)
      //console.log(menuItemData, "menuItemData")
    }
  } catch (error) {
    console.log("加载数据失败", error)
  }
}

const toggleItem = (item) => {
  if (activeCategory.value === item.id) {
    activeCategory.value = ""
  } else {
    activeCategory.value = item.id
  }
}

const selectSubcategory = (category, subcategory) => {
  activeCategory.value = category
  activeSubcategory.value = subcategory
  console.log('模拟场景点击======',category,subcategory);
  router.push({
    name: "category",
    params: {
      category,
      subcategory,
    },
  })
}

const navigateToDashboard = () => {
  router.push("/")
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.sidebar {
  width: 320px;
  height: 100vh;
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.logo {
  padding: 25px 20px;
  border-bottom: 1px solid var(--border-color);
}

.logo h2 {
  color: var(--text-color);
  font-size: 1.8rem;
}

.menu {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

.main-menu {
  list-style: none;
}

.menu-item {
  margin-bottom: 8px;
}

.menu-title {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 4px;
  margin: 0 10px;
}

.menu-title:hover {
  background-color: var(--menu-hover);
}

.menu-title i {
  margin-right: 10px;
  width: 20px;
  text-align: center;
}

.menu-title span {
  flex: 1;
  text-transform: capitalize;
}

.fa-chevron-down {
  font-size: 0.8rem;
  transition: transform 0.3s ease;
}

.menu-item.active .fa-chevron-down {
  transform: rotate(180deg);
}

.submenu {
  list-style: none;
  margin: 5px 0 10px 48px;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.menu-item.active .submenu {
  max-height: 999px;
}

.submenu li {
  padding: 10px 15px;
  font-size: 0.95rem;
  color: #bbbbbb;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 4px;
  text-transform: capitalize;
}

.light-theme .submenu li {
  color: #666666;
}

.submenu li:hover {
  color: var(--text-color);
  background-color: rgba(255, 255, 255, 0.05);
}

.light-theme .submenu li:hover {
  color: var(--text-color);
  background-color: rgba(0, 0, 0, 0.05);
}

.submenu li.active {
  color: var(--text-color);
  background-color: rgba(255, 255, 255, 0.1);
  font-weight: 500;
}

.light-theme .submenu li.active {
  background-color: rgba(0, 0, 0, 0.07);
}

.customize-btn {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

#customize-button,
.topology-btn,
.data-transform-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  /* cursor: pointer; */
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s ease;
  font-size: 1rem;
  height: 45px;
  margin-left: 0 !important;
}

#customize-button {
  background-color: var(--accent-color);
  color: white;
}

.topology-btn {
  background-color: #2a9d8f;
  color: white;
}

.data-transform-btn {
  background-color: #f4a261;
  color: white;
  margin-top: 10px;
}

#customize-button:hover {
  background-color: #4170f3;
}

#customize-button:hover {
  background-color: #4170f3;
}

.data-transform-btn:hover {
  background-color: #e76f51;
}

#customize-button i,
.topology-btn i,
.data-transform-btn i {
  margin-right: 8px;
}

.data-transform-btn:hover {
  background-color: #e76f51;
}

#customize-button i,
.topology-btn i,
.data-transform-btn i {
  margin-right: 8px;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
    z-index: 1;
  }

  .menu {
    max-height: 0;
    padding: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }

  .menu.open {
    max-height: 400px;
    padding: 15px 0;
  }

  .logo {
    padding: 15px;
    cursor: pointer;
  }

  .customize-btn {
    padding: 15px;
  }

  .chatbox {
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 350px;
  }
}
</style>
