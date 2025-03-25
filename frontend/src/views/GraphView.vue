<!-- views/GraphView.vue -->
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
          
          <!-- 其他控制选项... -->
        </div>
      </div>
      
      <div class="graph-area">
        <div class="graph-container" ref="graphContainer"></div>
      </div>
      
      <div class="detail-panel" v-if="selectedEntity">
        <entity-detail 
          :entity="selectedEntity" 
          :relationships="entityRelationships"
          @select-entity="selectEntity"
          @view-source="viewSource"
          @trace-knowledge="traceKnowledge"
          @explore-context="exploreContext"
        ></entity-detail>
        
        <button class="close-detail" @click="clearSelection">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
  </template>
  
  <script>
  import EntityDetail from '@/components/graph/EntityDetail.vue';
  import { KnowledgeGraphVisualizer } from '@/utils/graph-visualization';
  import { mapState, mapActions } from 'vuex';
  
  export default {
    name: 'GraphView',
    components: {
      EntityDetail
    },
    data() {
      return {
        isPanelCollapsed: false,
        searchQuery: '',
        activeFilters: [],
        selectedEntity: null,
        entityRelationships: [],
        visualizer: null
      };
    },
    computed: {
      ...mapState('graph', ['nodes', 'relationships']),
      
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
      ...mapActions('graph', ['fetchGraph', 'fetchEntityRelationships']),
      
      togglePanel() {
        this.isPanelCollapsed = !this.isPanelCollapsed;
      },
      
      filterNodes() {
        if (this.visualizer) {
          this.updateVisualization();
        }
      },
      
      updateVisualization() {
        const graphData = {
          nodes: this.filteredNodes,
          links: this.filteredRelationships.map(rel => ({
            source: rel.source,
            target: rel.target,
            type: rel.type,
            id: rel.id
          }))
        };
        
        this.visualizer.updateData(graphData);
      },
      
      async selectEntity(entity) {
        this.selectedEntity = entity;
        
        try {
          const relationships = await this.fetchEntityRelationships(entity.id);
          this.entityRelationships = relationships;
        } catch (error) {
          console.error('Error fetching entity relationships:', error);
          this.entityRelationships = [];
        }
      },
      
      clearSelection() {
        this.selectedEntity = null;
        this.entityRelationships = [];
      },
      
      viewSource(source) {
        this.$router.push({ 
          name: 'document-view', 
          params: { id: source.id } 
        });
      },
      
      traceKnowledge(entity) {
        this.$router.push({ 
          name: 'knowledge-trace', 
          params: { 
            type: 'entity',
            id: entity.id 
          } 
        });
      },
      
      exploreContext(entity) {
        // 实现上下文探索，例如展开节点周围的实体
        if (this.visualizer) {
          this.visualizer.focusOnNode(entity.id);
        }
      }
    },
    async mounted() {
      // 获取图谱数据
      try {
        await this.fetchGraph();
        
        // 初始化可视化
        this.visualizer = new KnowledgeGraphVisualizer(
          this.$refs.graphContainer, 
          {
            nodes: this.filteredNodes,
            links: this.filteredRelationships.map(rel => ({
              source: rel.source,
              target: rel.target,
              type: rel.type,
              id: rel.id
            }))
          },
          {
            onNodeClick: this.selectEntity
          }
        );
        
        // 设置所有类型为默认选中
        this.activeFilters = [...this.entityTypes];
        
        // 响应窗口大小变化
        window.addEventListener('resize', this.handleResize);
      } catch (error) {
        console.error('Error initializing graph view:', error);
      }
    },
    beforeUnmount() {
      window.removeEventListener('resize', this.handleResize);
    },
    methods: {
      handleResize() {
        if (this.visualizer) {
          this.visualizer.resetView();
        }
      }
    },
    watch: {
      activeFilters() {
        if (this.visualizer) {
          this.updateVisualization();
        }
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
  }
  
  .graph-container {
    width: 100%;
    height: 100%;
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