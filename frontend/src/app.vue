<!-- App.vue -->
<template>
    <div class="app-container">
      <header class="app-header">
        <div class="logo">
          <img src="@/assets/logo.svg" alt="Knowledge Graph System">
          <h1>个人知识图谱系统</h1>
        </div>
        <nav class="main-nav">
          <router-link to="/" exact>首页</router-link>
          <router-link to="/graph">知识图谱</router-link>
          <router-link to="/documents">文档管理</router-link>
          <router-link to="/search">查询分析</router-link>
        </nav>
        <div class="user-controls">
          <button class="theme-toggle" @click="toggleTheme">
            <i :class="isDarkTheme ? 'fas fa-sun' : 'fas fa-moon'"></i>
          </button>
          <div class="user-menu">
            <span>用户名</span>
            <i class="fas fa-chevron-down"></i>
          </div>
        </div>
      </header>
      
      <main class="app-content">
        <transition name="fade" mode="out-in">
          <router-view />
        </transition>
      </main>
      
      <footer class="app-footer">
        <p>&copy; 2025 个人知识图谱系统</p>
      </footer>
    </div>
  </template>
  
  <script>
  export default {
    name: 'App',
    data() {
      return {
        isDarkTheme: false
      };
    },
    methods: {
      toggleTheme() {
        this.isDarkTheme = !this.isDarkTheme;
        document.body.classList.toggle('dark-theme', this.isDarkTheme);
        localStorage.setItem('theme', this.isDarkTheme ? 'dark' : 'light');
      }
    },
    created() {
      // 检查保存的主题偏好
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark') {
        this.isDarkTheme = true;
        document.body.classList.add('dark-theme');
      }
      
      // 监听窗口大小变化
      window.addEventListener('resize', this.handleResize);
      this.handleResize();
    },
    beforeUnmount() {
      window.removeEventListener('resize', this.handleResize);
    },
    methods: {
      handleResize() {
        // 更新视窗高度变量，用于移动设备
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
      }
    }
  };
  </script>
  
  <style>
  :root {
    --primary-color: #4a90e2;
    --secondary-color: #5cb85c;
    --danger-color: #d9534f;
    --warning-color: #f0ad4e;
    --text-color: #333;
    --bg-color: #f9f9f9;
    --card-bg: #fff;
    --border-color: #eee;
    --header-height: 60px;
    --footer-height: 40px;
  }
  
  .dark-theme {
    --primary-color: #5f9eed;
    --secondary-color: #6dbd6d;
    --danger-color: #e46764;
    --warning-color: #f1b55e;
    --text-color: #e1e1e1;
    --bg-color: #222;
    --card-bg: #333;
    --border-color: #444;
  }
  
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  
  body {
    font-family: 'Open Sans', 'Helvetica Neue', sans-serif;
    font-size: 16px;
    line-height: 1.5;
    color: var(--text-color);
    background-color: var(--bg-color);
    transition: background-color 0.3s, color 0.3s;
  }
  
  .app-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    min-height: calc(var(--vh, 1vh) * 100);
  }
  
  .app-header {
    height: var(--header-height);
    background-color: var(--card-bg);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    padding: 0 20px;
    z-index: 100;
  }
  
  .logo {
    display: flex;
    align-items: center;
  }
  
  .logo img {
    height: 32px;
    margin-right: 10px;
  }
  
  .logo h1 {
    font-size: 1.2rem;
    font-weight: 600;
  }
  
  .main-nav {
    margin-left: 40px;
    display: flex;
    gap: 20px;
  }
  
  .main-nav a {
    color: var(--text-color);
    text-decoration: none;
    font-weight: 500;
    padding: 5px 10px;
    border-radius: 4px;
  }
  
  .main-nav a.router-link-active {
    color: var(--primary-color);
    background-color: rgba(74, 144, 226, 0.1);
  }
  
  .user-controls {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .theme-toggle {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: var(--text-color);
  }
  
  .user-menu {
    display: flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
  }
  
  .app-content {
    flex: 1;
    padding: 20px;
    overflow-x: hidden;
  }
  
  .app-footer {
    height: var(--footer-height);
    background-color: var(--card-bg);
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 0.9rem;
    color: #888;
  }
  
  .fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s;
  }
  
  .fade-enter-from, .fade-leave-to {
    opacity: 0;
  }
  
  /* Responsive styles */
  @media (max-width: 768px) {
    .app-header {
      flex-direction: column;
      height: auto;
      padding: 10px;
    }
    
    .logo {
      margin-bottom: 10px;
    }
    
    .main-nav {
      margin-left: 0;
      width: 100%;
      justify-content: space-between;
    }
    
    .user-controls {
      margin-left: 0;
      margin-top: 10px;
      width: 100%;
      justify-content: flex-end;
    }
    
    .app-content {
      padding: 10px;
    }
  }
  </style>