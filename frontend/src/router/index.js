// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

// 页面组件
const Home = () => import('../views/Home.vue')
const Graph = () => import('../views/Graph.vue')
const Documents = () => import('../views/Documents.vue')
const Search = () => import('../views/Search.vue')

// 路由配置
const routes = [
  {
    path: '/',
    name: 'home',
    component: Home
  },
  {
    path: '/graph',
    name: 'graph',
    component: Graph
  },
  {
    path: '/documents',
    name: 'documents',
    component: Documents
  },
  {
    path: '/search',
    name: 'search',
    component: Search
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router