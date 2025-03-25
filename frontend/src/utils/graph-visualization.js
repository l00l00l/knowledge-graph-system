// utils/graph-visualization.js
import * as d3 from 'd3';

export class KnowledgeGraphVisualizer {
  constructor(container, data, options = {}) {
    this.container = container;
    this.data = data;
    this.options = {
      nodeRadius: 12,
      linkDistance: 150,
      chargeStrength: -400,
      ...options
    };
    
    this.svg = null;
    this.simulation = null;
    this.nodes = null;
    this.links = null;
    this.tooltip = null;
    this.zoom = null;
    
    this.colorScale = d3.scaleOrdinal(d3.schemeCategory10);
    this.initialize();
  }
  
  initialize() {
    // 清空容器
    d3.select(this.container).selectAll("*").remove();
    
    const containerRect = this.container.getBoundingClientRect();
    const width = containerRect.width;
    const height = containerRect.height;
    
    // 创建SVG
    this.svg = d3.select(this.container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('class', 'knowledge-graph');
    
    // 创建缩放行为
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        this.svg.select('.graph-container')
          .attr('transform', event.transform);
      });
    
    this.svg.call(this.zoom);
    
    // 创建容器组
    const g = this.svg.append('g')
      .attr('class', 'graph-container');
    
    // 添加箭头标记
    this.svg.append('defs').selectAll('marker')
      .data(this._getRelationshipTypes())
      .enter()
      .append('marker')
      .attr('id', d => `arrowhead-${d}`)
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', d => this._getLinkColor(d))
      .style('stroke', 'none');
    
    // 创建提示框
    this.tooltip = d3.select(this.container)
      .append('div')
      .attr('class', 'graph-tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background-color', 'white')
      .style('border', '1px solid #ddd')
      .style('padding', '8px')
      .style('border-radius', '3px')
      .style('pointer-events', 'none')
      .style('z-index', 100);
    
    // 创建连接线
    this.links = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(this.data.links)
      .enter()
      .append('line')
      .attr('class', d => `link ${d.type}`)
      .attr('stroke', d => this._getLinkColor(d.type))
      .attr('stroke-width', 1.5)
      .attr('marker-end', d => `url(#arrowhead-${d.type})`);
    
    // 创建连接线标签
    g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(this.data.links)
      .enter()
      .append('text')
      .attr('class', 'link-label')
      .attr('dy', -4)
      .attr('text-anchor', 'middle')
      .text(d => d.type)
      .style('font-size', '10px')
      .style('fill', '#666')
      .style('pointer-events', 'none')
      .style('opacity', 0.7);
    
    // 创建节点组
    const nodeGroup = g.append('g')
      .attr('class', 'nodes');
    
    const nodeGroups = nodeGroup
      .selectAll('g')
      .data(this.data.nodes)
      .enter()
      .append('g')
      .attr('class', d => `node ${d.type}`)
      .on('mouseover', this._handleNodeMouseOver.bind(this))
      .on('mouseout', this._handleNodeMouseOut.bind(this))
      .on('click', this._handleNodeClick.bind(this))
      .call(d3.drag()
        .on('start', this._dragStarted.bind(this))
        .on('drag', this._dragged.bind(this))
        .on('end', this._dragEnded.bind(this)));
    
    // 添加节点圆形
    nodeGroups.append('circle')
      .attr('r', this.options.nodeRadius)
      .attr('fill', d => this._getNodeColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);
    
    // 添加节点图标
    nodeGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.3em')
      .text(d => this._getNodeIcon(d.type))
      .attr('fill', '#fff')
      .attr('font-family', 'FontAwesome')
      .attr('font-size', '10px');
    
    // 添加节点标签
    nodeGroups.append('text')
      .attr('class', 'node-label')
      .attr('dy', 25)
      .attr('text-anchor', 'middle')
      .text(d => d.name)
      .attr('font-size', '12px')
      .attr('fill', '#333');
    
    this.nodes = nodeGroups;
    
    // 创建力导向模拟
    this.simulation = d3.forceSimulation(this.data.nodes)
      .force('link', d3.forceLink(this.data.links)
        .id(d => d.id)
        .distance(this.options.linkDistance))
      .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(this.options.nodeRadius * 2))
      .on('tick', this._ticked.bind(this));
    
    // 初始视图
    this.resetView();
  }
  
  _ticked() {
    // 更新连接线位置
    this.links
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    
    // 更新连接线标签位置
    this.svg.selectAll('.link-label')
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2);
    
    // 更新节点位置
    this.nodes
      .attr('transform', d => `translate(${d.x}, ${d.y})`);
  }
  
  _handleNodeMouseOver(event, d) {
    // 显示提示框
    this.tooltip.transition()
      .duration(200)
      .style('opacity', .9);
    
    const tooltipContent = `
      <div><strong>${d.name}</strong></div>
      <div>类型: ${d.type}</div>
      ${d.description ? `<div>${d.description}</div>` : ''}
    `;
    
    this.tooltip.html(tooltipContent)
      .style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 28) + 'px');
    
    // 高亮连接的边和节点
    this.links
      .transition()
      .duration(200)
      .style('opacity', link => 
        link.source.id === d.id || link.target.id === d.id ? 1.0 : 0.2);
    
    this.nodes
      .transition()
      .duration(200)
      .style('opacity', node => 
        this._isConnected(d, node) ? 1.0 : 0.2);
  }
  
  _handleNodeMouseOut() {
    // 隐藏提示框
    this.tooltip.transition()
      .duration(500)
      .style('opacity', 0);
    
    // 恢复所有边和节点的可见性
    this.links
      .transition()
      .duration(200)
      .style('opacity', 1.0);
    
    this.nodes
      .transition()
      .duration(200)
      .style('opacity', 1.0);
  }
  
  _handleNodeClick(event, d) {
    // 触发选择事件
    if (this.options.onNodeClick) {
      this.options.onNodeClick(d);
    }
  }
  
  _isConnected(a, b) {
    return a.id === b.id || this.data.links.some(link => 
      (link.source.id === a.id && link.target.id === b.id) ||
      (link.source.id === b.id && link.target.id === a.id)
    );
  }
  
  _dragStarted(event, d) {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  _dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  _dragEnded(event, d) {
    if (!event.active) this.simulation.alphaTarget(0);
    if (!this.options.fixNodesAfterDrag) {
      d.fx = null;
      d.fy = null;
    }
  }
  
  _getNodeColor(type) {
    const colorMap = {
      'person': '#ff7f0e',
      'organization': '#1f77b4',
      'location': '#2ca02c',
      'concept': '#d62728',
      'time': '#9467bd',
      'event': '#8c564b'
    };
    return colorMap[type] || this.colorScale(type);
  }
  
  _getLinkColor(type) {
    const colorMap = {
      'is_a': '#aaa',
      'part_of': '#777',
      'created_by': '#ff7f0e',
      'located_in': '#2ca02c'
    };
    return colorMap[type] || '#999';
  }
  
  _getNodeIcon(type) {
    const iconMap = {
      'person': '\uf007', // fa-user
      'organization': '\uf1ad', // fa-building
      'location': '\uf3c5', // fa-map-marker-alt
      'concept': '\uf02d', // fa-book
      'time': '\uf017', // fa-clock
      'event': '\uf073'  // fa-calendar
    };
    return iconMap[type] || '';
  }
  
  _getRelationshipTypes() {
    return [...new Set(this.data.links.map(link => link.type))];
  }
  
  resetView() {
    const containerRect = this.container.getBoundingClientRect();
    const width = containerRect.width;
    const height = containerRect.height;
    
    this.svg.transition().duration(500).call(
      this.zoom.transform,
      d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(0.8)
        .translate(-width / 2, -height / 2)
    );
  }
  
  updateData(data) {
    this.data = data;
    this.initialize();
  }
  
  filterByType(type) {
    if (!type || type === 'all') {
      this.nodes.style('display', 'block');
      this.links.style('display', 'block');
      return;
    }
    
    this.nodes.style('display', d => d.type === type ? 'block' : 'none');
    this.links.style('display', d => {
      return (d.source.type === type || d.target.type === type) ? 'block' : 'none';
    });
  }
  
  highlightPath(nodeIds) {
    if (!nodeIds || nodeIds.length === 0) {
      this.nodes.style('opacity', 1);
      this.links.style('opacity', 1);
      return;
    }
    
    const nodeIdSet = new Set(nodeIds);
    
    this.nodes.style('opacity', d => nodeIdSet.has(d.id) ? 1 : 0.2);
    
    this.links.style('opacity', d => {
      return (nodeIdSet.has(d.source.id) && nodeIdSet.has(d.target.id)) ? 1 : 0.2;
    });
  }
  
  focusOnNode(nodeId) {
    const node = this.data.nodes.find(n => n.id === nodeId);
    if (!node || !node.x || !node.y) return;
    
    const containerRect = this.container.getBoundingClientRect();
    const width = containerRect.width;
    const height = containerRect.height;
    
    const scale = 1.5;
    const x = width / 2 - node.x * scale;
    const y = height / 2 - node.y * scale;
    
    this.svg.transition().duration(750).call(
      this.zoom.transform,
      d3.zoomIdentity
        .translate(x, y)
        .scale(scale)
    );
  }
}