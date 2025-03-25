<!-- components/common/FeedbackCollector.vue -->
<template>
    <div class="feedback-collector">
      <button class="feedback-button" @click="openFeedback">
        <i class="fas fa-comment"></i>
        <span>反馈</span>
      </button>
      
      <div class="feedback-modal" v-if="showModal" @click.self="closeModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>用户反馈</h3>
            <button class="close-button" @click="closeModal">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <div class="feedback-type-selector">
              <button 
                v-for="type in feedbackTypes" 
                :key="type.value"
                :class="['type-button', { active: feedbackType === type.value }]"
                @click="selectFeedbackType(type.value)"
              >
                <i :class="type.icon"></i>
                <span>{{ type.label }}</span>
              </button>
            </div>
            
            <div class="feedback-form">
              <div v-if="feedbackType === 'issue'">
                <div class="form-group">
                  <label>问题描述</label>
                  <textarea 
                    v-model="issueDescription" 
                    placeholder="请描述您遇到的问题..."
                    rows="4"
                  ></textarea>
                </div>
                
                <div class="form-group">
                  <label>问题类型</label>
                  <select v-model="issueType">
                    <option value="bug">功能错误</option>
                    <option value="ui">界面问题</option>
                    <option value="performance">性能问题</option>
                    <option value="knowledge">知识错误</option>
                    <option value="other">其他</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label>严重程度</label>
                  <div class="severity-selector">
                    <div 
                      v-for="i in 5" 
                      :key="i"
                      :class="['severity-level', { active: issueSeverity >= i }]"
                      @click="issueSeverity = i"
                    ></div>
                  </div>
                  <span class="severity-label">{{ severityLabels[issueSeverity - 1] }}</span>
                </div>
              </div>
              
              <div v-else-if="feedbackType === 'suggestion'">
                <div class="form-group">
                  <label>功能建议</label>
                  <textarea 
                    v-model="suggestionText" 
                    placeholder="请描述您希望系统增加的功能..."
                    rows="4"
                  ></textarea>
                </div>
                
                <div class="form-group">
                  <label>预期效果</label>
                  <textarea 
                    v-model="expectedOutcome" 
                    placeholder="这个功能将如何帮助您..."
                    rows="3"
                  ></textarea>
                </div>
              </div>
              
              <div v-else-if="feedbackType === 'rating'">
                <div class="form-group">
                  <label>系统评分</label>
                  <div class="star-rating">
                    <i 
                      v-for="i in 5" 
                      :key="i"
                      :class="['fas', i <= rating ? 'fa-star' : 'fa-star-o']"
                      @click="rating = i"
                    ></i>
                  </div>
                </div>
                
                <div class="form-group">
                  <label>评价内容</label>
                  <textarea 
                    v-model="ratingComment" 
                    placeholder="请分享您的使用体验..."
                    rows="4"
                  ></textarea>
                </div>
                
                <div class="form-group">
                  <label>推荐意愿</label>
                  <div class="nps-selector">
                    <div 
                      v-for="i in 10" 
                      :key="i"
                      :class="['nps-level', { active: npsScore === i }]"
                      @click="npsScore = i"
                    >
                      {{ i }}
                    </div>
                  </div>
                  <div class="nps-labels">
                    <span>不太可能</span>
                    <span>非常可能</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="secondary-button" @click="closeModal">取消</button>
            <button class="primary-button" @click="submitFeedback" :disabled="!isFormValid">
              提交反馈
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'FeedbackCollector',
    data() {
      return {
        showModal: false,
        feedbackType: 'issue',
        
        // 问题反馈表单
        issueDescription: '',
        issueType: 'bug',
        issueSeverity: 3,
        
        // 建议反馈表单
        suggestionText: '',
        expectedOutcome: '',
        
        // 评分反馈表单
        rating: 0,
        ratingComment: '',
        npsScore: 0,
        
        // 表单选项
        feedbackTypes: [
          { value: 'issue', label: '问题反馈', icon: 'fas fa-bug' },
          { value: 'suggestion', label: '功能建议', icon: 'fas fa-lightbulb' },
          { value: 'rating', label: '系统评分', icon: 'fas fa-star' }
        ],
        severityLabels: ['轻微', '一般', '中等', '严重', '阻塞']
      };
    },
    computed: {
      isFormValid() {
        if (this.feedbackType === 'issue') {
          return this.issueDescription.trim().length > 0;
        } else if (this.feedbackType === 'suggestion') {
          return this.suggestionText.trim().length > 0;
        } else if (this.feedbackType === 'rating') {
          return this.rating > 0;
        }
        return false;
      }
    },
    methods: {
      openFeedback() {
        this.showModal = true;
      },
      closeModal() {
        this.showModal = false;
      },
      selectFeedbackType(type) {
        this.feedbackType = type;
      },
      async submitFeedback() {
        if (!this.isFormValid) return;
        
        const feedbackData = {
          type: this.feedbackType,
          timestamp: new Date().toISOString(),
          url: window.location.href,
          userAgent: navigator.userAgent
        };
        
        // 根据反馈类型添加不同数据
        if (this.feedbackType === 'issue') {
          feedbackData.description = this.issueDescription;
          feedbackData.issueType = this.issueType;
          feedbackData.severity = this.issueSeverity;
        } else if (this.feedbackType === 'suggestion') {
          feedbackData.suggestion = this.suggestionText;
          feedbackData.expectedOutcome = this.expectedOutcome;
        } else if (this.feedbackType === 'rating') {
          feedbackData.rating = this.rating;
          feedbackData.comment = this.ratingComment;
          feedbackData.npsScore = this.npsScore;
        }
        
        try {
          // 发送反馈数据到服务器
          const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
          });
          
          if (response.ok) {
            this.$toast.success('感谢您的反馈！');
            this.resetForm();
            this.closeModal();
          } else {
            this.$toast.error('提交反馈失败，请稍后重试');
          }
        } catch (error) {
          console.error('Error submitting feedback:', error);
          this.$toast.error('提交反馈时发生错误');
        }
      },
      resetForm() {
        this.issueDescription = '';
        this.issueSeverity = 3;
        this.suggestionText = '';
        this.expectedOutcome = '';
        this.rating = 0;
        this.ratingComment = '';
        this.npsScore = 0;
      }
    }
  };
  </script>
  
  <style scoped>
  /* 样式代码... */
  </style>