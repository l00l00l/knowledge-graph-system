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
          <div v-if="isEditing" class="edit-modal">
            <div class="edit-modal-content">
              <div class="edit-modal-header">
                <h3>编辑实体</h3>
                <button @click="cancelEdit" class="close-btn">
                  <i class="fas fa-times"></i>
                </button>
              </div>
              
              <div class="edit-modal-body">
                <div class="form-group">
                  <label>名称</label>
                  <input type="text" v-model="editFormData.name" class="form-input">
                </div>
                
                <div class="form-group">
                  <label>类型</label>
                  <div class="type-selector">
                    <select v-model="selectedEntityTypeCategory" class="form-input category-select">
                      <option value="">-- 选择类型分类 --</option>
                      <option v-for="category in entityTypeCategories" :key="category">
                        {{ category }}
                      </option>
                    </select>
                    
                    <select v-model="editFormData.type" class="form-input type-select">
                      <option value="">-- 选择类型 --</option>
                      <option v-for="type in filteredEntityTypes" :key="type.type_code" :value="type.type_code">
                        {{ type.type_name }}
                      </option>
                    </select>
                  </div>
                </div>
                
                <div class="form-group">
                  <label>描述</label>
                  <textarea v-model="editFormData.description" class="form-input" rows="3"></textarea>
                </div>
                
                <div class="form-group">
                  <label>属性</label>
                  <button @click="addEntityProperty" class="add-property-btn">
                    <i class="fas fa-plus"></i> 添加属性
                  </button>
                  
                  <div v-for="(value, key) in editFormData.properties" :key="key" class="property-edit-row">
                    <div class="property-key">{{ key }}:</div>
                    <input type="text" v-model="editFormData.properties[key]" class="property-value-input">
                    <button @click="removeEntityProperty(key)" class="remove-property-btn">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
                
                <!-- 添加关系管理区域 -->
                <div class="form-group relationships-section">
                  <label>关系</label>
                  <button @click="showAddRelationship = true" class="add-relationship-btn">
                    <i class="fas fa-plus"></i> 添加关系
                  </button>
                  
                  <div v-if="entityRelationships.length === 0" class="no-relationships">
                    暂无关系数据
                  </div>
                  
                  <div v-else class="entity-relationships-list">
                    <div v-for="(rel, index) in entityRelationships" :key="index" class="relationship-edit-row">
                      <div class="relationship-direction">
                        <i :class="rel.direction === 'outgoing' ? 'fas fa-arrow-right' : 'fas fa-arrow-left'"></i>
                      </div>
                      <div class="relationship-type">{{ getRelationshipTypeName(rel.type) }}</div>
                      <div class="related-entity">{{ rel.target.name }}</div>
                      <button @click="removeRelationship(index)" class="remove-relationship-btn">
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                </div>
                <!-- 添加关系对话框 -->
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
                          <label>
                            <input type="radio" v-model="newRelationship.direction" value="outgoing">
                            <span>出发 ({{ editFormData.name }} → 目标)</span>
                          </label>
                          <label>
                            <input type="radio" v-model="newRelationship.direction" value="incoming">
                            <span>接收 (目标 → {{ editFormData.name }})</span>
                          </label>
                        </div>
                      </div>
                      
                      <div class="form-group">
                        <label>关系类型</label>
                        <div class="type-selector">
                          <select v-model="selectedRelationshipTypeCategory" class="form-input category-select">
                            <option value="">-- 选择关系类型分类 --</option>
                            <option v-for="category in relationshipTypeCategories" :key="category">
                              {{ category }}
                            </option>
                          </select>
                          
                          <select v-model="newRelationship.type" class="form-input type-select">
                            <option value="">-- 选择关系类型 --</option>
                            <option v-for="type in filteredRelationshipTypes" :key="type.type_code" :value="type.type_code">
                              {{ type.type_name }}
                            </option>
                          </select>
                        </div>
                      </div>
                      
                      <div class="form-group">
                        <label>目标实体</label>
                        <div class="entity-search">
                          <input 
                            type="text" 
                            v-model="targetEntitySearch" 
                            @input="searchTargetEntities"
                            placeholder="搜索实体..." 
                            class="form-input"
                          >
                          
                          <div v-if="searchResults.length > 0" class="search-results">
                            <div 
                              v-for="entity in searchResults" 
                              :key="entity.id" 
                              class="search-result-item"
                              @click="selectTargetEntity(entity)"
                            >
                              {{ entity.name }} ({{ getEntityTypeName(entity.type) }})
                            </div>
                          </div>
                        </div>
                        
                        <div v-if="newRelationship.targetEntity" class="selected-target-entity">
                          已选择: {{ newRelationship.targetEntity.name }}
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
              
              <div class="edit-modal-footer">
                <button @click="cancelEdit" class="btn cancel-btn">取消</button>
                <button @click="saveEntityChanges" class="btn save-btn">保存</button>
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
        entityTypes: [],
        relationshipTypes: [],
        entityTypeCategories: [],
        relationshipTypeCategories: [],
        selectedEntityTypeCategory: '',
        selectedRelationshipTypeCategory: '',
        showAddRelationship: false,
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
        ]
      };
    },
    computed: {
      entityTypes() {
        return [...new Set(this.nodes.map(node => node.type))];
      },
      

      filteredEntityTypes() {
        if (!this.selectedEntityTypeCategory) return this.entityTypes;
        return this.entityTypes.filter(type => type.category === this.selectedEntityTypeCategory);
      },
      
      filteredRelationshipTypes() {
        if (!this.selectedRelationshipTypeCategory) return this.relationshipTypes;
        return this.relationshipTypes.filter(type => type.category === this.selectedRelationshipTypeCategory);
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
        this.editingEntity = JSON.parse(JSON.stringify(this.selectedEntity)); // Create a deep copy
        this.editFormData = {
          name: this.selectedEntity.name,
          type: this.selectedEntity.type,
          description: this.selectedEntity.description || '',
          properties: {...this.selectedEntity.properties}
        };
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
        console.log('Window resized, reinitializing visualization');
        this.initVisualization();
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

      async fetchEntityTypes() {
        try {
          const response = await fetch('/api/v1/entity-types');
          if (response.ok) {
            const data = await response.json();
            this.entityTypes = data;
            
            // Extract unique categories
            this.entityTypeCategories = [...new Set(data.map(type => type.category))];
            console.log('Loaded entity types:', data);
          } else {
            console.error('Failed to load entity types:', response.statusText);
          }
        } catch (error) {
          console.error('Error fetching entity types:', error);
        }
      },

      async fetchRelationshipTypes() {
        try {
          const response = await fetch('/api/v1/relationship-types');
          if (response.ok) {
            const data = await response.json();
            this.relationshipTypes = data;
            
            // Extract unique categories
            this.relationshipTypeCategories = [...new Set(data.map(type => type.category))];
            console.log('Loaded relationship types:', data);
          } else {
            console.error('Failed to load relationship types:', response.statusText);
          }
        } catch (error) {
          console.error('Error fetching relationship types:', error);
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
          .attr('width', width)
          .attr('height', height)
          .attr('class', 'graph-svg')
          .style('position', 'absolute');
        
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
      
      searchTargetEntities() {
        if (!this.targetEntitySearch) {
          this.searchResults = [];
          return;
        }
        
        const query = this.targetEntitySearch.toLowerCase();
        this.searchResults = this.nodes
          .filter(node => 
            node.id !== this.editingEntity.id && 
            node.name.toLowerCase().includes(query)
          )
          .slice(0, 5); // Limit to 5 results
      },
      
      selectTargetEntity(entity) {
        this.newRelationship.targetEntity = entity;
        this.targetEntitySearch = '';
        this.searchResults = [];
      },
      
      addRelationship() {
        if (!this.isNewRelationshipValid) return;
        
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
    mounted() {
      console.log('Graph component mounted, fetching graph data...');
      this.fetchEntityTypes();
      this.fetchGraphData();
      this.fetchRelationshipTypes();
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
    display: flex;
    align-items: center;
    justify-content: center;
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
  
  @media (max-width: 768px) {
    .graph-area {
      height: 50vh;
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
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    width: 500px;
    max-width: 90%;
    max-height: 90vh;
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

  .edit-modal-body {
    padding: 20px;
    overflow-y: auto;
    max-height: 60vh;
  }

  .edit-modal-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
  }

  .form-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }

  .property-edit-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }

  .property-key {
    width: 120px;
    font-weight: 500;
  }

  .property-value-input {
    flex: 1;
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }

  .add-property-btn {
    background-color: #e8f5e9;
    color: #2e7d32;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 10px;
  }

  .remove-property-btn {
    background: none;
    border: none;
    color: #d9534f;
    cursor: pointer;
    padding: 0 5px;
  }

  .save-btn {
    background-color: #4caf50;
    color: white;
  }

  .cancel-btn {
    background-color: #f0f0f0;
    color: #333;
  }

  /* Type selector styles */
  .type-selector {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
  }

  .category-select {
    width: 40%;
  }

  .type-select {
    width: 60%;
  }

  /* Relationship section styles */
  .relationships-section {
    margin-top: 20px;
    border-top: 1px solid #eee;
    padding-top: 20px;
  }

  .add-relationship-btn {
    background-color: #e1f5fe;
    color: #0277bd;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    cursor: pointer;
    margin-bottom: 10px;
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
    padding: 8px;
    background-color: #f5f5f5;
    border-radius: 4px;
    margin-bottom: 5px;
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
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    width: 500px;
    max-width: 90%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
  }

  .direction-selector {
    display: flex;
    gap: 20px;
    margin-bottom: 10px;
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
  }
  </style>