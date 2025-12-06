<template>
  <div class="config-container">
    <h2>API配置</h2>
    
    <!-- 模型切换 -->
    <div class="model-switcher">
      <h3>切换模型</h3>
      <div class="model-selector">
        <select v-model="selectedModel" @change="handleModelChange" :disabled="loading">
          <option value="">选择模型</option>
          <option v-for="(modelConfig, modelName) in models" :key="modelName" :value="modelName">
            {{ modelName }}
          </option>
        </select>
        <button v-if="selectedModel" @click="applyModelConfig" :disabled="loading" class="apply-btn">
          应用模型
        </button>
      </div>
    </div>
    
    <form @submit.prevent="saveConfig" class="config-form">
      <div class="form-group">
        <label for="apiUrl">API URL</label>
        <input 
          type="text" 
          id="apiUrl" 
          v-model="config.api_url"
          placeholder="https://api.openai.com/v1/chat/completions"
          :disabled="loading"
        >
      </div>
      
      <div class="form-group">
        <label for="apiKey">API密钥</label>
        <input 
          type="password" 
          id="apiKey" 
          v-model="config.api_key"
          placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          :disabled="loading"
        >
      </div>
      
      <div class="form-group">
        <label for="model">模型名称</label>
        <input 
          type="text" 
          id="model" 
          v-model="config.model"
          placeholder="gpt-3.5-turbo"
          :disabled="loading"
        >
      </div>
      
      <div class="form-row">
        <div class="form-group half">
          <label for="temperature">温度参数</label>
          <input 
            type="number" 
            id="temperature" 
            v-model.number="config.temperature"
            min="0" 
            max="2" 
            step="0.1"
            placeholder="0.7"
            :disabled="loading"
          >
        </div>
        
        <div class="form-group half">
          <label for="maxTokens">最大Tokens</label>
          <input 
            type="number" 
            id="maxTokens" 
            v-model.number="config.max_tokens"
            min="1" 
            max="4000"
            placeholder="1000"
            :disabled="loading"
          >
        </div>
      </div>
      
      <div class="form-actions">
        <button type="submit" class="save-btn" :disabled="loading">
          {{ loading ? '保存中...' : '保存配置' }}
        </button>
        <button type="button" @click="resetConfig" class="reset-btn" :disabled="loading">
          重置
        </button>
      </div>
      
      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useConfigStore } from '../stores/config'

const configStore = useConfigStore()

const config = ref({
  api_url: '',
  api_key: '',
  model: '',
  temperature: 0.7,
  max_tokens: 1000
})

const selectedModel = ref('')
const loading = ref(false)
const error = ref(null)

// 计算属性：获取可用模型
const models = computed(() => configStore.models)

// 加载现有配置
onMounted(async () => {
  await configStore.loadConfig()
  updateLocalConfig()
})

// 监听配置变化，更新本地状态
watch(
  () => configStore.config,
  (newConfig) => {
    updateLocalConfig(newConfig)
  },
  { deep: true }
)

// 更新本地配置
const updateLocalConfig = (newConfig = configStore.config) => {
  config.value = { ...config.value, ...newConfig }
  
  // 查找当前模型在模型列表中的名称
  for (const [modelName, modelConfig] of Object.entries(models.value)) {
    if (modelConfig.model === newConfig.model) {
      selectedModel.value = modelName
      break
    }
  }
}

// 处理模型选择变化
const handleModelChange = (event) => {
  const modelName = event.target.value
  if (modelName && models.value[modelName]) {
    const modelConfig = models.value[modelName]
    // 预览模型配置，但不立即应用
    config.value = { ...config.value, ...modelConfig }
  }
}

// 应用模型配置
const applyModelConfig = async () => {
  if (!selectedModel.value) return
  
  loading.value = true
  error.value = null
  
  try {
    await configStore.switchModel(selectedModel.value)
    alert('模型已切换！')
  } catch (err) {
    error.value = '切换模型失败: ' + err.message
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  loading.value = true
  error.value = null
  
  try {
    await configStore.saveConfig(config.value)
    alert('配置已保存！')
  } catch (err) {
    error.value = '保存配置失败: ' + err.message
  } finally {
    loading.value = false
  }
}

// 重置配置
const resetConfig = () => {
  config.value = {
    api_url: '',
    api_key: '',
    model: '',
    temperature: 0.7,
    max_tokens: 1000
  }
  selectedModel.value = ''
}
</script>

<style scoped>
.config-container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
  background-color: white;
  height: 100%;
  overflow-y: auto;
}

h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 24px;
  font-weight: bold;
}

h3 {
  margin-bottom: 10px;
  color: #555;
  font-size: 18px;
  font-weight: medium;
}

/* 模型切换器样式 */
.model-switcher {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #e0e0e0;
}

.model-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.model-selector select {
  flex: 1;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
}

.model-selector select:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

.apply-btn {
  padding: 10px 20px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: medium;
  transition: background-color 0.3s;
}

.apply-btn:hover:not(:disabled) {
  background-color: #218838;
}

.apply-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-row {
  display: flex;
  gap: 15px;
}

.half {
  flex: 1;
}

label {
  font-size: 14px;
  font-weight: medium;
  color: #555;
}

input, select {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

input:focus, select:focus {
  border-color: #0078d4;
  box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.25);
}

input:disabled, select:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
  opacity: 0.7;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.save-btn {
  padding: 10px 20px;
  background-color: #0078d4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: medium;
  transition: background-color 0.3s;
}

.save-btn:hover:not(:disabled) {
  background-color: #106ebe;
}

.save-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

.reset-btn {
  padding: 10px 20px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: medium;
  transition: background-color 0.3s;
}

.reset-btn:hover:not(:disabled) {
  background-color: #5a6268;
}

.reset-btn:disabled {
  background-color: #adb5bd;
  cursor: not-allowed;
  opacity: 0.7;
}

/* 错误信息样式 */
.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 10px;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin-top: 10px;
  font-size: 14px;
}
</style>