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
        
        <!-- Make sure this div is present and correctly positioned -->
        <div class="graph-controls">
          <button @click="zoomIn" title="放大">
            <i class="fas fa-search-plus"></i>
          </button>
          <button @click="zoomOut" title="缩小">
            <i class="fas fa-search-minus"></i>
          </button>
          <button @click="resetView" title="重置视图">
            <i class="fas fa-home"></i>
          </button>
        </div>
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
          .attr('class', 'graph-svg');
        
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
        
        // Center the graph initially
        this.resetView();
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

      // Make sure these methods are included in your methods section
      zoomIn() {
        if (!this.svg || !this.zoom) return;
        this.svg.transition().duration(300).call(
          this.zoom.scaleBy, 1.3
        );
      },

      zoomOut() {
        if (!this.svg || !this.zoom) return;
        this.svg.transition().duration(300).call(
          this.zoom.scaleBy, 0.7
        );
      },

      resetView() {
        if (!this.svg || !this.zoom) return;
        
        const container = this.$refs.graphContainer;
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        this.svg.transition().duration(750).call(
          this.zoom.transform,
          d3.zoomIdentity.translate(width/2, height/2).scale(0.8)
        );
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
      this.fetchGraphData();
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

  .graph-controls {
    position: absolute;
    bottom: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 100; /* Increase z-index to ensure visibility */
    background-color: rgba(255, 255, 255, 0.8); /* Add background to make buttons stand out */
    padding: 5px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .graph-controls button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: white;
    border: 1px solid #ddd;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 14px; /* Ensure icons are large enough */
    color: #333; /* Make icons visible */
  }

  .graph-controls button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    background-color: #f0f0f0;
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
  }
  </style>