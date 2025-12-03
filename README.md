# AI对话软件

## 项目介绍

AI对话软件是一个功能强大、灵活易用的Python对话工具，支持多种大模型API服务。该软件提供命令行和图形界面两种交互方式，可根据用户需求自由切换。

### 设计理念

- **灵活性**：支持自定义API URL、API密钥和模型，兼容多种大模型服务
- **易用性**：提供直观的界面和清晰的操作流程
- **可靠性**：完善的错误处理和详细的错误提示
- **可扩展性**：模块化设计，便于添加新功能和支持更多API格式

### 核心优势

- 支持多种API响应格式，无需修改代码即可切换不同大模型服务
- 提供详细的错误信息，便于调试和问题排查
- 支持对话历史记录，保持上下文连贯
- 跨平台兼容，可在Windows、macOS和Linux上运行
- 开源免费，可自由修改和扩展

## 功能特点

- ✅ 支持自定义API URL
- ✅ 支持自定义API密钥
- ✅ 支持自定义模型名称
- ✅ 支持调整temperature和max_tokens参数
- ✅ 对话历史记录
- ✅ 命令行界面，简单易用
- ✅ 图形界面（GUI），可视化操作
- ✅ 启动动画效果
- ✅ 配置自动保存
- ✅ 消息时间戳和彩色显示
- ✅ 异步API调用，不阻塞界面
- ✅ 支持多种API响应格式
- ✅ 详细的错误信息提示
- ✅ 支持iflow.cn平台API
- ✅ 支持OpenAI API兼容接口
- ✅ 控制台调试输出

## 技术栈

- **开发语言**：Python 3.7+
- **依赖库**：
  - requests：用于HTTP请求
  - PyQt6：用于图形界面（可选）
  - tkinter：用于图形界面（Python标准库，可选）

## 安装依赖

1. 确保已安装Python 3.7或更高版本
   - 可以从[Python官方网站](https://www.python.org/)下载并安装
   - 安装完成后，在命令行中运行`python --version`或`python3 --version`验证安装

2. 克隆或下载项目代码
   - 直接下载：点击GitHub页面的"Code"按钮，选择"Download ZIP"
   - 克隆代码：`git clone https://github.com/yourusername/ai-chat-software.git`

3. 进入项目目录
   ```bash
   cd ai-chat-software
   ```

4. 安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```
   - 如果使用Python 3.8+，可以使用以下命令：
     ```bash
     python -m pip install -r requirements.txt
     ```
   - 如果遇到权限问题，可以使用`--user`选项：
     ```bash
     pip install --user -r requirements.txt
     ```

## 运行程序

### 主入口文件（推荐）

```bash
python main.py
```

### 命令行版本

```bash
python ai_chat_cli.py
```

### PyQt图形界面版本

```bash
python ai_chat_pyqt.py
```

## 使用说明

### 命令行版本使用

#### 初始配置

首次运行程序时，会提示你配置API信息。你可以使用`/config`命令来更新配置：

```
你: /config
```

配置选项包括：
- `api_url`: API地址，例如 `https://api.openai.com/v1/chat/completions`
- `api_key`: 你的API密钥
- `model`: 模型名称，例如 `gpt-3.5-turbo`
- `temperature`: 温度参数，影响回复的随机性（0.0-2.0）
- `max_tokens`: 最大生成 tokens 数

#### 对话命令

- `/config`: 更新API配置
- `/clear`: 清空对话历史
- `/help`: 显示帮助信息
- `/exit`: 退出程序

### 图形界面（GUI）版本使用

#### 初始配置

1. 运行GUI版本后，会显示启动动画
2. 如果API密钥未配置，会提示是否立即配置
3. 你也可以通过菜单 "文件" -> "配置" 随时更新配置

#### 基本操作

- **发送消息**: 在输入框中输入消息，按 `Enter` 发送
- **换行**: 按 `Shift+Enter` 可以在输入框中换行
- **清空历史**: 点击 "清空" 按钮或通过菜单 "文件" -> "清空历史"
- **查看帮助**: 菜单 "帮助" -> "帮助"
- **查看关于**: 菜单 "帮助" -> "关于"

#### 界面特点

- 对话历史显示发送者、时间戳和消息内容
- 不同发送者的消息使用不同颜色区分
- 实时状态栏显示程序状态
- 异步API调用，发送消息后界面不会卡顿
- 自动滚动到最新消息

### 对话示例

```
[2024-01-01 12:00:00] 你:
你好

[2024-01-01 12:00:01] AI:
你好！有什么可以帮助你的吗？

[2024-01-01 12:00:05] 你:
什么是人工智能？

[2024-01-01 12:00:06] AI:
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，它旨在创建能够模拟人类智能的系统...
```

## 支持的API格式

该软件支持多种API响应格式，包括：

### 1. OpenAI API兼容格式

支持与OpenAI API兼容的聊天接口，包括但不限于：
- OpenAI GPT系列（GPT-3.5, GPT-4等）
- DeepSeek
- Claude（通过兼容接口）
- 百度文心一言（通过OpenAI兼容接口）
- 阿里云通义千问（通过OpenAI兼容接口）
- 其他遵循OpenAI API格式的大模型服务

### 2. iflow.cn平台格式

专门支持iflow.cn平台的API响应格式，包括：
- 成功响应：包含`status`、`msg`和`body`字段
- 错误响应：从`msg`字段提取详细错误信息
- 支持API Token过期等错误提示

### 3. 简化响应格式

支持直接返回`content`字段的简化响应格式

## API配置示例

### OpenAI API配置

```
api_url: https://api.openai.com/v1/chat/completions
api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
model: gpt-3.5-turbo
```

### iflow.cn API配置

```
api_url: https://apis.iflow.cn/v1/chat/completions
api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
model: deepseek-v3.1
```

### 其他平台API配置

根据平台提供的API文档，填写相应的API URL、API密钥和模型名称即可。

## 配置文件

配置信息会自动保存到当前目录的`config.json`文件中，你也可以直接编辑该文件来修改配置。

## 高级功能

### 对话历史管理

- 对话历史会自动保存到内存中，保持上下文连贯
- 可以通过命令或按钮清空对话历史
- 重启程序后，对话历史会重置

### 参数调整

- **temperature**：控制生成文本的随机性，取值范围0.0-2.0
  - 较低值（如0.1）：生成更确定、更保守的回复
  - 较高值（如1.5）：生成更多样、更有创造性的回复
  - 默认值：0.7

- **max_tokens**：控制生成文本的最大长度
  - 取值范围：1-4096（具体取决于API服务支持）
  - 默认值：1000
  - 注意：不同API服务对最大tokens的限制可能不同

## 故障排除

### 常见问题及解决方案

1. **API调用失败：ConnectionError**
   - 检查网络连接是否正常
   - 检查API URL是否正确
   - 检查防火墙设置，确保允许程序访问网络
   - 部分API服务可能需要科学上网

2. **API返回格式异常**
   - 查看控制台输出的原始API响应
   - 检查API配置是否正确
   - 确保使用的模型名称与API服务兼容
   - 尝试调整API参数

3. **API请求失败：Your API Token has expired**
   - 前往相应平台重置API Token
   - 更新配置中的API密钥
   - 注意不同平台的API Token有效期可能不同

4. **图形界面无法启动**
   - 检查PyQt6或tkinter是否正确安装
   - 尝试使用命令行版本
   - 查看控制台输出的错误信息

5. **程序崩溃或无响应**
   - 确保使用的Python版本符合要求（3.7+）
   - 重新安装依赖：`pip install -r requirements.txt --upgrade`
   - 查看控制台输出的错误堆栈信息

### 调试技巧

- 查看控制台输出的API原始响应
- 检查配置文件（config.json）中的参数是否正确
- 尝试使用不同的API服务进行测试
- 调整日志级别，获取更详细的调试信息

## 开发说明

### 项目结构

```
ai-chat-software/
├── main.py              # 主入口文件
├── ai_chat_cli.py       # 命令行版本
├── ai_chat_pyqt.py      # PyQt图形界面版本
├── config.json          # 配置文件（自动生成）
├── requirements.txt     # 依赖配置
└── README.md            # 项目文档
```

### 代码结构

- **AIChat类**：核心功能实现，包括API调用、配置管理和对话历史
- **图形界面类**：基于Tkinter或PyQt6的界面实现
- **API调用线程**：异步处理API请求，避免阻塞界面
- **配置管理**：加载、保存和验证配置

### 扩展开发

1. **添加新的API响应格式支持**：
   - 修改`call_api`方法中的响应处理逻辑
   - 添加新的响应格式检查和解析

2. **添加新功能**：
   - 基于现有的模块化设计添加新功能
   - 注意保持代码的可读性和可维护性

3. **界面定制**：
   - 修改图形界面类的布局和样式
   - 添加新的UI组件

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request，一起改进这个项目！

### 贡献指南

1. Fork本项目
2. 创建新的分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交Pull Request

## 联系方式

如果您有任何问题或建议，欢迎通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至：your-email@example.com

## 更新日志

### v1.0.0（2024-01-01）

- 初始版本发布
- 支持命令行和图形界面
- 支持多种API响应格式
- 完善的错误处理机制
- 详细的文档说明
