<!-- GraphViewer.vue -->
<template>
  <div class="graph-container" ref="graphContainer">
    <div class="controls">
      <button @click="zoomIn"><i class="fas fa-search-plus"></i></button>
      <button @click="zoomOut"><i class="fas fa-search-minus"></i></button>
      <button @click="resetView"><i class="fas fa-home"></i></button>
      <div class="filter-controls">
        <select v-model="activeFilter" @change="applyFilter">
          <option value="all">所有实体类型</option>
          <option v-for="type in entityTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>
    </div>
    <div class="graph-view" ref="graphView"></div>
    <div class="graph-legend">
      <div v-for="type in visibleTypes" :key="type" class="legend-item">
        <span :class="['node-badge', type]"></span>
        <span>{{ type }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';
import { KnowledgeGraphVisualizer } from '@/utils/graph-visualization';

export default {
  name: 'GraphViewer',
  props: {
    nodes: {
      type: Array,
      required: true
    },
    relationships: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      simulation: null,
      svg: null,
      activeFilter: 'all',
      visibleTypes: [],
      zoom: null
    };
  },
  computed: {
    entityTypes() {
      // 从节点数据中提取所有实体类型
      return [...new Set(this.nodes.map(node => node.type))];
    }
  },
  mounted() {
    this.initializeGraph();
    window.addEventListener('resize', this.resizeGraph);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeGraph);
    if (this.simulation) {
      this.simulation.stop();
    }
  },
  methods: {
    initializeGraph() {
      const container = this.$refs.graphView;
      const width = container.clientWidth;
      const height = container.clientHeight;
      const graphData = {
        nodes: this.nodes,
        links: this.relationships
      };
      
      this.visualizer = new KnowledgeGraphVisualizer(container, graphData, {
        onNodeClick: this.handleNodeClick
      });
    },
    handleNodeClick(node) {
      this.$emit('node-selected', node);
      
      this.visibleTypes = this.entityTypes;
      
      // 初始化SVG
      this.svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('class', 'graph-svg');
      
      // 创建缩放行为
      this.zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          this.svg.select('g.graph-container')
            .attr('transform', event.transform);
        });
      
      this.svg.call(this.zoom);
      
      // 添加箭头标记
      this.svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('xoverflow', 'visible')
        .append('svg:path')
        .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
        .attr('fill', '#999')
        .style('stroke', 'none');
      
      // 创建容器组
      const g = this.svg.append('g')
        .attr('class', 'graph-container');
      
      // 创建力导向模拟
      this.simulation = d3.forceSimulation(this.nodes)
        .force('link', d3.forceLink(this.relationships)
          .id(d => d.id)
          .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(60))
        .on('tick', this.ticked);
      
      // 创建连接线
      this.links = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(this.relationships)
        .enter()
        .append('line')
        .attr('stroke-width', 1.5)
        .attr('stroke', '#999')
        .attr('marker-end', 'url(#arrowhead)');
      
      // 创建节点
      this.nodeGroup = g.append('g')
        .attr('class', 'nodes');
      
      this.nodes = this.nodeGroup
        .selectAll('g')
        .data(this.nodes)
        .enter()
        .append('g')
        .attr('class', d => `node ${d.type}`)
        .call(d3.drag()
          .on('start', this.dragStarted)
          .on('drag', this.dragged)
          .on('end', this.dragEnded));
      
      // 添加节点圆形
      this.nodes.append('circle')
        .attr('r', 10)
        .attr('fill', d => this.getColorByType(d.type));
      
      // 添加节点标签
      this.nodes.append('text')
        .attr('dy', -15)
        .attr('text-anchor', 'middle')
        .text(d => d.name)
        .attr('font-size', '12px');
      
      this.resetView();
    },
    ticked() {
      // 更新连线位置
      this.links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      // 更新节点位置
      this.nodes
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
    },
    dragStarted(event, d) {
      if (!event.active) this.simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    },
    dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    },
    dragEnded(event, d) {
      if (!event.active) this.simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    },
    getColorByType(type) {
      // 根据实体类型返回不同颜色
      const colorMap = {
        'person': '#ff7f0e',
        'organization': '#1f77b4',
        'location': '#2ca02c',
        'concept': '#d62728',
        'time': '#9467bd',
        'event': '#8c564b'
      };
      return colorMap[type] || '#aaa';
    },
    applyFilter() {
      // 实现过滤逻辑
      if (this.activeFilter === 'all') {
        this.visibleTypes = this.entityTypes;
        this.nodes.style('display', 'block');
      } else {
        this.visibleTypes = [this.activeFilter];
        this.nodes.style('display', d => d.type === this.activeFilter ? 'block' : 'none');
      }
      
      // 更新连线显示
      this.links.style('display', d => {
        if (this.activeFilter === 'all') return 'block';
        return (d.source.type === this.activeFilter || d.target.type === this.activeFilter) ? 'block' : 'none';
      });
    },
    zoomIn() {
      this.svg.transition().duration(300).call(
        this.zoom.scaleBy, 1.2
      );
    },
    zoomOut() {
      this.svg.transition().duration(300).call(
        this.zoom.scaleBy, 0.8
      );
    },
    resetView() {
      const container = this.$refs.graphView;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      this.svg.transition().duration(500).call(
        this.zoom.transform,
        d3.zoomIdentity
          .translate(width / 2, height / 2)
          .scale(0.8)
      );
    },
    resizeGraph() {
      if (!this.svg) return;
      
      const container = this.$refs.graphView;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      this.svg
        .attr('width', width)
        .attr('height', height);
      
      this.simulation
        .force('center', d3.forceCenter(width / 2, height / 2))
        .restart();
    }
  }
};
</script>

<style scoped>
.graph-container {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #f9f9f9;
  border-radius: 4px;
  overflow: hidden;
}

.graph-view {
  width: 100%;
  height: 100%;
}

.controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  z-index: 100;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 5px;
  border-radius: 4px;
}

.graph-legend {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.node-badge {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

/* 为不同类型的节点定义类名和颜色 */
.node-badge.person { background-color: #ff7f0e; }
.node-badge.organization { background-color: #1f77b4; }
.node-badge.location { background-color: #2ca02c; }
.node-badge.concept { background-color: #d62728; }
.node-badge.time { background-color: #9467bd; }
.node-badge.event { background-color: #8c564b; }
</style>