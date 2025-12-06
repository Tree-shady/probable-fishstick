import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 创建应用实例
const app = createApp(App)

// 安装插件
app.use(createPinia())
app.use(router)

// 挂载应用
app.mount('#app')