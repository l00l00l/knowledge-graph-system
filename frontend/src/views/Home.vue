<!-- frontend/src/views/Home.vue -->
<template>
    <div class="home">
      <h1>个人知识图谱系统</h1>
      <p>欢迎使用个人知识图谱构建与查询系统</p>
      
      <div class="feature-cards">
        <div class="card" @click="$router.push('/graph')">
          <h2>知识图谱</h2>
          <p>可视化浏览你的知识网络</p>
        </div>
        
        <div class="card" @click="$router.push('/documents')">
          <h2>文档管理</h2>
          <p>上传与管理知识源文档</p>
        </div>
        
        <div class="card" @click="$router.push('/search')">
          <h2>查询分析</h2>
          <p>智能查询与知识探索</p>
        </div>
      </div>
    </div>
  </template>
  
  <style scoped>
  .home {
    text-align: center;
    padding: 2rem;
  }
  
  .feature-cards {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 2rem;
  }
  
  .card {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 1.5rem;
    width: 250px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  h1 {
    margin-bottom: 1rem;
  }
  </style>