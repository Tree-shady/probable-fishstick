# AI对话软件Web版本

AI对话软件的Web版本，支持自定义API大模型，提供聊天和配置功能。

## 技术栈

**前端**：
- Vue 3：现代化的JavaScript框架
- Vite：快速的构建工具
- Pinia：状态管理库
- Vue Router：路由管理
- Axios：HTTP客户端

**后端**：
- Flask：轻量级Python Web框架
- Flask-CORS：处理跨域请求
- Requests：HTTP客户端

## 项目结构

```
web/
├── src/
│   ├── views/          # 页面组件
│   │   ├── ChatView.vue      # 聊天界面
│   │   └── ConfigView.vue    # 配置界面
│   ├── stores/         # 状态管理
│   │   ├── chat.js           # 聊天状态管理
│   │   └── config.js         # 配置管理
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML入口
├── vite.config.js      # Vite配置
├── package.json        # 依赖配置
├── backend.py          # Python后端服务
└── README.md           # 项目文档
```

## 主要功能

1. **聊天功能**
   - 实时聊天界面，显示用户和AI的对话
   - 支持发送消息、清空历史、新对话
   - 支持Enter发送消息，Shift+Enter换行
   - 消息显示时间戳

2. **配置功能**
   - 配置API URL
   - 配置API密钥
   - 配置模型名称
   - 调整temperature和max_tokens参数
   - 配置自动保存到本地存储

3. **模型管理功能**
   - 支持从预定义模型列表中选择和切换模型
   - 实现模型配置预览和应用功能
   - 支持多模型管理，可快速切换不同API服务商配置

4. **配置同步功能**
   - 与桌面版共享配置文件（config.json和model_configs.json）
   - 配置更改实时同步，支持跨版本配置管理
   - 当前模型配置自动保存到主配置文件

5. **后端服务**
   - 处理API请求，解决跨域问题
   - 保护API密钥，避免暴露在前端
   - 支持多种API格式
   - 提供详细的错误信息
   - 支持配置管理API端点
   - 支持模型切换API端点

## 如何运行

### 1. 前端开发模式

```bash
# 进入web目录
cd web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器将运行在 `http://localhost:3000`

### 2. 构建生产版本

```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

构建产物将生成在 `dist` 目录

### 3. 启动后端服务

#### 开发模式

```bash
# 安装依赖
pip install flask flask-cors requests

# 启动后端服务（开发模式）
python backend.py
```

#### 生产模式

```bash
# 生产模式（禁用调试）
python backend.py --production

# 或指定端口
python backend.py --production --port 8000

# 或指定主机和端口
python backend.py --production --host 127.0.0.1 --port 8000
```

后端服务默认运行在 `http://localhost:5000`

## 生产环境部署建议

### 关于Flask开发服务器警告

当你直接运行 `python backend.py --production` 时，你可能会看到以下警告：
```
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
```

**这是正常现象**，因为Flask的内置服务器是为开发环境设计的，不适合生产使用。在实际生产环境中，你应该使用专业的WSGI服务器，如Gunicorn或uWSGI。

### 前端部署

1. **使用Nginx或Apache作为Web服务器**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/web/dist;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           # 增加超时设置
           proxy_connect_timeout 60s;
           proxy_read_timeout 60s;
           proxy_send_timeout 60s;
       }
   }
   ```

2. **使用CDN加速静态资源**
   - 将构建产物上传到CDN
   - 配置Nginx从CDN加载静态资源

3. **启用HTTPS**
   - 使用Let's Encrypt获取免费SSL证书
   - 在Nginx中配置HTTPS
   - 强制HTTP重定向到HTTPS

### 后端部署

#### 1. 使用Gunicorn作为WSGI服务器（推荐）

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务（生产模式）
gunicorn -w 4 -b 0.0.0.0:5000 backend:app

# 带超时设置的启动命令
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 60 backend:app

# 带日志配置的启动命令
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 60 --access-logfile access.log --error-logfile error.log backend:app
```

#### 2. 使用uWSGI作为WSGI服务器

```bash
# 安装uWSGI
pip install uwsgi

# 启动服务
uwsgi --http :5000 --wsgi-file backend.py --callable app --processes 4 --threads 2 --timeout 60

# 使用配置文件启动
# uwsgi.ini
[uwsgi]
http = :5000
wsgi-file = backend.py
callable = app
processes = 4
threads = 2
timeout = 60

# 启动命令
uwsgi --ini uwsgi.ini
```

#### 3. 使用systemd管理服务

```ini
# /etc/systemd/system/ai-chat-backend.service
[Unit]
Description=AI Chat Backend Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/web
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 --timeout 60 backend:app
Restart=always
RestartSec=5
Environment="PATH=/usr/bin:/path/to/venv/bin"

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl enable ai-chat-backend
sudo systemctl start ai-chat-backend

# 查看服务状态
sudo systemctl status ai-chat-backend

# 查看日志
sudo journalctl -u ai-chat-backend
```

#### 4. 使用Docker容器化部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend.py .

# 暴露端口
EXPOSE 5000

# 使用Gunicorn启动服务
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "60", "backend:app"]
```

```bash
# 构建镜像
docker build -t ai-chat-backend .

# 运行容器
docker run -d -p 5000:5000 --name ai-chat-backend ai-chat-backend

# 查看日志
docker logs ai-chat-backend
```

### 推荐的生产部署架构

```
用户浏览器 → Nginx（前端静态资源 + 反向代理） → Gunicorn/uWSGI → Flask应用
```

### 生产环境优化建议

1. **调整工作进程数**
   - 通常设置为CPU核心数的2-4倍
   - 例如：`gunicorn -w 8 -b 0.0.0.0:5000 backend:app`

2. **设置合理的超时时间**
   - 考虑到AI模型可能需要较长时间生成响应
   - 建议设置为60秒或更长

3. **启用日志轮替**
   - 使用logrotate管理Gunicorn/UWSGI日志
   - 定期归档和清理旧日志

4. **配置监控**
   - 使用Prometheus + Grafana监控服务状态
   - 设置告警机制，及时发现问题

5. **使用负载均衡**
   - 对于高流量场景，使用Nginx或专业负载均衡器
   - 部署多个后端实例，提高可用性

6. **定期备份**
   - 备份重要配置和数据
   - 制定恢复计划

7. **安全加固**
   - 关闭不必要的端口
   - 使用防火墙限制访问
   - 定期更新依赖包
   - 配置适当的文件权限

## API接口文档

### 1. 获取配置

**请求方法**：GET
**请求路径**：/api/config
**响应格式**：JSON
**响应示例**：
```json
{
  "config": {
    "api_url": "https://apis.iflow.cn/v1/chat/completions",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "model": "deepseek-v3.1",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "model_configs": {
    "deepseek-v3.1": {
      "api_url": "https://apis.iflow.cn/v1/chat/completions",
      "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "model": "deepseek-v3.1",
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "硅基流动": {
      "api_url": "https://api.siliconflow.cn/v1/chat/completions",
      "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "model": "deepseek-ai/DeepSeek-R1",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
}
```

### 2. 更新配置

**请求方法**：POST
**请求路径**：/api/config
**请求格式**：JSON
**请求示例**：
```json
{
  "config": {
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```
**响应格式**：JSON
**响应示例**：
```json
{
  "message": "配置更新成功",
  "config": {
    "api_url": "https://api.openai.com/v1/chat/completions",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### 3. 获取模型列表

**请求方法**：GET
**请求路径**：/api/models
**响应格式**：JSON
**响应示例**：
```json
{
  "models": {
    "deepseek-v3.1": {
      "api_url": "https://apis.iflow.cn/v1/chat/completions",
      "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "model": "deepseek-v3.1",
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "硅基流动": {
      "api_url": "https://api.siliconflow.cn/v1/chat/completions",
      "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "model": "deepseek-ai/DeepSeek-R1",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
}
```

### 4. 切换模型

**请求方法**：POST
**请求路径**：/api/models/{model_name}
**请求示例**：
```
POST /api/models/deepseek-v3.1
```
**响应格式**：JSON
**响应示例**：
```json
{
  "message": "已切换到模型: deepseek-v3.1",
  "config": {
    "api_url": "https://apis.iflow.cn/v1/chat/completions",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "model": "deepseek-v3.1",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

## 环境变量配置

### 前端环境变量

在 `.env` 文件中配置：
```
VITE_API_BASE_URL=http://localhost:5000/api
```

### 后端环境变量

在 `.env` 文件中配置：
```
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0
```

## 安全建议

1. **保护API密钥**
   - 不要将API密钥硬编码到前端代码中
   - 使用后端服务代理API请求
   - 定期更换API密钥

2. **启用HTTPS**
   - 生产环境必须使用HTTPS
   - 使用Let's Encrypt获取免费SSL证书

3. **限制API访问**
   - 配置Nginx的IP限制
   - 使用API密钥验证
   - 配置访问频率限制

4. **监控和日志**
   - 配置日志记录
   - 使用监控工具（如Prometheus + Grafana）
   - 设置告警机制

## 开发指南

### 添加新页面

1. 在 `src/views/` 目录下创建新的Vue组件
2. 在 `src/router/index.js` 中添加路由
3. 在 `src/stores/` 中添加对应的状态管理

### 添加新功能

1. 在组件中定义功能
2. 在store中管理状态
3. 在后端添加对应的API接口（如果需要）

## 常见问题

### 1. 跨域问题

确保后端服务已正确配置CORS，默认配置允许所有来源访问。

### 2. API调用失败

检查：
- API URL是否正确
- API密钥是否有效
- 网络连接是否正常
- 查看浏览器控制台和后端日志

### 3. 后端服务启动失败

检查：
- 端口是否被占用
- 依赖是否已正确安装
- 查看终端输出的错误信息

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request，一起改进这个项目！

## 联系方式

如有问题或建议，请通过GitHub Issue反馈。