// cypress/integration/knowledge_graph_spec.js

describe('知识图谱系统测试', () => {
    beforeEach(() => {
      // 访问系统首页
      cy.visit('/');
    });
    
    it('基本页面导航测试', () => {
      // 检查标题
      cy.contains('h1', '个人知识图谱系统');
      
      // 导航到图谱页面
      cy.contains('知识图谱').click();
      cy.url().should('include', '/graph');
      
      // 导航到文档管理页面
      cy.contains('文档管理').click();
      cy.url().should('include', '/documents');
      
      // 导航到查询分析页面
      cy.contains('查询分析').click();
      cy.url().should('include', '/search');
    });
    
    it('图谱可视化测试', () => {
      // 访问图谱页面
      cy.visit('/graph');
      
      // 等待图谱加载
      cy.get('.graph-container svg').should('be.visible');
      cy.get('.node').should('have.length.at.least', 1);
      
      // 测试缩放功能
      cy.get('button').contains('i.fa-search-plus').click();
      cy.get('button').contains('i.fa-search-minus').click();
      cy.get('button').contains('i.fa-home').click();
      
      // 测试节点交互
      cy.get('.node').first().click();
      cy.get('.entity-detail-container').should('be.visible');
      cy.get('.entity-detail-container h2').should('not.be.empty');
    });
    
    it('文档上传测试', () => {
      // 访问文档管理页面
      cy.visit('/documents');
      
      // 测试文件上传
      cy.get('input[type=file]').selectFile({
        contents: Cypress.Buffer.from('测试文档内容'),
        fileName: 'test.txt',
        mimeType: 'text/plain'
      }, { force: true });
      
      cy.get('button').contains('上传').click();
      
      // 验证文档被添加到列表
      cy.contains('test.txt').should('be.visible');
    });
    
    it('自然语言查询测试', () => {
      // 访问查询页面
      cy.visit('/search');
      
      // 输入自然语言查询
      cy.get('input[placeholder*="输入您的问题"]').type('什么是知识图谱');
      cy.get('button').contains('查询').click();
      
      // 验证结果显示
      cy.get('.search-results').should('be.visible');
      cy.get('.search-results').should('contain', '知识图谱');
    });
    
    it('知识溯源测试', () => {
      // 访问图谱页面并选择节点
      cy.visit('/graph');
      cy.get('.node').first().click();
      
      // 点击溯源按钮
      cy.get('button').contains('溯源').click();
      
      // 验证溯源结果显示
      cy.get('.trace-result').should('be.visible');
      cy.get('.source-document').should('be.visible');
    });
  });