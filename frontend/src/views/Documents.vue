<!-- Documents.vue -->
<template>
  <div class="documents-container">
    <h1>文档管理</h1>
    
    <div class="documents-actions">
      <div class="upload-area">
        <h2>上传文档</h2>
        <div 
          class="dropzone"
          :class="{ active: isDragging }"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
        >
          <div class="dropzone-content">
            <i class="fas fa-cloud-upload-alt"></i>
            <p>拖拽文件到此处上传，或</p>
            <input 
              type="file" 
              ref="fileInput" 
              @change="handleFileSelect" 
              multiple 
              class="file-input"
            >
            <button @click="triggerFileInput" class="btn upload-btn">选择文件</button>
          </div>
        </div>
        
        <div v-if="selectedFiles.length > 0" class="selected-files">
          <h3>已选择 {{ selectedFiles.length }} 个文件</h3>
          <ul class="file-list">
            <li v-for="(file, index) in selectedFiles" :key="index" class="file-item">
              <div class="file-info">
                <i class="fas fa-file-alt"></i>
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">({{ formatFileSize(file.size) }})</span>
              </div>
              <button @click="removeFile(index)" class="btn-remove">
                <i class="fas fa-times"></i>
              </button>
            </li>
          </ul>
          
          <div class="upload-options">
            <label class="option">
              <input type="checkbox" v-model="extractKnowledge">
              <span>上传后提取知识</span>
            </label>
            
            <button @click="uploadFiles" class="btn btn-primary" :disabled="isUploading">
              <i class="fas fa-upload"></i>
              {{ isUploading ? '上传中...' : '开始上传' }}
            </button>
          </div>
        </div>
      </div>
      
      <div class="web-url-import">
        <h2>从网页导入</h2>
        <div class="url-input-group">
          <input 
            type="text"
            v-model="webUrl"
            placeholder="输入网页URL..."
            :disabled="isProcessingUrl"
          >
          <button @click="processUrl" class="btn" :disabled="!webUrl || isProcessingUrl">
            <i class="fas fa-globe"></i>
            {{ isProcessingUrl ? '处理中...' : '导入' }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="documents-list">
      <h2>文档列表</h2>
      
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
      
      <div v-if="loading" class="loading">
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
              <button @click="viewDocument(doc)" class="btn-action">
                <i class="fas fa-eye"></i>
              </button>
              <button @click="extractFromDocument(doc)" class="btn-action">
                <i class="fas fa-magic"></i>
              </button>
              <button @click="downloadDocument(doc)" class="btn-action">
                <i class="fas fa-download"></i>
              </button>
              <button @click="deleteDocument(doc)" class="btn-action delete">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Documents',
  data() {
    return {
      loading: true,
      isDragging: false,
      isUploading: false,
      isProcessingUrl: false,
      selectedFiles: [],
      extractKnowledge: true,
      webUrl: '',
      searchQuery: '',
      typeFilter: '',
      documents: []
    };
  },
  computed: {
    filteredDocuments() {
      let filtered = [...this.documents];
      
      // Apply search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(doc => 
          doc.title.toLowerCase().includes(query)
        );
      }
      
      // Apply type filter
      if (this.typeFilter) {
        filtered = filtered.filter(doc => doc.type === this.typeFilter);
      }
      
      return filtered;
    }
  },
  methods: {
    // File drag and drop handlers
    onDragOver() {
      this.isDragging = true;
    },
    onDragLeave() {
      this.isDragging = false;
    },
    onDrop(e) {
      this.isDragging = false;
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.addFiles(files);
      }
    },
    
    // File selection methods
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleFileSelect(e) {
      const files = e.target.files;
      if (files.length > 0) {
        this.addFiles(files);
        // Reset the input to allow selecting the same file again
        this.$refs.fileInput.value = null;
      }
    },
    addFiles(fileList) {
      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        // Check if file already exists in selection
        const exists = this.selectedFiles.some(f => 
          f.name === file.name && f.size === file.size
        );
        if (!exists) {
          this.selectedFiles.push(file);
        }
      }
    },
    removeFile(index) {
      this.selectedFiles.splice(index, 1);
    },
    
    // Upload methods
    async uploadFiles() {
      if (this.selectedFiles.length === 0) return;
      
      this.isUploading = true;
      
      // 用于跟踪上传的文件
      const uploadedFiles = [];
      let failedFiles = 0;
      
      // 逐个处理每个文件
      for (const file of this.selectedFiles) {
        try {
          const formData = new FormData();
          formData.append('file', file); // 单个文件上传
          formData.append('extract_knowledge', this.extractKnowledge.toString());
          
          // 调用实际的后端API
          const response = await fetch('/api/v1/documents/upload', {
            method: 'POST',
            body: formData
          });
          
          if (!response.ok) {
            throw new Error(`上传失败：${response.status} ${response.statusText}`);
          }
          
          const result = await response.json();
          
          // 添加上传的文件到文档列表
          if (result.document) {
            this.documents.push(result.document);
            uploadedFiles.push(result.document);
            console.log(`文件 ${file.name} 已存储在:`, result.document.file_path || result.document.archived_path);
          }
        } catch (error) {
          console.error(`文件 ${file.name} 上传错误:`, error);
          failedFiles++;
        }
      }
      
      // 显示上传结果
      if (uploadedFiles.length > 0) {
        alert(`成功上传 ${uploadedFiles.length} 个文件！${failedFiles > 0 ? `${failedFiles} 个文件上传失败。` : ''}`);
      } else {
        alert('所有文件上传失败！请检查控制台获取详细错误信息。');
      }
      
      // 清除已选择的文件
      this.selectedFiles = [];
      
      // 刷新文档列表
      await this.fetchDocuments();
      
      this.isUploading = false;
    },
    
    // URL processing
    async processUrl() {
      if (!this.webUrl) return;
      
      this.isProcessingUrl = true;
      
      try {
        // 调用实际的后端API
        const response = await fetch('/api/v1/documents/url', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            'url': this.webUrl,
            'extract_knowledge': this.extractKnowledge.toString()
          })
        });
        
        if (!response.ok) {
          throw new Error(`处理URL失败：${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // 添加处理的网页到文档列表
        if (result.document) {
          this.documents.push(result.document);
          console.log('网页已存储在:', result.document.archived_path);
          
          // 显示成功消息
          alert(`网页导入成功！${result.extracted_entities > 0 ? `已提取 ${result.extracted_entities} 个实体和 ${result.extracted_relationships} 个关系。` : ''}`);
        }
        
        // 清除URL
        this.webUrl = '';
        
      } catch (error) {
        console.error('处理URL错误:', error);
        alert('处理URL失败：' + error.message);
      } finally {
        this.isProcessingUrl = false;
      }
    },
    
    // Document actions
    viewDocument(doc) {
      // 跳转到文档查看器页面
      if (doc.type === 'webpage') {
        // 对于网页类型，可以直接打开原始URL（如果有）
        if (doc.url) {
          window.open(doc.url, '_blank');
          return;
        }
      }
      
      // 其他文档类型或网页没有原始URL的情况
      // 使用预览API
      const previewUrl = `/api/v1/documents/${doc.id}/preview`;
      window.open(previewUrl, '_blank');
    },
    
    async extractFromDocument(doc) {
      // 触发知识提取
      try {
        if (!confirm(`确定要从文档 "${doc.title}" 提取知识吗？`)) {
          return;
        }
        
        const response = await fetch(`/api/v1/documents/${doc.id}/extract`, {
          method: 'POST'
        });
        
        if (!response.ok) {
          throw new Error(`提取知识失败：${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        alert(`知识提取成功！已提取 ${result.extracted_entities} 个实体和 ${result.extracted_relationships} 个关系。`);
      } catch (error) {
        console.error('知识提取错误:', error);
        alert('知识提取失败：' + error.message);
      }
    },
    
    downloadDocument(doc) {
      // 下载文档
      const downloadUrl = `/api/v1/documents/${doc.id}/download`;
      
      // 创建临时a元素用于下载
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = doc.title;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    },
    
    async deleteDocument(doc) {
      // 删除文档
      if (confirm(`确定要删除文档 "${doc.title}" 吗？这将同时删除与之关联的所有知识实体和关系。`)) {
        try {
          const response = await fetch(`/api/v1/documents/${doc.id}`, {
            method: 'DELETE'
          });
          
          if (!response.ok) {
            throw new Error(`删除失败：${response.status} ${response.statusText}`);
          }
          
          // 从列表中移除文档
          this.documents = this.documents.filter(d => d.id !== doc.id);
          
          alert('文档已成功删除');
        } catch (error) {
          console.error('删除文档错误:', error);
          alert('删除文档失败：' + error.message);
        }
      }
    },
    
    exportDocument(doc) {
      // 导出文档元数据和关联知识
      const exportUrl = `/api/v1/documents/${doc.id}/export`;
      window.open(exportUrl, '_blank');
    },
    
    // Helper methods
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString();
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
    
    // Lifecycle methods
    async fetchDocuments() {
      this.loading = true;
      
      try {
        // 调用实际的API获取文档列表
        const response = await fetch('/api/v1/documents', {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`获取文档列表失败：${response.status} ${response.statusText}`);
        }
        
        // 解析响应
        const data = await response.json();
        this.documents = data;
        
        console.log('文档列表已获取，共', this.documents.length, '个文档');
      } catch (error) {
        console.error('获取文档列表错误:', error);
        // 如果API调用失败，使用模拟数据
        this.documents = [
          {
            id: 'doc1',
            title: '知识图谱：机遇与挑战.pdf',
            type: 'pdf',
            created_at: '2023-01-15T09:28:00Z'
          },
          {
            id: 'doc2',
            title: '个人知识管理系统设计.docx',
            type: 'docx',
            created_at: '2023-02-20T14:35:00Z'
          },
          {
            id: 'doc3',
            title: '研究笔记.txt',
            type: 'txt',
            created_at: '2023-03-05T11:15:00Z'
          }
        ];
        alert('获取文档列表失败，显示模拟数据：' + error.message);
      } finally {
        this.loading = false;
      }
    }
  },
  mounted() {
    this.fetchDocuments();
  }
};
</script>

<style scoped>
.documents-container {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}

h2 {
  font-size: 1.2rem;
  margin-bottom: 15px;
}

.documents-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.upload-area,
.web-url-import {
  background-color: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dropzone {
  border: 2px dashed #ddd;
  border-radius: 4px;
  padding: 30px;
  text-align: center;
  transition: all 0.3s;
}

.dropzone.active {
  border-color: var(--primary-color);
  background-color: rgba(74, 144, 226, 0.05);
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.dropzone-content i {
  font-size: 2rem;
  color: #999;
}

.file-input {
  display: none;
}

.btn {
  padding: 8px 16px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn:hover {
  background-color: #3a80d2;
}

.btn:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.selected-files {
  margin-top: 20px;
}

.file-list {
  list-style: none;
  margin: 15px 0;
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  margin-bottom: 8px;
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-weight: 500;
}

.file-size {
  color: #777;
  font-size: 0.9rem;
}

.btn-remove {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-remove:hover {
  color: #d9534f;
}

.upload-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
}

.option {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.url-input-group {
  display: flex;
  gap: 10px;
}

.url-input-group input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.documents-list {
  background-color: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
  color: var(--primary-color);
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

@media (max-width: 768px) {
  .documents-actions {
    grid-template-columns: 1fr;
  }
}
</style>