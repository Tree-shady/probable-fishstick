import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useConfigStore } from './config'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const chatHistory = ref([])
  const isLoading = ref(false)
  const messageCounter = ref(0)
  
  // 获取配置
  const configStore = useConfigStore()
  
  // 发送消息
  const sendMessage = async (content) => {
    if (!content.trim() || isLoading.value) return
    
    // 创建用户消息
    const userMessage = {
      id: `msg_${messageCounter.value++}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }
    
    // 添加到聊天历史
    chatHistory.value.push(userMessage)
    isLoading.value = true
    
    try {
      // 调用后端API服务，保护API密钥
      const config = configStore.config
      const response = await axios.post('/api/chat', {
        api_url: config.api_url,
        api_key: config.api_key,
        model: config.model,
        messages: chatHistory.value.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        temperature: config.temperature,
        max_tokens: config.max_tokens
      }, {
        timeout: 30000
      })
      
      // 处理API响应
      const aiResponse = response.data
      let aiContent = ''
      
      // 检查是否为OpenAI API格式
      if (aiResponse.choices && aiResponse.choices.length > 0) {
        aiContent = aiResponse.choices[0].message.content
      } 
      // 检查是否为简化格式
      else if (aiResponse.content) {
        aiContent = aiResponse.content
      }
      
      // 创建AI消息
      const assistantMessage = {
        id: `msg_${messageCounter.value++}`,
        role: 'assistant',
        content: aiContent,
        timestamp: new Date().toISOString()
      }
      
      // 添加到聊天历史
      chatHistory.value.push(assistantMessage)
    } catch (error) {
      console.error('API调用失败:', error)
      
      // 创建错误消息
      const errorMessage = {
        id: `msg_${messageCounter.value++}`,
        role: 'assistant',
        content: `API调用失败: ${error.message}`,
        timestamp: new Date().toISOString()
      }
      
      // 添加到聊天历史
      chatHistory.value.push(errorMessage)
    } finally {
      isLoading.value = false
    }
  }
  
  // 清空聊天历史
  const clearHistory = () => {
    chatHistory.value = []
  }
  
  // 新对话
  const newConversation = () => {
    clearHistory()
  }
  
  return {
    chatHistory,
    isLoading,
    sendMessage,
    clearHistory,
    newConversation
  }
})