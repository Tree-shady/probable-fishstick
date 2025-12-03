# AI对话软件

一个支持自定义API大模型的Python AI对话软件，可以配置不同的API URL、API密钥和模型，提供命令行和GUI两种界面。

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

## 安装依赖

1. 确保已安装Python 3.7或更高版本
2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

## 运行程序

### 命令行版本

```bash
python ai_chat.py
```

### Tkinter图形界面版本

```bash
python ai_chat_gui.py
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

## 注意事项

1. 请妥善保管你的API密钥，不要分享给他人
2. 不同的API服务可能有不同的计费方式，请留意使用量
3. 如果你遇到连接问题，请检查网络连接和API配置是否正确
4. 部分API服务可能需要科学上网才能访问
5. 当遇到API错误时，查看控制台输出获取详细的错误信息
6. API Token过期时，根据错误提示前往相应平台重置
7. 不同平台的模型名称可能不同，请根据平台文档填写
8. 控制台会打印API原始响应，方便调试和问题排查
9. 如果API返回格式异常，软件会显示原始响应片段，帮助你诊断问题

## 许可证

MIT License
