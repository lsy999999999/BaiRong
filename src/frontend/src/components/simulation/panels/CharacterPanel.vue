<template>
  <div class="character-panel">
    <!-- <h2>Character List</h2> -->
    
    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="Search characters..." clearable>
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    
    <el-table :data="currentPageData" style="width: 100%" border stripe
      class="character-table" v-loading="loading" @sort-change="handleSortChange">
      <!-- Fixed columns -->
      <!-- <el-table-column prop="id" label="ID" width="80" sortable="custom" /> -->
      <el-table-column prop="agentId" label="Agent ID" width="80" sortable="custom"/>
      <el-table-column prop="profile.name" label="Name" width="120" sortable="custom"/>
      <el-table-column prop="profile.agent_type" label="Type" width="120" sortable="custom"/>
      
      <!-- Dynamic columns -->
      <el-table-column v-for="field in dynamicFields" :key="field.prop" 
        :prop="field.prop" :label="field.label" sortable="custom">
      </el-table-column>
      
      <el-table-column label="Actions" width="230">
        <template #default="scope">
          <el-button size="small" @click="viewCharacterInfo(scope.row)">View</el-button>
          <el-button size="small" type="info" @click="viewCharacterHistory(scope.row)">History</el-button>
          <el-button size="small" type="success" @click="viewCharacterChat(scope.row)">Chat</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      :total="totalCharacters"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue';
import { Search } from '@element-plus/icons-vue';
import { useGameStore } from '../../../stores/gameStore';
import { useRouter } from 'vue-router';

export default {
  name: 'CharacterPanel',
  components: {
    Search
  },
  setup(props, { emit }) {
    const router = useRouter();
    const gameStore = useGameStore();
    // Load agents data
    const characters = ref([]);
    const loading = ref(true);
    
    // Pagination and sorting states
    const searchQuery = ref('');
    const currentPage = ref(1);
    const pageSize = ref(10);
    const sortConfig = reactive({
      prop: 'agentId',
      order: 'ascending' // ascending or descending
    });
    
    // Dynamic fields configuration
    const dynamicFields = ref([
      { prop: 'trust_level', label: 'Trust Level', width: '100' },
      { prop: 'belief_system', label: 'Belief System', width: '120' },
      { prop: 'connection_strength', label: 'Connection Strength', width: '100' },
      { prop: 'influence_score', label: 'Influence Score', width: '100' }
    ]);
    
    // Computed properties: search, sort and pagination processing
    const filteredCharacters = computed(() => {
      // 1. Search filtering
      let result = characters.value;
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        result = result.filter(char => 
          (char.profile?.name && char.profile.name.toLowerCase().includes(query)) || 
          (char.profile?.agent_type && char.profile.agent_type.toLowerCase().includes(query)) ||
          (char.id && String(char.id).includes(query)) ||
          (char.agentId && String(char.agentId).includes(query))
        );
      }
      
      // 2. Sort processing
      result = [...result].sort((a, b) => {
        // Get property values, support nested properties (like profile.name)
        const getPropValue = (obj, path) => {
          const parts = path.split('.');
          let value = obj;
          for (const part of parts) {
            if (value === null || value === undefined) return undefined;
            value = value[part];
          }
          return value;
        };

        const propA = getPropValue(a, sortConfig.prop);
        const propB = getPropValue(b, sortConfig.prop);
        
        // Special handling for ID as numeric comparison
        if (sortConfig.prop === 'id' || sortConfig.prop === 'agentId') {
          const numA = parseInt(propA) || 0;
          const numB = parseInt(propB) || 0;
          return sortConfig.order === 'ascending' 
            ? numA - numB
            : numB - numA;
        }
        
        // String comparison
        if (typeof propA === 'string' && typeof propB === 'string') {
          return sortConfig.order === 'ascending'
            ? propA.localeCompare(propB)
            : propB.localeCompare(propA);
        }
        
        // Number comparison
        return sortConfig.order === 'ascending'
          ? propA - propB
          : propB - propA;
      });
      
      return result;
    });
    
    // Current page data
    const currentPageData = computed(() => {
      const startIndex = (currentPage.value - 1) * pageSize.value;
      return filteredCharacters.value.slice(startIndex, startIndex + pageSize.value);
    });
    
    const totalCharacters = computed(() => filteredCharacters.value.length);
    
    // Methods
    const handleSizeChange = (val) => {
      pageSize.value = val;
      // Reset to first page
      currentPage.value = 1;
    };
    
    const handleCurrentChange = (val) => {
      currentPage.value = val;
    };
    
    // Table sort change handler
    const handleSortChange = ({ prop, order }) => {
      sortConfig.prop = prop;
      sortConfig.order = order;
    };

    // View character info (default tab)
    const viewCharacterInfo = (character) => {
      console.log('View character info:', character);
      // Navigate using agentId
      const targetId = character.agentId;
      emit('view-character', targetId);
      
      // Set focused character ID to enable camera follow
      gameStore.setFocusedCharacterId(targetId);
      
      router.replace({ 
        query: { 
          panel: 'characterDetail',
          id: targetId,
          tab: 'info'
        }
      });
    };
    
    // View character history
    const viewCharacterHistory = (character) => {
      console.log('View character history:', character);
      // Navigate using agentId
      const targetId = character.agentId;
      emit('view-character', targetId);
      
      // Set focused character ID to enable camera follow
      gameStore.setFocusedCharacterId(targetId);
      
      router.replace({ 
        query: { 
          panel: 'characterDetail',
          id: targetId,
          tab: 'history'
        }
      });
    };
    
    // Chat with character
    const viewCharacterChat = (character) => {
      console.log('Chat with character:', character);
      // Navigate using agentId
      const targetId = character.agentId;
      emit('view-character', targetId);
      
      // Set focused character ID to enable camera follow
      gameStore.setFocusedCharacterId(targetId);
      
      router.replace({ 
        query: { 
          panel: 'characterDetail',
          id: targetId,
          tab: 'chat'
        }
      });
    };
    
    // Load dynamic fields from configuration file
    const loadDynamicFields = () => {
      if (characters.value.length > 0) {
        const firstCharacter = characters.value[0];
        // Ensure profile exists
        if (!firstCharacter.profile) return;
        
        const excludedFields = ['id', 'name', 'agent_type'];
        
        // Clear current dynamic fields
        dynamicFields.value = [];
        
        // Only add fields from profile as dynamic fields
        for (const key in firstCharacter.profile) {
          // 跳过对象类型的字段
          if (!excludedFields.includes(key) && typeof firstCharacter.profile[key] !== 'object') {
            const fieldLabel = key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
            dynamicFields.value.push({
              prop: `profile.${key}`,
              label: fieldLabel
            });
          }
        }
      }
    };
    
    // Initialize data loading and preprocessing
    const initializeData = async () => {
      loading.value = true;
      
      try {
        console.time('Loading character data');
        
        // Get original data
        const originalData = gameStore.getAllCharacters;
        console.log('Original data count:', originalData.length);
        
        // Filter data, keep only necessary fields
        const filteredData = originalData.map(char => ({
          id: char.id,
          agentId: char.agentId,
          profile: char.profile
        }));
        
        // Use filtered data
        characters.value = filteredData;
        console.log('Filtered data count:', characters.value.length);
        
        // Load dynamic fields
        loadDynamicFields();
        
        console.timeEnd('Loading character data');
        console.log(`Loaded ${characters.value.length} characters`);
      } catch (error) {
        console.error('Failed to load character data:', error);
      } finally {
        loading.value = false;
      }
    };
    
    onMounted(() => {
      // Initialize data
      initializeData();
    });
    
    return {
      characters,
      dynamicFields,
      searchQuery,
      currentPage,
      pageSize,
      loading,
      filteredCharacters,
      currentPageData,
      totalCharacters,
      handleSizeChange,
      handleCurrentChange,
      handleSortChange,
      viewCharacterInfo,
      viewCharacterHistory,
      viewCharacterChat
    };
  }
};
</script>

<style scoped>
.character-panel {
  /* padding: 20px; */
  height: 100%;
  overflow-y: auto;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-bar .el-input {
  width: 100%;
}

.character-table {
  margin-bottom: 20px;
}

h2 {
  margin-bottom: 20px;
  color: var(--text-color);
}
</style> 