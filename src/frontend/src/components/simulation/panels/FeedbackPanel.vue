<template>
  <div class="feedback-panel">
    <div class="panel-content">
      <div class="tool-bar">
        <div class="action-buttons">
          <!-- <el-button type="primary" @click="handleBatch('Score')" :disabled="selectedRows.length === 0">
            Score By LLMs
          </el-button>
          <el-button type="primary" @click="handleBatch('Feedback')" :disabled="selectedRows.length === 0">
            Response Refinement By LLMs
          </el-button> -->
          <el-button type="success" @click="loadAllData">
            Display all the data
          </el-button>
          <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
            Delete
          </el-button>
          <el-button type="primary" @click="toggleAdvancedSelection">
            Advanced Selection
          </el-button>
        </div>
        
        <div class="filter-bar" :class="{ 'filter-bar-visible': showFilterBar }">
          <div class="search-inputs">
            <el-input
              v-model="agentIdQuery"
              placeholder="Search agent_id..."
              clearable
              @input="handleSearch"
              class="search-input"
            />
            <el-select v-model="agentTypeFilter" placeholder="Filter by agent_type" clearable @change="handleSearch" class="filter-select">
              <el-option 
                v-for="item in agentTypeOptions" 
                :key="item" 
                :label="item" 
                :value="item" 
              />
            </el-select>
            
            <el-select v-model="ratingFilter" placeholder="Filter by Score By LLMs" clearable @change="handleSearch" class="filter-select">
              <el-option 
                v-for="item in ratingOptions" 
                :key="item.value" 
                :label="item.label" 
                :value="item.value" 
              />
            </el-select>
          </div>
        </div>
      </div>
      
      <div class="table-container">
        <div class="table-header-actions">
          <div class="selection-controls">
            <el-checkbox 
              v-model="selectAll" 
              @change="handleSelectAllChange"
              :indeterminate="isIndeterminate">
              Select all
            </el-checkbox>
            <span class="selected-count" v-if="selectedRows.length > 0">
              Selected {{ selectedRows.length }} items
            </span>
          </div>
          
          <div class="random-selection">
            <el-input-number 
              v-model="randomSelectCount" 
              :min="1" 
              :max="maxSelectCount" 
              size="small" 
              placeholder="Random selection count"
            />
            <el-button type="primary" @click="randomSelectData" size="small">Random Select</el-button>
          </div>
        </div>
        
        <el-table
          ref="dataTable"
          :data="paginatedData"
          style="width: 100%"
          border
          stripe
          v-loading="tableLoading"
          @selection-change="handleSelectionChange"
          @select-all="handleSelectAll">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="agent_id" label="Agent ID" width="85" />
          <el-table-column prop="agent_type" label="Agent Type" />
          <el-table-column label="Prompt" min-width="150">
            <template #default="scope">
              <div class="prompt-text" :title="scope.row.prompt">
                {{ truncateText(scope.row.prompt, 100) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="Response" min-width="120">
            <template #default="scope">
              <div class="response-text" :title="scope.row.output">
                {{ truncateText(scope.row.output, 100) }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="Score By LLMs" width="160">
            <template #default="scope">
              <el-rate
                v-model="scope.row.rating"
                :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                disabled
              />
            </template>
          </el-table-column>
          <el-table-column label="Response Refinement By LLMs"min-width="120">
            <template #default="scope">
              <div v-if="scope.row.feedback" class="feedback-text">
                {{ truncateText(scope.row.feedback, 50) }}
              </div>
              <div v-else>-</div>
            </template>
          </el-table-column>
          <el-table-column label="Actions" width="240" fixed="right">
            <template #default="scope">
              <div class="action-buttons-cell">
                <el-button size="small" type="primary" @click="Details(scope.row)">
                  Detail
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(scope.row)">
                  Delete
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :current-page="currentPage"
            :page-sizes="[10, 20, 50, 100]"
            :page-size="pageSize"
            layout="total, sizes, prev, pager, next"
            :total="filteredData.length"
          />
        </div>
        <div class="action-buttons-bototm">
          <el-button type="primary" @click="handleBatch('Score')" :disabled="selectedRows.length === 0">
            Score By LLMs
          </el-button>
          <el-button type="primary" @click="handleBatch('Feedback')" :disabled="selectedRows.length === 0">
            Response Refinement By LLMs
          </el-button>
          <el-button type="primary" @click="finish()">
            Finish
          </el-button>
          <!-- <el-button type="danger" @click="handleBatchDelete" :disabled="selectedRows.length === 0">
            Delete
          </el-button>
          <el-button type="success" @click="loadAllData">
            All Data
          </el-button> -->
        </div>
      </div>
    </div>
    
    <!-- Feedback Dialog -->
    <el-dialog
      v-model="feedbackDialogVisible"
      title="Add Feedback"
      width="50%">
      <el-form :model="feedbackForm">
        <el-form-item label="Feedback Content">
          <el-input
            v-model="feedbackForm.feedback"
            type="textarea"
            :rows="4"
            placeholder="Please enter your feedback..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="feedbackDialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="submitFeedback">Submit</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- Batch Rating Dialog -->
    <el-dialog
      v-model="batchScoreDialogVisible"
      :title="feedbackForm.row ? 'Add Rating' : 'Batch Rating'"
      width="50%">
      <el-form :model="batchScoreForm">
        <el-form-item label="Rating">
          <el-rate
            v-model="batchScoreForm.rating"
            :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchScoreDialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="submitBatchScore">Submit</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- Batch Feedback Dialog -->
    <el-dialog
      v-model="batchFeedbackDialogVisible"
      :title="batchFeedbackTitle"
      width="50%">
      <el-form :model="batchFeedbackForm" class="batch-feedback-form">
        <el-form-item label="Select Model">
          <el-select v-model="batchFeedbackForm.selectedModel" placeholder="Please select model" :disabled="batchSubmitting">
            <el-option 
              v-for="val in modelOptions" 
              :key="val" 
              :label="val" 
              :value="val" 
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <div class="selected-info">
            Selected {{ batchFeedbackForm.selectedData.length }} items for {{ batchFeedbackTitle }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeBatchFeedbackDialog" :disabled="batchSubmitting">Cancel</el-button>
          <el-button type="primary" @click="submitBatchFeedback" :loading="batchSubmitting" :disabled="!batchFeedbackForm.selectedModel || batchSubmitting">Submit</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- Details Dialog -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="Feedback Details"
      width="60%">
      <el-form class="details-form" :model="detailsForm" label-width="200px">
        <el-form-item label="Prompt">
          <div class="details-text-area">
            <pre>{{ detailsForm.prompt }}</pre>
          </div>
        </el-form-item>
        <el-form-item label="Response">
          <div class="details-text-area">
            <pre>{{ detailsForm.output }}</pre>
          </div>
        </el-form-item>
        <el-form-item label="Response Refinement By LLMs">
          <el-input
            v-model="detailsForm.feedback"
            type="textarea"
            :rows="4"
            placeholder="Please enter the feedback content..."
          />
        </el-form-item>
        <el-form-item label="Score By LLMs">
          <el-rate
            v-model="detailsForm.rating"
            :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">  
          <el-button @click="closeDetailsDialog">Cancel</el-button>
          <el-button type="primary" @click="saveDetails">Save</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios';
import { useGameStore } from '../../../stores/gameStore';

export default {
  name: 'FeedbackPanel',
  data() {
    return {
      // Table data
      tableData: [],
      tableLoading: false,
      
      // Selected rows
      selectedRows: [],
      selectAll: false,
      selectedAll: false,
      isIndeterminate: false,
      
      // Filtering and search
      showFilterBar: false,
      agentIdQuery: '',
      promptQuery: '',
      outputQuery: '',
      agentTypeFilter: null,
      ratingFilter: null,
      
      // Random selection
      randomSelectCount: 5,
      
      // Pagination
      currentPage: 1,
      pageSize: 10,
      
      // Dialogs
      feedbackDialogVisible: false,
      batchScoreDialogVisible: false,
      batchFeedbackDialogVisible: false,
      detailsDialogVisible: false,
      batchFeedbackTitle:'Batch Refinement',
      
      // Form data
      feedbackForm: {
        feedback: '',
        row: null
      },
      batchScoreForm: {
        rating: 0
      },
      batchFeedbackForm: {
        selectedModel: '',
        selectedData: []
      },
      detailsForm: {
        prompt: '',
        output: '',
        feedback: '',
        rating: 0,
        row: null
      },
      
      // Operated data
      operatedData: [],
      
      // Show only operated data
      showOnlyOperated: false,
      
      // Rating options
      ratingOptions: [
        { value: 1, label: '1 Star' },
        { value: 2, label: '2 Stars' },
        { value: 3, label: '3 Stars' },
        { value: 4, label: '4 Stars' },
        { value: 5, label: '5 Stars' },
        { value: null, label: 'Not Rated' }
      ],
      handleBatchType:'',
      batchSubmitting: false,
    }
  },
  computed: {
    // Data filtered by conditions
    filteredData() {
      // 首先应用条件过滤
      let result;
      if (this.showOnlyOperated) {
        // 当显示已操作数据时，确保operatedData中的数据是最新的
        const updatedOperatedData = [];
        
        // 遍历所有操作过的数据
        this.operatedData.forEach(operatedItem => {
          // 查找最新数据
          const latestItem = this.tableData.find(item => item.decision_id === operatedItem.decision_id);
          if (latestItem) {
            // 使用最新的tableData中的数据
            updatedOperatedData.push({...latestItem});
          } else {
            // 如果在tableData中找不到，使用原始操作数据
            updatedOperatedData.push({...operatedItem});
          }
        });
        
        // 应用过滤条件
        result = this.filterByConditions(updatedOperatedData);
      } else {
        result = this.filterByConditions(this.tableData);
      }
      
      // 最后返回过滤后的结果
      return result;
    },
    
    // Current page data
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.filteredData.slice(start, end);
    },
    
    // agent_type options
    agentTypeOptions() {
      // Extract unique agent_type values from data
      const types = new Set();
      this.tableData.forEach(item => {
        if (item.agent_type) {
          types.add(item.agent_type);
        }
      });
      return Array.from(types);
    },
    
    // Ensure max value is always greater than or equal to min value, to avoid Element Plus warnings
    maxSelectCount() {
      return Math.max(this.tableData.length, 1);
    },
    
    // 获取gameStore
    gameStore() {
      return useGameStore();
    },
    
    // 获取模型列表
    modelOptions() {
      const chatModels = this.gameStore.systemConfig?.model?.chat || {};
      return chatModels;
    }
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    // 切换高级筛选栏的显示/隐藏
    toggleAdvancedSelection() {
      this.showFilterBar = !this.showFilterBar;
    },
    finish(){
      axios.post('/api/feedback/save',{
        env_name:localStorage.getItem('scenarioName'),
      }).then(response => {
        console.log(response.data);
        this.$message.success(response.data.file_path);
      });
    },
    // 获取反馈数据
    getFeedBack() {
      this.tableLoading = true;

      axios.get('/api/feedback/decisions?env_name='+localStorage.getItem('scenarioName'))
      .then(response => {
        console.log(response.data);
        this.tableData = Array.isArray(response.data.data) ? response.data.data : [];
        
        // 更新operatedData中的数据，保持与最新数据一致
        if (this.operatedData.length > 0) {
          // 创建新的operatedData数组
          const newOperatedData = [];
          
          // 遍历所有被标记为已操作的数据
          this.operatedData.forEach(operatedItem => {
            // 查找最新数据
            const latestItem = this.tableData.find(item => item.decision_id === operatedItem.decision_id);
            if (latestItem) {
              // 如果找到对应数据，使用最新数据
              newOperatedData.push({...latestItem});
            } else {
              // 如果找不到，保留原有数据
              newOperatedData.push({...operatedItem});
            }
          });
          
          // 替换operatedData
          this.operatedData = newOperatedData;
        }
        
        this.tableLoading = false;
      })
      .catch(error => {
        console.error('Error fetching feedback data:', error);
        // 确保发生错误时也将tableData设置为空数组
        this.tableData = [];
        this.tableLoading = false;
      });
    },
    fetchData() {
      this.getFeedBack();
    },
    Details(data){
      this.detailsForm = {
        prompt: data.prompt || '',
        output: data.output || '',
        feedback: data.feedback || '',
        rating: data.rating || 0,
        row: data
      };
      this.detailsDialogVisible = true;
    },
    closeDetailsDialog() {
      this.detailsDialogVisible = false;
      this.detailsForm = {
        prompt: '',
        output: '',
        feedback: '',
        rating: 0,
        row: null
      };
    },
    /*
     * 保存详情
     */
    saveDetails() {
      if (!this.detailsForm.row) {
        this.$message.warning('Data abnormal, please try again');
        return;
      }
      
      // 更新行数据
      this.detailsForm.row.feedback = this.detailsForm.feedback;
      this.detailsForm.row.rating = this.detailsForm.rating;
      
      // 清空之前的操作记录，只记录本次修改的数据
      this.operatedData = [];
      // 记录操作过的数据
      this.markAsOperated(this.detailsForm.row);
      let arr = [];
      arr.push(this.detailsForm.row);
      // 更新服务器数据（这里应该是实际的API调用）
      axios.post('/api/feedback/update',{
        env_name:localStorage.getItem('scenarioName'),
        updated_data:arr
      })
      .then(response => {
        this.$message.success('Saved successfully');
        this.detailsDialogVisible = false;
        
        // 更新表格中对应的数据
        const index = this.tableData.findIndex(item => item.decision_id === this.detailsForm.row.decision_id);
        if (index !== -1) {
          this.tableData[index] = {...this.detailsForm.row};
        }
        
        // 切换到仅显示操作过的数据
        this.showOnlyOperated = true;
      })
      .catch(error => {
        console.error('Error updating feedback data:', error);
      });
    },
    // 随机选择数据
    randomSelectData() {
      // 清空表格选择状态
      this.$refs.dataTable.clearSelection();
      
      // 清空selectedRows数组
      this.selectedRows = [];
      
      if (this.randomSelectCount > this.tableData.length) {
        this.randomSelectCount = this.tableData.length || 1;
      }
      
      // 如果没有数据，不进行随机选择
      if (this.tableData.length === 0) {
        this.$message.warning('No data available for selection');
        return;
      }
      
      // 获取随机索引
      const indices = new Set();
      while (indices.size < this.randomSelectCount) {
        const randomIndex = Math.floor(Math.random() * this.tableData.length);
        indices.add(randomIndex);
      }
      
      // 临时存储随机选中的所有行
      const randomSelectedRows = [];
      
      // 选择随机行
      indices.forEach(index => {
        const row = this.tableData[index];
        randomSelectedRows.push(row);
        
        // 如果行在当前页，使用表格的选择功能
        if (this.paginatedData.includes(row)) {
          this.$refs.dataTable.toggleRowSelection(row, true);
        }
      });
      
      // 统一设置selectedRows，避免handleSelectionChange方法覆盖
      this.selectedRows = randomSelectedRows;
    },
    
    // 根据条件过滤数据
    filterByConditions(data) {
      return data.filter(item => {
        const matchesAgentId = !this.agentIdQuery || 
          (item.agent_id && item.agent_id.toString().includes(this.agentIdQuery));
          
        const matchesPrompt = !this.promptQuery || 
          (item.prompt && item.prompt.toLowerCase().includes(this.promptQuery.toLowerCase()));
          
        const matchesOutput = !this.outputQuery || 
          (item.output && item.output.toLowerCase().includes(this.outputQuery.toLowerCase()));
          
        const matchesAgentType = !this.agentTypeFilter || item.agent_type === this.agentTypeFilter;
        
        // 修改评分筛选逻辑，更精确地处理null和undefined情况
        const matchesRating = this.ratingFilter === undefined || this.ratingFilter === null || 
          (this.ratingFilter === null ? item.rating === null || item.rating === undefined : 
           item.rating === this.ratingFilter);
        
        return matchesAgentId && matchesPrompt && matchesOutput && matchesAgentType && matchesRating;
      });
    },
    
    // 处理搜索
    handleSearch() {
      this.currentPage = 1;
    },
    
    // 处理分页
    handleSizeChange(size) {
      this.pageSize = size;
      
      // 如果处于全选状态，设置当前页的选中状态
      if (this.selectedAll) {
        this.$nextTick(() => {
          this.paginatedData.forEach(row => {
            this.$refs.dataTable.toggleRowSelection(row, true);
          });
        });
      }
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      
      // 如果处于全选状态，设置当前页的选中状态
      if (this.selectedAll) {
        this.$nextTick(() => {
          this.paginatedData.forEach(row => {
            this.$refs.dataTable.toggleRowSelection(row, true);
          });
        });
      }
    },
    
    // 处理选中变化
    handleSelectionChange(selection) {
      if (this.selectedAll) {
        // 如果是全选状态，只更新表格视觉上的选择，不改变selectedRows
        return;
      }
      
      // 正常选择处理
      this.selectedRows = selection;
      this.isIndeterminate = selection.length > 0 && selection.length < this.paginatedData.length;
      this.selectAll = selection.length === this.paginatedData.length && this.paginatedData.length > 0;
    },
    
    // 处理全选
    handleSelectAll(selection) {
      if (selection.length === this.paginatedData.length) {
        // 点击全选当前页，实际选中所有数据
        this.selectedAll = true;
        this.selectAll = true;
        this.selectedRows = [...this.filteredData]; // 选中所有过滤后的数据
      } else {
        // 取消全选
        this.selectedAll = false;
        this.selectAll = false;
        this.selectedRows = [];
      }
    },
    
    // 全选/取消全选 checkbox点击事件
    handleSelectAllChange(val) {
      this.selectAll = val;
      if (val) {
        this.selectedAll = true;
        // 选择所有过滤后的数据
        this.selectedRows = [...this.filteredData];
        
        // 对于当前页的数据，使用表格的选择功能
        this.$refs.dataTable.clearSelection();
        this.paginatedData.forEach(row => {
          this.$refs.dataTable.toggleRowSelection(row, true);
        });
      } else {
        this.selectedAll = false;
        this.$refs.dataTable.clearSelection();
        this.selectedRows = [];
      }
    },
    
    // 打开反馈弹窗
    handleFeedback(row) {
      this.feedbackForm.row = row;
      this.feedbackForm.feedback = row.feedback || '';
      this.feedbackDialogVisible = true;
    },
    
    // Submit feedback
    submitFeedback() {
      if (!this.feedbackForm.feedback) {
        this.$message.warning('Please enter feedback content');
        return;
      }
      
      // 更新行数据
      this.feedbackForm.row.feedback = this.feedbackForm.feedback;
      
      // 记录操作过的数据
      this.markAsOperated(this.feedbackForm.row);
      
      // Update server data (this should be an actual API call)
      // this.updateData(this.feedbackForm.row);
      
      this.$message.success('Feedback submitted');
      this.feedbackDialogVisible = false;
      
      // 切换到仅显示操作过的数据
      this.showOnlyOperated = true;
    },
    
    // 评分
    handleRatingChange(row) {
      // 打开评分弹窗
      this.batchScoreForm.rating = row.rating || 0;
      this.feedbackForm.row = row;
      this.batchScoreDialogVisible = true;
    },
    
    
    // 提交评分
    submitBatchScore() {
      // 更新所有选中的行评分
      if (this.feedbackForm.row) {
        // 单行评分
        this.feedbackForm.row.rating = this.batchScoreForm.rating;
        this.markAsOperated(this.feedbackForm.row);
        this.$message.success('Rating submitted');
      } else {
        // 批量评分
        this.selectedRows.forEach(row => {
          row.rating = this.batchScoreForm.rating;
          this.markAsOperated(row);
        });
        this.$message.success(`Rated ${this.selectedRows.length} records`);
      }
      
      // Update server data (this should be an actual API call)
      // this.updateBatchData(this.selectedRows);
      
      this.batchScoreDialogVisible = false;
      this.feedbackForm.row = null;
      
      // Switch to show only operated data
      this.showOnlyOperated = true;
    },
    
    // 删除
    handleDelete(row) {
      this.$confirm('Are you sure you want to delete this record?', 'Warning', {
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        // 从tableData和operatedData中删除
        this.tableData = this.tableData.filter(item => item.decision_id !== row.decision_id);
        this.operatedData = this.operatedData.filter(item => item.decision_id !== row.decision_id);
        
        // 更新服务器数据（这里应该是实际的API调用）
        // this.deleteData(row);
        
        this.$message.success('Successfully deleted');
      }).catch(() => {
        this.$message.info('Delete cancelled');
      });
    },
    
    // 批量操作
    handleBatch(type) {
      if(type === 'Feedback'){
        this.batchFeedbackTitle = 'Batch Refinement';
      }else{
        this.batchFeedbackTitle = 'Batch Rating';
      }
      this.handleBatchType = type;
      if (this.selectedRows.length === 0) {
        this.$message.warning('Please select at least one record');
        return;
      }
      
      // 记录操作前的所有选中数据状态
      const selectedDataSnapshot = JSON.parse(JSON.stringify(this.selectedRows));
      
      // 将选中的数据组成数组
      this.batchFeedbackForm.selectedData = selectedDataSnapshot;
      
      // 保存操作前的数据以便后续对比变化
      this.batchFeedbackForm.selectedData.forEach(item => {
        // 添加原始数据标记
        item._originalState = true;
      });
      
      // 打开弹窗
      this.batchFeedbackDialogVisible = true;
    },
    
    // 关闭批量反馈弹窗
    closeBatchFeedbackDialog() {
      if (this.batchSubmitting) {
        return; // 如果正在提交，不允许关闭
      }
      
      this.batchFeedbackDialogVisible = false;
      this.batchFeedbackForm = {
        selectedModel: '',
        selectedData: []
      };
      this.batchSubmitting = false;
      this.tableLoading = false;
    },
    
    // 提交批量操作
    submitBatchFeedback() {
      if (!this.batchFeedbackForm.selectedModel) {
        this.$emit('show-message', {
          message: 'Please select a model',
          type: 'warning'
        });
        return;
      }
      
      // 保存选中的数据作为提交记录
      const submittedData = [...this.batchFeedbackForm.selectedData];
      // 保存提交数据的ID列表，用于后续对比变化
      const submittedIds = submittedData.map(item => item.decision_id);
      
      // 立即关闭弹窗并设置加载状态
      this.batchFeedbackDialogVisible = false;
      this.tableLoading = true;
      this.batchSubmitting = true;
      
      // 显示全屏loading
      const loadingInstance = this.$loading({
        lock: true,
        text: '正在处理数据，请稍候...',
        background: 'rgba(0, 0, 0, 0.7)'
      });
      
      // 清空之前的操作记录，只记录本次修改的数据
      this.operatedData = [];
      
      // 调用接口
      if(this.handleBatchType === 'Feedback'){
        axios.post('/api/feedback/refine', {
          env_name: localStorage.getItem('scenarioName'),
          model_name: this.batchFeedbackForm.selectedModel,
          selected_data: submittedData
        })
        .then(response => {
          // 获取API返回的所有数据
          const allReturnedData = response.data.data || [];
          
          // 如果返回了完整数据，则直接替换表格数据
          if (allReturnedData.length > 0) {
            this.tableData = allReturnedData;
          }
          
          // 记录变更的数据数量
          let changedCount = 0;
          let unchangedCount = 0;
          let notFoundCount = 0;
          
          // 找出本次提交的数据在返回结果中的对应项
          const updatedItems = [];
          
          // 对每个提交的数据，在返回结果中找对应项
          submittedData.forEach(submittedItem => {
            const itemId = submittedItem.decision_id;
            const returnedItem = allReturnedData.find(item => item.decision_id === itemId);
            
            if (returnedItem) {
              updatedItems.push(returnedItem);
              
              // 检查数据是否有变化（主要检查feedback字段）
              const hasChanged = (
                (!submittedItem.feedback && returnedItem.feedback) || 
                (submittedItem.feedback !== returnedItem.feedback)
              );
              
              if (hasChanged) {
                changedCount++;
                // 只标记有变化的数据为已操作
                this.markAsOperated(returnedItem);
              } else {
                unchangedCount++;
              }
            } else {
              notFoundCount++;
              console.warn(`Submitted data ID:${itemId} not found in results`);
            }
          });
          
          // 清除表格选择状态
          if (this.$refs.dataTable) {
            this.$refs.dataTable.clearSelection();
          }
          this.selectedRows = [];
          this.selectAll = false;
          this.selectedAll = false;
          
          // 只展示修改后的数据
          this.showOnlyOperated = true;
          
          // 确保显示最新的已操作数据
          this.$nextTick(() => {
            // 重新应用过滤条件
            this.handleSearch();
          });
          
          // 显示详细的操作结果
          if (notFoundCount > 0) {
            this.$emit('show-message', {
              message: `Submitted ${submittedData.length} items, ${changedCount} with content changes, ${unchangedCount} unchanged, ${notFoundCount} not found in results`,
              type: 'warning'
            });
          } else if (changedCount === 0) {
            this.$emit('show-message', {
              message: `Processed ${updatedItems.length} items, but no content changes`,
              type: 'info'
            });
          } else {
            this.$emit('show-message', {
              message: `Processed ${updatedItems.length} items, ${changedCount} with content changes, ${updatedItems.length - changedCount} unchanged`,
              type: 'success'
            });
          }
          
          // 重置表单数据
          this.batchFeedbackForm = {
            selectedModel: '',
            selectedData: []
          };
          this.tableLoading = false;
          this.batchSubmitting = false;
          
          // 关闭loading
          loadingInstance.close();
        })
        .catch(error => {
          console.error('Error refining feedback data:', error);
          this.$emit('show-message', {
            message: 'Data optimization failed: ' + (error.response?.data?.message || error.message),
            type: 'error'
          });
          this.tableLoading = false;
          this.batchSubmitting = false;
          // 关闭loading
          loadingInstance.close();
        });
      }else if(this.handleBatchType === 'Score'){
        axios.post('/api/feedback/rate', {
          env_name: localStorage.getItem('scenarioName'),
          model_name: this.batchFeedbackForm.selectedModel,
          selected_data: submittedData
        })
        .then(response => {
          // 获取API返回的所有数据
          const allReturnedData = response.data.data || [];
          
          // 如果返回了完整数据，则直接替换表格数据
          if (allReturnedData.length > 0) {
            this.tableData = allReturnedData;
          }
          
          // 记录变更的数据数量
          let changedCount = 0;
          let unchangedCount = 0;
          let notFoundCount = 0;
          
          // 找出本次提交的数据在返回结果中的对应项
          const updatedItems = [];
          
          // 对每个提交的数据，在返回结果中找对应项
          submittedData.forEach(submittedItem => {
            const itemId = submittedItem.decision_id;
            const returnedItem = allReturnedData.find(item => item.decision_id === itemId);
            
            if (returnedItem) {
              updatedItems.push(returnedItem);
              
              // 检查数据是否有变化（主要检查rating字段）
              const hasChanged = submittedItem.rating !== returnedItem.rating;
              
              if (hasChanged) {
                changedCount++;
                // 只标记有变化的数据为已操作
                this.markAsOperated(returnedItem);
              } else {
                unchangedCount++;
              }
            } else {
              notFoundCount++;
              console.warn(`Submitted data ID:${itemId} not found in results`);
            }
          });
          
          // 清除表格选择状态
          if (this.$refs.dataTable) {
            this.$refs.dataTable.clearSelection();
          }
          this.selectedRows = [];
          this.selectAll = false;
          this.selectedAll = false;
          
          // 只展示修改后的数据
          this.showOnlyOperated = true;
          
          // 确保显示最新的已操作数据
          this.$nextTick(() => {
            // 重新应用过滤条件
            this.handleSearch();
          });
          
          // 显示详细的操作结果
          if (notFoundCount > 0) {
            this.$emit('show-message', {
              message: `Submitted ${submittedData.length} items, ${changedCount} with rating changes, ${unchangedCount} unchanged, ${notFoundCount} not found in results`,
              type: 'warning'
            });
          } else if (changedCount === 0) {
            this.$emit('show-message', {
              message: `Processed ${updatedItems.length} items, but no rating changes`,
              type: 'info'
            });
          } else {
            this.$emit('show-message', {
              message: `Processed ${updatedItems.length} items, ${changedCount} with rating changes, ${updatedItems.length - changedCount} unchanged`,
              type: 'success'
            });
          }
          
          // 重置表单数据
          this.batchFeedbackForm = {
            selectedModel: '',
            selectedData: []
          };
          this.tableLoading = false;
          this.batchSubmitting = false;
          
          // 关闭loading
          loadingInstance.close();
        })
        .catch(error => {
          console.error('Error refining score data:', error);
          this.$emit('show-message', {
            message: 'Rating data failed: ' + (error.response?.data?.message || error.message),
            type: 'error'
          });
          this.tableLoading = false;
          this.batchSubmitting = false;
          // 关闭loading
          loadingInstance.close();
        });
      }
    },
    
    // 批量删除
    handleBatchDelete() {
      if (this.selectedRows.length === 0) {
        this.$message.warning('Please select at least one record');
        return;
      }
      
      this.$confirm(`Are you sure you want to delete the selected ${this.selectedRows.length} records?`, 'Warning', {
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        // 获取所有选中的行ID
        const selectedIds = this.selectedRows.map(row => row.decision_id);
        
        // 从tableData和operatedData中删除
        this.tableData = this.tableData.filter(item => !selectedIds.includes(item.decision_id));
        this.operatedData = this.operatedData.filter(item => !selectedIds.includes(item.decision_id));
        
        // 更新服务器数据（这里应该是实际的API调用）
        // this.deleteBatchData(selectedIds);
        
        this.$message.success(`Deleted ${this.selectedRows.length} records`);
        this.selectedRows = [];
      }).catch(() => {
        this.$message.info('Delete cancelled');
      });
    },
    
    // 加载所有数据
    loadAllData() {
      this.showOnlyOperated = false;
      this.currentPage = 1;
      this.tableLoading = true;
      
      // 重新从服务器获取最新数据
      this.getFeedBack();
      this.$message.success('Loading all latest data');
    },
    
    // 标记为操作过
    markAsOperated(row) {
      // 检查是否已经在操作过的列表中
      const exists = this.operatedData.some(item => item.decision_id === row.decision_id);
      if (!exists) {
        this.operatedData.push(JSON.parse(JSON.stringify(row)));
      } else {
        // 更新已存在的数据
        const index = this.operatedData.findIndex(item => item.decision_id === row.decision_id);
        if (index !== -1) {
          this.operatedData[index] = JSON.parse(JSON.stringify(row));
        }
      }
    },
    
    // 截断文本
    truncateText(text, maxLength) {
      if (!text) return '';
      if (text.length <= maxLength) return text;
      return text.substring(0, maxLength) + '...';
    }
  }
}
</script>

<style scoped>
.feedback-panel {
  padding: 20px;
  height: 100%;
  background-color: var(--panel-bg, #ffffff);
  transition: all 0.3s ease;
}

.panel-content {
  height: 100%;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  padding: 15px;
  background-color: var(--panel-bg, #f8f8f8);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

/* 工具栏样式 */
.tool-bar {
  /* margin-bottom: 15px; */
  display: flex;
  flex-wrap: wrap;
  /* gap: 10px; */
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-buttons-bototm{
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: all 1s ease;
}

.filter-bar-visible {
  max-height: 500px;
  opacity: 1;
  margin-top: 15px;
  margin-bottom: 10px;
}

.search-inputs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-selects {
  display: flex;
  gap: 10px;
}

.search-input {
  min-width: 180px;
  flex: 1;
}

.filter-select {
  min-width: 180px;
  flex: 1;
}

/* 表格容器 */
.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.selection-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.selected-count {
  color: var(--primary-color, #409EFF);
  font-weight: 500;
}

.random-selection {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 操作按钮单元格样式 */
.action-buttons-cell {
  display: flex;
  gap: 5px;
  flex-wrap: nowrap;
  /* justify-content: space-between; */
  align-items: center;
  height: 100%;
}

/* 表格内容样式 */
.prompt-text, .response-text, .feedback-text {
  max-height: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  word-break: break-word;
}

/* 分页容器 */
.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

/* Element Plus 组件样式覆盖 */
:deep(.el-table) {
  --el-table-border-color: var(--border-color, #e0e0e0);
  --el-table-header-bg-color: var(--card-bg, #f5f7fa);
  --el-table-row-hover-bg-color: var(--hover-bg, #f5f7fa);
  --el-table-bg-color: var(--card-bg, #ffffff);
  flex: 1;
  overflow: auto;
}

:deep(.el-table__header-wrapper) {
  background-color: var(--bg-color, #f5f7fa);
}

:deep(.el-input__wrapper),
:deep(.el-textarea__wrapper) {
  background-color: var(--input-bg, #ffffff);
  box-shadow: 0 0 0 1px var(--border-color, #e0e0e0);
}

/* 修复选中样式 */
:deep(.el-table-column--selection .el-checkbox) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--primary-color, #409EFF);
  border-color: var(--primary-color, #409EFF);
}

:deep(.el-table__row.current-row td) {
  background-color: var(--hover-bg, #ecf5ff);
}

/* 暗色模式适配 */
.simulation-layout.dark-theme .feedback-panel {
  background-color: var(--dark-panel-bg, #1a1a1a);
}

.simulation-layout.dark-theme .panel-content {
  background-color: var(--dark-panel-bg, #1a1a1a);
  border-color: var(--dark-border-color, #333333);
}

.simulation-layout.dark-theme :deep(.el-table) {
  --el-table-border-color: var(--dark-border-color, #333333);
  --el-table-header-bg-color: var(--dark-card-bg, #1e1e1e);
  --el-table-row-hover-bg-color: var(--dark-hover-bg, #2c2c2c);
  --el-table-bg-color: var(--dark-card-bg, #1a1a1a);
  --el-table-text-color: var(--dark-text-color, #ffffff);
  --el-table-header-text-color: var(--dark-text-color, #ffffff);
}

.simulation-layout.dark-theme :deep(.el-table__header-wrapper) {
  background-color: var(--dark-bg-color, #1e1e1e);
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

.simulation-layout.dark-theme :deep(.el-table__row.current-row td) {
  background-color: var(--dark-hover-bg, #283142);
}

/* 响应式样式 */
@media (max-width: 768px) {
  .tool-bar {
    flex-direction: column;
  }
  
  .filter-bar, .filter-selects, .search-inputs {
    flex-direction: column;
  }
  
  .search-input, .filter-select {
    width: 100%;
  }
  
  .table-header-actions {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .random-selection {
    margin-top: 10px;
    width: 100%;
  }
}

/* 详情对话框样式 */
.details-text-area {
  background-color: var(--input-bg, #f5f7fa);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 4px;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.details-text-area pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-family: inherit;
}

/* 暗色模式适配 */
.simulation-layout.dark-theme .details-text-area {
  background-color: var(--dark-input-bg, #2a2a2a);
  border-color: var(--dark-border-color, #333333);
  color: var(--dark-text-color, #ffffff);
}
.batch-feedback-form{
  margin-top: 20px;
}
.details-form{
  margin-top: 20px;
}
</style> 