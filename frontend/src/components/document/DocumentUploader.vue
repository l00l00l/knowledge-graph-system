<!-- frontend/src/components/document/DocumentUploader.vue -->
<template>
    <div class="document-uploader">
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
            <i :class="isUploading ? 'fas fa-spinner fa-spin' : 'fas fa-upload'"></i>
            {{ isUploading ? '上传中...' : '开始上传' }}
          </button>
        </div>
      </div>
      
      <div v-if="uploadResults.length > 0" class="upload-results">
        <h3>上传结果</h3>
        <div v-for="(result, index) in uploadResults" :key="index" class="result-item">
          <div :class="['result-status', result.success ? 'success' : 'error']">
            <i :class="result.success ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
            <span>{{ result.fileName }}</span>
          </div>
          <div v-if="result.error" class="error-message">
            {{ result.error }}
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'DocumentUploader',
    props: {
      apiEndpoint: {
        type: String,
        default: '/api/v1/documents/upload'
      }
    },
    data() {
      return {
        isDragging: false,
        isUploading: false,
        selectedFiles: [],
        extractKnowledge: false,
        uploadResults: []
      };
    },
    methods: {
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
      formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
      },
      async uploadFiles() {
        if (this.selectedFiles.length === 0) return;
        
        this.isUploading = true;
        this.uploadResults = [];
        
        const totalFiles = this.selectedFiles.length;
        let successCount = 0;
        
        // 逐个处理每个文件
        for (const file of this.selectedFiles) {
          try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('extract_knowledge', this.extractKnowledge.toString());
            
            // 调用API上传文件
            const response = await fetch(this.apiEndpoint, {
              method: 'POST',
              body: formData
            });
            
            if (!response.ok) {
              const errorText = await response.text();
              throw new Error(`Upload failed: ${response.status} - ${errorText}`);
            }
            
            const result = await response.json();
            
            // 添加成功结果
            this.uploadResults.push({
              fileName: file.name,
              success: true,
              document: result.document
            });
            
            successCount++;
            
            // 提交事件，通知父组件上传成功
            this.$emit('document-uploaded', result.document);
            
          } catch (error) {
            console.error(`Error uploading ${file.name}:`, error);
            
            // 添加错误结果
            this.uploadResults.push({
              fileName: file.name,
              success: false,
              error: error.message
            });
          }
        }
        
        // 所有文件处理完毕
        this.isUploading = false;
        
        // 提交完成事件
        this.$emit('upload-complete', {
          total: totalFiles,
          success: successCount,
          failed: totalFiles - successCount
        });
        
        // 如果全部成功，清空选择的文件
        if (successCount === totalFiles) {
          setTimeout(() => {
            this.selectedFiles = [];
          }, 3000);
        }
      }
    }
  };
  </script>
  
  <style scoped>
  .document-uploader {
    margin-bottom: 20px;
  }
  
  .dropzone {
    border: 2px dashed #ddd;
    border-radius: 4px;
    padding: 30px;
    text-align: center;
    transition: all 0.3s;
  }
  
  .dropzone.active {
    border-color: var(--primary-color, #4a90e2);
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
    background-color: var(--primary-color, #4a90e2);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }
  
  .btn:hover {
    background-color: var(--primary-hover, #3a80d2);
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
    padding: 0;
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
  
  .upload-results {
    margin-top: 20px;
    border-top: 1px solid #eee;
    padding-top: 15px;
  }
  
  .result-item {
    margin-bottom: 10px;
  }
  
  .result-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
  }
  
  .result-status.success i {
    color: #28a745;
  }
  
  .result-status.error i {
    color: #dc3545;
  }
  
  .error-message {
    color: #dc3545;
    font-size: 0.9rem;
    margin-left: 24px;
  }
  </style>