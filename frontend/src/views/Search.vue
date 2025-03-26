<!-- Search.vue -->
<template>
    <div class="search-container">
      <h1>查询分析</h1>
      
      <div class="search-types">
        <div 
          class="search-type-tab" 
          :class="{ active: activeTab === 'natural' }"
          @click="activeTab = 'natural'"
        >
          <i class="fas fa-comment"></i>
          <span>自然语言查询</span>
        </div>
        
        <div 
          class="search-type-tab" 
          :class="{ active: activeTab === 'structured' }"
          @click="activeTab = 'structured'"
        >
          <i class="fas fa-project-diagram"></i>
          <span>结构化查询</span>
        </div>
      </div>
      
      <div class="search-panel">
        <div v-if="activeTab === 'natural'" class="natural-language-search">
          <div class="search-input-container">
            <input 
              type="text"
              v-model="naturalQuery"
              placeholder="输入您的问题，例如：什么是知识图谱？谁创建了知识图谱？"
              class="search-input"
              @keyup.enter="executeNaturalQuery"
              :disabled="isSearching"
            >
            <button 
              class="search-button"
              @click="executeNaturalQuery"
              :disabled="!naturalQuery || isSearching"
            >
              <i :class="isSearching ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
              <span>{{ isSearching ? '查询中...' : '查询' }}</span>
            </button>
          </div>
          
          <div class="query-suggestions">
            <h3>示例查询：</h3>
            <div class="suggestion-list">
              <div 
                v-for="(suggestion, index) in naturalSuggestions" 
                :key="index"
                class="suggestion-item"
                @click="applySuggestion(suggestion)"
              >
                {{ suggestion }}
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="activeTab === 'structured'" class="structured-search">
          <div class="structured-builder">
            <div class="builder-section">
              <h3>实体过滤</h3>
              <div class="builder-row">
                <select v-model="structuredQuery.entityType" class="builder-input">
                  <option value="">选择实体类型</option>
                  <option value="person">人物</option>
                  <option value="organization">组织</option>
                  <option value="location">地点</option>
                  <option value="concept">概念</option>
                  <option value="event">事件</option>
                </select>
                
                <input 
                  type="text"
                  v-model="structuredQuery.entityName"
                  placeholder="实体名称（可选）"
                  class="builder-input"
                >
              </div>
            </div>
            
            <div class="builder-section">
              <h3>关系过滤</h3>
              <div class="builder-row">
                <select v-model="structuredQuery.relationType" class="builder-input">
                  <option value="">选择关系类型</option>
                  <option value="is_a">是一种</option>
                  <option value="part_of">是部分</option>
                  <option value="located_in">位于</option>
                  <option value="related_to">相关</option>
                </select>
                
                <select v-model="structuredQuery.direction" class="builder-input">
                  <option value="any">任意方向</option>
                  <option value="outgoing">向外</option>
                  <option value="incoming">向内</option>
                </select>
              </div>
            </div>
            
            <div class="builder-section">
              <h3>高级选项</h3>
              <div class="builder-row">
                <div class="builder-option">
                  <label>
                    <input type="checkbox" v-model="structuredQuery.includeProperties">
                    <span>包含属性</span>
                  </label>
                </div>
                
                <div class="builder-option">
                  <label>
                    <input type="number" v-model="structuredQuery.maxDepth" min="1" max="5" class="depth-input">
                    <span>最大深度</span>
                  </label>
                </div>
              </div>
            </div>
            
            <div class="builder-actions">
              <button 
                class="reset-button"
                @click="resetStructuredQuery"
              >
                <i class="fas fa-undo"></i>
                <span>重置</span>
              </button>
              
              <button 
                class="search-button"
                @click="executeStructuredQuery"
                :disabled="!isStructuredQueryValid || isSearching"
              >
                <i :class="isSearching ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
                <span>{{ isSearching ? '查询中...' : '查询' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="showResults" class="search-results">
        <div class="results-header">
          <h2>查询结果</h2>
          
          <div class="results-actions">
            <button @click="toggleVisualization" class="toggle-view-button">
              <i :class="showVisualization ? 'fas fa-list' : 'fas fa-project-diagram'"></i>
              <span>{{ showVisualization ? '列表视图' : '图谱视图' }}</span>
            </button>
            
            <button @click="exportResults" class="export-button">
              <i class="fas fa-download"></i>
              <span>导出</span>
            </button>
          </div>
        </div>
        
        <div v-if="isSearching" class="loading-results">
          <i class="fas fa-spinner fa-spin"></i>
          <span>正在处理查询...</span>
        </div>
        
        <div v-else-if="results.length === 0" class="no-results">
          <i class="fas fa-search"></i>
          <p>未找到匹配的结果</p>
        </div>
        
        <div v-else-if="showVisualization" class="visualization-view">
          <!-- 简化的图可视化组件 -->
          <div class="visualization-placeholder">
            <p>图谱可视化组件占位符</p>
            <p>在实际应用中，这里将加载Graph组件</p>
          </div>
        </div>
        
        <div v-else class="list-view">
          <div v-for="(result, index) in results" :key="index" class="result-item">
            <div class="result-header">
              <h3 class="result-title">{{ result.name }}</h3>
              <span class="result-type">{{ result.type }}</span>
            </div>
            
            <div v-if="result.description" class="result-description">
              {{ result.description }}
            </div>
            
            <div v-if="result.relationships && result.relationships.length > 0" class="result-relationships">
              <h4>关系：</h4>
              <ul class="relationship-list">
                <li v-for="(rel, relIdx) in result.relationships" :key="relIdx">
                  <span class="relationship-type">{{ rel.type }}</span>
                  <i class="fas fa-arrow-right"></i>
                  <span 
                    class="relationship-target"
                    @click="selectRelatedEntity(rel.target)"
                  >
                    {{ rel.target.name }}
                  </span>
                </li>
              </ul>
            </div>
            
            <div v-if="result.properties && Object.keys(result.properties).length > 0" class="result-properties">
              <h4>属性：</h4>
              <div class="properties-table">
                <div 
                  v-for="(value, key) in result.properties" 
                  :key="key"
                  class="property-row"
                >
                  <span class="property-key">{{ key }}:</span>
                  <span class="property-value">{{ value }}</span>
                </div>
              </div>
            </div>
            
            <div class="result-actions">
              <button @click="viewEntityDetails(result)" class="action-button">
                <i class="fas fa-eye"></i>
                <span>查看详情</span>
              </button>
              
              <button @click="exploreContext(result)" class="action-button">
                <i class="fas fa-project-diagram"></i>
                <span>探索上下文</span>
              </button>
              
              <button @click="traceKnowledge(result)" class="action-button">
                <i class="fas fa-history"></i>
                <span>知识溯源</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'Search',
    data() {
      return {
        activeTab: 'natural',
        naturalQuery: '',
        structuredQuery: {
          entityType: '',
          entityName: '',
          relationType: '',
          direction: 'any',
          includeProperties: true,
          maxDepth: 2
        },
        isSearching: false,
        showResults: false,
        showVisualization: false,
        results: [],
        naturalSuggestions: [
          '什么是知识图谱？',
          '知识图谱和知识库有什么区别？',
          '谁创建了知识图谱概念？',
          '知识图谱有哪些应用场景？',
          '知识图谱如何与自然语言处理结合？'
        ]
      };
    },
    computed: {
      isStructuredQueryValid() {
        // 至少有一个查询条件
        return this.structuredQuery.entityType || 
               this.structuredQuery.entityName || 
               this.structuredQuery.relationType;
      }
    },
    methods: {
      applySuggestion(suggestion) {
        this.naturalQuery = suggestion;
        this.executeNaturalQuery();
      },
      
      async executeNaturalQuery() {
        if (!this.naturalQuery || this.isSearching) return;
        
        this.isSearching = true;
        
        try {
          // 模拟API调用
          console.log('Executing natural language query:', this.naturalQuery);
          
          // 模拟延迟
          await new Promise(r => setTimeout(r, 1500));
          
          // 模拟结果
          this.results = this.generateMockResults();
          this.showResults = true;
          
        } catch (error) {
          console.error('Error executing query:', error);
        } finally {
          this.isSearching = false;
        }
      },
      
      resetStructuredQuery() {
        this.structuredQuery = {
          entityType: '',
          entityName: '',
          relationType: '',
          direction: 'any',
          includeProperties: true,
          maxDepth: 2
        };
      },
      
      async executeStructuredQuery() {
        if (!this.isStructuredQueryValid || this.isSearching) return;
        
        this.isSearching = true;
        
        try {
          // 模拟API调用
          console.log('Executing structured query:', this.structuredQuery);
          
          // 模拟延迟
          await new Promise(r => setTimeout(r, 1500));
          
          // 模拟结果
          this.results = this.generateMockResults();
          this.showResults = true;
          
        } catch (error) {
          console.error('Error executing query:', error);
        } finally {
          this.isSearching = false;
        }
      },
      
      toggleVisualization() {
        this.showVisualization = !this.showVisualization;
      },
      
      exportResults() {
        // 导出结果功能
        console.log('Exporting results...');
        
        // 创建下载链接
        const dataStr = JSON.stringify(this.results, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = 'search-results.json';
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
      },
      
      selectRelatedEntity(entity) {
        // 选择相关实体
        console.log('Selected related entity:', entity);
        // 在实际应用中，可能会重新查询该实体
      },
      
      viewEntityDetails(entity) {
        // 查看实体详情
        console.log('Viewing entity details:', entity);
        // 在实际应用中，可能会导航到实体详情页面
      },
      
      exploreContext(entity) {
        // 探索实体上下文
        console.log('Exploring context of entity:', entity);
        // 在实际应用中，可能会导航到图谱视图并聚焦该实体
      },
      
      traceKnowledge(entity) {
        // 知识溯源
        console.log('Tracing knowledge for entity:', entity);
        // 在实际应用中，可能会导航到溯源页面
      },
      
      generateMockResults() {
        // 生成模拟结果
        if (this.naturalQuery.includes('知识图谱')) {
          return [
            {
              id: 'entity1',
              name: '知识图谱',
              type: 'concept',
              description: '知识图谱是一种表示知识的图结构，由节点和边组成，节点表示实体，边表示实体间的关系。',
              properties: {
                domain: '人工智能',
                created: '2012',
                popularity: '高'
              },
              relationships: [
                {
                  type: 'is_a',
                  target: {
                    id: 'entity2',
                    name: '知识表示方法',
                    type: 'concept'
                  }
                },
                {
                  type: 'used_in',
                  target: {
                    id: 'entity3',
                    name: '语义搜索',
                    type: 'concept'
                  }
                },
                {
                  type: 'related_to',
                  target: {
                    id: 'entity4',
                    name: '本体论',
                    type: 'concept'
                  }
                }
              ]
            },
            {
              id: 'entity5',
              name: '谷歌知识图谱',
              type: 'product',
              description: '谷歌知识图谱是由谷歌公司于2012年推出的一种知识库，用于增强其搜索引擎的语义搜索能力。',
              properties: {
                company: 'Google',
                launch_date: '2012-05-16',
                entities: '超过5亿'
              },
              relationships: [
                {
                  type: 'is_a',
                  target: {
                    id: 'entity1',
                    name: '知识图谱',
                    type: 'concept'
                  }
                },
                {
                  type: 'created_by',
                  target: {
                    id: 'entity6',
                    name: '谷歌',
                    type: 'organization'
                  }
                }
              ]
            }
          ];
        } else {
          // 默认结果
          return [
            {
              id: 'entity7',
              name: '默认结果',
              type: 'concept',
              description: '这是一个示例结果。在实际应用中，这里将显示真实的查询结果。',
              properties: {
                note: '示例数据'
              },
              relationships: []
            }
          ];
        }
      }
    }
  };
  </script>
  
  <style scoped>
  .search-container {
    padding: 20px;
  }
  
  h1 {
    margin-bottom: 20px;
  }
  
  .search-types {
    display: flex;
    margin-bottom: 20px;
  }
  
  .search-type-tab {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .search-type-tab.active {
    border-bottom-color: var(--primary-color);
    color: var(--primary-color);
  }
  
  .search-panel {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .search-input-container {
    display: flex;
    gap: 10px;
  }
  
  .search-input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  .search-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 20px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
  }
  
  .search-button:hover {
    background-color: #3a80d2;
  }
  
  .search-button:disabled {
    background-color: #aaa;
    cursor: not-allowed;
  }
  
  .query-suggestions {
    margin-top: 20px;
  }
  
  .query-suggestions h3 {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 10px;
  }
  
  .suggestion-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .suggestion-item {
    padding: 6px 12px;
    background-color: #f0f0f0;
    border-radius: 16px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .suggestion-item:hover {
    background-color: #e0e0e0;
  }
  
  .structured-builder {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .builder-section h3 {
    font-size: 1rem;
    margin-bottom: 10px;
  }
  
  .builder-row {
    display: flex;
    gap: 15px;
  }
  
  .builder-input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .builder-option {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .depth-input {
    width: 60px;
    padding: 4px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .builder-actions {
    display: flex;
    justify-content: flex-end;
    gap: 15px;
    margin-top: 10px;
  }
  
  .reset-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background-color: #f0f0f0;
    color: #333;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .reset-button:hover {
    background-color: #e0e0e0;
  }
  
  .search-results {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .results-actions {
    display: flex;
    gap: 10px;
  }
  
  .toggle-view-button,
  .export-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background-color: #f0f0f0;
    color: #333;
    border: none;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;
  }
  
  .toggle-view-button:hover,
  .export-button:hover {
    background-color: #e0e0e0;
  }
  
  .loading-results,
  .no-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0;
    color: #999;
  }
  
  .loading-results i,
  .no-results i {
    font-size: 2rem;
    margin-bottom: 15px;
  }
  
  .visualization-placeholder {
    height: 400px;
    border: 1px dashed #ccc;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #999;
  }
  
  .result-item {
    margin-bottom: 20px;
    padding: 16px;
    border: 1px solid #eee;
    border-radius: 4px;
  }
  
  .result-header {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .result-title {
    font-size: 1.2rem;
    margin-right: 10px;
  }
  
  .result-type {
    padding: 2px 8px;
    background-color: #f0f0f0;
    border-radius: 10px;
    font-size: 0.8rem;
    color: #666;
  }
  
  .result-description {
    margin-bottom: 15px;
    line-height: 1.5;
  }
  
  .result-relationships,
  .result-properties {
    margin-bottom: 15px;
  }
  
  .result-relationships h4,
  .result-properties h4 {
    font-size: 1rem;
    margin-bottom: 8px;
    color: #666;
  }
  
  .relationship-list {
    list-style: none;
  }
  
  .relationship-list li {
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .relationship-type {
    color: #666;
  }
  
  .relationship-target {
    color: var(--primary-color);
    cursor: pointer;
  }
  
  .relationship-target:hover {
    text-decoration: underline;
  }
  
  .properties-table {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 5px 15px;
  }
  
  .property-key {
    font-weight: 500;
  }
  
  .result-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
  }
  
  .action-button {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    background-color: #f0f0f0;
    color: #333;
    border: none;
    border-radius: 4px;
    font-size: 0.9rem;
    cursor: pointer;
  }
  
  .action-button:hover {
    background-color: #e0e0e0;
  }
  
  @media (max-width: 768px) {
    .search-input-container,
    .builder-row {
      flex-direction: column;
      gap: 10px;
    }
    
    .results-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }
  }
  </style>