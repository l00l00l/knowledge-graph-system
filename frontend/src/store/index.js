// frontend/src/store/index.js
import { createStore } from 'vuex'

export default createStore({
  state: {
    nodes: [],
    relationships: [],
    documents: [],
    selectedEntity: null
  },
  getters: {
    getNodes: state => state.nodes,
    getRelationships: state => state.relationships,
    getDocuments: state => state.documents,
    getSelectedEntity: state => state.selectedEntity
  },
  mutations: {
    SET_NODES(state, nodes) {
      state.nodes = nodes
    },
    SET_RELATIONSHIPS(state, relationships) {
      state.relationships = relationships
    },
    SET_DOCUMENTS(state, documents) {
      state.documents = documents
    },
    SET_SELECTED_ENTITY(state, entity) {
      state.selectedEntity = entity
    }
  },
  actions: {
    async fetchGraph({ commit }) {
      try {
        // 模拟API调用
        const response = await fetch('/api/v1/graph')
        const data = await response.json()
        commit('SET_NODES', data.nodes)
        commit('SET_RELATIONSHIPS', data.relationships)
      } catch (error) {
        console.error('Error fetching graph data:', error)
      }
    },
    async fetchDocuments({ commit }) {
      try {
        // 模拟API调用
        const response = await fetch('/api/v1/documents')
        const data = await response.json()
        commit('SET_DOCUMENTS', data)
      } catch (error) {
        console.error('Error fetching documents:', error)
      }
    },
    selectEntity({ commit }, entity) {
      commit('SET_SELECTED_ENTITY', entity)
    }
  },
  modules: {
    // 可以在这里添加模块化的状态
  }
})