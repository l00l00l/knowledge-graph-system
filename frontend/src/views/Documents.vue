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
      onDragOver(e) {
        this.isDragging = true;
      },
      onDragLeave(e) {
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
        const formData = new FormData();
        
        for (const file of this.selectedFiles) {
          formData.append('files', file);
        }
        
        formData.append('extract_knowledge', this.extractKnowledge);
        
        try {
          // Simulate API call
          console.log('Uploading files...', this.selectedFiles);
          
          // In a real app, you'd use something like:
          // const response = await fetch('/api/v1/documents/upload', {
          //   method: 'POST',
          //   body: formData
          // });
          
          // Simulate delay
          await new Promise(r => setTimeout(r, 1500));
          
          // Add uploaded files to the documents list (simulation)
          for (const file of this.selectedFiles) {
            this.documents.push({
              id: 'doc_' + Math.random().toString(36).substr(2, 9),
              title: file.name,
              type: file.name.split('.').pop().toLowerCase(),
              created_at: new Date().toISOString()
            });
          }
          
          // Clear selected files
          this.selectedFiles = [];
          
          // Show success message (in a real app)
          console.log('Files uploaded successfully!');
        } catch (error) {
          console.error('Error uploading files:', error);
        } finally {
          this.isUploading = false;
        }
      },
      
      // URL processing
      async processUrl() {
        if (!this.webUrl) return;
        
        this.isProcessingUrl = true;
        
        try {
          // Simulate API call
          console.log('Processing URL:', this.webUrl);
          
          // Simulate delay
          await new Promise(r => setTimeout(r, 1500));
          
          // Add processed URL to documents (simulation)
          const urlParts = this.webUrl.split('/');
          const title = urlParts[urlParts.length - 1] || 'webpage';
          
          this.documents.push({
            id: 'url_' + Math.random().toString(36).substr(2, 9),
            title: title.length > 0 ? title : 'Webpage',
            type: 'webpage',
            created_at: new Date().toISOString()
          });
          
          // Clear URL
          this.webUrl = '';
          
          // Show success message (in a real app)
          console.log('URL processed successfully!');
        } catch (error) {
          console.error('Error processing URL:', error);
        } finally {
          this.isProcessingUrl = false;
        }
      },
      
      // Document actions
      viewDocument(doc) {
        // Navigate to document viewer
        console.log('Viewing document:', doc);
      },
      extractFromDocument(doc) {
        // Trigger knowledge extraction
        console.log('Extracting knowledge from document:', doc);
      },
      downloadDocument(doc) {
        // Download document
        console.log('Downloading document:', doc);
      },
      async deleteDocument(doc) {
        // Delete document
        if (confirm(`确定要删除文档 "${doc.title}" 吗？`)) {
          console.log('Deleting document:', doc);
          this.documents = this.documents.filter(d => d.id !== doc.id);
        }
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
          // Simulate API call
          console.log('Fetching documents...');
          
          // Simulate delay
          await new Promise(r => setTimeout(r, 1000));
          
          // Sample data
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
        } catch (error) {
          console.error('Error fetching documents:', error);
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