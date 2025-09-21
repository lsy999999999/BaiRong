<template>
  <div class="model-library-panel">
    <h2>Model Library</h2>
    <div class="panel-content">
      <!-- Search and filter toolbar -->
      <div class="library-toolbar">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="Search models..."
            prefix-icon="el-icon-search"
            clearable
            @input="filterModels"
          />
        </div>
        <div class="filter-options">
          <el-select v-model="categoryFilter" placeholder="Category" clearable @change="filterModels">
            <el-option v-for="category in categories" :key="category" :label="category" :value="category" />
          </el-select>
          <el-select v-model="sortOption" placeholder="Sort by" @change="filterModels">
            <el-option label="Name (A-Z)" value="name-asc" />
            <el-option label="Name (Z-A)" value="name-desc" />
            <el-option label="Date (Newest)" value="date-desc" />
            <el-option label="Date (Oldest)" value="date-asc" />
          </el-select>
        </div>
      </div>
      
      <!-- Models grid -->
      <div class="models-grid">
        <div 
          v-for="model in filteredModels" 
          :key="model.id" 
          class="model-card"
          :class="{ 'featured': model.featured }"
        >
          <div class="model-card-content">
            <div class="model-icon">
              <i :class="getModelIcon(model.type)"></i>
            </div>
            <h3 class="model-name">{{ model.name }}</h3>
            <div class="model-tags">
              <el-tag size="small" :type="getTagType(model.category)">{{ model.category }}</el-tag>
              <el-tag size="small" type="info" v-if="model.verified">Verified</el-tag>
            </div>
            
            <!-- Hover information -->
            <div class="model-hover-info">
              <p class="model-description">{{ model.description }}</p>
              <div class="model-stats">
                <div class="stat-item">
                  <span class="stat-label">Accuracy:</span>
                  <span class="stat-value">{{ model.accuracy }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Parameters:</span>
                  <span class="stat-value">{{ formatNumber(model.parameters) }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Created:</span>
                  <span class="stat-value">{{ formatDate(model.createdAt) }}</span>
                </div>
              </div>
              <div class="model-actions">
                <el-button size="small" type="primary">Use Model</el-button>
                <el-button size="small">Details</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-if="filteredModels.length === 0" class="empty-state">
        <i class="el-icon-search"></i>
        <p>No models found matching your criteria</p>
        <el-button @click="resetFilters">Reset Filters</el-button>
      </div>
      
      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[12, 24, 36, 48]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next"
          :total="totalModels"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModelLibraryPanel',
  data() {
    return {
      // Search and filtering
      searchQuery: '',
      categoryFilter: '',
      sortOption: 'date-desc',
      currentPage: 1,
      pageSize: 12,
      
      // Model data
      models: [
        {
          id: 1,
          name: 'ResNet-50',
          type: 'cnn',
          category: 'Image Classification',
          description: 'A deep residual learning framework with 50 layers that improves accuracy in image recognition tasks.',
          accuracy: 93.2,
          parameters: 25600000,
          createdAt: '2022-06-10',
          verified: true,
          featured: true
        },
        {
          id: 2,
          name: 'BERT-Base',
          type: 'transformer',
          category: 'NLP',
          description: 'Bidirectional Encoder Representations from Transformers. Pre-trained on masked language modeling and next sentence prediction.',
          accuracy: 89.5,
          parameters: 110000000,
          createdAt: '2022-05-15',
          verified: true,
          featured: false
        },
        {
          id: 3,
          name: 'MobileNet v3',
          type: 'cnn',
          category: 'Mobile Vision',
          description: 'Efficient mobile-friendly CNN architecture with reduced computational requirements.',
          accuracy: 86.4,
          parameters: 5400000,
          createdAt: '2022-07-20',
          verified: true,
          featured: false
        },
        {
          id: 4,
          name: 'LSTM Sequence Predictor',
          type: 'rnn',
          category: 'Time Series',
          description: 'Long Short-Term Memory network for sequence prediction and time series forecasting.',
          accuracy: 88.3,
          parameters: 8200000,
          createdAt: '2022-04-12',
          verified: false,
          featured: false
        },
        {
          id: 5,
          name: 'GPT-2 Small',
          type: 'transformer',
          category: 'NLP',
          description: 'Generative Pre-trained Transformer for text generation with 12 layers and 117M parameters.',
          accuracy: 91.7,
          parameters: 117000000,
          createdAt: '2022-03-25',
          verified: true,
          featured: true
        },
        {
          id: 6,
          name: 'YOLOv5',
          type: 'cnn',
          category: 'Object Detection',
          description: 'You Only Look Once (YOLO) is a real-time object detection system with excellent speed-accuracy balance.',
          accuracy: 94.1,
          parameters: 7500000,
          createdAt: '2022-06-30',
          verified: true,
          featured: false
        },
        {
          id: 7,
          name: 'GAN Image Generator',
          type: 'gan',
          category: 'Image Generation',
          description: 'Generative Adversarial Network for creating realistic images from random noise.',
          accuracy: 85.9,
          parameters: 14300000,
          createdAt: '2022-07-05',
          verified: false,
          featured: false
        },
        {
          id: 8,
          name: 'Wave2Vec',
          type: 'rnn',
          category: 'Speech Recognition',
          description: 'Self-supervised learning model for speech recognition that works with raw audio.',
          accuracy: 90.2,
          parameters: 28000000,
          createdAt: '2022-05-28',
          verified: true,
          featured: false
        },
        {
          id: 9,
          name: 'DenseNet-121',
          type: 'cnn',
          category: 'Image Classification',
          description: 'Densely connected convolutional network that improves information flow between layers.',
          accuracy: 91.5,
          parameters: 8000000,
          createdAt: '2022-04-18',
          verified: true,
          featured: false
        },
        {
          id: 10,
          name: 'GRU Language Model',
          type: 'rnn',
          category: 'NLP',
          description: 'Gated Recurrent Unit model for natural language processing tasks.',
          accuracy: 87.6,
          parameters: 6800000,
          createdAt: '2022-06-22',
          verified: false,
          featured: false
        },
        {
          id: 11,
          name: 'EfficientNet-B0',
          type: 'cnn',
          category: 'Image Classification',
          description: 'Scaled CNN that achieves state-of-the-art accuracy with significantly fewer parameters.',
          accuracy: 92.8,
          parameters: 5300000,
          createdAt: '2022-07-15',
          verified: true,
          featured: false
        },
        {
          id: 12,
          name: 'AlphaFold',
          type: 'transformer',
          category: 'Protein Folding',
          description: 'Neural network for predicting protein structure from amino acid sequence.',
          accuracy: 95.3,
          parameters: 93000000,
          createdAt: '2022-02-10',
          verified: true,
          featured: true
        }
      ]
    };
  },
  computed: {
    filteredModels() {
      let result = [...this.models];
      
      // Apply search query filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(model => 
          model.name.toLowerCase().includes(query) || 
          model.description.toLowerCase().includes(query) ||
          model.category.toLowerCase().includes(query)
        );
      }
      
      // Apply category filter
      if (this.categoryFilter) {
        result = result.filter(model => model.category === this.categoryFilter);
      }
      
      // Apply sorting
      switch(this.sortOption) {
        case 'name-asc':
          result.sort((a, b) => a.name.localeCompare(b.name));
          break;
        case 'name-desc':
          result.sort((a, b) => b.name.localeCompare(a.name));
          break;
        case 'date-asc':
          result.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
          break;
        case 'date-desc':
          result.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
          break;
      }
      
      return result;
    },
    
    totalModels() {
      return this.filteredModels.length;
    },
    
    categories() {
      // Get unique categories from models
      const categorySet = new Set(this.models.map(model => model.category));
      return Array.from(categorySet);
    }
  },
  methods: {
    filterModels() {
      this.currentPage = 1; // Reset to first page when applying filters
    },
    
    resetFilters() {
      this.searchQuery = '';
      this.categoryFilter = '';
      this.sortOption = 'date-desc';
      this.currentPage = 1;
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
    },
    
    formatNumber(num) {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
      }
      if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
      }
      return num.toString();
    },
    
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    },
    
    getModelIcon(type) {
      // Return appropriate icon class based on model type
      switch(type) {
        case 'cnn':
          return 'el-icon-picture-outline';
        case 'transformer':
          return 'el-icon-connection';
        case 'rnn':
          return 'el-icon-refresh';
        case 'gan':
          return 'el-icon-brush';
        default:
          return 'el-icon-cpu';
      }
    },
    
    getTagType(category) {
      // Return tag type based on category
      switch(category) {
        case 'Image Classification':
          return 'success';
        case 'NLP':
          return 'primary';
        case 'Object Detection':
          return 'warning';
        case 'Time Series':
          return 'info';
        case 'Speech Recognition':
          return 'danger';
        default:
          return '';
      }
    }
  }
}
</script>

<style scoped>
.model-library-panel {
  padding: 20px;
  height: 100%;
  background-color: var(--panel-bg, #ffffff);
  transition: all 0.3s ease;
}

h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  color: var(--text-color, #333333);
}

.panel-content {
  height: calc(100% - 60px);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 15px;
  background-color: var(--panel-bg, #f8f8f8);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

/* Toolbar styles */
.library-toolbar {
  display: flex;
  margin-bottom: 20px;
  gap: 15px;
  flex-wrap: wrap;
  justify-content: space-between;
}

.search-bar {
  flex: 1;
  min-width: 200px;
}

.filter-options {
  display: flex;
  gap: 10px;
}

/* Grid layout for model cards */
.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
  flex: 1;
}

/* Model card styles */
.model-card {
  background-color: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
  height: 180px;
}

.model-card.featured {
  border-color: var(--primary-color, #409eff);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.model-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.model-card-content {
  padding: 15px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.model-icon {
  font-size: 2rem;
  margin-bottom: 10px;
  color: var(--primary-color, #409eff);
}

.model-name {
  font-size: 1.1rem;
  margin: 0 0 10px 0;
  color: var(--text-color, #333333);
}

.model-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: auto;
}

/* Hover info styles - hidden by default */
.model-hover-info {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--card-bg, rgba(255, 255, 255, 0.95));
  padding: 15px;
  display: flex;
  flex-direction: column;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  overflow: auto;
}

.model-card:hover .model-hover-info {
  opacity: 1;
  pointer-events: auto;
}

.model-description {
  font-size: 0.9rem;
  margin-bottom: 10px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  color: var(--text-color, #333333);
}

.model-stats {
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 0.85rem;
}

.stat-label {
  color: var(--text-color-secondary, #909399);
}

.stat-value {
  font-weight: bold;
  color: var(--text-color, #333333);
}

.model-actions {
  margin-top: auto;
  display: flex;
  gap: 10px;
}

/* Empty state styles */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-color-secondary, #909399);
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 15px;
}

.empty-state p {
  margin-bottom: 20px;
}

/* Pagination styles */
.pagination-container {
  margin-top: auto;
  display: flex;
  justify-content: flex-end;
  padding-top: 15px;
}

/* Dark theme styles */
.simulation-layout.dark-theme .model-library-panel {
  background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme h2 {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .panel-content {
  background-color: var(--dark-panel-bg, #1a1a1a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .model-card {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme .model-card.featured {
  border-color: var(--primary-color, #409eff);
}

.simulation-layout.dark-theme .model-name {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .model-hover-info {
  background-color: var(--dark-card-bg, rgba(42, 42, 42, 0.95));
}

.simulation-layout.dark-theme .model-description {
  color: var(--dark-text-color, #ffffff);
}
 
.simulation-layout.dark-theme .stat-value {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme .empty-state {
  color: var(--dark-text-color-secondary, #aaaaaa);
}

/* Element UI dark theme compatibility */
.simulation-layout.dark-theme :deep(.el-input__inner) {
  background-color: var(--dark-input-bg, #2a2a2a);
  color: var(--dark-text-color, #ffffff);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-input__wrapper),
.simulation-layout.dark-theme :deep(.el-textarea__wrapper) {
  background-color: var(--dark-input-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
  box-shadow: 0 0 0 1px var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-input__inner),
.simulation-layout.dark-theme :deep(.el-textarea__inner) {
  background-color: var(--dark-input-bg, #2a2a2a);
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown) {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-select-dropdown__item) {
  color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning):not(.el-button--danger)) {
  background-color: var(--dark-card-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
  color: var(--dark-text-color, #ffffff);
}

/* Responsive styles */
@media (max-width: 768px) {
  .library-toolbar {
    flex-direction: column;
  }
  
  .filter-options {
    width: 100%;
  }
  
  .models-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
</style> 