<!-- frontend/src/components/document/DocumentList.vue -->
<template>
    <div class="documents-list">
      <div class="list-header">
        <h2>文档列表</h2>
        <div class="list-actions">
          <button @click="refreshDocuments" class="refresh-btn" :disabled="isLoading">
            <i :class="isLoading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"></i>
            <span>{{ isLoading ? '加载中...' : '刷新' }}</span>
          </button>
        </div>
      </div>
      
      <div class="filters">
        <input 
          type="text"
          v-model="searchQuery"
          placeholder="搜索文档..."
          class="search-input"
        >
        
        <select v-model="typeFilter" class="type-filter">
          <option value="">所有类型</option>
          <option value="pdf">PDF</option>
          <option value="docx">Word</option>
          <option value="txt">文本</option>
          <option value="webpage">网页</option>
        </select>
      </div>
      
      <div v-if="isLoading" class="loading">
        <i class="fas fa-spinner fa-spin"></i>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="filteredDocuments.length === 0" class="no-documents">
        <i class="fas fa-file-alt"></i>
        <p>暂无文档</p>
      </div>
      
      <table v-else class="documents-table">
        <thead>
          <tr>
            <th>标题</th>
            <th>类型</th>
            <th>上传时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in filteredDocuments" :key="doc.id" class="document-row">
            <td class="document-title">
              <i :class="getDocumentIcon(doc.type)"></i>
              <span>{{ doc.title }}</span>
            </td>
            <td>{{ doc.type.toUpperCase() }}</td>
            <td>{{ formatDate(doc.created_at) }}</td>
            <td class="document-actions">
              <button @click="previewDocument(doc)" class="btn-action" title="预览">
                <i class="fas fa-eye"></i>
              </button>
              <button @click="downloadDocument(doc)" class="btn-action" title="下载">
                <i class="fas fa-download"></i>
              </button>
              <button @click="extractFromDocument(doc)" class="btn-action" title="提取知识">
                <i class="fas fa-magic"></i>
              </button>
              <button @click="deleteDocument(doc)" class="btn-action delete" title="删除">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- 预览对话框 -->
      <div v-if="showPreview" class="preview-dialog">
        <div class="preview-content">
          <div class="preview-header">
            <h3>{{ previewingDocument.title }}</h3>
            <button @click="closePreview" class="close-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="preview-body">
            <div v-if="previewLoading" class="preview-loading">
              <i class="fas fa-spinner fa-spin"></i>
              <span>加载中...</span>
            </div>
            <div v-else-if="previewError" class="preview-error">
              <i class="fas fa-exclamation-circle"></i>
              <span>{{ previewError }}</span>
            </div>
            <pre v-else class="content-preview">{{ documentContent }}</pre>
          </div>
          <div class="preview-footer">
            <button @click="closePreview" class="btn">关闭</button>
            <button @click="downloadDocument(previewingDocument)" class="btn btn-primary">下载</button>
          </div>
        </div>
      </div>
      
      <!-- 确认删除对话框 -->
      <div v-if="showDeleteConfirm" class="confirm-dialog">
        <div class="confirm-content">
          <div class="confirm-header">
            <h3>确认删除</h3>
          </div>
          <div class="confirm-body">
            <p>您确定要删除文档 "{{ deletingDocument.title }}" 吗？此操作无法撤销。</p>
          </div>
          <div class="confirm-footer">
            <button @click="cancelDelete" class="btn">取消</button>
            <button @click="confirmDelete" class="btn btn-danger">删除</button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'DocumentList',
    props: {
      apiBaseUrl: {
        type: String,
        default: '/api/v1/documents'
      },
      autoRefresh: {
        type: Boolean,
        default: true
      }
    },
    data() {
      return {
        documents: [],
        isLoading: false,
        searchQuery: '',
        typeFilter: '',
        
        // 预览相关
        showPreview: false,
        previewingDocument: null,
        previewLoading: false,
        documentContent: '',
        previewError: null,
        
        // 删除确认相关
        showDeleteConfirm: false,
        deletingDocument: null,
        
        // 提取知识相关
        isExtracting: false
      };
    },
    computed: {
      filteredDocuments() {
        let filtered = [...this.documents];
        
        // 应用搜索过滤
        if (this.searchQuery) {
          const query = this.searchQuery.toLowerCase();
          filtered = filtered.filter(doc => 
            doc.title.toLowerCase().includes(query)
          );
        }
        
        // 应用类型过滤
        if (this.typeFilter) {
          filtered = filtered.filter(doc => doc.type === this.typeFilter);
        }
        
        return filtered;
      }
    },
    methods: {
      async refreshDocuments() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
          const response = await fetch(this.apiBaseUrl);
          
          if (!response.ok) {
            throw new Error(`获取文档失败: ${response.status}`);
          }
          
          this.documents = await response.json();
          console.log(`成功获取 ${this.documents.length} 份文档`);
        } catch (error) {
          console.error('获取文档列表失败:', error);
        } finally {
          this.isLoading = false;
        }
      },
      
      formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString();
      },
      
      getDocumentIcon(type) {
        const iconMap = {
          'pdf': 'fas fa-file-pdf',
          'docx': 'fas fa-file-word',
          'doc': 'fas fa-file-word',
          'txt': 'fas fa-file-alt',
          'webpage': 'fas fa-file-code'
        };
        
        return iconMap[type] || 'fas fa-file';
      },
      
      async previewDocument(doc) {
        this.previewingDocument = doc;
        this.showPreview = true;
        this.previewLoading = true;
        this.documentContent = '';
        this.previewError = null;
        
        try {
          const response = await fetch(`${this.apiBaseUrl}/${doc.id}/preview`);
          
          if (!response.ok) {
            throw new Error(`预览失败: ${response.status}`);
          }
          
          const result = await response.json();
          this.documentContent = result.content;
        } catch (error) {
          console.error('预览文档失败:', error);
          this.previewError = error.message;
        } finally {
          this.previewLoading = false;
        }
      },
      
      closePreview() {
        this.showPreview = false;
        this.previewingDocument = null;
        this.documentContent = '';
      },
      
      downloadDocument(doc) {
        window.open(`${this.apiBaseUrl}/${doc.id}/download`, '_blank');
      },
      
      async extractFromDocument(doc) {
        if (this.isExtracting) return;
        
        this.isExtracting = true;
        
        try {
          const response = await fetch(`${this.apiBaseUrl}/${doc.id}/extract`, {
            method: 'POST'
          });
          
          if (!response.ok) {
            throw new Error(`提取知识失败: ${response.status}`);
          }
          
          const result = await response.json();
          alert(`知识提取成功！已提取 ${result.extracted_entities} 个实体和 ${result.extracted_relationships} 个关系。`);
        } catch (error) {
          console.error('知识提取失败:', error);
          alert('知识提取失败: ' + error.message);
        } finally {
          this.isExtracting = false;
        }
      },
      
      deleteDocument(doc) {
        this.deletingDocument = doc;
        this.showDeleteConfirm = true;
      },
      
      cancelDelete() {
        this.showDeleteConfirm = false;
        this.deletingDocument = null;
      },
      
      async confirmDelete() {
        if (!this.deletingDocument) return;
        
        try {
          const response = await fetch(`${this.apiBaseUrl}/${this.deletingDocument.id}`, {
            method: 'DELETE'
          });
          
          if (!response.ok) {
            throw new Error(`删除失败: ${response.status}`);
          }
          
          // 从本地列表中移除
          this.documents = this.documents.filter(doc => doc.id !== this.deletingDocument.id);
          
          // 关闭确认对话框
          this.showDeleteConfirm = false;
          this.deletingDocument = null;
        } catch (error) {
          console.error('删除文档失败:', error);
          alert('删除文档失败: ' + error.message);
        }
      },
      
      // 处理新上传的文档
      handleNewDocument(document) {
        // 检查是否已存在
        const exists = this.documents.some(doc => doc.id === document.id);
        
        if (!exists) {
          // 添加到文档列表
          this.documents.unshift(document);
        }
      }
    },
    mounted() {
      if (this.autoRefresh) {
        this.refreshDocuments();
      }
    }
  };
  </script>
  
  <style scoped>
  .documents-list {
    position: relative;
  }
  
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }
  
  .refresh-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .refresh-btn:hover {
    background-color: #e0e0e0;
  }
  
  .refresh-btn:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
  
  .filters {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .search-input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .type-filter {
    width: 150px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .loading,
  .no-documents {
    text-align: center;
    padding: 40px 0;
    color: #999;
  }
  
  .loading i,
  .no-documents i {
    font-size: 2rem;
    margin-bottom: 10px;
  }
  
  .documents-table {
    width: 100%;
    border-collapse: collapse;
  }
  
  .documents-table th,
  .documents-table td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #eee;
  }
  
  .documents-table th {
    font-weight: 600;
    color: #666;
  }
  
  .document-title {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .document-title i {
    font-size: 1.2rem;
    color: var(--primary-color, #4a90e2);
  }
  
  .document-actions {
    display: flex;
    gap: 5px;
  }
  
  .btn-action {
    background: none;
    border: none;
    cursor: pointer;
    padding: 5px;
    border-radius: 4px;
    transition: background-color 0.2s;
  }
  
  .btn-action:hover {
    background-color: #f0f0f0;
  }
  
  .btn-action.delete:hover {
    color: #d9534f;
  }
  
  /* 预览对话框 */
  .preview-dialog,
  .confirm-dialog {
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
  
  .preview-content {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    width: 80%;
    max-width: 900px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
  }
  
  .preview-header,
  .confirm-header {
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
  }
  
  .preview-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    min-height: 200px;
    max-height: 60vh;
  }
  
  .content-preview {
    white-space: pre-wrap;
    font-family: monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    overflow-x: auto;
  }
  
  .preview-loading,
  .preview-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 200px;
    color: #999;
  }
  
  .preview-loading i,
  .preview-error i {
    font-size: 2rem;
    margin-bottom: 10px;
  }
  
  .preview-error {
    color: #d9534f;
  }
  
  .preview-footer,
  .confirm-footer {
    padding: 15px 20px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
  
  /* 确认对话框 */
  .confirm-content {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    width: 400px;
  }
  
  .confirm-body {
    padding: 20px;
  }
  
  .btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .btn-primary {
    background-color: var(--primary-color, #4a90e2);
    color: white;
  }
  
  .btn-danger {
    background-color: #d9534f;
    color: white;
  }
  
  @media (max-width: 768px) {
    .filters {
      flex-direction: column;
    }
    
    .document-actions {
      flex-direction: column;
      gap: 8px;
    }
    
    .preview-content {
      width: 95%;
    }
  }
  </style>