<template>
  <div class="agent-config-container">
    <h2 class="page-title">Agent Properties Configuration</h2>
    <p class="page-description">
      Configure properties for each agent type in your simulation. These settings
      determine agent behaviors and interactions.
    </p>

    <div class="config-content">
      <div class="agent-list-panel" v-loading="isLoading">
        <div class="panel-header">
          <div class="title-section">
            <h3>Agent Types</h3>
          </div>
          <div class="search-box">
            <input type="text" v-model="searchQuery" placeholder="Search agent types..." @input="filterAgentTypes" />
            <i class="fa fa-search"></i>
          </div>
        </div>

        <div class="agent-grid">
          <div v-for="(agentType, index) in filteredAgentTypes" :key="index" class="agent-card"
            :class="{ selected: currentAgentType === agentType.type }" @click="selectAgentType(agentType)">
            <div class="agent-card-top">
              <div class="agent-name">{{ agentType }}</div>
            </div>
            <div class="agent-card-bottom">
              <div class="agent-actions">
                <span class="property-count">{{ getPropertyCount(agentType) }} properties</span>
              </div>
              <div class="agent-count">
                <span>Count: {{ agentCounts[agentType] || getDefaultCount(agentType) }}</span>
              </div>
            </div>
          </div>

          <div v-if="filteredAgentTypes.length === 0" class="no-results">
            No agent types found. Try a different search.
          </div>
        </div>
      </div>

      <div class="properties-panel" v-if="currentAgentType">
        <div class="panel-header">
          <div class="header-left">
            <div class="title-section">
              <h3>{{ currentAgentType }} Properties</h3>
            </div>
            <div class="count-editor">
              <label>Population Size:</label>
              <div style="display: flex; align-items: flex-end; gap: 8px">
                <el-input v-model.number="currentAgentCount" type="number" min="1" @blur="addPopulationPreset" style="width: 180px"  />
                <!-- <button @click="showAddModal = true" class="count-btn">Add</button> -->
              </div>
            </div>
          </div>
          <div class="header-right">
            <div class="agent-type-selector">
              <!-- <el-select v-model="selectedAgentType" placeholder="Select Agent Type"
                style="width: 200px; margin-right: 10px">
                <el-option v-for="type in agentTypes" :key="type" :label="type" :value="type"></el-option>
              </el-select> -->
              <button class="add-agent-btn" @click="showAddAgentModalOpen()">
                Add Field
              </button>
            </div>
            <div class="search-box">
              <input type="text" v-model="propertySearchQuery" placeholder="Search properties..."
                @input="filterAgentProperties" />
              <i class="fa fa-search"></i>
            </div>
          </div>
        </div>

        <div class="properties-grid">
          <div v-for="(property, propName) in filteredProperties" :key="propName" class="property-card"
            @click="editProperty(propName, property)">
            <div class="property-header">
              <div class="property-name">{{ propName }}</div>
              <div class="property-type">{{ property.type }}</div>
            </div>
            <div class="property-details">
              <div class="property-description" v-if="property.description">
                {{ property.description }}
              </div>
              <div class="property-attributes">
                <span class="property-attribute" v-if="property.default !== undefined">
                  Default: {{ displayValue(property.default) }}
                </span>
                <span class="property-attribute" v-if="property.private !== undefined">
                  {{ property.private ? "Private" : "Public" }}
                </span>
                <span class="property-attribute" v-if="property.sampling">
                  Sampling: {{ property.sampling }}
                </span>
              </div>
              <div class="property-constraints" v-if="hasConstraints(property)">
                <span class="constraint" v-if="property.choices">
                  Options: {{ property.choices.join(", ") }}
                </span>
                <span class="constraint" v-if="property.range">
                  Range: {{ property.range.join(" - ") }}
                </span>
              </div>
            </div>
            <div class="property-actions">
              <button class="action-btn edit" v-if="propName != 'name' && propName != 'id'"
                @click.stop="editProperty(propName, property)">
                <i class="fa fa-edit"></i>
              </button>
              <button class="action-btn delete" v-if="propName != 'name' && propName != 'id'"
                @click.stop="deleteProperty(propName)">
                <i class="fa fa-trash"></i>
              </button>
            </div>
          </div>

          <div v-if="Object.keys(filteredProperties).length === 0" class="no-results">
            No properties found. Try a different search.
          </div>
        </div>
      </div>

      <div class="empty-state" v-else>
        <div class="empty-state-content">
          <i class="fa fa-info-circle"></i>
          <h3>Select an Agent Type</h3>
          <p>Choose an agent type from the list to view and edit its properties.</p>
        </div>
      </div>

      <div class="loading-overlay" v-if="isLoading">
        <div class="spinner"></div>
        <div class="loading-text">Loading agent properties...</div>
        <TipsCarousel />
      </div>
    </div>

    <div class="action-buttons">
      <button class="next-btn" @click="goToNextStep">
        Proceed to Simulation <i class="fa fa-arrow-right"></i>
      </button>
    </div>

    <!-- Property Edit Modal -->
    <div class="modal-overlay" v-if="showPropertyModal" @click.self="cancelPropertyEdit">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Edit {{ currentPropertyName }}</h3>
          <button class="close-btn" @click="cancelPropertyEdit">
            <i class="fa fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="property-info">
            <div class="property-type-badge">{{ currentProperty.type }}</div>
            <div class="property-description" v-if="currentProperty.description">
              {{ currentProperty.description }}
            </div>
          </div>
          <form @submit.prevent="savePropertyChanges">
            <!-- Different inputs based on property type -->
            <!-- String type -->
            <div class="form-group" v-if="currentProperty.type === 'str'">
              <label :for="currentPropertyName">Default</label>
              <el-select v-if="currentProperty.choices" v-model="editedValue" placeholder="Select value"
                class="full-width">
                <el-option v-for="choice in currentProperty.choices" :key="choice" :label="choice" :value="choice">
                </el-option>
              </el-select>
              <input v-else :id="currentPropertyName" type="text" v-model="editedValue" placeholder="Enter value" />
            </div>
            <!-- List type -->
            <div class="form-group" v-else-if="currentProperty.type === 'list'">
              <label :for="currentPropertyName">{{
                currentProperty.choices ? "Choices" : "Default"
                }}</label>
              <div class="list-editor">
                <div class="list-items">
                  <div v-for="(item, index) in editedListValues" :key="index" class="list-item">
                    <input type="text" v-model="editedListValues[index]" placeholder="Enter value" class="list-input"
                      @blur="validateListItem(index)" :class="{ 'invalid-input': invalidInputs[index] }" />
                    <button type="button" class="list-remove-btn" @click="removeListItem(index)">
                      <i class="fa fa-trash"></i>
                    </button>
                  </div>
                  <div v-if="hasInvalidInput" class="validation-error">
                    所有列表项不能为空
                  </div>
                  <button type="button" class="list-add-btn" @click="addListItem()">
                    <i class="fa fa-plus"></i> Add Item
                  </button>
                </div>
              </div>
            </div>
            <!-- Number type (int/float) -->
            <div class="form-group" v-else-if="
                currentProperty.type === 'int' || currentProperty.type === 'float'
              ">
              <label :for="currentPropertyName">Default</label>
              <div class="number-input-container">
                <input :id="currentPropertyName" :type="currentProperty.type === 'int' ? 'number' : 'text'"
                  v-model="editedValue" :step="currentProperty.type === 'int' ? 1 : 0.1"
                  :min="currentProperty.range ? currentProperty.range[0] : null"
                  :max="currentProperty.range ? currentProperty.range[1] : null" />
                <div class="range-slider" v-if="currentProperty.range">
                  <input type="range" v-model.number="editedValue" :min="currentProperty.range[0]"
                    :max="currentProperty.range[1]" :step="currentProperty.type === 'int' ? 1 : 0.1" />
                  <div class="range-values">
                    <span>{{ currentProperty.range[0] }}</span>
                    <span>{{ currentProperty.range[1] }}</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- Boolean type -->
            <div class="form-group" v-else-if="currentProperty.type === 'bool'">
              <label>Default</label>
              <div class="toggle-switch">
                <input type="checkbox" :id="currentPropertyName" v-model="editedValue" />
                <label :for="currentPropertyName"></label>
                <span class="toggle-label">{{ editedValue ? "True" : "False" }}</span>
              </div>
            </div>
            <!-- Metadata options -->
            <div class="form-group">
              <label>Privacy Setting</label>
              <div class="radio-group">
                <div class="radio-item">
                  <input type="radio" id="public" :value="false" v-model="editedPrivate" />
                  <label for="public">Public</label>
                </div>
                <div class="radio-item">
                  <input type="radio" id="private" :value="true" v-model="editedPrivate" />
                  <label for="private">Private</label>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label>Sampling Method</label>
              <el-select v-model="editedSampling" placeholder="Select sampling method" class="full-width">
                <el-option value="random" label="Random"></el-option>
                <el-option value="preset" label="Preset"></el-option>
                <el-option value="llm" label="LLM"></el-option>
              </el-select>
            </div>
            <div class="form-actions">
              <button type="button" class="cancel-btn" @click="cancelPropertyEdit">
                Cancel
              </button>
              <button type="submit" class="save-btn">Save Changes</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 新增的添加人口数量弹窗 -->
    <div class="modal-overlay" v-if="showAddModal" @click.self="cancelAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Add Population Size</h3>
          <button class="close-btn" @click="cancelAddModal">
            <i class="fa fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="addPopulationPreset">
            <div class="form-group">
              <label>Population Size:</label>
              <el-input v-model.number="currentAgentCount" type="number" min="1" @input="handleInput" />
              <!-- <input type="number" v-model.number="currentAgentCount" min="1" /> -->
            </div>
            <div class="form-actions">
              <button type="button" class="cancel-btn" @click="cancelAddModal">
                Cancel
              </button>
              <button type="submit" class="save-btn">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    <!-- 添加新的 Field 弹窗 -->
    <div class="modal-overlay" v-if="showAddAgentModal" @click.self="cancelAddAgentModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Add New Field</h3>
          <button class="close-btn" @click="cancelAddAgentModal">
            <i class="fa fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveNewField">
            <!-- 字段名称 -->
            <div class="form-group">
              <label>Field Name</label>
              <input type="text" v-model="newFieldName" placeholder="Enter Field name" />
            </div>
            <!-- 字段类型 -->
            <div class="form-group">
              <label>Field Type</label>
              <el-select v-model="newFieldType" placeholder="Select Field Type" class="full-width"
                @change="handleAgentTypeChange">
                <el-option v-for="type in propertyTypes" :key="type.value" :label="type.label"
                  :value="type.value"></el-option>
              </el-select>
            </div>
            <!-- 取样方式 -->
            <div class="form-group">
              <label>Sampling Method</label>
              <el-select v-model="newPropertySampling" placeholder="Select sampling method" class="full-width">
                <el-option value="llm" label="LLM"></el-option>
                <el-option value="random" label="Random"></el-option>
                <el-option value="default" label="Default"></el-option>
              </el-select>
            </div>
            <!-- 生成默认值 -->
            <div class="form-group">
              <label>Default Value</label>
              <template v-if="newPropertySampling === 'llm'">
                <template v-if="newFieldType === 'str'">
                  <input type="text" v-model="newPropertyDefault" placeholder="Enter default value" />
                </template>
                <template v-if="newFieldType === 'int'">
                  <div class="number-input-container">
                    <div style="display: flex; justify-content: space-between;">
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Min</label>
                        <el-input type="number" v-model.number="rangeMin" min="0" max="99999999999999999" step="1"
                          placeholder="Enter min value"></el-input>
                      </div>
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Max</label>
                        <el-input type="number" v-model.number="rangeMax" min="0" max="99999999999999999" step="1"
                          placeholder="Enter max value"></el-input>
                      </div>
                    </div>
                    <div class="form-group" style="margin-bottom: 5px;">
                      <label style="font-size: 12px;">Default</label>
                      <el-input type="number" v-model="newPropertyDefault" step="1" :min="rangeMin" :max="rangeMax"
                        placeholder="Enter default value"></el-input>
                    </div>
                  </div>
                </template>
                <template v-if="newFieldType === 'float'">
                  <div class="number-input-container">
                    <div style="display: flex; justify-content: space-between;">
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Min</label>
                        <el-input type="number" v-model.number="rangeMin" min="0" max="1" step="0.1"
                          placeholder="Enter min value"></el-input>
                      </div>
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Max</label>
                        <el-input type="number" v-model.number="rangeMax" min="0" max="1" step="0.1"
                          placeholder="Enter max value"></el-input>
                      </div>
                    </div>
                    <div class="form-group" style="margin-bottom: 5px;">
                      <label style="font-size: 12px;">Default</label>
                      <el-input type="number" v-model="newPropertyDefault" step="0.1" :min="rangeMin" :max="rangeMax"
                        placeholder="Enter default value"></el-input>
                    </div>
                  </div>
                </template>
                <template v-if="newFieldType === 'list'">
                  <div class="list-editor">
                    <div class="list-items">
                      <div v-for="(item, index) in listDefault" :key="index" class="list-item">
                        <input type="text" v-model="listDefault[index]" placeholder="Enter value" class="list-input" />
                        <button type="button" class="list-remove-btn" @click="removeNewListItem(index)">
                          <i class="fa fa-trash"></i>
                        </button>
                      </div>
                      <div class="list-add-container">
                        <button type="button" class="list-add-btn" @click="addNewListItem">
                          <i class="fa fa-plus"></i> Add Item
                        </button>
                      </div>
                    </div>
                  </div>
                </template>
              </template>
              <template v-else-if="newPropertySampling === 'random'">
                <div class="radio-group">
                  <div class="radio-item">
                    <input type="radio" id="choices" :value="false" v-model="restrain" />
                    <label for="choices">choices</label>
                  </div>
                  <div class="radio-item" v-if="newFieldType === 'int' || newFieldType === 'float'">
                    <input type="radio" id="range" :value="true" v-model="restrain" />
                    <label for="range">range</label>
                  </div>
                </div>
                <template v-if="restrain === false">
                  <div class="list-editor">
                    <div class="list-items">
                      <div v-for="(item, index) in listDefault" :key="index" class="list-item">
                        <input type="text" v-model="listDefault[index]" placeholder="Enter value" class="list-input" />
                        <button type="button" class="list-remove-btn" @click="removeNewListItem(index)">
                          <i class="fa fa-trash"></i>
                        </button>
                      </div>
                      <div class="list-add-container">
                        <button type="button" class="list-add-btn" @click="addNewListItem">
                          <i class="fa fa-plus"></i> Add Item
                        </button>
                      </div>
                    </div>
                  </div>

                </template>
                <template v-if="restrain === true">
                  <template v-if="newFieldType === 'int'">
                    <div class="number-input-container">
                      <div style="display: flex; justify-content: space-between;">
                        <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                          <label style="font-size: 12px;">Min</label>
                          <el-input type="number" v-model.number="rangeMin" min="0" max="99999999999999999" step="1"
                            placeholder="Enter min value"></el-input>
                        </div>
                        <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                          <label style="font-size: 12px;">Max</label>
                          <el-input type="number" v-model.number="rangeMax" min="0" max="99999999999999999" step="1"
                            placeholder="Enter max value"></el-input>
                        </div>
                      </div>
                      <div class="form-group" style="margin-bottom: 5px;">
                        <label style="font-size: 12px;">Default</label>
                        <el-input type="number" v-model="newPropertyDefault" step="1" :min="rangeMin" :max="rangeMax"
                          placeholder="Enter default value"></el-input>
                      </div>
                    </div>
                  </template>
                  <template v-if="newFieldType === 'float'">
                    <div class="number-input-container">
                      <div style="display: flex; justify-content: space-between;">
                        <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                          <label style="font-size: 12px;">Min</label>
                          <el-input type="number" v-model.number="rangeMin" min="0" max="1" step="0.1"
                            placeholder="Enter min value"></el-input>
                        </div>
                        <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                          <label style="font-size: 12px;">Max</label>
                          <el-input type="number" v-model.number="rangeMax" min="0" max="1" step="0.1"
                            placeholder="Enter max value"></el-input>
                        </div>
                      </div>
                      <div class="form-group" style="margin-bottom: 5px;">
                        <label style="font-size: 12px;">Default</label>
                        <el-input type="number" v-model="newPropertyDefault" step="0.1" :min="rangeMin" :max="rangeMax"
                          placeholder="Enter default value"></el-input>
                      </div>
                    </div>
                  </template>
                </template>
              </template>
              <template v-else-if="newPropertySampling === 'default'">
                <template v-if="newFieldType === 'str'">
                  <input type="text" v-model="newPropertyDefault" placeholder="Enter default value" />
                </template>
                <template v-if="newFieldType === 'int'">
                  <div class="number-input-container">
                    <div style="display: flex; justify-content: space-between;">
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Min</label>
                        <el-input type="number" v-model.number="rangeMin" min="0" max="99999999999999999" step="1"
                          placeholder="Enter min value"></el-input>
                      </div>
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Max</label>
                        <el-input type="number" v-model.number="rangeMax" min="0" max="99999999999999999" step="1"
                          placeholder="Enter max value"></el-input>
                      </div>
                    </div>
                    <div class="form-group" style="margin-bottom: 5px;">
                      <label style="font-size: 12px;">Default</label>
                      <el-input type="number" v-model="newPropertyDefault" step="1" :min="rangeMin" :max="rangeMax"
                        placeholder="Enter default value"></el-input>
                    </div>
                  </div>
                </template>
                <template v-if="newFieldType === 'float'">
                  <div class="number-input-container">
                    <div style="display: flex; justify-content: space-between;">
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Min</label>
                        <el-input type="number" v-model.number="rangeMin" min="0" max="1" step="0.1"
                          placeholder="Enter min value"></el-input>
                      </div>
                      <div class="form-group" style="margin-bottom: 5px; width: 48%;">
                        <label style="font-size: 12px;">Max</label>
                        <el-input type="number" v-model.number="rangeMax" min="0" max="1" step="0.1"
                          placeholder="Enter max value"></el-input>
                      </div>
                    </div>
                    <div class="form-group" style="margin-bottom: 5px;">
                      <label style="font-size: 12px;">Default</label>
                      <el-input type="number" v-model="newPropertyDefault" step="0.1" :min="rangeMin" :max="rangeMax"
                        placeholder="Enter default value"></el-input>
                    </div>
                  </div>
                </template>
                <template v-if="newFieldType === 'list'">
                  <div class="list-editor">
                    <div class="list-items">
                      <div v-for="(item, index) in listDefault" :key="index" class="list-item">
                        <input type="text" v-model="listDefault[index]" placeholder="Enter value" class="list-input" />
                        <button type="button" class="list-remove-btn" @click="removeNewListItem(index)">
                          <i class="fa fa-trash"></i>
                        </button>
                      </div>
                      <div class="list-add-container">
                        <button type="button" class="list-add-btn" @click="addNewListItem">
                          <i class="fa fa-plus"></i> Add Item
                        </button>
                      </div>
                    </div>
                  </div>
                </template>
              </template>
            </div>
            <div class="form-group" v-if="newPropertySampling === 'random' && newFieldType === 'list'">
              <label>sample_size</label>
              <div class="constraints-container">
                <el-input type="number" v-model="sampleSize" step="1" placeholder="Enter default value"></el-input>
              </div>
            </div>
            <div class="form-group" v-if="newPropertySampling === 'llm'">
              <label>Description Value</label>
              <div class="constraints-container">
                <input type="text" v-model="newPropertyDescription" placeholder="Enter description" />
              </div>
            </div>
            <div class="form-group">
              <label>Privacy Setting</label>
              <div class="radio-group">
                <div class="radio-item">
                  <input type="radio" id="public" :value="false" v-model="newPropertyPrivate" />
                  <label for="public">Public</label>
                </div>
                <div class="radio-item">
                  <input type="radio" id="private" :value="true" v-model="newPropertyPrivate" />
                  <label for="private">Private</label>
                </div>
              </div>
            </div>
            <div class="form-actions">
              <button type="button" class="cancel-btn" @click="cancelAddAgentModal">
                Cancel
              </button>
              <button type="submit" class="save-btn">Save</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import schemaData from "../assets/js/schema.json";
import axios from "axios";
import TipsCarousel from "../components/TipsCarousel.vue";
import { ElSelect, ElOption , ElMessageBox} from "element-plus";
export default {
  name: "AgentConfigurationView",
  components: {
    ElSelect,
    ElOption,
    TipsCarousel,
  },
  data() {
    return {
      schemaData: [],
      agentTypes: [],
      filteredAgentTypes: [],
      searchQuery: "",
      currentAgentType: "",
      propertySearchQuery: "",
      properties: {},
      filteredProperties: {},

      // Property editing
      showPropertyModal: false,
      showAddAgentModal: false,
      currentPropertyName: "",
      currentProperty: null,
      editedValue: null,
      editedListValues: [],
      editedPrivate: false,
      editedSampling: "",
      invalidList: false,
      invalidInputs: [],

      // Track configurations
      configuredAgentTypes: new Set(),

      // Agent counts
      agentCounts: {},
      currentAgentCount: 1,//生成的人口规模
      isLoading: false,
      restrain: false,
      populationPresets: [1, 5, 10, 20, 50, 100], // 预设人口数量
      showAddModal: false,
      selectedAgentType: "",
      newFieldType: "default",//选中的字段类型
      newFieldName: "",//字段名称
      newPropertyType: "",
      newPropertySampling: "",//选中抽样类型
      newPropertyDescription: "",
      newPropertyDefault: "",
      newPropertyPrivate: false,
      constraintType: "range",
      rangeMin: null,
      rangeMax: null,
      choices: [],
      choiceInput: "",
      sampleSize: 1,
      listDefault: [],
      listItemInput: "",
      validationErrors: [],
      propertyTypes: [
        { value: "str", label: "str" },
        { value: "int", label: "int" },
        { value: "float", label: "float" },
        { value: "list", label: "list" },
      ],
      samplingMethods: [
        { value: "llm", label: "LLM" },
        { value: "random", label: "Random" },
        { value: "default", label: "Default" },
      ],
      countObj:{},
    };
  },
  created() {
    // Extract agent types from schema
    this.agentTypes = Object.keys(this.schemaData);
    this.filteredAgentTypes = [...this.agentTypes];

    // console.log(this.agentTypes, 'this.agentTypes')

    // Try to load saved configuration
    const savedConfig = localStorage.getItem("agentPropertiesConfig");
    if (savedConfig) {
      try {
        const parsedConfig = JSON.parse(savedConfig);
        if (parsedConfig && typeof parsedConfig === "object") {
          const configuredTypes = Object.keys(parsedConfig);
          this.configuredAgentTypes = new Set(configuredTypes);
        }
      } catch (error) {
        console.error("Error parsing saved agent configuration:", error);
      }
    }

    //这里不知道干嘛的，导致会出现错误的agentCounts，所以暂时注释掉
    // Try to load saved agent counts
    // const savedCounts = localStorage.getItem("agentCounts");
    // if (savedCounts) {
    //   try {
    //     const parsedCounts = JSON.parse(savedCounts);
    //     if (parsedCounts && typeof parsedCounts === "object") {
    //       this.agentCounts = parsedCounts;
    //     }
    //   } catch (error) {
    //     console.error("Error parsing saved agent counts:", error);
    //   }
    // }
  },
  computed: {
    canProceed() {
      return true;
    },
    hasInvalidInput() {
      return this.invalidInputs.some((invalid) => invalid);
    },
  },
  mounted() {
    this.loadAgents();
    //初始化各个类型人数
  },
  methods: {
    deleteProperty(propName) {
      ElMessageBox.confirm("Delete", {
        confirmButtonText: "OK",
        cancelButtonText: "Cancel",
      }).then(() => {
        if (this.currentAgentType && this.filteredProperties[propName]) {
        // 从 filteredProperties 中删除属性
        delete this.filteredProperties[propName];

        // 从 schemaData 中删除属性
        if (this.schemaData[this.currentAgentType]) {
          delete this.schemaData[this.currentAgentType][propName];
        }
        // 保存更新后的 schema
        this.saveUpdateSchema();
      }
      });
    },
    async loadAgents() {
      this.isLoading = true;
      try {
        await this.getDataProfileSchemas();
      } finally {
        //this.isLoading = false;
      }
    },
    getDataProfileSchemas() {
      axios
        .get("/api/pipeline/profile_schemas?env_name=" + localStorage.getItem('scenarioName'))
        .then((response) => {
          this.isLoading = false;
          this.filteredAgentTypes = Object.keys(response.data.schemas);
          this.schemaData = response.data.schemas;
          let agentCountsData = response.data.profile_counts;
          for(let key in agentCountsData){
            this.agentCounts[key] = agentCountsData[key] == 0? 5: agentCountsData[key];
          }
        });
    },
    filterAgentTypes() {
      if (!this.searchQuery) {
        this.filteredAgentTypes = [...this.agentTypes];
        return;
      }

      const query = this.searchQuery.toLowerCase();
      this.filteredAgentTypes = this.agentTypes.filter((agentType) =>
        agentType.toLowerCase().includes(query)
      );
    },

    filterAgentProperties() {
      if (!this.propertySearchQuery) {
        this.filteredProperties = {
          ...this.properties,
        };
        return;
      }

      const query = this.propertySearchQuery.toLowerCase();
      this.filteredProperties = Object.entries(this.properties)
        .filter(
          ([propName, prop]) =>
            propName.toLowerCase().includes(query) ||
            (prop.description && prop.description.toLowerCase().includes(query))
        )
        .reduce((obj, [key, value]) => {
          obj[key] = value;
          return obj;
        }, {});
    },

    selectAgentType(agentType) {
      this.currentAgentType = agentType;
      this.properties = this.schemaData[agentType];
      this.propertySearchQuery = "";
      this.filteredProperties = {
        ...this.properties,
      };

      // Set current count for the agent type
      this.currentAgentCount =
        this.agentCounts[agentType] || this.getDefaultCount(agentType);
    },

    getPropertyCount(agentType) {
      return Object.keys(this.schemaData[agentType]).length;
    },
    // 默认人口数量
    getDefaultCount(agentType) {
      // Default population counts based on agent type
      return this.agentCounts[agentType] || 5;
    },

    setAgentCount() {
      console.log('2');
      if (!this.currentAgentType) return;

      // Ensure count is a valid positive integer
      let count = parseInt(this.currentAgentCount);
      if (isNaN(count) || count < 1) {
        count = 1;
      } else if (count > 100) {
        count = 100;
      }

      this.currentAgentCount = count;
      this.agentCounts[this.currentAgentType] = count;

      // Also save count to configuration
      this.saveConfiguration();
    },

    displayValue(value) {
      if (value === null) return "null";
      if (Array.isArray(value)) {
        if (value.length === 0) return "[]";
        return "[...]";
      }
      return String(value);
    },

    hasConstraints(property) {
      return property.choices || property.range;
    },

    editProperty(propName, property) {
      this.currentPropertyName = propName;
      this.currentProperty = {
        ...property,
      };
      this.invalidList = false;
      this.invalidInputs = [];

      // Set initial values
      if (property.type === "list") {
        if (Array.isArray(property.default) && property.default.length > 0) {
          this.editedListValues = [...property.default];
          // 初始化验证状态
          this.invalidInputs = Array(property.default.length).fill(false);
        } else {
          // 如果没有默认值或默认值为空数组，但有choices，则添加choices里的所有选项
          if (property.choices && property.choices.length > 0) {
            this.editedListValues = [...property.choices];
            this.invalidInputs = Array(property.choices.length).fill(false);
          } else {
            this.editedListValues = [];
            this.invalidInputs = [];
          }
        }
        this.editedValue = null;
      } else {
        this.editedValue = property.default;
      }

      this.editedPrivate = property.private || false;
      this.editedSampling = property.sampling || "random";

      this.showPropertyModal = true;
    },

    cancelPropertyEdit() {
      this.showPropertyModal = false;
      this.currentPropertyName = "";
      this.currentProperty = null;
      this.editedValue = null;
      this.editedListValues = [];
      this.invalidList = false;
      this.invalidInputs = [];
    },

    // 添加列表项方法(编辑模式)
    addListItem() {
      if (this.currentProperty.type === "list") {
        this.editedListValues.push("");
        this.invalidInputs.push(false);
      }
    },
    // 添加列表项方法(新建模式)
    addNewListItem() {

      // 先添加一个空列表项
      this.listDefault.push("");

      // 如果有输入值,则更新最后一项
      if (this.listItemInput && this.listItemInput.trim() !== "") {
        const newItem = this.listItemInput.trim();
        // 检查是否已存在相同值(不区分大小写)
        const exists = this.listDefault.some(
          (item) => item.toLowerCase() === newItem.toLowerCase()
        );

        if (!exists) {
          this.listDefault[this.listDefault.length - 1] = newItem;
          this.listItemInput = "";
        } else {
          console.warn("列表项已存在");
          // 如果已存在,则移除刚添加的空项
          this.listDefault.pop();
        }
      }
    },

    // 移除列表项方法(编辑模式)
    removeListItem(index) {
      this.editedListValues.splice(index, 1);
      this.invalidInputs.splice(index, 1);
    },

    // 移除列表项方法(新建模式)
    removeNewListItem(index) {
      this.listDefault.splice(index, 1);
    },

    // 验证所有列表项
    validateAllListItems() {
      let isValid = true;
      if (this.currentProperty.type === "list") {
        this.editedListValues.forEach((item, index) => {
          const isEmpty = !item || item.trim() === "";
          this.invalidInputs[index] = isEmpty;
          if (isEmpty) isValid = false;
        });
      }
      return isValid;
    },

    savePropertyChanges() {
      // 验证list类型数据，确保没有空项
      if (this.currentProperty.type === "list") {
        // 验证所有项
        if (!this.validateAllListItems()) {
          return; // 如果有无效项，不保存
        }
      }

      // Apply changes to property
      if (this.currentProperty.type === "list") {
        this.currentProperty.default = [...this.editedListValues];
      } else {
        this.currentProperty.default = this.editedValue;
      }

      this.currentProperty.private = this.editedPrivate;
      this.currentProperty.sampling = this.editedSampling;

      // Update property in schema
      this.properties[this.currentPropertyName] = this.currentProperty;
      this.filteredProperties = {
        ...this.properties,
      };

      // Mark agent type as configured
      this.configuredAgentTypes.add(this.currentAgentType);

      // Save changes to localStorage (simplified approach)
      //这里不应该保存数据，只是将数据记录一下
      // this.saveConfiguration();

      // Close modal
      this.showPropertyModal = false;
    },

    saveConfiguration() {
      //在最终保存前先保存人员数量信息
      this.isLoading = true;
      let param = {
        env_name: localStorage.getItem('scenarioName'),
        agent_schemas: this.schemaData, 
      };
      axios.post("/api/pipeline/profile_schema", param).then((response) => {
        console.log("response", response);
        let data = {
          env_name: localStorage.getItem('scenarioName'),
          agent_types: this.agentCounts,
          model_name: this.$route.query.model_name,
          category: this.$route.query.category,
        };
        axios.post("/api/pipeline/generate_profiles",data).then((response) => {
          console.log("response", response);
          this.$nextTick(()=>{
            // Create config object that includes only configured agent types
            const configObj = {};
            for (const agentType of this.configuredAgentTypes) {
              configObj[agentType] = {
                properties: this.schemaData[agentType],
                count: this.agentCounts[agentType] || this.getDefaultCount(agentType),
              };
            }
            localStorage.setItem("agentPropertiesConfig", JSON.stringify(configObj));
            localStorage.setItem("agentCounts", JSON.stringify(this.agentCounts));
            this.isLoading = false;
            this.$nextTick(()=>{
              // 触发事件进入下一步
              this.$emit("step-complete");
            })
          })
        });
      });
    },

    goToNextStep() {
      // 保存最终配置
      this.saveConfiguration();
    },

    cancelAddModal() {
      this.showAddModal = false;
    },

    addPopulationPreset() {
      // this.isLoading = true;
      const val = parseInt(this.currentAgentCount);
      this.agentCounts[this.currentAgentType] = val;
      if (!isNaN(val) && !this.populationPresets.includes(val)) {
        this.populationPresets.push(val);
        this.populationPresets.sort((a, b) => a - b);
      }
      //传一下各个类型的人员规模/数量
      let data = {
        env_name: localStorage.getItem('scenarioName'),
        agent_types: this.agentCounts,
        model_name: this.$route.query.model_name,
        category: this.$route.query.category,
      };

      this.showAddModal = false;
    },

    showAddAgentModalOpen() {
      this.showAddAgentModal = true;
      this.resetNewAgentForm();
    },

    cancelAddAgentModal() {
      this.showAddAgentModal = false;
      this.resetNewAgentForm();
    },

    resetNewAgentForm() {
      this.newFieldType = "";
      this.newFieldName = "";
      this.newPropertyType = "";
      this.newPropertySampling = "";
      this.newPropertyDescription = "";
      this.newPropertyDefault = "";
      this.newPropertyPrivate = false;
      this.constraintType = "range";
      this.rangeMin = null;
      this.rangeMax = null;
      this.choices = [];
      this.choiceInput = "";
      this.sampleSize = 1;
      this.listDefault = [];
      this.listItemInput = "";
      this.validationErrors = [];
    },

    addChoice() {
      if (this.choiceInput && !this.choices.includes(this.choiceInput)) {
        this.choices.push(this.choiceInput);
        this.choiceInput = "";
      }
    },

    removeChoice(index) {
      this.choices.splice(index, 1);
    },

    validateNewAgent() {
      this.validationErrors = [];
      if (!this.newFieldName) {
        this.validationErrors.push("Agent name is required");
      }
      if (!this.newFieldType) {
        this.validationErrors.push("Agent type is required");
      }
      if (!this.newPropertySampling) {
        this.validationErrors.push("Sampling method is required");
      }

      if (this.newFieldType === "int" || this.newFieldType === "float") {
        if (this.newPropertySampling === "random") {
          if (this.restrain) {
            if (this.rangeMin === null || this.rangeMax === null) {
              this.validationErrors.push("Range values are required");
            } else if (this.rangeMin >= this.rangeMax) {
              this.validationErrors.push("Range min must be less than max");
            }
          } else if (!this.restrain && this.listDefault.length === 0) {
            this.validationErrors.push("At least one choice is required");
          }
        }
      } else if (
        this.newFieldType === "str" && this.newPropertySampling === "random" && this.listDefault.length === 0
      ) {
        this.validationErrors.push("At least one choice is required");
      } else if (this.newFieldType === "list") {
        if (this.newPropertySampling === "random" && !this.sampleSize) {
          this.validationErrors.push(
            "Sample size is required for list type with random sampling"
          );
        }
        if (this.listDefault.length === 0) {
          this.validationErrors.push("At least one list item is required");
        }
      }
      return this.validationErrors.length === 0;
    },

    saveNewField() {
      if (!this.validateNewAgent()) {
        return;
      }

      const newProperty = {
        type: this.newFieldType,
        default: this.newFieldType === "list" ? [...this.listDefault] : this.newPropertyDefault,
        private: this.newPropertyPrivate,
        sampling: this.newPropertySampling,
      };

      // 根据不同的属性类型和采样方式添加特定字段
      if (this.newPropertySampling === "llm"){
        newProperty.description = this.newPropertyDescription;
        if (this.newFieldType === "int" || this.newFieldType === "float") {
          newProperty.range = [this.rangeMin, this.rangeMax];
        }
      }else if(this.newPropertySampling === "random"){
        if (this.restrain){
          if (this.newFieldType === "int" || this.newFieldType === "float") {
            newProperty.range = [this.rangeMin, this.rangeMax];
          }
        }else{
          if(this.newFieldType === "int" || this.newFieldType === "float"){
            newProperty.choices = [...this.listDefault];
          }else if(this.newFieldType === "str"){
            newProperty.choices = [...this.listDefault];
          }else if(this.newFieldType === "list"){
            newProperty.choices = [...this.listDefault];
            newProperty.sample_size = this.sampleSize;
          }
        }
      }else if(this.newPropertySampling === "default"){
        if (this.newFieldType === "int" || this.newFieldType === "float") {
          newProperty.range = [this.rangeMin, this.rangeMax];
        }
      }
      //类型为default时不需要额外字段

      // 更新 schemaData
      if (!this.schemaData[this.currentAgentType]) {
        this.schemaData[this.currentAgentType] = {};
      }
      this.schemaData[this.currentAgentType][this.newFieldName] = newProperty;

      // return

      // 保存到后端
       this.saveUpdateSchema();
    },
    saveUpdateSchema() {
      let param = {
        env_name: localStorage.getItem('scenarioName'),
        agent_schemas: this.schemaData,
      };

      axios.post("/api/pipeline/profile_schema", param).then((response) => {
        console.log("response", response);
        if(response.response == '200'){
          this.cancelAddAgentModal()
        }
      });
    },
    handleAgentTypeChange() {
      // 重置相关字段
      this.newPropertyDefault = "";
      this.listDefault = [];
      this.listItemInput = "";
      this.choices = [];
      this.choiceInput = "";
      this.rangeMin = null;
      this.rangeMax = null;
      this.constraintType = "range";

      // 根据类型设置默认值
      if (this.newFieldType === "int") {
        this.newPropertyDefault = 0;
        this.rangeMin = null;
        this.rangeMax = null;
      } else if (this.newFieldType === "float") {
        this.newPropertyDefault = 0.0;
        this.rangeMin = 0;
        this.rangeMax = 1; // 限制最大值为1
      } else if (this.newFieldType === "list") {
        this.listDefault = [];
      } else if (this.newFieldType === "str") {
        this.newPropertyDefault = "";
      }
    },
    handleInput(value) {
      // 确保输入是正整数（过滤非数字字符）
      this.currentAgentCount = value.replace(/[^\d]/g, "");
      // 如果输入是0或空，强制设为1
      if (this.currentAgentCount === "0" || this.currentAgentCount === "") {
        this.currentAgentCount = "1";
      }
    }
  },
  watch: {
    canProceed: {
      handler(newValue) {
        // Send status update to parent component
        this.$emit("update:canProceed", newValue);
      },
      immediate: true,
    },
    isLoading: {
      handler(newValue) {
        this.$emit("update:loading", newValue);
      },
      immediate: true,
    },
  },
};
</script>

<style scoped>
.agent-config-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease;
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }

  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.page-title {
  color: var(--text-color);
  font-size: 1.8rem;
  margin-bottom: 10px;
}

.page-description {
  color: var(--secondary-color);
  font-size: 1.1rem;
  margin-bottom: 30px;
}

.config-content {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  height: calc(100vh - 340px);
  min-height: 500px;
  position: relative;
}

.agent-list-panel {
  width: 300px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  animation-name: slideInUp;
  animation-duration: 0.5s;
  animation-fill-mode: both;
  animation-timing-function: ease;
  will-change: transform, opacity;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  min-height: 200px; /* 确保有足够的高度显示加载动画 */
}

.properties-panel {
  flex: 1;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  animation: slideInUp 0.5s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.properties-grid {
  display: flex;
  flex-direction: column;
  gap: 15px;
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 10px;
}

.empty-state {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  color: var(--secondary-color);
  animation: fadeIn 0.5s ease;
}

.empty-state-content {
  text-align: center;
  padding: 40px;
}

.empty-state-content i {
  font-size: 48px;
  margin-bottom: 20px;
  opacity: 0.7;
}

.empty-state-content h3 {
  font-size: 1.4rem;
  margin-bottom: 10px;
}

.panel-header {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 20px;
}

.header-left {
  width: 40%;
  display: grid;
  gap: 36px;
}

.header-right {
  width:60%;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.count-editor {
  display: flex;
  align-items: center;
  gap: 4px;
}

.count-editor label {
  font-size: 0.85rem;
  color: var(--secondary-color);
}

.count-input-group {
  display: flex;
  gap: 8px;
}

.count-input {
  width: 80px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.count-btn {
  padding: 6px 12px;
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.count-btn:hover {
  transform: translateY(-2px);
}

.title-section {
  width: 100%;
}

.panel-header h3 {
  color: var(--text-color);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-box {
  position: relative;
  width: 160px;
}

.search-box input {
  width: 100%;
  padding: 8px 30px 8px 10px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.search-box .fa-search {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--secondary-color);
}

.agent-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  overflow-x: hidden;
  flex-grow: 1;
  padding-right: 10px;
}

.agent-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background-color: var(--card-bg-color, rgba(255, 255, 255, 0.05));
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
  height: fit-content;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
}

.agent-card:hover {
  background-color: var(--card-hover-bg-color, rgba(255, 255, 255, 0.1));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: var(--border-hover-color, rgba(255, 255, 255, 0.2));
}

.agent-card.selected {
  background-color: var(--accent-color, #4170f3);
  color: white;
  border-color: var(--accent-color, #4170f3);
}

.agent-card-top {
  width: 100%;
}

.agent-card-bottom {
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.agent-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-count {
  font-size: 0.8rem;
  color: var(--accent-color, #4170f3);
  font-weight: 500;
}

.agent-card.selected .agent-count {
  color: white;
}

.property-count {
  font-size: 0.8rem;
  opacity: 0.8;
}

.property-card {
  padding: 15px;
  background-color: var(--card-bg-color, rgba(255, 255, 255, 0.05));
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
  position: relative;
}

.property-card:hover {
  background-color: var(--card-hover-bg-color, rgba(255, 255, 255, 0.1));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: var(--border-hover-color, rgba(255, 255, 255, 0.2));
}

.property-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.property-name {
  font-weight: 500;
  font-size: 1.1rem;
}

.property-type {
  font-size: 0.8rem;
  padding: 3px 8px;
  background-color: rgba(65, 112, 243, 0.2);
  color: var(--accent-color, #4170f3);
  border-radius: 12px;
}

.property-description {
  color: var(--secondary-color);
  margin-bottom: 10px;
  line-height: 1.4;
  font-size: 0.9rem;
}

.property-attributes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.property-attribute {
  font-size: 0.8rem;
  padding: 2px 6px;
  background-color: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
}

.property-constraints {
  font-size: 0.8rem;
  margin-top: 5px;
  color: var(--secondary-color);
}

.constraint {
  display: block;
  margin-top: 3px;
}

.property-actions {
  position: absolute;
  top: 15px;
  right: 15px;
}

.action-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.edit {
  background-color: rgba(65, 105, 225, 0.2);
  color: #4169e1;
}

.action-btn.delete {
  background-color: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  margin-top: 10px;
}

.action-btn:hover {
  transform: scale(1.1);
}

.no-results {
  padding: 20px;
  text-align: center;
  color: var(--secondary-color);
  font-style: italic;
  animation: fadeIn 0.5s ease;
  width: 100%;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
  animation: fadeIn 0.6s ease both;
}

.next-btn {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--accent-color);
  color: white;
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: rgba(65, 112, 243, 0.5);
}

.next-btn:not(:disabled):hover {
  transform: translateY(-2px);
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  /* z-index: 10001; */
  animation: fadeIn 0.3s ease;
}

:deep(.modal-overlay .el-select) {
  /* z-index: 10002 !important; */
}

:deep(.modal-overlay .el-select-dropdown) {
  z-index: 10003 !important;
}

.modal-content {
  width: 600px;
  max-width: 90%;
  background-color: var(--bg-color);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  animation: slideInUp 0.3s ease;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-color);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-color);
  font-size: 1.2rem;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.property-info {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
}

.property-type-badge {
  display: inline-block;
  padding: 4px 10px;
  background-color: var(--accent-color);
  color: white;
  border-radius: 15px;
  font-size: 0.9rem;
  margin-bottom: 10px;
}

.form-group {
  margin-bottom: 20px;
  animation: fadeIn 0.5s ease both;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-color);
  font-weight: 500;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea,
.form-group select,
.form-group .el-select {
  width: 100%;
  height: 40px;
  /* padding: 10px 0; */
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
  font-size: 1rem;
}
.form-group .el-select__wrapper {
  /* background: none !important;
  border: none !important;
  box-shadow: none !important; */
}
.full-width {
  width: 100%;
}

:deep(.el-select) {
  /* z-index: 10000 !important; */
}

:deep(.form-group .el-select .el-select__wrapper) {
  /* z-index: 10001 !important; */
  background: none !important;
  border: none !important;
  box-shadow: none !important;
  display: flex;
  align-items: center;
  height: 40px;
}
.form-group input[type="text"],
.form-group input[type="number"] {
  height: 40px;
  padding: 0 10px;
  box-sizing: border-box;
}

/* 列表编辑器样式 */
.list-editor {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  background-color: rgba(255, 255, 255, 0.05);
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.list-input,
.list-select {
  flex: 1;
}

.list-remove-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background-color: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.list-remove-btn:hover {
  background-color: rgba(231, 76, 60, 0.4);
}

.list-add-btn {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px dashed var(--border-color);
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--accent-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s ease;
  width: 100%;
}

.list-add-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.number-input-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.range-slider {
  padding: 10px 0;
}

.range-values {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  font-size: 0.8rem;
  color: var(--secondary-color);
}

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-switch input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-switch label {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
  background-color: #ccc;
  border-radius: 34px;
  transition: 0.4s;
  cursor: pointer;
}

.toggle-switch label:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

.toggle-switch input:checked + label {
  background-color: var(--accent-color);
}

.toggle-switch input:checked + label:before {
  transform: translateX(26px);
}

.toggle-label {
  font-weight: 500;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
}

.cancel-btn,
.save-btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.cancel-btn {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.save-btn {
  background-color: var(--accent-color);
  color: white;
}

.cancel-btn:hover,
.save-btn:hover {
  transform: translateY(-2px);
}

/* Responsive design */
@media (max-width: 968px) {
  .config-content {
    flex-direction: column;
    height: auto;
  }

  .agent-list-panel {
    width: 100%;
    height: 300px;
  }

  .properties-panel {
    height: 800px;
  }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .header-right {
    width: 100%;
  }

  .search-box {
    width: 100%;
  }
}

.invalid-input {
  border: 1px solid #e74c3c !important;
  background-color: rgba(231, 76, 60, 0.1) !important;
}

.validation-error {
  color: #e74c3c;
  font-size: 0.85rem;
  margin-top: 5px;
  padding: 5px;
  background-color: rgba(231, 76, 60, 0.1);
  border-radius: 4px;
}

.range-slider input[type="range"] {
  width: 100%;
  -webkit-appearance: none;
  margin: 10px 0;
  background: transparent;
}

.range-slider input[type="range"]::-webkit-slider-runnable-track {
  width: 100%;
  height: 6px;
  cursor: pointer;
  background: rgba(65, 112, 243, 0.3);
  border-radius: 3px;
}

.range-slider input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  height: 16px;
  width: 16px;
  border-radius: 50%;
  background: var(--accent-color);
  cursor: pointer;
  margin-top: -5px;
}

.radio-group {
  display: flex;
  gap: 20px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radio-item input[type="radio"] {
  margin: 0;
}

.radio-item label {
  margin: 0;
  font-weight: normal;
}

/* 自定义加载动画样式 */
.el-loading-mask {
  background-color: rgba(0, 0, 0, 0.1);
}

.el-loading-spinner .circular {
  width: 30px;
  height: 30px;
}

.el-loading-spinner .path {
  stroke: var(--accent-color);
  stroke-width: 3;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top: 3px solid var(--accent-color);
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 10px;
  font-size: 1rem;
  color: #333;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(50px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }

  to {
    opacity: 0;
    transform: translateX(50px);
  }
}

.agent-type-selector {
  display: flex;
  align-items: center;
  margin-top: 64px;
  /* margin-right: 120px; */
}

.add-agent-btn {
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  gap: 6px;
  transition: all 0.2s ease;
  width: 80px;
  height: 30px;
  text-align: center;
}

.add-agent-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.add-agent-btn i {
  font-size: 14px;
}
.el-select__wrapper {
  z-index: 1;
}

.constraints-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.constraint-option {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-inputs {
  display: flex;
  gap: 10px;
  margin-left: 20px;
}

.range-inputs input {
  width: 100px;
}

.choices-input {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-left: 20px;
}

.choices-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.choice-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.choice-item button {
  padding: 0;
  background: none;
  border: none;
  color: #e74c3c;
  cursor: pointer;
  font-size: 16px;
}

.list-default-input {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.list-item button {
  padding: 0;
  background: none;
  border: none;
  color: #e74c3c;
  cursor: pointer;
  font-size: 16px;
}

.validation-error {
  color: #e74c3c;
  font-size: 0.9rem;
  margin-top: 5px;
}

textarea {
  width: 100%;
  min-height: 100px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.1);
  resize: vertical;
}
/* ::v-deep .el-input__wrapper{background: none !important;} */
</style>
