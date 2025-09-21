<template>
  <div class="category-layout">
    <Sidebar />

    <div class="main-content">
      <div class="breadcrumb">
        <router-link to="/">
          <i class="fa fa-home"></i>
        </router-link>
        <span class="separator">/</span>
        <span>{{ category }}</span>
        <span class="separator">/</span>
        <span>{{ subcategory }}</span>

        <div class="button-area">
          <button class="modify-btn" @click="handleModifyClick">
            <i class="fa fa-edit"></i> Modify
          </button>
          <button class="next-btn" @click="showNextStepAlert">
            <i class="fa fa-forward"></i> Next Step
          </button>
        </div>
      </div>

      <div class="category-header">
        <h1>{{ categoryTitle }}</h1>
      </div>

      <div class="topology-container">
        <TopologyGraph :category="category" :subcategory="subcategory" @odd_protocol="handleOddProtocol" />
      </div>
      <div class="description-container">
        <h2>{{ subcategoryName }}</h2>
        <div class="description-content">
          <!-- 使用 v-html 渲染 markdown 内容 -->
          <div class="markdown-content" v-html="parseMarkdown(odd_protocol)"></div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showModelDialog" title="Please select the model." width="400px">
      <el-select v-model="tempSelectedModel" placeholder="Please select the model." style="width: 100%;">
        <el-option
          v-for="item in models"
          :key="item.value"
          :label="item.name"
          :value="item.value"
        />
      </el-select>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showModelDialog = false">Cancel</el-button>
          <el-button type="primary" @click="handleModelDialogConfirm">OK</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, h } from "vue";
import { useRouter } from "vue-router";
import Sidebar from "../components/Sidebar.vue";
import TopologyGraph from "../components/TopologyGraph.vue";
import axios from "axios";
import { ElMessageBox, ElMessage } from "element-plus";
import { Codemirror } from 'vue-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { githubLight } from "@uiw/codemirror-theme-github";
import { useGameStore } from "../stores/gameStore";
import { fa } from "element-plus/es/locale/index.mjs";

const router = useRouter();
const gameStore = useGameStore();
const props = defineProps({
  category: {
    type: String,
    required: true,
  },
  subcategory: {
    type: String,
    required: true,
  },
});
const codemirror = ref(null);
const loading = ref(false);
const categories = ref({});

/**
 * 接收子组件传值
 */
const odd_protocol = ref('');
const handleOddProtocol = (protocol) => {
  odd_protocol.value = protocol;
};

const categoryTitle = computed(() => {
  const categoryData = getCategoryData();
  if (!categoryData) return "Unknown Category";
  const subcategoryData = getSubcategoryData(categoryData);
  if (!subcategoryData) return categoryData.name;
  let env_name = subcategoryData.name.replace(/_/g, " ");
  return `${categoryData.name}: ${replaceUnderscoreWithSpace(subcategoryData.name)}`;
});

const subcategoryName = computed(() => {
  const categoryData = getCategoryData();
  if (!categoryData) return "";

  const subcategoryData = getSubcategoryData(categoryData);
  if (!subcategoryData) return "";

  return replaceUnderscoreWithSpace(subcategoryData.name);
});

const replaceUnderscoreWithSpace = (str)=>{
  if (typeof str !== 'string') {
    console.warn('输入不是字符串类型，已返回空字符串');
    return '';
  }
  // 1. 替换所有下划线为空格
  const stringWithSpaces = str.replace(/_/g, ' ');
  // 2. 将每个单词的首字母大写
  const titleCaseString = stringWithSpaces.replace(/\b\w/g, (match) => {
    return match.toUpperCase();
  });
  return titleCaseString;
}

const categoryDescription = computed(() => {
  try {
    const categoryData = getCategoryData();
    const subcategoryData = getSubcategoryData(categoryData);
    return subcategoryData.description;
  } catch (e) {
    return "Description for this category has not been added yet. We are working on it...";
  }
});

const loadData = async () => {
  localStorage.removeItem("sessionId");
  localStorage.removeItem("scenarioName");
  try {
    const response = await axios.get("/api/scenes/" + props.category);
    console.log(response);
    let resData = response.data;
    let subcategoriesData = {};
    for (let i in resData) {
      subcategoriesData[resData[i].name] = {
        name: resData[i].name,
        description: resData[i].description,
      };
    }
    categories.value[props.category] = {
      name: props.category,
      subcategories: subcategoriesData,
    };
  } catch (error) {
    console.error("加载数据失败", error);
  }
};

const getCategoryData = () => {
  return categories.value[props.category];
};

const getSubcategoryData = (categoryData) => {
  if (!categoryData || !categoryData.subcategories) return null;
  return categoryData.subcategories[props.subcategory];
};

const showModelDialog = ref(false);
const tempSelectedModel = ref("");
const handleModifyClick = () => {
  tempSelectedModel.value = selectedModel.value || (models.value[0] && models.value[0].value) || '';
  showModelDialog.value = true;
};
const handleModelDialogConfirm = () => {
  if (!tempSelectedModel.value) {
    ElMessage.warning('请选择模型');
    return;
  }
  selectedModel.value = tempSelectedModel.value;
  localStorage.setItem("scenarioName", props.subcategory);
  axios.post("/api/pipeline/initialize", {
    env_name: props.subcategory,
    category: "chat",
    model_name: selectedModel.value,
  }).then(() => {
    localStorage.setItem("sessionId", "");
    router.push({
      path: "/simulation",
      query: { step: 2 },
    });
  });
  showModelDialog.value = false;
};

const showNextStepAlert = () => {
  ElMessageBox.confirm("Start Simulation?", {
    confirmButtonText: "OK",
    cancelButtonText: "Cancel",
  })
    .then(() => {
       localStorage.setItem("sessionId", "");

       localStorage.setItem("scenarioName", props.subcategory);

      router.push({
        path: "/simulation-system",
      
      });
      console.log("ok");


    })
    .catch(() => {
      console.log("cancel");
    });
};

// 添加简单的 Markdown 解析函数
const parseMarkdown = (str) => {
  if (!str) return '';
  
  // 转义 HTML 标签，防止 XSS 攻击
  const escapeHtml = (unsafe) => {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };
  
  // 处理标题 (# 标题)
  let html = escapeHtml(str)
    .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
    .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
    .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
    .replace(/^#### (.*?)$/gm, '<h4>$1</h4>');
  
  // 处理列表 (- 项目)
  html = html.replace(/^- (.*?)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*?<\/li>\n)+/g, function(match) {
    return '<ul>' + match + '</ul>';
  });
  
  // 处理普通段落
  html = html.replace(/^([^<\n].*?)$/gm, '<p>$1</p>');
  
  // 处理换行
  html = html.replace(/\n/g, '');
  
  return html;
};

const strToJson = (str) => {
  try {
    return JSON.parse(str);
  } catch (error) {
    return str;
  }
};

/**获取模型列表 */
const modelItem = ref({});
const models = ref([]);
const selectedModel = ref('');
const fetchModels = () => {
  axios
  .get("/api/config/models",{
    params: {
      category: "chat"
    }
  }).then((response) => {
    for (let i in response.data.models) {
      for (let j in response.data.models[i]) {
        let item = response.data.models[i][j];
        models.value.push({
          value: item,
          name: item,
          category: i,
        });
      }
    }
    // 如果models不为空，设置第一个模型为默认选择
    if (models.value.length > 0) {
      selectedModel.value = models.value[0].value;
      handleModelChange();
    }
  }).catch((error) => {
    console.error("获取模型列表失败:", error);
  });
}
/**模型选择（如果models不为空，设置第一个模型为默认选择） */
const handleModelChange = () => {
  modelItem.value = {};
  for (let i in models.value) {
    if (selectedModel.value == models.value[i].value) {
      modelItem.value = models.value[i];
    }
  }
}

watch(
  () => props.category,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      loadData();
    }
  },
  { immediate: true }
);

onMounted(() => {
  loadData();
  //获取模型列表
  fetchModels();
});
</script>

<style scoped>
.category-layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 320px;
  padding: 30px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.5s ease;
  overflow: auto;
}

.breadcrumb {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  font-size: 1rem;
  color: #aaa;
  background-color: var(--bg-color);
  position: relative;
  padding: 10px 0;
  top: -10px;
  /* left: -20px; */
  /* background: #ff0000; */
}

.breadcrumb a {
  color: var(--accent-color);
  text-decoration: none;
}

.breadcrumb a:hover {
  color: var(--text-color);
}

.separator {
  margin: 0 8px;
  color: #666;
}

.category-header {
  margin-bottom: 25px;
}

.category-header h1 {
  font-size: 2.2rem;
  color: var(--text-color);
  animation: fadeIn 0.5s ease;
}

.topology-container {
  width: 100%;
  height: 400px;
  margin-bottom: 30px;
  animation: slideUp 0.8s ease;
}

.description-container {
  background-color: var(--card-bg-color, rgba(255, 255, 255, 0.9));
  color: var(--card-text-color, #222);
  height: 300px;
  border-radius: 15px;
  padding: 16px;
  margin-bottom: 30px;
  position: relative;
  animation: fadeIn 0.5s ease;
  box-shadow: var(--box-shadow);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.description-container h2 {
  color: var(--card-heading-color, #333);
  margin-bottom: 15px;
  font-size: 1.8rem;
  transition: color 0.3s ease;
}

.description-content {
  font-size: 1.1rem;
  line-height: 1.6;
  /* margin-bottom: 50px; */
  color: var(--card-text-color, #222);
  transition: color 0.3s ease;
}

.modify-btn {
  background-color: #2196f3;
  color: white;
  margin-right: 15px;
}

.dark-theme .modify-btn {
  background-color: #1976d2;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
}

.modify-btn:hover {
  background-color: #0d8bf2;
  transform: translateY(-2px);
}

.next-btn {
  background-color: var(--accent-color);
  color: white;
}

.next-btn:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

/* Responsive design */
@media (max-width: 1200px) {
  .category-header h1 {
    font-size: 2rem;
  }
}

@media (max-width: 1024px) {
  .main-content {
    margin-left: 280px;
    padding: 25px;
  }

  .category-header h1 {
    font-size: 2rem;
  }
}

@media (max-width: 768px) {
  .category-layout {
    flex-direction: column;
  }

  .main-content {
    margin-left: 0;
    padding: 20px;
    order: 1;
  }

  .topology-container {
    height: 250px;
  }

  .category-header h1 {
    font-size: 1.8rem;
  }

  .description-content {
    font-size: 1rem;
    margin-bottom: 70px;
  }
}
.button-area {
  height: 24px;
  /* flex-direction: column; */
  /* align-items: flex-end; */
  bottom: 13px !important;
  right: 80px !important;
}
.next-btn {
  height: 30px;
  font-size: 14px;
}
.modify-btn {
  font-size: 14px;
  height: 30px;
  margin-right: 20px;
  margin-bottom: 0px;
}
.button-area button i {
  font-size: 12px;
  position: relative;
  top: 1px;
}
.button-area button {
  padding: 10px 15px;
}

.markdown-content {
  white-space: normal;
  overflow: auto;
  max-height: 210px;
  padding: 10px;
}

.markdown-content h1, 
.markdown-content h2, 
.markdown-content h3 {
  margin-top: 16px;
  margin-bottom: 8px;
}

.markdown-content ul, 
.markdown-content ol {
  padding-left: 20px;
}

.markdown-content p {
  margin-bottom: 8px;
}

/* 修复 scoped 样式问题，使 markdown 内容样式生效 */
:deep(.markdown-content ul) {
  list-style-type: disc;
}

:deep(.markdown-content ol) {
  list-style-type: decimal;
}

:deep(.el-select .el-select__wrapper) {
  border: 1px solid var(--border-color);
  box-shadow: 0 0 0 0 var(--el-border-color) inset !important;
}

:deep(.el-dialog__header) {
  border-bottom: 0px solid #eee !important;
}

:deep(.el-dialog__footer) {
  border-top: 0px solid #eee !important;
}
</style>
