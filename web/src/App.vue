<template>
  <div class="app-container">
    <header class="app-header">
      <h1>AI对话软件</h1>
      <nav class="nav-menu">
        <router-link to="/">聊天</router-link>
        <router-link to="/config">配置</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #0078d4;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
}

.nav-menu {
  display: flex;
  gap: 20px;
}

.nav-menu a {
  color: white;
  text-decoration: none;
  padding: 5px 10px;
  border-radius: 3px;
  transition: background-color 0.3s;
}

.nav-menu a:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.app-main {
  flex: 1;
  overflow: hidden;
}
</style>