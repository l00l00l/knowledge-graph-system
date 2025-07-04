<!-- Documents.vue -->
<template>
  <div class="documents-container">
    <h1>文档管理</h1>
    
    <div class="documents-actions">
      <div class="upload-area">
        <h2>上传文档</h2>
        <document-uploader @entity-created="handleEntityCreated"></document-uploader>
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
                <i :class="getFileIcon(file.name)"></i>
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
              <i :class="isUploading ? 'fas fa-spinner fa-spin' : 'fas fa-upload'"></i>
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
            <i :class="isProcessingUrl ? 'fas fa-spinner fa-spin' : 'fas fa-globe'"></i>
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
        
        <button @click="fetchDocuments" class="refresh-btn" :disabled="loading">
          <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"></i>
          <span>{{ loading ? '加载中...' : '刷新' }}</span>
        </button>
      </div>
      
      <div v-if="loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i>
        <span>加载中... ({{ documents.length }} 个文档)</span>
      </div>
      
      <div v-else-if="filteredDocuments.length === 0" class="no-documents">
        <i class="fas fa-file-alt"></i>
        <p>暂无文档 (总文档数: {{ documents.length }})</p>
        <button @click="fetchDocuments" class="btn">
          <i class="fas fa-sync"></i> 重新加载
        </button>
      </div>
      
      <table v-else class="documents-table">
        <thead>
          <tr>
            <th>标题</th>
            <th>类型</th>
            <th>上传时间</th>
            <th style="min-width: 150px; text-align: right;">操作</th>
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
              <!-- Remove any v-if conditions on these buttons -->
              <button @click="viewDocument(doc)" class="btn-action" title="预览">
                <i class="fas fa-eye"></i>
              </button>
              <button @click="extractFromDocument(doc)" class="btn-action" title="提取知识">
                <i class="fas fa-magic"></i>
              </button>
              <button @click="downloadDocument(doc)" class="btn-action" title="下载">
                <i class="fas fa-download"></i>
              </button>
              <button @click="deleteDocument(doc)" class="btn-action delete" title="删除">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
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
        <div v-else-if="previewingDocument && previewingDocument.type.toLowerCase() === 'pdf'" class="pdf-preview">
          <div class="pdf-content">
            <pre class="content-preview">{{ documentContent }}</pre>
          </div>
          <div class="pdf-footer">
            <p>PDF预览可能不完整。要查看完整内容，请下载文件。</p>
          </div>
        </div>
        <div v-else-if="previewingDocument && ['docx', 'doc'].includes(previewingDocument.type.toLowerCase())" class="word-preview">
          <div class="word-content">
            <pre class="content-preview">{{ documentContent }}</pre>
          </div>
          <div class="word-footer">
            <p>Word预览可能不完整。要查看完整格式，请下载文件。</p>
          </div>
        </div>
        <div v-else-if="previewingDocument && previewingDocument.is_image" class="image-preview">
          <img 
            :src="previewingDocument.preview_url" 
            :alt="previewingDocument.title" 
            class="preview-image"
          />
        </div>
        <div v-else-if="documentContent && documentContent.startsWith('[')" class="binary-preview">
          <i :class="getPreviewIcon()"></i>
          <p>{{ documentContent }}</p>
          <button @click="downloadDocument(previewingDocument)" class="btn btn-primary">
            <i class="fas fa-download"></i> 下载文件
          </button>
        </div>
        <pre v-else class="content-preview">{{ documentContent }}</pre>
      </div>
        <div class="preview-footer">
          <button @click="closePreview" class="btn">关闭</button>
          <button @click="downloadDocument(previewingDocument)" class="btn btn-primary">
            <i class="fas fa-download"></i> 下载
          </button>
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
          <p>您确定要删除文档 "{{ deletingDocument.title }}" 吗？此操作无法撤销，并且将同时删除与之关联的所有知识实体和关系。</p>
        </div>
        <div class="confirm-footer">
          <button @click="cancelDelete" class="btn">取消</button>
          <button @click="confirmDelete" class="btn btn-danger" :disabled="isDeleting">
            <i :class="isDeleting ? 'fas fa-spinner fa-spin' : 'fas fa-trash'"></i>
            {{ isDeleting ? '删除中...' : '删除' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 提取知识进度对话框 -->
    <div v-if="showExtractProgress" class="progress-dialog">
      <div class="progress-content">
        <div class="progress-header">
          <h3>知识提取</h3>
        </div>
        <div class="progress-body">
          <div class="progress-status">
            <i class="fas fa-spinner fa-spin"></i>
            <p>正在从"{{ extractingDocument.title }}"提取知识...</p>
            <p class="progress-info">这可能需要一段时间，请耐心等待</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- 实体JSON编辑器模态框 - 确保这段代码存在于 Documents.vue 中 -->
  <div v-if="showEntityModal" class="json-edit-modal">
    <div class="json-edit-content">
      <div class="json-edit-header">
        <h3>编辑新创建的文档实体</h3>
        <button @click="closeEntityModal" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="json-edit-body">
        <div class="entity-info-box">
          <div class="entity-info-item">
            <span class="label">文档:</span>
            <span class="value">{{ editingEntity?.name || '未命名' }}</span>
          </div>
          <div class="entity-info-item">
            <span class="label">类型:</span>
            <span class="value">{{ getEntityTypeName(editingEntity?.type) || '概念' }}</span>
          </div>
        </div>
        
        <div class="entity-edit-message">
          <i class="fas fa-info-circle"></i>
          <span>您可以编辑这个由文档自动创建的实体，修改其属性、标签等信息。</span>
        </div>
        
        <textarea 
          v-model="entityJsonContent" 
          class="json-editor"
          spellcheck="false"
          rows="20"
          placeholder="实体JSON数据"
        ></textarea>
        
        <div v-if="jsonValidationError" class="json-validation-error">
          <i class="fas fa-times-circle"></i>
          <span>{{ jsonValidationError }}</span>
        </div>
      </div>
      
      <div class="json-edit-footer">
        <button @click="formatEntityJson" class="format-btn">
          <i class="fas fa-code"></i> 格式化JSON
        </button>
        <div class="right-actions">
          <button @click="closeEntityModal" class="cancel-btn">关闭</button>
          <button @click="saveEntityChanges" class="save-btn" :disabled="!!jsonValidationError">
            <i class="fas fa-save"></i> 保存修改
          </button>
        </div>
      </div>
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
      isDeleting: false,
      selectedFiles: [],
      extractKnowledge: false,
      webUrl: '',
      searchQuery: '',
      typeFilter: '',
      documents: [],
      
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
      showExtractProgress: false,
      extractingDocument: null,
      isExtracting: false,
      hasShownFetchError: false,
      showEntityModal: false,
      editingEntity: null,
      entityJsonContent: '',
      jsonValidationError: null
    };
  },
  computed: {
    filteredDocuments() {
      console.log('Computing filteredDocuments, documents array:', this.documents);
      console.log('Current document count:', this.documents?.length);
      
      if (!Array.isArray(this.documents)) {
        console.error('documents is not an array:', this.documents);
        return [];
      }
      
      let filtered = [...this.documents];
      
      // Apply search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(doc => 
          doc && doc.title && doc.title.toLowerCase().includes(query)
        );
      }
      
      // Apply type filter
      if (this.typeFilter) {
        filtered = filtered.filter(doc => doc && doc.type === this.typeFilter);
      }
      
      // Sort by upload time in descending order (with error handling)
      try {
        filtered.sort((a, b) => {
          if (!a || !a.created_at) return 1;
          if (!b || !b.created_at) return -1;
          
          const dateA = new Date(a.created_at);
          const dateB = new Date(b.created_at);
          
          if (isNaN(dateA.getTime()) || isNaN(dateB.getTime())) {
            return 0;
          }
          
          return dateB - dateA;
        });
      } catch (error) {
        console.error('Error sorting documents:', error);
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
            // 确保document.id是字符串类型
            if (typeof result.document.id === 'object') {
              result.document.id = String(result.document.id);
            }
            
            // 添加到列表顶部而不是追加到末尾
            this.documents.unshift(result.document);
            uploadedFiles.push(result.document);
            console.log(`文件 ${file.name} 已存储在:`, result.document.file_path || result.document.archived_path);
            console.log('Upload completed, forcing document list refresh');
            // 检查是否包含实体信息并显示编辑器
            // 重要：无论是否勾选提取知识，只要返回了实体，就打开编辑器
            if (result.entity) {
              console.log('Entity detected in upload response, opening editor:', result.entity);
              
              // 设置实体数据
              this.editingEntity = result.entity;
              this.entityJsonContent = JSON.stringify(result.entity, null, 2);
              this.showEntityModal = true;
            } else {
              console.log('No entity data in upload response');
            }

            //this.documents = []; // 清空当前列表
            //await this.fetchDocuments(); // 重新获取
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
      
      // 刷新文档列表确保数据最新
      await this.fetchDocuments();
      
      this.isUploading = false;
    },
    
    // URL processing
    async processUrl() {
      if (!this.webUrl) return;
      
      this.isProcessingUrl = true;
      
      try {
        // 使用FormData而非URLSearchParams，保持一致性
        const formData = new FormData();
        formData.append('url', this.webUrl);
        formData.append('extract_knowledge', this.extractKnowledge.toString());
        
        // 调用实际的后端API
        const response = await fetch('/api/v1/documents/url', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`处理URL失败：${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // 添加处理的网页到文档列表
        if (result.document) {
          this.documents.unshift(result.document); // 添加到列表顶部
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
    
    // Document preview actions
    async viewDocument(doc) {
      // 设置预览状态
      this.previewingDocument = doc;
      this.showPreview = true;
      this.previewLoading = true;
      this.documentContent = '';
      this.previewError = null;
      
      try {
        // 对于网页类型，可以直接打开原始URL
        if (doc.type === 'webpage' && doc.url) {
          window.open(doc.url, '_blank');
          this.closePreview();
          return;
        }
        
        // 调用API获取文档预览内容
        const response = await fetch(`/api/v1/documents/${doc.id}/preview`);
        
        if (!response.ok) {
          throw new Error(`预览失败: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.preview_available) {
          this.documentContent = result.content || '(无内容)';
        } else {
          throw new Error('无法预览此类型的文档');
        }
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
    // 获取实体类型的中文名称
    getEntityTypeName(typeCode) {
      // 静态实体类型映射表
      const typeMap = {
        'concept': '概念',
        'person': '人物',
        'organization': '组织',
        'location': '地点',
        'time': '时间',
        'event': '事件',
        'technology': '技术',
        'theory': '理论',
        'method': '方法',
        'problem': '问题',
        'tool': '工具',
        'solution': '解决方案',
        'note': '笔记',
        'question': '问题',
        'idea': '想法',
        'goal': '目标',
        'plan': '计划'
      };
      
      return typeMap[typeCode] || typeCode || '未知类型';
    },
    // Knowledge extraction
    async extractFromDocument(doc) {
      if (this.isExtracting) return;
      
      // 设置提取状态
      this.isExtracting = true;
      this.extractingDocument = doc;
      this.showExtractProgress = true;
      
      try {
        // 调用API执行知识提取
        const response = await fetch(`/api/v1/documents/${doc.id}/extract`, {
          method: 'POST'
        });
        
        if (!response.ok) {
          throw new Error(`提取知识失败: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 提取完成后关闭进度对话框
        this.showExtractProgress = false;
        
        // 显示结果提示
        alert(`知识提取成功！已提取 ${result.extracted_entities} 个实体和 ${result.extracted_relationships} 个关系。`);
      } catch (error) {
        console.error('知识提取失败:', error);
        alert('知识提取失败: ' + error.message);
        this.showExtractProgress = false;
      } finally {
        this.isExtracting = false;
        this.extractingDocument = null;
      }
    },
    
    // Document download
    downloadDocument(doc) {
      // 使用更简洁的下载方法
      const downloadUrl = `/api/v1/documents/${doc.id}/download`;
      window.open(downloadUrl);
    },
    
    // Document delete actions
    deleteDocument(doc) {
      // 显示删除确认对话框
      this.deletingDocument = doc;
      this.showDeleteConfirm = true;
    },
    
    cancelDelete() {
      // 取消删除
      this.showDeleteConfirm = false;
      this.deletingDocument = null;
    },
    
    async confirmDelete() {
      if (!this.deletingDocument || this.isDeleting) return;
      
      // 设置删除状态
      this.isDeleting = true;
      
      try {
        // 调用API删除文档
        const response = await fetch(`/api/v1/documents/${this.deletingDocument.id}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`删除失败: ${response.status}`);
        }
        
        // 从列表中移除文档
        this.documents = this.documents.filter(d => d.id !== this.deletingDocument.id);
        
        // 关闭确认对话框
        this.showDeleteConfirm = false;
        this.deletingDocument = null;
        
        // 显示成功提示
        alert('文档已成功删除');
      } catch (error) {
        console.error('删除文档错误:', error);
        alert('删除文档失败：' + error.message);
      } finally {
        this.isDeleting = false;
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
    // 处理新创建的实体
    handleEntityCreated(entity) {
      this.editingEntity = entity;
      this.entityJsonContent = JSON.stringify(entity, null, 2);
      this.showEntityModal = true;
    },
     // 格式化JSON
    formatEntityJson() {
      try {
        const parsed = JSON.parse(this.entityJsonContent);
        this.entityJsonContent = JSON.stringify(parsed, null, 2);
        this.jsonValidationError = null;
      } catch (e) {
        this.jsonValidationError = 'JSON格式错误：' + e.message;
      }
    },

    // 验证JSON
    validateEntityJson() {
      try {
        JSON.parse(this.entityJsonContent);
        this.jsonValidationError = null;
        return true;
      } catch (e) {
        this.jsonValidationError = 'JSON格式错误：' + e.message;
        return false;
      }
    },

    // 保存实体修改
    async saveEntityChanges() {
      if (!this.validateEntityJson()) return;
      
      try {
        const updatedEntity = JSON.parse(this.entityJsonContent);
        
        const response = await fetch(`/api/v1/entities/${updatedEntity.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: this.entityJsonContent
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`操作失败: ${response.status} - ${errorText}`);
        }
        
        const savedEntity = await response.json();
        console.log('实体保存成功:', savedEntity);
        
        this.closeEntityModal();
        alert('实体数据已成功更新');
      } catch (error) {
        console.error('保存实体数据错误:', error);
        alert('更新失败: ' + error.message);
      }
    },
    
    // 关闭编辑模态框
    closeEntityModal() {
      this.showEntityModal = false;
      this.editingEntity = null;
      this.entityJsonContent = '';
      this.jsonValidationError = null;
    },
    formatDate(dateString) {
      if (!dateString) return '';
      try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
          return 'Invalid Date';
        }
        return date.toLocaleString();
      } catch (error) {
        console.error('Error formatting date:', error);
        return 'Error';
      }
    },
    
    // Add this method to your Vue component
    getPreviewIcon() {
      if (!this.previewingDocument) return 'fas fa-file';
      
      const type = this.previewingDocument.type.toLowerCase();
      const iconMap = {
        'pdf': 'fas fa-file-pdf fa-3x',
        'docx': 'fas fa-file-word fa-3x',
        'doc': 'fas fa-file-word fa-3x',
        'ppt': 'fas fa-file-powerpoint fa-3x',
        'pptx': 'fas fa-file-powerpoint fa-3x',
        'xls': 'fas fa-file-excel fa-3x',
        'xlsx': 'fas fa-file-excel fa-3x',
        'txt': 'fas fa-file-alt fa-3x',
      };
      
      return iconMap[type] || 'fas fa-file fa-3x';
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
    
    getFileIcon(filename) {
      const ext = filename.split('.').pop().toLowerCase();
      
      const iconMap = {
        'pdf': 'fas fa-file-pdf',
        'docx': 'fas fa-file-word',
        'doc': 'fas fa-file-word',
        'txt': 'fas fa-file-alt',
        'html': 'fas fa-file-code',
        'htm': 'fas fa-file-code',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'png': 'fas fa-file-image',
        'gif': 'fas fa-file-image'
      };
      
      return iconMap[ext] || 'fas fa-file';
    },
    
    // In the fetchDocuments method in Documents.vue, add more debugging and error handling
    async fetchDocuments() {
      console.log('Starting to fetch documents...');
      this.loading = true;
      
      try {
        const response = await fetch('/api/v1/documents/', {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`服务器响应错误: ${response.status}`);
        }
        
        // First, get the raw text to debug
        const responseText = await response.text();
        console.log('Raw API response:', responseText);
        
        // Parse it manually
        let data;
        try {
          data = JSON.parse(responseText);
          console.log('Parsed document data, length:', data.length);
        } catch (e) {
          console.error('Failed to parse JSON response:', e);
          throw new Error('API返回了无效的JSON格式');
        }
        
        // Explicitly set documents with the parsed data
        if (Array.isArray(data)) {
          this.documents = data;
          console.log('Successfully set documents array, length:', this.documents.length);
        } else {
          console.error('API response is not an array:', data);
          this.documents = [];
        }
      } catch (error) {
        console.error('Error fetching documents:', error);
        this.documents = []; // Clear documents on error
      } finally {
        this.loading = false;
        console.log('Document fetch complete, loading set to false');
      }
    }
  },
  mounted() {
    console.log('Documents component mounted, fetching documents...');
    this.fetchDocuments().catch(err => {
      console.error('Error in mounted hook when fetching documents:', err);
      this.loading = false;
    });
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
  display: inline-flex;
  align-items: center;
  gap: 5px;
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
  padding-left: 0;
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
  word-break: break-word;
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
  flex-shrink: 0;
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

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background-color: #f0f0f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #333;
}

.refresh-btn:hover {
  background-color: #e0e0e0;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  display: block;
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

/* 共用对话框样式 */
.preview-dialog,
.confirm-dialog,
.progress-dialog {
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

.confirm-content,
.progress-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 400px;
}

.preview-header,
.confirm-header,
.progress-header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-header h3,
.confirm-header h3,
.progress-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
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

.confirm-body,
.progress-body {
  padding: 20px;
}

.preview-footer,
.confirm-footer {
  padding: 15px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.progress-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.progress-status i {
  font-size: 2rem;
  margin-bottom: 15px;
  color: var(--primary-color);
}

.progress-info {
  font-size: 0.9rem;
  color: #666;
  margin-top: 10px;
}

.btn-primary {
  background-color: var(--primary-color);
}

.btn-danger {
  background-color: #d9534f;
}

@media (max-width: 768px) {
  .documents-actions {
    grid-template-columns: 1fr;
  }
  
  .filters {
    flex-direction: column;
  }
  
  .document-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  .preview-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .confirm-content,
  .progress-content {
    width: 90%;
  }
}

/* Add this CSS to the <style> section of Documents.vue */
.document-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  min-width: 140px;
}

.btn-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  color: #555;
  transition: all 0.2s ease;
}

.btn-action:hover {
  background-color: #e0e0e0;
  color: #333;
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.btn-action i {
  font-size: 14px;
}

/* Different colors for different action types */
.btn-action.preview {
  background-color: #e3f2fd;
  color: #2196F3;
}

.btn-action.extract {
  background-color: #e8f5e9;
  color: #4CAF50;
}

.btn-action.download {
  background-color: #fff3e0;
  color: #FF9800;
}

.btn-action.delete {
  background-color: #ffebee;
  color: #F44336;
}

.btn-action.preview:hover {
  background-color: #bbdefb;
}

.btn-action.extract:hover {
  background-color: #c8e6c9;
}

.btn-action.download:hover {
  background-color: #ffe0b2;
}

.btn-action.delete:hover {
  background-color: #ffcdd2;
}

.pdf-preview, .word-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pdf-content, .word-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.pdf-footer, .word-footer {
  padding: 10px 0;
  text-align: center;
  font-style: italic;
  color: #666;
  border-top: 1px solid #eee;
}

.binary-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.binary-preview i {
  font-size: 3rem;
  margin-bottom: 20px;
  color: #607d8b;
}

.binary-preview p {
  margin-bottom: 20px;
  font-size: 1.1rem;
}

.json-edit-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100;
}

.json-edit-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 800px;
  max-width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.json-edit-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.json-edit-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.entity-info-box {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.entity-info-item {
  display: flex;
  gap: 6px;
  align-items: center;
}

.entity-info-item .label {
  font-weight: 500;
  color: #666;
}

.entity-info-item .value {
  font-weight: 600;
  color: #333;
}

.entity-edit-message {
  background-color: #e3f2fd;
  color: #0277bd;
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.entity-edit-message i {
  font-size: 1.2em;
}

.json-editor {
  width: 100%;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f8f9fa;
  color: #333;
  resize: vertical;
  min-height: 300px;
  white-space: pre;
  overflow-wrap: normal;
  overflow-x: auto;
}

.json-validation-error {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px 16px;
  border-radius: 4px;
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.json-edit-footer {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.format-btn {
  background-color: #e9ecef;
  color: #495057;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.format-btn:hover {
  background-color: #dde2e6;
}

.right-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn {
  padding: 8px 16px;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn {
  padding: 8px 16px;
  background-color: var(--primary-color, #4a90e2);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.save-btn:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.image-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background-color: #f5f5f5;
  height: 100%;
  min-height: 200px;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>