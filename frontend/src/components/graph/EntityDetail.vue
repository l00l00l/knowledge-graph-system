<!-- EntityDetail.vue -->
<template>
    <div class="entity-detail-container">
      <div v-if="entity" class="entity-card">
        <div class="entity-header" :class="entity.type">
          <h2>{{ entity.name }}</h2>
          <span class="entity-type-badge">{{ entity.type }}</span>
        </div>
        
        <div class="entity-body">
          <div v-if="entity.description" class="entity-description">
            {{ entity.description }}
          </div>
          
          <div class="entity-properties">
            <h3>属性</h3>
            <div v-for="(value, key) in entity.properties" :key="key" class="property-item">
              <span class="property-key">{{ key }}:</span>
              <span class="property-value">{{ formatPropertyValue(value) }}</span>
            </div>
          </div>
          
          <div class="entity-relationships">
            <h3>关系 ({{ relationships.length }})</h3>
            <div v-if="relationships.length === 0" class="no-data">
              无相关关系
            </div>
            <div v-else class="relationship-list">
              <div v-for="rel in relationships" :key="rel.id" class="relationship-item" 
                  @click="selectRelatedEntity(rel)">
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
          
          <div v-if="sourcesAvailable" class="entity-sources">
            <h3>知识来源</h3>
            <div class="source-list">
              <div v-for="source in entity.sources" :key="source.id" class="source-item"
                  @click="viewSource(source)">
                <div class="source-icon">
                  <i class="fas fa-file-alt"></i>
                </div>
                <div class="source-details">
                  <div class="source-title">{{ source.title }}</div>
                  <div class="source-excerpt">{{ source.excerpt }}</div>
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
      
      <div v-else class="no-entity-selected">
        <i class="fas fa-info-circle"></i>
        <p>请从图谱中选择一个实体查看详情</p>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'EntityDetail',
    props: {
      entity: {
        type: Object,
        default: null
      },
      relationships: {
        type: Array,
        default: () => []
      }
    },
    computed: {
      sourcesAvailable() {
        return this.entity && this.entity.sources && this.entity.sources.length > 0;
      }
    },
    methods: {
      formatPropertyValue(value) {
        if (typeof value === 'object') {
          return JSON.stringify(value);
        }
        return value;
      },
      selectRelatedEntity(relationship) {
        this.$emit('select-entity', relationship.target);
      },
      viewSource(source) {
        this.$emit('view-source', source);
      },
      editEntity() {
        this.$emit('edit-entity', this.entity);
      },
      traceKnowledge() {
        this.$emit('trace-knowledge', this.entity);
      },
      exploreContext() {
        this.$emit('explore-context', this.entity);
      }
    }
  };
  </script>
  
  <style scoped>
  .entity-detail-container {
    height: 100%;
    overflow-y: auto;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  
  .entity-properties, .entity-relationships, .entity-sources {
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
  
  .source-item {
    display: flex;
    padding: 8px;
    margin-bottom: 8px;
    background-color: #f9f9f9;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .source-item:hover {
    background-color: #f0f0f0;
  }
  
  .source-icon {
    margin-right: 12px;
    font-size: 1.2rem;
    color: #666;
  }
  
  .source-details {
    flex: 1;
  }
  
  .source-title {
    font-weight: 500;
    margin-bottom: 4px;
  }
  
  .source-excerpt {
    font-size: 0.9rem;
    color: #666;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
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
  
  .no-entity-selected {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #999;
    padding: 20px;
  }
  
  .no-entity-selected i {
    font-size: 3rem;
    margin-bottom: 16px;
  }
  
  .no-data {
    color: #999;
    font-style: italic;
    padding: 12px 0;
  }
  </style>