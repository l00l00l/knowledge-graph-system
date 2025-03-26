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
        </div>
        
        <button class="close-detail" @click="clearSelection">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
  </template>
  
  <script>
  // import { KnowledgeGraphVisualizer } from '@/utils/graph-visualization';
  
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
        this.isPanelCollapsed = !this.isPanelCollapsed;
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
        // In a real app, this would open an edit dialog
      },
      
      traceKnowledge() {
        console.log('Trace knowledge for:', this.selectedEntity);
        // In a real app, this would navigate to a knowledge trace page
      },
      
      exploreContext() {
        console.log('Explore context for:', this.selectedEntity);
        // In a real app, this might expand the graph visualization
      },
      
      initVisualization() {
        // In a real app, we would initialize the graph visualization
        // using the GraphViewer component or D3.js directly
        console.log('Initializing graph visualization...');
        
        // For now, just log that we would initialize the visualization
        // with the filtered nodes and relationships
        console.log('Graph would show:', this.filteredNodes.length, 'nodes and', this.filteredRelationships.length, 'relationships');
        
        // Set default filters to all entity types
        this.activeFilters = [...this.entityTypes];
      },
      
      handleResize() {
        // In a real app, we would resize the visualization
        console.log('Handling resize event...');
      }
    },
    mounted() {
      this.initVisualization();
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
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    border-bottom: 1px solid var(--border-color);
  }
  
  .toggle-button {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: var(--text-color);
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
  
  .graph-container::after {
    content: 'Graph visualization will be rendered here';
    font-size: 1.2rem;
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
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: var(--text-color);
    z-index: 10;
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
    padding: 16px;
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
    
    .control-panel.collapsed {
      width: 100%;
      height: 50px;
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
  }
  </style>