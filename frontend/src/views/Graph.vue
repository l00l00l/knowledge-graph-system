<!-- Graph.vue -->
<template>
  <div class="graph-view">
    <div class="control-panel" :class="{ 'collapsed': isPanelCollapsed }">
      <div class="panel-header">
        <h2>控制面板</h2>
        <button class="toggle-button" @click="togglePanel">
          <i :class="isPanelCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'"></i>
        </button>
      </div>
      
      <div v-show="!isPanelCollapsed" class="panel-content">
        <div class="search-box">
          <input type="text" placeholder="搜索实体..." v-model="searchQuery" @input="filterNodes">
          <i class="fas fa-search"></i>
        </div>
        
        <div class="filter-section">
          <h3>实体类型过滤</h3>
          <div class="type-filters">
            <label v-for="type in entityTypes" :key="type" class="filter-checkbox">
              <input type="checkbox" :value="type" v-model="activeFilters">
              <span :class="['node-badge', type]"></span>
              <span>{{ type }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>
    
    <div class="graph-area">
      <div class="graph-container" ref="graphContainer"></div>
    </div>
          
    <div class="detail-panel" v-if="selectedEntity">
      <div class="entity-detail-container">
        <div v-if="selectedEntity" class="entity-card">
          <div class="entity-header" :class="selectedEntity.type">
            <h2>{{ selectedEntity.name }}</h2>
            <span class="entity-type-badge">{{ selectedEntity.type }}</span>
          </div>
          
          <div class="entity-body">
            <div v-if="selectedEntity.description" class="entity-description">
              {{ selectedEntity.description }}
            </div>
            
            <div class="entity-properties">
              <h3>属性</h3>
              <div v-for="(value, key) in selectedEntity.properties" :key="key" class="property-item">
                <span class="property-key">{{ key }}:</span>
                <span class="property-value">{{ formatPropertyValue(value) }}</span>
              </div>
            </div>
            
            <div class="entity-relationships">
              <h3>关系 ({{ entityRelationships.length }})</h3>
              <div v-if="entityRelationships.length === 0" class="no-data">
                无相关关系
              </div>
              <div v-else class="relationship-list">
                <div v-for="rel in entityRelationships" :key="rel.id" class="relationship-item" 
                    @click="selectEntity(rel.target)">
                  <div class="relationship-direction">
                    <i v-if="rel.direction === 'outgoing'" class="fas fa-arrow-right"></i>
                    <i v-else-if="rel.direction === 'incoming'" class="fas fa-arrow-left"></i>
                    <i v-else class="fas fa-arrows-alt-h"></i>
                  </div>
                  <div class="relationship-type">{{ rel.type }}</div>
                  <div class="related-entity" :class="rel.target.type">
                    {{ rel.target.name }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="entity-actions">
            <button @click="editEntity" class="btn edit-btn">
              <i class="fas fa-edit"></i> 编辑
            </button>
            <button @click="traceKnowledge" class="btn trace-btn">
              <i class="fas fa-history"></i> 溯源
            </button>
            <button @click="exploreContext" class="btn explore-btn">
              <i class="fas fa-project-diagram"></i> 探索上下文
            </button>
          </div>
        </div>
        <!-- Replace the current edit-modal with this improved version -->
        <div v-if="isEditing" class="edit-modal">
          <div class="edit-modal-content">
            <div class="edit-modal-header">
              <h3>编辑实体</h3>
              <button @click="cancelEdit" class="close-btn">
                <i class="fas fa-times"></i>
              </button>
            </div>
            
            <div class="edit-modal-body">
              <div class="form-section">
                <h4 class="section-title">基本信息</h4>
                <div class="form-group">
                  <label>名称</label>
                  <input type="text" v-model="editFormData.name" class="form-input">
                </div>
                
                <!-- 在edit-modal-body中的实体类型选择器部分 -->
                <div class="form-group">
                  <label>类型</label>
                  <div class="type-selector">
                    <div>
                      <span class="type-selector-label">分类</span>
                      <select v-model="selectedEntityTypeCategory" class="category-select">
                        <option value="">所有分类</option>
                        <option v-for="category in entityTypeCategories" :key="category">
                          {{ category }}
                        </option>
                      </select>
                    </div>
                    
                    <div>
                      <span class="type-selector-label">具体类型</span>
                      <select v-model="editFormData.type" class="type-select">
                        <option value="">请选择类型</option>
                        <option v-for="type in filteredEntityTypes" :key="type.type_code" :value="type.type_code">
                          {{ type.type_name }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
                
                <div class="form-group">
                  <label>描述</label>
                  <textarea v-model="editFormData.description" class="form-input" rows="3"></textarea>
                </div>
              </div>
              
              <!-- Replace the edit form "Properties" section with this improved version -->
              <div class="form-section">
                <h4 class="section-title">属性</h4>
                <button @click="addEntityProperty" class="add-property-btn">
                  <i class="fas fa-plus"></i> 添加属性
                </button>
                
                <div v-if="Object.keys(editFormData.properties).length === 0" class="no-data-message">
                  暂无属性数据
                </div>
                
                <div v-else class="properties-list">
                  <div v-for="(value, key) in editFormData.properties" :key="key" class="property-edit-row">
                    <div class="property-key">{{ key }}:</div>
                    <input type="text" v-model="editFormData.properties[key]" class="property-value-input">
                    <button @click="removeEntityProperty(key)" class="remove-property-btn">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Similarly update the "Relationships" section -->
              <div class="form-section">
                <h4 class="section-title">关系</h4>
                <button @click="showAddRelationshipDialog" class="add-relationship-btn">
                  <i class="fas fa-plus"></i> 添加关系
                </button>
                
                <div v-if="entityRelationships.length === 0" class="no-data-message">
                  暂无关系数据
                </div>
                
                <div v-else class="relationships-list">
                  <div v-for="(rel, index) in entityRelationships" :key="index" class="relationship-edit-row">
                    <div class="relationship-direction">
                      <i :class="rel.direction === 'outgoing' ? 'fas fa-arrow-right' : 'fas fa-arrow-left'"></i>
                    </div>
                    <div class="relationship-type">{{ getRelationshipTypeName(rel.type) }}</div>
                    <div class="related-entity">{{ rel.target.name }}</div>
                    <button @click="removeRelationship(index)" class="remove-property-btn">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="edit-modal-footer">
              <button @click="cancelEdit" class="btn cancel-btn">取消</button>
              <button @click="saveEntityChanges" class="btn save-btn">保存</button>
            </div>
          </div>
        </div>
        <!-- Place this at the root level of your template, outside the detail-panel -->
        <div v-if="showAddRelationship" class="add-relationship-modal">
          <div class="add-relationship-content">
            <div class="modal-header">
              <h3>添加关系</h3>
              <button @click="showAddRelationship = false" class="close-btn">
                <i class="fas fa-times"></i>
              </button>
            </div>
            
            <div class="modal-body">
              <div class="form-group">
                <label>关系方向</label>
                <div class="direction-selector">
                  <label class="radio-option">
                    <input type="radio" v-model="newRelationship.direction" value="outgoing">
                    <span>出发 ({{ editFormData.name }} → 目标实体)</span>
                  </label>
                  <label class="radio-option">
                    <input type="radio" v-model="newRelationship.direction" value="incoming">
                    <span>接收 (目标实体 → {{ editFormData.name }})</span>
                  </label>
                </div>
              </div>
              
              <!-- 在添加关系对话框中的类型选择器部分 -->
              <div class="form-group">
                <label>关系类型</label>
                <div class="type-selector">
                  <div>
                    <span class="type-selector-label">分类</span>
                    <select v-model="selectedRelationshipTypeCategory" class="category-select">
                      <option value="">所有分类</option>
                      <option v-for="category in relationshipTypeCategories" :key="category">
                        {{ category }}
                      </option>
                    </select>
                  </div>
                  
                  <div>
                    <span class="type-selector-label">关系类型</span>
                    <select v-model="newRelationship.type" class="type-select">
                      <option value="">请选择关系类型</option>
                      <option v-for="type in filteredRelationshipTypes" :key="type.type_code" :value="type.type_code">
                        {{ type.type_name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>目标实体</label>
                <div class="entity-search-wrapper">
                  <input 
                    type="text" 
                    v-model="targetEntitySearch" 
                    @input="searchTargetEntities"
                    placeholder="搜索实体..." 
                    class="form-input search-input"
                  >
                  
                  <div v-if="searchResults.length > 0" class="search-results">
                    <div 
                      v-for="entity in searchResults" 
                      :key="entity.id" 
                      class="search-result-item"
                      @click="selectTargetEntity(entity)"
                    >
                      <span>{{ entity.name }}</span>
                      <small>({{ getEntityTypeName(entity.type) }})</small>
                    </div>
                  </div>
                </div>
                
                <div v-if="newRelationship.targetEntity" class="selected-target-entity">
                  <span>{{ newRelationship.targetEntity.name }}</span>
                  <button @click="newRelationship.targetEntity = null" class="clear-entity-btn">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
            
            <div class="modal-footer">
              <button @click="showAddRelationship = false" class="btn cancel-btn">取消</button>
              <button 
                @click="addRelationship" 
                class="btn save-btn" 
                :disabled="!isNewRelationshipValid"
              >
                添加
              </button>
            </div>
          </div>
        </div>
      </div>
      <!-- Entity Edit Form Modal -->
      
      <button class="close-detail" @click="clearSelection">
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>
  
  <script>
  // import { KnowledgeGraphVisualizer } from '@/utils/graph-visualization';
  import * as d3 from 'd3';
  export default {
    name: 'Graph',
    data() {
      return {
        isPanelCollapsed: false,
        searchQuery: '',
        activeFilters: [],
        selectedEntity: null,
        entityRelationships: [],
        visualizer: null,
        simulation: null,
        svg: null,
        zoom: null,
        isEditing: false,
        editingEntity: null,
        editFormData: {},
        availableEntityTypes: [],
        showAddRelationship: false,
        selectedEntityTypeCategory: '',
        selectedRelationshipTypeCategory: '',
        newRelationship: {
          direction: 'outgoing',
          type: '',
          targetEntity: null
        },
        targetEntitySearch: '',
        searchResults: [],
        // Mock nodes data for testing
        nodes: [
          { id: 'n1', name: '知识图谱', type: 'concept', description: '知识图谱是一种表示知识的图结构', properties: { domain: '人工智能', popularity: '高' } },
          { id: 'n2', name: '谷歌', type: 'organization', description: '美国的跨国科技公司', properties: { founded: '1998', location: '美国' } },
          { id: 'n3', name: '知识表示', type: 'concept', description: '人工智能中表示知识的方法', properties: { domain: '人工智能' } },
          { id: 'n4', name: '语义网', type: 'concept', description: '万维网的延伸，允许数据被共享和重用', properties: { related: '知识图谱, 本体论' } },
          { id: 'n5', name: 'Tim Berners-Lee', type: 'person', description: '万维网的发明者', properties: { nationality: '英国', birth: '1955' } }
        ],
        // Mock relationships data for testing
        relationships: [
          { id: 'r1', source: 'n1', target: 'n3', type: 'is_a' },
          { id: 'r2', source: 'n2', target: 'n1', type: 'created' },
          { id: 'r3', source: 'n4', target: 'n1', type: 'related_to' },
          { id: 'r4', source: 'n5', target: 'n4', type: 'created' }
        ],
        // 静态实体类型数据
        entityTypes: [
          // 基础类型
          {"id": 1, "type_code": "concept", "type_name": "概念", "category": "基础类型", "icon": "fa-lightbulb", "color": "#d62728"},
          {"id": 2, "type_code": "person", "type_name": "人物", "category": "基础类型", "icon": "fa-user", "color": "#ff7f0e"},
          {"id": 3, "type_code": "organization", "type_name": "组织", "category": "基础类型", "icon": "fa-building", "color": "#1f77b4"},
          {"id": 4, "type_code": "location", "type_name": "地点", "category": "基础类型", "icon": "fa-map-marker", "color": "#2ca02c"},
          {"id": 5, "type_code": "time", "type_name": "时间", "category": "基础类型", "icon": "fa-clock", "color": "#9467bd"},
          {"id": 6, "type_code": "event", "type_name": "事件", "category": "基础类型", "icon": "fa-calendar", "color": "#8c564b"},
          
          // 领域类型
          {"id": 7, "type_code": "technology", "type_name": "技术", "category": "领域类型", "icon": "fa-microchip", "color": "#e377c2"},
          {"id": 8, "type_code": "theory", "type_name": "理论", "category": "领域类型", "icon": "fa-book", "color": "#7f7f7f"},
          {"id": 9, "type_code": "method", "type_name": "方法", "category": "领域类型", "icon": "fa-cogs", "color": "#bcbd22"},
          {"id": 10, "type_code": "problem", "type_name": "问题", "category": "领域类型", "icon": "fa-question-circle", "color": "#17becf"},
          {"id": 11, "type_code": "tool", "type_name": "工具", "category": "领域类型", "icon": "fa-wrench", "color": "#9edae5"},
          {"id": 12, "type_code": "solution", "type_name": "解决方案", "category": "领域类型", "icon": "fa-check-circle", "color": "#ffbb78"},
          
          // 个人类型
          {"id": 13, "type_code": "note", "type_name": "笔记", "category": "个人类型", "icon": "fa-sticky-note", "color": "#aec7e8"},
          {"id": 14, "type_code": "question", "type_name": "问题", "category": "个人类型", "icon": "fa-question", "color": "#ffbb78"},
          {"id": 15, "type_code": "idea", "type_name": "想法", "category": "个人类型", "icon": "fa-lightbulb", "color": "#98df8a"},
          {"id": 16, "type_code": "goal", "type_name": "目标", "category": "个人类型", "icon": "fa-bullseye", "color": "#ff9896"},
          {"id": 17, "type_code": "plan", "type_name": "计划", "category": "个人类型", "icon": "fa-tasks", "color": "#c5b0d5"}
        ],
        
        // 静态关系类型数据
        relationshipTypes: [
          // 基础类型
          {"id": 1, "type_code": "is_a", "type_name": "是一种", "category": "基础类型", "icon": "fa-sitemap", "color": "#666666"},
          {"id": 2, "type_code": "part_of", "type_name": "是部分", "category": "基础类型", "icon": "fa-puzzle-piece", "color": "#666666"},
          {"id": 3, "type_code": "attribute_of", "type_name": "是属性", "category": "基础类型", "icon": "fa-tag", "color": "#666666"},
          {"id": 4, "type_code": "instance_of", "type_name": "是实例", "category": "基础类型", "icon": "fa-copy", "color": "#666666"},
          
          // 领域类型
          {"id": 5, "type_code": "causes", "type_name": "导致", "category": "领域类型", "icon": "fa-arrow-right", "color": "#666666"},
          {"id": 6, "type_code": "influences", "type_name": "影响", "category": "领域类型", "icon": "fa-exchange-alt", "color": "#666666"},
          {"id": 7, "type_code": "depends_on", "type_name": "依赖于", "category": "领域类型", "icon": "fa-link", "color": "#666666"},
          {"id": 8, "type_code": "contradicts", "type_name": "矛盾于", "category": "领域类型", "icon": "fa-not-equal", "color": "#666666"},
          
          // 个人类型
          {"id": 9, "type_code": "similar_to", "type_name": "类似于", "category": "个人类型", "icon": "fa-equals", "color": "#666666"},
          {"id": 10, "type_code": "reminds_of", "type_name": "提醒我", "category": "个人类型", "icon": "fa-bell", "color": "#666666"},
          {"id": 11, "type_code": "inspires", "type_name": "启发", "category": "个人类型", "icon": "fa-lightbulb", "color": "#666666"},
          {"id": 12, "type_code": "confuses", "type_name": "困惑", "category": "个人类型", "icon": "fa-question-circle", "color": "#666666"}
        ],
        
        // 初始化分类选择器
        entityTypeCategories: ["基础类型", "领域类型", "个人类型"],
        relationshipTypeCategories: ["基础类型", "领域类型", "个人类型"]
      };
    },
    computed: {
      uniqueNodeTypes() {
        return [...new Set(this.nodes.map(node => node.type))];
      },
      

      filteredEntityTypes() {
        // 添加更多详细的调试日志
        console.log('Computing filteredEntityTypes');
        console.log('  Selected category:', this.selectedEntityTypeCategory);
        console.log('  All entity types:', this.entityTypes);
        
        // 如果没有选择分类，返回所有类型
        if (!this.selectedEntityTypeCategory) {
          console.log('  No category selected, returning all types');
          return this.entityTypes;
        }
        
        // 精确匹配分类
        const filtered = this.entityTypes.filter(type => {
          const matches = type.category === this.selectedEntityTypeCategory;
          if (matches) {
            console.log(`  Type ${type.type_name} matches category ${this.selectedEntityTypeCategory}`);
          }
          return matches;
        });
        
        console.log(`  Filtered ${filtered.length} entity types for category ${this.selectedEntityTypeCategory}`);
        
        // 如果过滤结果为空，可能是因为分类不匹配，日志警告
        if (filtered.length === 0) {
          console.warn('  Warning: No entity types match the selected category!');
          console.log('  Available categories in data:', [...new Set(this.entityTypes.map(t => t.category))]);
        }
        
        return filtered;
      },

      
      filteredRelationshipTypes() {
        // 添加更多详细的调试日志
        console.log('Computing filteredRelationshipTypes');
        console.log('  Selected category:', this.selectedRelationshipTypeCategory);
        console.log('  All relationship types:', this.relationshipTypes);
        
        // 如果没有选择分类，返回所有类型
        if (!this.selectedRelationshipTypeCategory) {
          console.log('  No category selected, returning all types');
          return this.relationshipTypes;
        }
        
        // 精确匹配分类
        const filtered = this.relationshipTypes.filter(type => {
          const matches = type.category === this.selectedRelationshipTypeCategory;
          if (matches) {
            console.log(`  Type ${type.type_name} matches category ${this.selectedRelationshipTypeCategory}`);
          }
          return matches;
        });
        
        console.log(`  Filtered ${filtered.length} relationship types for category ${this.selectedRelationshipTypeCategory}`);
        
        // 如果过滤结果为空，可能是因为分类不匹配，日志警告
        if (filtered.length === 0) {
          console.warn('  Warning: No relationship types match the selected category!');
          console.log('  Available categories in data:', [...new Set(this.relationshipTypes.map(t => t.category))]);
        }
        
        return filtered;
      },
      
      isNewRelationshipValid() {
        return this.newRelationship.type && this.newRelationship.targetEntity;
      },
      filteredNodes() {
        let result = this.nodes;
        
        // 过滤搜索查询
        if (this.searchQuery) {
          const query = this.searchQuery.toLowerCase();
          result = result.filter(node => 
            node.name.toLowerCase().includes(query) || 
            (node.description && node.description.toLowerCase().includes(query))
          );
        }
        
        // 过滤实体类型
        if (this.activeFilters.length > 0) {
          result = result.filter(node => this.activeFilters.includes(node.type));
        }
        
        return result;
      },
      
      filteredRelationships() {
        if (!this.filteredNodes.length) return [];
        
        const nodeIds = new Set(this.filteredNodes.map(node => node.id));
        return this.relationships.filter(rel => 
          nodeIds.has(rel.source) && nodeIds.has(rel.target)
        );
      }
    },
    methods: {
      togglePanel() {
        console.log(`Toggle panel - current state is ${this.isPanelCollapsed ? 'collapsed' : 'expanded'}`);
        this.isPanelCollapsed = !this.isPanelCollapsed;
        console.log(`Panel is now ${this.isPanelCollapsed ? 'collapsed' : 'expanded'}`);
      },
      
      filterNodes() {
        this.updateVisualization();
      },
      
      updateVisualization() {
        // Update visualization with filtered data
        console.log('Updating visualization with', this.filteredNodes.length, 'nodes and', this.filteredRelationships.length, 'relationships');
        
        // If we had the actual visualizer, we would call:
        // this.visualizer.updateData({
        //   nodes: this.filteredNodes,
        //   links: this.filteredRelationships
        // });
      },
      
      getEntityTypeIcon(typeCode) {
        const type = this.entityTypes.find(t => t.type_code === typeCode);
        return type && type.icon ? `fas ${type.icon}` : 'fas fa-circle';
      },
      async selectEntity(entity) {
        this.selectedEntity = entity;
        
        // In a real app, we would fetch real data
        // For now, generate some mock relationships
        this.entityRelationships = this.getMockRelationships(entity.id);
      },
      


      getMockRelationships(entityId) {
        // Generate mock relationships for demo purposes
        const rels = [];
        
        // Find incoming relationships
        this.relationships.forEach(rel => {
          if (rel.target === entityId) {
            const sourceEntity = this.nodes.find(n => n.id === rel.source);
            if (sourceEntity) {
              rels.push({
                id: rel.id,
                type: rel.type,
                direction: 'incoming',
                target: sourceEntity
              });
            }
          }
        });
        
        // Find outgoing relationships
        this.relationships.forEach(rel => {
          if (rel.source === entityId) {
            const targetEntity = this.nodes.find(n => n.id === rel.target);
            if (targetEntity) {
              rels.push({
                id: rel.id,
                type: rel.type,
                direction: 'outgoing',
                target: targetEntity
              });
            }
          }
        });
        
        return rels;
      },
      
      clearSelection() {
        this.selectedEntity = null;
        this.entityRelationships = [];
      },
      
      formatPropertyValue(value) {
        if (typeof value === 'object') {
          return JSON.stringify(value);
        }
        return value;
      },
      

      editEntity() {
        console.log('Edit entity:', this.selectedEntity);
        this.isEditing = true;
        this.editingEntity = JSON.parse(JSON.stringify(this.selectedEntity));
        
        this.editFormData = {
          name: this.selectedEntity.name,
          type: this.selectedEntity.type,
          description: this.selectedEntity.description || '',
          properties: {...this.selectedEntity.properties}
        };
        
        // 重置并直接设置分类，不使用 setTimeout
        this.selectedEntityTypeCategory = '';
        
        // 根据当前实体类型查找对应的分类并设置
        if (this.selectedEntity.type && this.entityTypes.length > 0) {
          const entityType = this.entityTypes.find(t => t.type_code === this.selectedEntity.type);
          if (entityType) {
            // 直接设置分类变量，不需要 setTimeout 和 forceUpdate
            this.selectedEntityTypeCategory = entityType.category;
            console.log('Updated selected entity category to:', this.selectedEntityTypeCategory);
          }
        }
      },
            
      traceKnowledge() {
        console.log('Trace knowledge for:', this.selectedEntity);
        // In a real app, this would navigate to a knowledge trace page
      },
      
      exploreContext() {
        console.log('Explore context for:', this.selectedEntity);
        // In a real app, this might expand the graph visualization
      },
      
      handleResize() {
        if (this.svg) {
          const container = this.$refs.graphContainer;
          if (container) {
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            // 更新SVG尺寸
            this.svg
              .attr('width', '100%')
              .attr('height', height);
            
            // 更新力模拟的中心力
            if (this.simulation) {
              this.simulation.force('center', d3.forceCenter(width / 2, height / 2))
                .alpha(0.3) // 重新加热模拟以触发调整
                .restart();
            }
          }
        }
      },

      handleEntityCategoryChange() {
        console.log('Entity category changed to:', this.selectedEntityTypeCategory);
        // 强制更新计算属性
        this.$forceUpdate();
      },
      
      // 添加新方法：处理关系类型分类变化
      handleRelationshipCategoryChange() {
        console.log('Relationship category changed to:', this.selectedRelationshipTypeCategory);
        // 强制更新计算属性
        this.$forceUpdate();
      },
      async fetchGraphData() {
        try {
          console.log('Fetching graph data...');
          this.loading = true;
          
          // First test if API is accessible
          try {
            console.log('Testing graph API endpoint...');
            const testResponse = await fetch('/api/v1/graph/test');
            console.log('Test response status:', testResponse.status);
            
            if (testResponse.ok) {
              const testData = await testResponse.json();
              console.log('Test endpoint response:', testData);
            } else {
              console.error('Test endpoint failed:', await testResponse.text());
            }
          } catch (testError) {
            console.error('Test endpoint error:', testError);
          }
          
          // Now try the actual data endpoint
          console.log('Fetching actual graph data...');
          const response = await fetch('/api/v1/graph');
          console.log('Response status:', response.status);
          
          if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response text:', errorText);
            throw new Error(`Failed to fetch graph data: ${response.status} - ${errorText || 'No error details'}`);
          }
          
          const data = await response.json();
          console.log('Graph data received:', data);
          
          // Handle empty result gracefully
          if (!data.nodes || data.nodes.length === 0) {
            console.log('No nodes found in database');
            // Still set empty arrays to avoid errors
            this.nodes = [];
            this.relationships = [];
            // Display empty graph with message
            const container = this.$refs.graphContainer;
            if (container) {
              container.innerHTML = '<div class="empty-graph-message"><i class="fas fa-info-circle"></i><p>知识图谱为空，请先通过文档提取知识</p></div>';
            }
            return;
          }
          
          // Update the local data
          this.nodes = data.nodes || [];
          this.relationships = data.links || [];
          
          // Initialize visualization with the new data
          this.initVisualization();
          
        } catch (error) {
          console.error('Error fetching graph data:', error);
          alert('获取图谱数据失败: ' + error.message);
        } finally {
          this.loading = false;
        }
      },

      initVisualization() {
        // Clear previous visualization
        const container = this.$refs.graphContainer;
        
        if (!container) {
          console.error('Graph container not found');
          return;
        }
        container.innerHTML = '';
        
        // Check if we have nodes to display
        if (!this.nodes || this.nodes.length === 0) {
          console.log('No nodes to display in graph');
          const emptyMessage = document.createElement('div');
          emptyMessage.className = 'empty-graph-message';
          emptyMessage.innerHTML = '<i class="fas fa-info-circle"></i><p>知识图谱为空，请先通过文档提取知识</p>';
          container.appendChild(emptyMessage);
          return;
        }

        console.log(`Initializing graph with ${this.nodes.length} nodes and ${this.relationships.length} links`);
        
        // Set up dimensions
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // Create SVG
        const svg = d3.select(container)
          .append('svg')
          .attr('width', '100%')  // 从固定宽度改为100%
          .attr('height', height)
          .attr('class', 'graph-svg')
          .style('position', 'absolute')
          .style('left', 0)     // 确保从左边缘开始
          .style('top', 0);     // 确保从顶部边缘开始
        
        // 保存svg引用用于后续调整大小
        this.svg = svg;
        // Add zoom functionality
        const zoom = d3.zoom()
          .scaleExtent([0.1, 4])
          .on('zoom', (event) => {
            g.attr('transform', event.transform);
          });
        
        svg.call(zoom);
        
        // Create container group for zoom
        const g = svg.append('g');
        
        // Define arrow markers for links
        svg.append('defs').selectAll('marker')
          .data(this.relationships.map(r => r.type))
          .enter().append('marker')
          .attr('id', d => `arrow-${d}`)
          .attr('viewBox', '0 -5 10 10')
          .attr('refX', 20)
          .attr('refY', 0)
          .attr('markerWidth', 6)
          .attr('markerHeight', 6)
          .attr('orient', 'auto')
          .append('path')
          .attr('fill', '#999')
          .attr('d', 'M0,-5L10,0L0,5');
        
        // Create links
        const link = g.append('g')
          .attr('class', 'links')
          .selectAll('line')
          .data(this.relationships)
          .enter().append('line')
          .attr('stroke', '#999')
          .attr('stroke-width', 1.5)
          .attr('marker-end', d => `url(#arrow-${d.type})`);
        
        // Create link labels
        const linkLabel = g.append('g')
          .attr('class', 'link-labels')
          .selectAll('text')
          .data(this.relationships)
          .enter().append('text')
          .attr('class', 'link-label')
          .attr('font-size', '8px')
          .attr('fill', '#666')
          .text(d => d.type);
        
        // Create nodes
        const node = g.append('g')
          .attr('class', 'nodes')
          .selectAll('g')
          .data(this.nodes)
          .enter().append('g')
          .attr('class', 'node')
          .call(d3.drag()
            .on('start', this.dragStarted)
            .on('drag', this.dragged)
            .on('end', this.dragEnded))
          .on('click', (event, d) => {
            this.selectEntity(d);
            event.stopPropagation();
          });
        
        // Add circle to each node
        node.append('circle')
          .attr('r', 10)
          .attr('fill', d => this.getNodeColor(d.type));
        
        // Add label to each node
        node.append('text')
          .attr('dy', -15)
          .attr('text-anchor', 'middle')
          .text(d => d.name)
          .attr('font-size', '10px');
        
        // Set up force simulation
        this.simulation = d3.forceSimulation(this.nodes)
          .force('link', d3.forceLink(this.relationships)
            .id(d => d.id)
            .distance(150))
          .force('charge', d3.forceManyBody().strength(-300))
          .force('center', d3.forceCenter(width / 2, height / 2))
          .force('collision', d3.forceCollide().radius(30))
          .on('tick', () => {
            // Update link positions
            link
              .attr('x1', d => d.source.x)
              .attr('y1', d => d.source.y)
              .attr('x2', d => d.target.x)
              .attr('y2', d => d.target.y);
            
            // Update link label positions
            linkLabel
              .attr('x', d => (d.source.x + d.target.x) / 2)
              .attr('y', d => (d.source.y + d.target.y) / 2);
            
            // Update node positions
            node
              .attr('transform', d => `translate(${d.x}, ${d.y})`);
          });
        
      },

      getEntityTypeName(typeCode) {
        const type = this.entityTypes.find(t => t.type_code === typeCode);
        return type ? type.type_name : typeCode;
      },
      
      getRelationshipTypeName(typeCode) {
        const type = this.relationshipTypes.find(t => t.type_code === typeCode);
        return type ? type.type_name : typeCode;
      },
      
      async searchTargetEntities() {
        if (!this.targetEntitySearch || this.targetEntitySearch.length < 2) {
          this.searchResults = [];
          return;
        }
        
        try {
          // First try to search entities from current loaded nodes (faster)
          const query = this.targetEntitySearch.toLowerCase();
          const localResults = this.nodes
            .filter(node => 
              node.id !== this.editingEntity.id && 
              node.name.toLowerCase().includes(query)
            )
            .slice(0, 10); // Limit to 10 results
          
          if (localResults.length > 0) {
            this.searchResults = localResults;
            return;
          }
          
          // If no local results, try to search from Neo4j
          const response = await fetch(`/api/v1/entities/search?query=${encodeURIComponent(this.targetEntitySearch)}&limit=10`);
          
          if (response.ok) {
            const data = await response.json();
            this.searchResults = data;
          } else {
            console.error('Error searching entities:', response.statusText);
            // Fall back to local search only
            this.searchResults = localResults;
          }
        } catch (error) {
          console.error('Error searching entities:', error);
          // In case of error, try local search
          const query = this.targetEntitySearch.toLowerCase();
          this.searchResults = this.nodes
            .filter(node => 
              node.id !== this.editingEntity.id && 
              node.name.toLowerCase().includes(query)
            )
            .slice(0, 10);
        }
      },
      
      selectTargetEntity(entity) {
        this.newRelationship.targetEntity = entity;
        this.targetEntitySearch = '';
        this.searchResults = [];
      },
      
      addRelationship() {
        if (!this.isNewRelationshipValid) return;
        
        // Check if relationship already exists to prevent duplicates
        const isDuplicate = this.entityRelationships.some(rel => 
          rel.direction === this.newRelationship.direction &&
          rel.type === this.newRelationship.type &&
          rel.target.id === this.newRelationship.targetEntity.id
        );
        
        if (isDuplicate) {
          alert('该关系已存在！');
          return;
        }
        
        const relationship = {
          id: 'temp-' + Date.now(),
          type: this.newRelationship.type,
          direction: this.newRelationship.direction,
          target: this.newRelationship.targetEntity
        };
        
        this.entityRelationships.push(relationship);
        
        // Reset the form
        this.newRelationship = {
          direction: 'outgoing',
          type: '',
          targetEntity: null
        };
        
        this.showAddRelationship = false;
        this.searchResults = [];
        this.targetEntitySearch = '';
      },
      resetRelationshipForm() {
        // 重置关系表单数据
        this.newRelationship = {
          direction: 'outgoing',
          type: '',
          targetEntity: null
        };
        
        // 直接设置默认分类，不使用 setTimeout
        this.selectedRelationshipTypeCategory = '基础类型';
        console.log('Reset relationship category to:', this.selectedRelationshipTypeCategory);
      },
      showAddRelationshipDialog() {
        console.log('Opening relationship dialog');
        
        // 重置关系表单
        this.resetRelationshipForm();
        
        // 显示对话框
        this.showAddRelationship = true;
      },
      removeRelationship(index) {
        if (confirm('确定要删除这个关系吗？')) {
          this.entityRelationships.splice(index, 1);
        }
      },
      saveEntityChanges() {
        console.log('Saving entity changes');
        
        // Check if we have an entity ID
        if (!this.editingEntity || !this.editingEntity.id) {
          alert('缺少实体ID，无法更新');
          return;
        }
        
        // Prepare the updated entity data
        const updatedEntity = {
          ...this.editingEntity,
          name: this.editFormData.name,
          type: this.editFormData.type,
          description: this.editFormData.description,
          properties: this.editFormData.properties
        };
        
        console.log('Sending update request for entity:', updatedEntity);
        
        // Call API to update entity
        fetch(`/api/v1/entities/${this.editingEntity.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updatedEntity)
        })
        .then(response => {
          console.log('Update response status:', response.status);
          if (!response.ok) {
            return response.text().then(text => {
              throw new Error(`Failed to update entity: ${response.status} - ${text || response.statusText}`);
            });
          }
          return response.json();
        })
        .then(data => {
          console.log('Update successful, received data:', data);
          
          // Update the entity in the nodes array
          const index = this.nodes.findIndex(node => node.id === data.id);
          if (index !== -1) {
            this.nodes[index] = data;
          }
          
          // Update selected entity
          this.selectedEntity = data;
          
          // Reset edit mode
          this.isEditing = false;
          this.editingEntity = null;
          
          // Reinitialize visualization
          this.fetchGraphData();
          
          // Show success message
          alert('实体更新成功');
        })
        .catch(error => {
          console.error('Error updating entity:', error);
          alert('更新失败: ' + error.message);
        });
      },

      cancelEdit() {
        this.isEditing = false;
        this.editingEntity = null;
      },

      addEntityProperty() {
        const key = prompt('请输入属性名称:');
        if (key && key.trim()) {
          this.editFormData.properties[key.trim()] = '';
        }
      },

      removeEntityProperty(key) {
        if (confirm(`确定要删除属性 "${key}" 吗?`)) {
          const updatedProperties = {...this.editFormData.properties};
          delete updatedProperties[key];
          this.editFormData.properties = updatedProperties;
        }
      },
      // Add these helper methods
      dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      },

      dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      },

      dragEnded(event,d) {
        if (!event.active) this.simulation.alphaTarget(0);
        // Keep nodes fixed where they're dragged
         d.fx = null;
         d.fy = null;
      },

      getNodeColor(type) {
        const colorMap = {
          'person': '#ff7f0e',
          'organization': '#1f77b4',
          'location': '#2ca02c',
          'concept': '#d62728',
          'time': '#9467bd',
          'event': '#8c564b'
        };
        return colorMap[type] || '#aaa';
      }
    },
    async mounted() {
      console.log('Graph component mounted, fetching graph data...');
      //this.fetchEntityTypes();
      await this.fetchGraphData();
      //this.fetchRelationshipTypes();
      // 初始化分类数据 - 这里直接从静态数据计算出来
      this.entityTypeCategories = [...new Set(this.entityTypes.map(type => type.category))];
      this.relationshipTypeCategories = [...new Set(this.relationshipTypes.map(type => type.category))];
      
      console.log('Entity type categories:', this.entityTypeCategories);
      console.log('Relationship type categories:', this.relationshipTypeCategories);
      window.addEventListener('resize', this.handleResize);
    },
    beforeUnmount() {
      window.removeEventListener('resize', this.handleResize);
    },
    watch: {
      activeFilters() {
        this.updateVisualization();
      }
    }

  };
  </script>
  
  <style scoped>
  .graph-view {
    display: grid;
    grid-template-columns: auto 1fr auto;
    grid-template-rows: 100%;
    height: calc(100vh - var(--header-height) - var(--footer-height) - 40px);
    overflow: hidden;
  }
  
  .control-panel {
    width: 300px;
    background-color: var(--card-bg);
    border-right: 1px solid var(--border-color);
    transition: width 0.3s;
    overflow: hidden;
  }
  
  .control-panel.collapsed {
    width: 50px;
    overflow: visible;
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border-bottom: 1px solid var(--border-color);
    min-width: 50px;
    position: relative;

  }
  
  .toggle-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: var(--text-color);
    z-index: 10;
  }
  
  .panel-content {
    padding: 15px;
    overflow-y: auto;
    height: calc(100% - 60px);
  }
  
  .search-box {
    position: relative;
    margin-bottom: 20px;
  }
  
  .search-box input {
    width: 100%;
    padding: 8px 10px 8px 30px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-color);
    color: var(--text-color);
  }
  
  .search-box i {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #999;
  }
  
  .filter-section {
    margin-bottom: 20px;
  }
  
  .filter-section h3 {
    font-size: 1rem;
    margin-bottom: 10px;
  }
  
  .type-filters {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .filter-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }
  
  .node-badge {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  
  .node-badge.person { background-color: #ff7f0e; }
  .node-badge.organization { background-color: #1f77b4; }
  .node-badge.location { background-color: #2ca02c; }
  .node-badge.concept { background-color: #d62728; }
  .node-badge.time { background-color: #9467bd; }
  .node-badge.event { background-color: #8c564b; }
  
  .graph-area {
    position: relative;
    overflow: hidden;
    background-color: #f5f5f5;
  }
  
  .graph-container {
    width: 100%;
    height: 100%;
    color: #999;
    font-style: italic;
  }
  

  
  .detail-panel {
    position: relative;
    width: 350px;
    background-color: var(--card-bg);
    border-left: 1px solid var(--border-color);
    overflow: auto;
  }
  
  .close-detail {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 32px;
    height: 32px;
    background: rgba(255, 255, 255, 0.8); /* Add background to prevent overlap */
    border: 1px solid #eee;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    cursor: pointer;
    color: #666;
    z-index: 20; /* Ensure it's above other content */
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
  
  .close-detail:hover {
    background: #f5f5f5;
    color: #333;
    }

  .entity-detail-container {
    height: 100%;
    overflow-y: auto;
    background-color: #fff;
    border-radius: 4px;
  }
  
  .entity-card {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .entity-header {
    padding: 16px 50px 16px 16px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .entity-header.person { background-color: rgba(255, 127, 14, 0.1); }
  .entity-header.organization { background-color: rgba(31, 119, 180, 0.1); }
  .entity-header.location { background-color: rgba(44, 160, 44, 0.1); }
  .entity-header.concept { background-color: rgba(214, 39, 40, 0.1); }
  .entity-header.time { background-color: rgba(148, 103, 189, 0.1); }
  .entity-header.event { background-color: rgba(140, 86, 75, 0.1); }
  
  .entity-type-badge {
    font-size: 0.8rem;
    padding: 2px 8px;
    border-radius: 12px;
    background-color: #f0f0f0;
  }
  
  .entity-body {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
  }
  
  .entity-description {
    margin-bottom: 16px;
    line-height: 1.6;
    color: #555;
  }
  
  .entity-properties, .entity-relationships {
    margin-bottom: 20px;
  }
  
  h3 {
    font-size: 1.1rem;
    margin-bottom: 12px;
    padding-bottom: 4px;
    border-bottom: 1px solid #eee;
  }
  
  .property-item {
    display: flex;
    margin-bottom: 8px;
  }
  
  .property-key {
    font-weight: 500;
    width: 120px;
    flex-shrink: 0;
  }
  
  .property-value {
    flex: 1;
    word-break: break-word;
  }
  
  .relationship-item {
    display: flex;
    align-items: center;
    padding: 8px;
    border-radius: 4px;
    margin-bottom: 4px;
    cursor: pointer;
    background-color: #f9f9f9;
    transition: background-color 0.2s;
  }
  
  .relationship-item:hover {
    background-color: #f0f0f0;
  }
  
  .relationship-direction {
    width: 24px;
    text-align: center;
    margin-right: 8px;
  }
  
  .relationship-type {
    width: 100px;
    font-weight: 500;
    margin-right: 8px;
  }
  
  .related-entity {
    flex: 1;
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  .entity-actions {
    padding: 12px 16px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: space-between;
  }
  
  .btn {
    padding: 8px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .edit-btn {
    background-color: #f0f0f0;
    color: #333;
  }
  
  .trace-btn {
    background-color: #e1f5fe;
    color: #0277bd;
  }
  
  .explore-btn {
    background-color: #e8f5e9;
    color: #2e7d32;
  }
  
  .no-data {
    color: #999;
    font-style: italic;
    padding: 12px 0;
  }
  
  /* Responsive styles */
  @media (max-width: 1200px) {
    .graph-view {
      display: flex;
      flex-direction: column;
      height: auto;
    }
    
    .control-panel {
      width: 100%;
      border-right: none;
      border-bottom: 1px solid var(--border-color);
    }
    
    
    .panel-content {
      padding: 10px;
    }
    
    .type-filters {
      flex-direction: row;
      flex-wrap: wrap;
      gap: 12px;
    }
    
    .graph-area {
      height: 60vh;
    }
    
    .detail-panel {
      width: 100%;
      border-left: none;
      border-top: 1px solid var(--border-color);
    }
  }
  

  .empty-graph-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #999;
    }

  .empty-graph-message i {
    font-size: 3rem;
    margin-bottom: 1rem;
    }

  .graph-svg {
    width: 100%;
    height: 100%;
    background-color: #f9f9f9;
  }

  .reset-button {
    position: absolute;
    bottom: 20px;
    right: 20px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: white;
    border: 1px solid #ddd;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .nodes circle {
    stroke: white;
    stroke-width: 1.5px;
  }

  .nodes text {
    pointer-events: none;
  }

  .links line {
    stroke-opacity: 0.6;
  }

  .link-label {
    pointer-events: none;
  }

  .control-panel.collapsed .panel-content {
    display: none;
  }

  /* Ensure toggle button always visible and styled properly */
  

  .toggle-button:hover {
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: 50%;
  }

  .control-panel.collapsed .panel-header h2 {
    display: none; /* Hide title when collapsed but keep toggle button */
  }

  .control-panel.collapsed .toggle-button {
    position: absolute;
    right: 10px;
    top: 15px;
  }
    /* Edit modal styles */
  .edit-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .edit-modal-content {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
    width: 650px;
    max-width: 95%;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
  }

  .edit-modal-header {
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .edit-modal-header h3 {
    font-size: 18px;
    margin: 0;
    color: #333;
    font-weight: 600;
  }
  .edit-modal-content {
    padding: 16px 24px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #f8f9fa;
    border-radius: 8px 8px 0 0;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 18px;
    color: #666;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s;
  }
  .close-btn:hover {
    background-color: #f0f0f0;
    color: #333;
  }
  .modal-body {
    padding: 24px;
  }
  
  .edit-modal-body {
    padding: 24px;
    overflow-y: auto;
    max-height: calc(85vh - 130px);
  }

  .edit-modal-footer {
    padding: 16px 24px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    background-color: #f8f9fa;
    border-radius: 0 0 8px 8px;
  }

  .form-group {
    margin-bottom: 18px;
  }

  .form-group:last-child {
    margin-bottom: 0;
  }

  .form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
    color: #444;
    font-size: 14px;
  }

  .form-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    background-color: white;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .form-input:focus {
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    outline: none;
  }

  textarea.form-input {
    min-height: 80px;
    resize: vertical;
  }
  .property-edit-row {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    border-bottom: 1px solid #f0f0f0;
  }
  .property-edit-row:last-child {
    border-bottom: none;
  }
  .property-key {
    width: 120px;
    font-weight: 500;
    color: #555;
    padding-right: 10px;
  }

  .property-value-input {
    flex: 1;
    padding: 8px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }

  .add-property-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background-color: #e8f5e9;
    color: #2e7d32;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 12px;
    transition: background-color 0.2s;
  }
  .add-property-btn:hover {
    background-color: #c8e6c9;
  }
  .remove-property-btn {
    background: none;
    border: none;
    color: #d9534f;
    cursor: pointer;
    padding: 0 5px;
  }
  .remove-property-btn:hover {
    background-color: #ffebee;
  }

  .save-btn {
    padding: 8px 20px;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .save-btn:hover {
    background-color: #43a047;
  }
  .cancel-btn {
    padding: 8px 20px;
    background-color: #f5f5f5;
    color: #333;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .cancel-btn:hover {
    background-color: #e0e0e0;
  }
  /* Type selector styles */
  .type-selector {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 0;
  }

  .category-select, .type-select {
    width: 100%;
    height: 40px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    background-color: white;
    transition: border-color 0.2s;
  }
  .category-select:focus, .type-select:focus {
    border-color: #4a90e2;
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    outline: none;
  }

  .type-selector-label {
    display: block;
    font-weight: 500;
    margin-bottom: 6px;
    color: #555;
    font-size: 13px;
  }
  /* Relationship section styles */
  .relationships-section {
    margin-top: 20px;
    border-top: 1px solid #eee;
    padding-top: 20px;
  }

  .add-relationship-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background-color: #e1f5fe;
    color: #0277bd;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 12px;
    transition: background-color 0.2s;
  }

  .add-relationship-btn:hover {
    background-color: #b3e5fc;
  }
  .no-relationships {
    color: #999;
    font-style: italic;
    padding: 10px 0;
  }

  .entity-relationships-list {
    margin-top: 10px;
    max-height: 200px;
    overflow-y: auto;
  }

  .relationship-edit-row {
    display: flex;
    align-items: center;
    padding: 10px 12px;
    border-bottom: 1px solid #f0f0f0;
  }

  .relationship-direction {
    width: 30px;
    text-align: center;
  }

  .relationship-type {
    width: 100px;
    font-weight: 500;
  }

  .related-entity {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .remove-relationship-btn {
    background: none;
    border: none;
    color: #d9534f;
    cursor: pointer;
    padding: 0 5px;
  }

  /* Add relationship modal styles */
  .add-relationship-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1100;
  }

  .add-relationship-content {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    width: 550px;
    max-width: 95%;
    display: flex;
    flex-direction: column;
  }

  .direction-selector {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 20px;
    background-color: #f5f7fa;
    padding: 16px;
    border-radius: 6px;
  }

  .entity-search {
    position: relative;
  }

  .search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 10;
  }

  .search-result-item {
    padding: 8px 12px;
    cursor: pointer;
    border-bottom: 1px solid #eee;
  }

  .search-result-item:last-child {
    border-bottom: none;
  }

  .search-result-item:hover {
    background-color: #f5f5f5;
  }

  .selected-target-entity {
    margin-top: 10px;
    padding: 8px;
    background-color: #e3f2fd;
    border-radius: 4px;
    color: #0277bd;
  }

  /* Add these styles to the <style> section in Graph.vue */
  .form-section {
    margin-bottom: 24px;
    border: 1px solid #eaeaea;
    border-radius: 8px;
    padding: 20px;
    background-color: #fff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
  .form-section:last-child {
    margin-bottom: 0;
  }
  .section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eee;
    color: #444;
  }

  .property-actions, .relationship-actions {
    margin-bottom: 12px;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .add-btn {
    background-color: #e8f5e9;
    color: #2e7d32;
  }

  .add-btn:hover {
    background-color: #c8e6c9;
  }

  .remove-btn {
    background: none;
    color: #d32f2f;
    padding: 4px 8px;
  }

  .remove-btn:hover {
    background-color: #ffebee;
  }

  .relationships-list {
    background-color: white;
    border: 1px solid #eee;
    border-radius: 6px;
    max-height: 180px;
    overflow-y: auto;
  }
  .properties-list {
    background-color: white;
    border: 1px solid #eee;
    border-radius: 6px;
    max-height: 180px;
    overflow-y: auto;
  }
  
  .property-edit-row:last-child, .relationship-edit-row:last-child {
    border-bottom: none;
  }

  .property-key {
    width: 120px;
    font-weight: 500;
    color: #555;
  }

  .property-value-input {
    flex: 1;
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }

  .no-data-message {
    padding: 16px;
    text-align: center;
    color: #999;
    font-style: italic;
    background-color: #fff;
    border: 1px dashed #ddd;
    border-radius: 4px;

  .radio-option {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.2s;
  }

  .radio-option:hover {
    background-color: #edf2f7;
  }

  .radio-option input[type="radio"] {
    width: 18px;
    height: 18px;
  }
  .entity-search-wrapper {
    position: relative;
  }

  .search-input {
    width: 100%;
    padding-right: 30px;
  }

  .search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 10;
    max-height: 200px;
    overflow-y: auto;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 0 0 4px 4px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .search-result-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    cursor: pointer;
    border-bottom: 1px solid #eee;
    transition: background-color 0.2s;
  }

  .search-result-item:last-child {
    border-bottom: none;
  }

  .search-result-item:hover {
    background-color: #f5f5f5;
  }

  .search-result-item i {
    font-size: 14px;
    width: 20px;
    text-align: center;
  }

  .search-result-item small {
    color: #999;
    margin-left: auto;
  }

  .selected-target-entity {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    padding: 8px 12px;
    background-color: #e3f2fd;
    border-radius: 4px;
    color: #0277bd;
  }

  .clear-entity-btn {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    margin-left: auto;
  }

  .clear-entity-btn:hover {
    color: #d32f2f;
  }
  .save-btn:disabled {
    background-color: #a5d6a7;
    cursor: not-allowed;
  }

  }
  </style>