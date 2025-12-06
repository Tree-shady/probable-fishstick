import { defineStore } from 'pinia'
import { ref, onMounted } from 'vue'
import axios from 'axios'

export const useConfigStore = defineStore('config', () => {
  // 状态
  const config = ref({
    api_url: '',
    api_key: '',
    model: '',
    temperature: 0.7,
    max_tokens: 1000
  })
  
  const models = ref({})
  const loading = ref(false)
  const error = ref(null)
  
  // 加载配置
  const loadConfig = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/config')
      config.value = response.data.config || {
        api_url: '',
        api_key: '',
        model: '',
        temperature: 0.7,
        max_tokens: 1000
      }
      models.value = response.data.model_configs || {}
      loading.value = false
      return true
    } catch (err) {
      error.value = '加载配置失败: ' + err.message
      loading.value = false
      return false
    }
  }
  
  // 保存配置
  const saveConfig = async (newConfig) => {
    loading.value = true
    error.value = null
    try {
      // 更新本地状态
      const updatedConfig = { ...config.value, ...newConfig }
      config.value = updatedConfig
      
      // 保存到服务器
      const response = await axios.post('/api/config', {
        config: updatedConfig
      })
      
      loading.value = false
      return true
    } catch (err) {
      error.value = '保存配置失败: ' + err.message
      loading.value = false
      return false
    }
  }
  
  // 切换模型
  const switchModel = async (modelName) => {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post(`/api/models/${modelName}`)
      config.value = response.data.config || config.value
      loading.value = false
      return true
    } catch (err) {
      error.value = '切换模型失败: ' + err.message
      loading.value = false
      return false
    }
  }
  
  // 初始化加载配置
  onMounted(() => {
    loadConfig()
  })
  
  return {
    config,
    models,
    loading,
    error,
    loadConfig,
    saveConfig,
    switchModel
  }
})