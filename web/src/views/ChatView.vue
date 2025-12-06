<template>
  <div class="chat-container">
    <!-- 聊天历史区域 -->
    <div class="chat-history">
      <div v-for="message in chatHistory" :key="message.id" :class="['message', message.role]">
        <div class="message-avatar">{{ message.role === 'user' ? '你' : 'AI' }}</div>
        <div class="message-content">{{ message.content }}</div>
        <div class="message-time">{{ formatTime(message.timestamp) }}</div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-controls">
        <button @click="clearHistory" class="control-btn clear-btn">清空</button>
        <button @click="newConversation" class="control-btn new-btn">新对话</button>
      </div>
      <textarea 
        v-model="inputMessage" 
        placeholder="请输入消息... (Enter发送, Shift+Enter换行)"
        @keydown="handleKeyDown"
        rows="3"
      ></textarea>
      <button @click="sendMessage" class="send-btn">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()

const inputMessage = ref('')
const chatHistory = ref([])

// 监听聊天历史变化
onMounted(() => {
  chatHistory.value = chatStore.chatHistory
})

// 处理键盘事件
const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  await chatStore.sendMessage(inputMessage.value)
  inputMessage.value = ''
  chatHistory.value = chatStore.chatHistory
}

// 清空历史
const clearHistory = () => {
  chatStore.clearHistory()
  chatHistory.value = chatStore.chatHistory
}

// 新对话
const newConversation = () => {
  chatStore.newConversation()
  chatHistory.value = chatStore.chatHistory
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: white;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f9f9f9;
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #0078d4;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  margin: 0 10px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background-color: #28a745;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  white-space: pre-wrap;
}

.message.user .message-content {
  background-color: #0078d4;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin: 0 10px;
  align-self: flex-end;
}

.input-area {
  display: flex;
  flex-direction: column;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  gap: 10px;
}

.input-controls {
  display: flex;
  gap: 10px;
  justify-content: flex-start;
}

.control-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: medium;
  transition: background-color 0.3s;
}

.clear-btn {
  background-color: #dc3545;
  color: white;
}

.new-btn {
  background-color: #6c757d;
  color: white;
}

.clear-btn:hover {
  background-color: #c82333;
}

.new-btn:hover {
  background-color: #5a6268;
}

textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  resize: none;
  font-size: 14px;
  font-family: Arial, sans-serif;
  outline: none;
  transition: border-color 0.3s;
}

textarea:focus {
  border-color: #0078d4;
  box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.25);
}

.send-btn {
  align-self: flex-end;
  padding: 12px 24px;
  background-color: #0078d4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: medium;
  transition: background-color 0.3s;
}

.send-btn:hover {
  background-color: #106ebe;
}

.send-btn:disabled {
  background-color: #a0c4e2;
  cursor: not-allowed;
}
</style>