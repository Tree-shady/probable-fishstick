#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
import sys
import time
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCursor, QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QMenuBar, QMenu, QStatusBar,
    QDialog, QLabel, QLineEdit, QGridLayout, QMessageBox, QProgressBar,
    QInputDialog, QListWidget, QSplitter, QTabWidget
)

# 导入对话管理模块
from conversation_manager import ConversationManager
# 导入预设管理模块
from preset_manager import PresetManager
# 导入审计日志相关模块
import os
import datetime

class ApiCallThread(QThread):
    """异步API调用线程"""
    response_received = pyqtSignal(str, str)  # sender, message
    error_occurred = pyqtSignal(str)  # error message
    status_changed = pyqtSignal(str)  # status message
    debug_info = pyqtSignal(str)  # debug information
    
    def __init__(self, config, conversation_history, message):
        super().__init__()
        self.config = config
        self.conversation_history = conversation_history.copy()
        self.message = message
    
    def run(self):
        """执行API调用"""
        try:
            self.status_changed.emit("正在请求...")
            
            # 准备请求数据
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # 注意：用户消息已经在send_message方法中添加到了conversation_history
            # 这里不需要再次添加，否则会导致消息重复
            
            data = {
                "model": self.config["model"],
                "messages": self.conversation_history,
                "temperature": self.config["temperature"],
                "max_tokens": self.config["max_tokens"]
            }
            
            # 发送调试信息
            self.debug_info.emit(f"API请求URL: {self.config['api_url']}")
            self.debug_info.emit(f"API请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
            self.debug_info.emit(f"API请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            response = requests.post(
                self.config["api_url"],
                headers=headers,
                json=data,
                timeout=30
            )
            
            # 发送调试信息
            self.debug_info.emit(f"API响应状态码: {response.status_code}")
            
            # 格式化响应头
            self.debug_info.emit(f"API响应头: {json.dumps(dict(response.headers), indent=2, ensure_ascii=False)}")
            
            # 格式化原始响应
            try:
                # 尝试解析为JSON并格式化
                json_response = response.json()
                self.debug_info.emit(f"API原始响应: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接显示
                self.debug_info.emit(f"API原始响应: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # 检查是否为iflow.cn平台响应格式
            if isinstance(result, dict):
                # 处理iflow.cn平台响应格式
                if "status" in result and "msg" in result:
                    status = result["status"]
                    msg = result["msg"]
                    
                    if status == "0" or status == 0:
                        # 成功响应，检查body字段
                        if "body" in result and isinstance(result["body"], dict):
                            body = result["body"]
                            # 检查是否包含choices或content字段
                            if "choices" in body:
                                choices = body["choices"]
                                if isinstance(choices, list) and len(choices) > 0:
                                    choice = choices[0]
                                    if isinstance(choice, dict):
                                        if "message" in choice and isinstance(choice["message"], dict):
                                            if "content" in choice["message"]:
                                                assistant_message = choice["message"]["content"]
                                                self.response_received.emit("AI", assistant_message)
                                                self.status_changed.emit("就绪")
                                                return
                            elif "content" in body:
                                # 直接返回content内容
                                assistant_message = body["content"]
                                self.response_received.emit("AI", assistant_message)
                                self.status_changed.emit("就绪")
                                return
                    
                    # 处理错误响应
                    error_msg = f"API请求失败: {msg}"
                    self.error_occurred.emit(error_msg)
                    self.status_changed.emit("错误")
                    return
                
                # 处理OpenAI API响应格式
                elif "choices" in result:
                    if isinstance(result["choices"], list) and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        if isinstance(choice, dict) and "message" in choice:
                            message = choice["message"]
                            if isinstance(message, dict) and "content" in message:
                                assistant_message = message["content"]
                                self.response_received.emit("AI", assistant_message)
                                self.status_changed.emit("就绪")
                                return
                
                # 处理其他可能的响应格式
                elif "content" in result:
                    # 直接返回content内容
                    assistant_message = result["content"]
                    self.response_received.emit("AI", assistant_message)
                    self.status_changed.emit("就绪")
                    return
            
            # 响应格式不符合预期，提供更详细的错误信息
            error_msg = f"API返回格式异常。"
            self.error_occurred.emit(error_msg)
            self.status_changed.emit("错误")
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"API调用失败: {str(e)}")
            self.status_changed.emit("错误")
        except json.JSONDecodeError:
            self.error_occurred.emit("API返回格式错误，无法解析。")
            self.status_changed.emit("错误")
        except Exception as e:
            self.error_occurred.emit(f"意外错误: {str(e)}")
            self.status_changed.emit("错误")

class SplashScreen(QDialog):
    """启动动画窗口"""
    splash_ended = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(400, 200)
        self.setWindowOpacity(1.0)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # 创建布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题标签
        self.title_label = QLabel("AI对话软件")
        font = QFont("Arial", 24, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #4A90E2;")
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  #  indeterminate mode
        self.progress_bar.setFixedWidth(300)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        
        # 加载标签
        self.loading_label = QLabel("正在加载...")
        self.loading_label.setFont(QFont("Arial", 12))
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 淡出动画定时器
        self.fade_timer = QTimer()
        self.fade_timer.setInterval(30)
        self.fade_timer.timeout.connect(self.fade_out)
        self.opacity = 1.0
    
    def fade_out(self):
        """淡出动画"""
        self.opacity -= 0.05
        if self.opacity <= 0:
            self.opacity = 0
            self.fade_timer.stop()
            self.close()
            self.splash_ended.emit()
        self.setWindowOpacity(self.opacity)
    
    def start_fade_out(self):
        """开始淡出动画"""
        self.fade_timer.start()

class ConfigDialog(QDialog):
    """配置对话框"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置")
        self.setFixedSize(500, 300)
        self.config = config.copy()
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # 创建布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 配置网格布局
        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)
        
        # 配置项
        config_items = [
            ("API URL", "api_url"),
            ("API密钥", "api_key"),
            ("模型名称", "model"),
            ("温度参数", "temperature"),
            ("最大Tokens", "max_tokens")
        ]
        
        # 存储输入框引用
        self.inputs = {}
        
        for i, (label_text, config_key) in enumerate(config_items):
            label = QLabel(label_text)
            grid_layout.addWidget(label, i, 0, 1, 1, Qt.AlignmentFlag.AlignRight)
            
            input_field = QLineEdit(str(self.config[config_key]))
            grid_layout.addWidget(input_field, i, 1, 1, 3)
            self.inputs[config_key] = input_field
        
        # 按钮布局
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # 保存按钮
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addSpacing(10)
    
    def save_config(self):
        """保存配置"""
        try:
            for key, input_field in self.inputs.items():
                value = input_field.text().strip()
                if key in ["temperature", "max_tokens"]:
                    if key == "temperature":
                        self.config[key] = float(value)
                    else:
                        self.config[key] = int(value)
                else:
                    self.config[key] = value
            
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"配置错误: {str(e)}")
    
    def get_config(self):
        """获取配置"""
        return self.config

class AIChatPyQt(QMainWindow):
    """PyQt版本AI对话软件主窗口"""
    def __init__(self):
        super().__init__()
        self.config_file = 'config.json'
        self.config = self.load_config()
        
        # 初始化对话管理器
        self.conversation_manager = ConversationManager()
        self.current_conversation_id = None
        self.message_counter = 0  # 用于生成消息ID
        
        # 初始化预设管理器
        self.preset_manager = PresetManager()
        self.current_prompt = None  # 当前使用的角色预设
        
        # 初始化审计日志
        self._init_audit_log()
        
        # 初始化动态人格与情绪模拟
        self.emotions = [
            {"id": "neutral", "name": "中性", "description": "保持中立，客观回答"},
            {"id": "excited", "name": "兴奋", "description": "充满活力，积极热情"},
            {"id": "sympathetic", "name": "同情", "description": "表达理解，温暖关怀"},
            {"id": "curious", "name": "好奇", "description": "充满好奇，积极探索"},
            {"id": "humorous", "name": "幽默", "description": "风趣幽默，轻松愉快"}
        ]
        self.current_emotion = "neutral"  # 默认情绪
        self.emotion_modifiers = {
            "neutral": "保持中立的语气，客观回答问题。",
            "excited": "使用充满活力、积极热情的语气，表达兴奋情绪。",
            "sympathetic": "表达理解和温暖关怀，使用同情的语气。",
            "curious": "表达好奇心，使用探索性的语气，鼓励进一步讨论。",
            "humorous": "使用风趣幽默的语气，保持轻松愉快的氛围。"
        }
        
        # 创建或加载当前对话
        self._init_current_conversation()
        
        # 初始化UI
        self.init_ui()
        
        # 显示启动动画
        self.show_splash()
        
    def _init_current_conversation(self):
        """初始化当前对话"""
        # 获取最近的对话
        conversations = self.conversation_manager.get_conversations()
        if conversations:
            # 使用最近的对话
            latest_conv = conversations[0]
            self.current_conversation_id = latest_conv["id"]
            self.conversation_history = self.conversation_manager.load_conversation(self.current_conversation_id)
        else:
            # 创建新对话
            self.current_conversation_id = self.conversation_manager.create_conversation()
            self.conversation_history = []
        
        # 初始化消息ID
        self._init_message_ids()
        
    def _init_message_ids(self):
        """为现有对话历史添加消息ID"""
        for i, message in enumerate(self.conversation_history):
            if "id" not in message:
                message["id"] = f"msg_{self.message_counter}"
                self.message_counter += 1
    
    def _init_audit_log(self):
        """初始化审计日志"""
        # 创建logs目录
        self.logs_dir = "logs"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        # 创建审计日志文件
        self.audit_log_file = os.path.join(self.logs_dir, f"audit_{datetime.date.today().strftime('%Y%m%d')}.log")
        
        # 记录启动日志
        self.write_audit_log("系统", "启动", "AI对话软件启动成功")
    
    def save_history_auto(self):
        """自动保存对话历史"""
        if self.current_conversation_id:
            self.conversation_manager.update_conversation(
                self.current_conversation_id, 
                self.conversation_history
            )
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "api_url": "https://api.openai.com/v1/chat/completions",
            "api_key": "",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 合并默认配置和用户配置
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
        else:
            # 保存默认配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def save_history_auto(self):
        """自动保存对话历史"""
        if self.current_conversation_id:
            self.conversation_manager.update_conversation(
                self.current_conversation_id, 
                self.conversation_history
            )
            print(f"已保存对话到ID: {self.current_conversation_id}")
    
    def show_splash(self):
        """显示启动动画"""
        self.splash = SplashScreen()
        self.splash.splash_ended.connect(self.on_splash_ended)
        self.splash.show()
        
        # 模拟加载延迟
        QTimer.singleShot(2000, self.splash.start_fade_out)
    
    def write_audit_log(self, actor, action, details):
        """写入审计日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] 执行者: {actor} | 操作: {action} | 详情: {details}\n"
        
        # 写入日志文件
        with open(self.audit_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def on_splash_ended(self):
        """启动动画结束后处理"""
        # 检查配置
        if not self.config["api_key"]:
            self.show_config_prompt()
        
        # 显示主窗口并执行淡入动画
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_in()
        
        # 加载历史记录到聊天窗口
        self.load_history_to_chat()
    
    def fade_in(self):
        """主窗口淡入动画"""
        self.opacity = 0.0
        self.fade_in_timer = QTimer()
        self.fade_in_timer.setInterval(30)
        self.fade_in_timer.timeout.connect(self._fade_in_step)
        self.fade_in_timer.start()
    
    def _fade_in_step(self):
        """淡入动画步骤"""
        self.opacity += 0.05
        if self.opacity >= 1.0:
            self.opacity = 1.0
            self.fade_in_timer.stop()
        self.setWindowOpacity(self.opacity)
    
    def init_ui(self):
        """初始化主界面"""
        self.setWindowTitle("AI对话软件")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建菜单
        self.create_menu()
        
        # 创建对话历史区域
        self.create_chat_history(main_layout)
        
        # 创建输入区域
        self.create_input_area(main_layout)
        
        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
    
    def create_menu(self):
        """创建菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = QMenu("文件", self)
        menubar.addMenu(file_menu)
        
        config_action = QAction("配置", self)
        config_action.triggered.connect(self.open_config_dialog)
        file_menu.addAction(config_action)
        
        new_conv_action = QAction("新对话", self)
        new_conv_action.triggered.connect(self.new_conversation)
        file_menu.addAction(new_conv_action)
        
        clear_action = QAction("清空历史", self)
        clear_action.triggered.connect(self.clear_history)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        # 对话菜单
        chat_menu = QMenu("对话", self)
        menubar.addMenu(chat_menu)
        
        regenerate_action = QAction("重新生成回答", self)
        regenerate_action.triggered.connect(self.regenerate_response)
        chat_menu.addAction(regenerate_action)
        
        # 编辑消息功能将在后续实现，需要选择要编辑的消息
        # edit_action = QAction("编辑消息", self)
        # edit_action.triggered.connect(self.edit_selected_message)
        # chat_menu.addAction(edit_action)
        
        chat_menu.addSeparator()
        
        # 分支对话功能
        branch_menu = QMenu("分支对话", self)
        chat_menu.addMenu(branch_menu)
        
        new_branch_action = QAction("创建分支", self)
        new_branch_action.triggered.connect(self.create_new_branch)
        branch_menu.addAction(new_branch_action)
        
        # 切换分支功能将在后续实现，需要选择分支
        # switch_branch_action = QAction("切换分支", self)
        # switch_branch_action.triggered.connect(self.switch_branch_dialog)
        # branch_menu.addAction(switch_branch_action)
        
        # 添加新功能菜单
        file_menu.addSeparator()
        
        save_history_action = QAction("保存对话历史", self)
        save_history_action.triggered.connect(self.save_history)
        file_menu.addAction(save_history_action)
        
        export_config_action = QAction("导出配置", self)
        export_config_action.triggered.connect(self.export_config)
        file_menu.addAction(export_config_action)
        
        import_config_action = QAction("导入配置", self)
        import_config_action.triggered.connect(self.import_config)
        file_menu.addAction(import_config_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 预设菜单
        preset_menu = QMenu("预设", self)
        menubar.addMenu(preset_menu)
        
        # 角色预设子菜单
        prompt_menu = QMenu("角色预设", self)
        preset_menu.addMenu(prompt_menu)
        
        # 填充角色预设选项
        self.populate_prompt_menu(prompt_menu)
        
        # 情绪选择子菜单
        emotion_menu = QMenu("情绪选择", self)
        preset_menu.addMenu(emotion_menu)
        
        # 填充情绪选择选项
        self.populate_emotion_menu(emotion_menu)
        
        # 风格模仿选项
        style_action = QAction("风格模仿", self)
        style_action.triggered.connect(self.show_style_imitation_dialog)
        preset_menu.addAction(style_action)
        
        # 帮助菜单
        help_menu = QMenu("帮助", self)
        menubar.addMenu(help_menu)
        
        help_action = QAction("帮助", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_chat_history(self, layout):
        """创建对话历史区域"""
        # 创建分割器，左侧显示调试信息，右侧显示对话历史
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)
        
        # 左侧调试信息区域
        self.debug_info = QTextEdit()
        self.debug_info.setReadOnly(True)
        self.debug_info.setFont(QFont("Courier New", 10))
        self.debug_info.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.debug_info.setPlaceholderText("调试信息将显示在这里...")
        self.debug_info.setMinimumWidth(200)  # 进一步减小最小宽度
        splitter.addWidget(self.debug_info)
        
        # 右侧对话历史区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Arial", 12))
        self.chat_history.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        splitter.addWidget(self.chat_history)
        
        # 设置分割器初始比例，进一步减小调试信息区域宽度
        splitter.setSizes([200, 600])
    
    def create_input_area(self, layout):
        """创建输入区域"""
        # 输入布局
        input_layout = QHBoxLayout()
        layout.addLayout(input_layout)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setFont(QFont("Arial", 12))
        self.input_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.input_text.setPlaceholderText("请输入消息... (Enter发送, Shift+Enter换行)")
        self.input_text.installEventFilter(self)
        input_layout.addWidget(self.input_text, 1)
        
        # 按钮布局
        button_layout = QVBoxLayout()
        input_layout.addLayout(button_layout)
        input_layout.setSpacing(10)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)
        
        # 重新生成按钮
        self.regenerate_button = QPushButton("重新生成")
        self.regenerate_button.clicked.connect(self.regenerate_response)
        button_layout.addWidget(self.regenerate_button)
        
        # 反馈按钮区域
        feedback_layout = QHBoxLayout()
        button_layout.addLayout(feedback_layout)
        feedback_layout.setSpacing(5)
        
        # 点赞按钮
        self.like_button = QPushButton("👍")
        self.like_button.setFixedSize(40, 25)
        self.like_button.clicked.connect(self.on_like)
        self.like_button.setEnabled(False)  # 默认禁用
        feedback_layout.addWidget(self.like_button)
        
        # 点踩按钮
        self.dislike_button = QPushButton("👎")
        self.dislike_button.setFixedSize(40, 25)
        self.dislike_button.clicked.connect(self.on_dislike)
        self.dislike_button.setEnabled(False)  # 默认禁用
        feedback_layout.addWidget(self.dislike_button)
        
        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_button)
        
        # 新对话按钮
        self.new_conv_button = QPushButton("新对话")
        self.new_conv_button.clicked.connect(self.new_conversation)
        button_layout.addWidget(self.new_conv_button)
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理输入框的按键事件"""
        if obj == self.input_text and event.type() == event.type().KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter 换行
                    return False
                else:
                    # Enter 发送消息
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
    
    def send_message(self):
        """发送消息"""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        # 清空输入框
        self.input_text.clear()
        
        # 显示用户消息
        self.add_message_to_history("你", message)
        
        # 为新消息生成唯一ID
        message_id = f"msg_{self.message_counter}"
        self.message_counter += 1
        
        # 更新对话历史
        self.conversation_history.append({
            "id": message_id,
            "role": "user", 
            "content": message
        })
        
        # 自动保存对话历史
        self.save_history_auto()
        
        # 记录审计日志
        self.write_audit_log("用户", "发送消息", f"消息内容: {message[:50]}...")
        
        # 禁用发送按钮
        self.send_button.setEnabled(False)
        
        # 启动API调用线程
        self.api_thread = ApiCallThread(self.config, self.conversation_history, message)
        self.api_thread.response_received.connect(self.on_response_received)
        self.api_thread.error_occurred.connect(self.on_error_occurred)
        self.api_thread.status_changed.connect(self.status_bar.showMessage)
        self.api_thread.debug_info.connect(self.add_debug_info)
        self.api_thread.finished.connect(self.on_api_thread_finished)
        self.api_thread.start()
    
    def new_conversation(self):
        """开始新对话"""
        response = QMessageBox.question(
            self, "确认", "确定要开始新对话吗？当前对话历史将被保存。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if response == QMessageBox.StandardButton.Yes:
            # 保存当前对话
            if self.current_conversation_id:
                self.save_history_auto()
            
            # 创建新对话
            self.current_conversation_id = self.conversation_manager.create_conversation()
            self.conversation_history = []
            self.message_counter = 0
            
            # 清空聊天窗口
            self.chat_history.clear()
            
            # 记录审计日志
            self.write_audit_log("用户", "开始新对话", f"新对话ID: {self.current_conversation_id}")
            
            self.status_bar.showMessage("已开始新对话")
    
    def on_response_received(self, sender, message):
        """处理API响应"""
        self.add_message_to_history(sender, message)
        
        # 根据OpenAI API规范，role应该是'user', 'assistant', 'system'之一
        # 修正role值，确保符合API规范
        role = sender.lower()
        if role == "ai":
            role = "assistant"
        
        # 为新消息生成唯一ID
        message_id = f"msg_{self.message_counter}"
        self.message_counter += 1
        
        # 添加到对话历史
        self.conversation_history.append({
            "id": message_id,
            "role": role,
            "content": message
        })
        
        # 打印对话历史用于调试
        print(f"当前对话历史: {json.dumps(self.conversation_history, ensure_ascii=False, indent=2)}")
        print(f"当前对话历史长度: {len(self.conversation_history)}条消息")
        
        # 自动保存对话历史
        self.save_history_auto()
        
    def regenerate_response(self):
        """重新生成上一条AI回答"""
        if not self.conversation_history:
            QMessageBox.information(self, "提示", "没有对话历史，无法重新生成回答。")
            return
        
        # 检查最后一条消息是否是AI回复
        last_message = self.conversation_history[-1]
        if last_message["role"] != "assistant":
            QMessageBox.information(self, "提示", "最后一条消息不是AI回复，无法重新生成。")
            return
        
        # 移除最后一条AI回复
        self.conversation_history.pop()
        
        # 清空聊天窗口并重新加载历史
        self.chat_history.clear()
        self.load_history_to_chat()
        
        # 记录审计日志
        self.write_audit_log("用户", "重新生成回答", "重新生成上一条AI回复")
        
        # 重新发送上一条用户消息
        user_message = self.conversation_history[-1]
        self.input_text.setPlainText(user_message["content"])
        self.send_message()
        
    def edit_message(self, message_id, new_content):
        """编辑指定ID的消息"""
        # 查找消息
        for i, message in enumerate(self.conversation_history):
            if message["id"] == message_id:
                # 更新消息内容
                self.conversation_history[i]["content"] = new_content
                
                # 移除该消息之后的所有消息
                self.conversation_history = self.conversation_history[:i+1]
                
                # 清空聊天窗口并重新加载历史
                self.chat_history.clear()
                self.load_history_to_chat()
                
                # 如果是用户消息，将新内容放入输入框
                if message["role"] == "user":
                    self.input_text.setPlainText(new_content)
                
                return True
        return False
        
    def create_branch(self, branch_name, from_message_id=None):
        """创建对话分支"""
        if not branch_name:
            QMessageBox.warning(self, "错误", "分支名称不能为空。")
            return False
        
        if branch_name in self.conversation_branches:
            QMessageBox.warning(self, "错误", "分支名称已存在。")
            return False
        
        # 确定分支起始位置
        if from_message_id:
            # 从指定消息开始分支
            branch_start = 0
            for i, message in enumerate(self.conversation_history):
                if message["id"] == from_message_id:
                    branch_start = i + 1
                    break
            branch_history = self.conversation_history[:branch_start]
        else:
            # 从当前位置开始分支
            branch_history = self.conversation_history.copy()
        
        # 保存当前分支
        self.conversation_branches[branch_name] = branch_history.copy()
        
        QMessageBox.information(self, "成功", f"分支 '{branch_name}' 创建成功！")
        return True
        
    def create_new_branch(self):
        """创建新分支的对话框"""
        from PyQt6.QtWidgets import QInputDialog
        
        branch_name, ok = QInputDialog.getText(self, "创建分支", "请输入分支名称:")
        if ok and branch_name.strip():
            self.create_branch(branch_name.strip())
        
    def switch_branch(self, branch_name):
        """切换到指定分支"""
        if branch_name not in self.conversation_branches:
            QMessageBox.warning(self, "错误", "分支不存在。")
            return False
        
        # 保存当前分支
        self.conversation_branches[self.current_branch] = self.conversation_history.copy()
        
        # 切换到新分支
        self.conversation_history = self.conversation_branches[branch_name].copy()
        self.current_branch = branch_name
        
        # 更新聊天窗口
        self.chat_history.clear()
        self.load_history_to_chat()
        
        return True
    
    def on_error_occurred(self, error_message):
        """处理API错误"""
        self.add_message_to_history("系统", error_message)
    
    def on_api_thread_finished(self):
        """API线程结束处理"""
        self.send_button.setEnabled(True)
    
    def add_message_to_history(self, sender, message):
        """添加消息到对话历史"""
        # 添加发送者和时间
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 设置不同发送者的颜色
        if sender == "你":
            color = "#0066CC"
        elif sender == "AI":
            color = "#009900"
        else:
            color = "#FF6600"
        
        # 插入消息
        self.chat_history.moveCursor(QTextCursor.MoveOperation.End)
        
        # 发送者和时间
        self.chat_history.insertHtml(f"<b><font color='{color}'>[{now}] {sender}:</font></b><br>")
        # 消息内容
        self.chat_history.insertPlainText(f"{message}\n\n")
        
        # 滚动到底部
        self.chat_history.ensureCursorVisible()
        
        # 如果是AI消息，启用反馈按钮
        if sender == "AI":
            self.like_button.setEnabled(True)
            self.dislike_button.setEnabled(True)
    
    def add_debug_info(self, message):
        """添加调试信息到左侧调试区域"""
        # 添加时间戳
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 插入调试信息
        self.debug_info.moveCursor(QTextCursor.MoveOperation.End)
        self.debug_info.insertHtml(f"<b>[{now}] 调试信息:</b><br>")
        self.debug_info.insertPlainText(f"{message}\n\n")
        
        # 滚动到底部
        self.debug_info.ensureCursorVisible()
    
    def open_config_dialog(self):
        """打开配置对话框"""
        dialog = ConfigDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config = dialog.get_config()
            self.save_config()
            QMessageBox.information(self, "成功", "配置已保存！")
    
    def show_config_prompt(self):
        """显示配置提示"""
        response = QMessageBox.question(
            self, "配置提示", "API密钥未配置，是否现在配置？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if response == QMessageBox.StandardButton.Yes:
            self.open_config_dialog()
    
    def clear_history(self):
        """清空对话历史"""
        response = QMessageBox.question(
            self, "确认", "确定要清空对话历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if response == QMessageBox.StandardButton.Yes:
            # 保存当前历史
            self.save_history_auto()
            self.conversation_history = []
            self.chat_history.clear()
            
            # 记录审计日志
            self.write_audit_log("用户", "清空历史", "清空当前对话历史")
            
            self.status_bar.showMessage("对话历史已清空")
    
    def load_history_to_chat(self):
        """将加载的历史记录显示到聊天窗口"""
        if self.conversation_history:
            self.chat_history.clear()
            for message in self.conversation_history:
                if message["role"] == "user":
                    self.add_message_to_history("你", message["content"])
                elif message["role"] == "assistant":
                    self.add_message_to_history("AI", message["content"])
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """AI对话软件帮助

支持自定义API大模型，使用说明：

1. 配置：点击菜单"文件"->"配置"，输入API信息
2. 发送消息：在输入框中输入消息，按Enter发送
3. 换行：按Shift+Enter换行
4. 清空历史：点击"清空"按钮或菜单"文件"->"清空历史"
5. 角色预设：点击菜单"预设"->"角色预设"，选择一个角色

支持的命令：
- 直接输入消息发送给AI
- 配置API URL、API密钥、模型等参数
- 使用角色预设切换AI身份

注意事项：
- 请妥善保管API密钥
- 确保网络连接正常
- 不同API服务可能有不同的计费方式
- 切换角色预设会清空当前对话历史"""
        QMessageBox.information(self, "帮助", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """AI对话软件

版本：1.0

支持自定义API大模型的对话软件，
可以配置不同的API URL、API密钥和模型。"""
        QMessageBox.information(self, "关于", about_text)
    
    def save_history(self):
        """保存对话历史到文件"""
        if not self.conversation_history:
            QMessageBox.information(self, "提示", "对话历史为空，无需保存！")
            return
        
        from PyQt6.QtWidgets import QFileDialog
        
        # 打开文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存对话历史", "chat_history.json", "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "成功", f"对话历史已保存到 {filename}！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存对话历史失败: {str(e)}")
    
    def export_config(self):
        """导出配置到文件"""
        from PyQt6.QtWidgets import QFileDialog
        
        # 打开文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "config_export.json", "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "成功", f"配置已导出到 {filename}！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置失败: {str(e)}")
    
    def populate_prompt_menu(self, menu):
        """填充角色预设菜单"""
        # 清空现有菜单项
        menu.clear()
        
        # 获取所有角色预设
        prompts = self.preset_manager.get_prompts()
        
        # 添加菜单项
        for prompt_id, prompt_info in prompts.items():
            action = QAction(prompt_info["name"], self)
            action.setToolTip(prompt_info["description"])
            action.triggered.connect(lambda checked=False, pid=prompt_id: self.on_prompt_selected(pid))
            menu.addAction(action)
    
    def on_prompt_selected(self, prompt_id):
        """处理角色预设选择"""
        prompt = self.preset_manager.get_prompt_by_id(prompt_id)
        if prompt:
            # 添加系统消息到对话历史
            system_message = {
                "id": f"msg_{self.message_counter}",
                "role": "system",
                "content": f"{prompt['system_prompt']} {self.emotion_modifiers[self.current_emotion]}"
            }
            self.message_counter += 1
            
            # 清空当前对话历史，添加新的系统消息
            self.conversation_history = [system_message]
            
            # 更新当前预设
            self.current_prompt = prompt_id
            
            # 清空聊天窗口
            self.chat_history.clear()
            
            # 添加预设信息到聊天窗口
            self.add_message_to_history("系统", f"已切换到角色：{prompt['name']}\n描述：{prompt['description']}\n当前情绪：{self._get_emotion_name(self.current_emotion)}")
            
            # 自动保存对话历史
            self.save_history_auto()
            
            # 记录审计日志
            self.write_audit_log("用户", "切换角色预设", f"切换到角色：{prompt['name']}")
    
    def populate_emotion_menu(self, menu):
        """填充情绪选择菜单"""
        # 清空现有菜单项
        menu.clear()
        
        # 添加菜单项
        for emotion in self.emotions:
            action = QAction(emotion["name"], self)
            action.setToolTip(emotion["description"])
            action.triggered.connect(lambda checked=False, eid=emotion["id"]: self.on_emotion_selected(eid))
            menu.addAction(action)
    
    def _get_emotion_name(self, emotion_id):
        """根据情绪ID获取情绪名称"""
        for emotion in self.emotions:
            if emotion["id"] == emotion_id:
                return emotion["name"]
        return "未知"
    
    def on_emotion_selected(self, emotion_id):
        """处理情绪选择"""
        if emotion_id not in self.emotion_modifiers:
            return
        
        # 更新当前情绪
        self.current_emotion = emotion_id
        
        # 获取当前情绪名称
        emotion_name = self._get_emotion_name(emotion_id)
        
        # 更新对话历史中的系统消息
        for i, message in enumerate(self.conversation_history):
            if message["role"] == "system":
                # 保留原有角色预设，添加新的情绪修饰
                original_prompt = message["content"]
                # 移除旧的情绪修饰
                for modifier in self.emotion_modifiers.values():
                    if modifier in original_prompt:
                        original_prompt = original_prompt.replace(modifier, "")
                # 添加新的情绪修饰
                new_prompt = f"{original_prompt.strip()} {self.emotion_modifiers[emotion_id]}"
                self.conversation_history[i]["content"] = new_prompt
                break
        
        # 记录审计日志
        self.write_audit_log("用户", "切换情绪", f"切换到情绪：{emotion_name}")
        
        # 添加情绪信息到聊天窗口
        self.add_message_to_history("系统", f"已切换到情绪：{emotion_name}\n描述：{self._get_emotion_description(emotion_id)}")
    
    def _get_emotion_description(self, emotion_id):
        """根据情绪ID获取情绪描述"""
        for emotion in self.emotions:
            if emotion["id"] == emotion_id:
                return emotion["description"]
        return "未知"
    
    def show_style_imitation_dialog(self):
        """显示风格模仿对话框"""
        # 创建风格模仿对话框
        from PyQt6.QtWidgets import QDialog, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("风格模仿")
        dialog.setFixedSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 提示标签
        prompt_label = QLabel("请输入一段文本，AI将模仿其风格进行对话：")
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)
        layout.addSpacing(10)
        
        # 文本输入框
        self.style_text_edit = QTextEdit()
        self.style_text_edit.setPlaceholderText("请输入要模仿的文本...")
        layout.addWidget(self.style_text_edit)
        layout.addSpacing(10)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.apply_style_imitation)
        button_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addSpacing(10)
        
        # 显示对话框
        dialog.exec()
    
    def apply_style_imitation(self):
        """应用风格模仿"""
        # 获取用户输入的风格文本
        style_text = self.style_text_edit.toPlainText().strip()
        if not style_text:
            QMessageBox.warning(self, "警告", "请输入要模仿的文本！")
            return
        
        # 更新对话历史中的系统消息
        style_prompt = f"请模仿以下文本的风格进行对话：\n{style_text}\n"
        
        # 检查是否已有系统消息
        system_message_exists = False
        for i, message in enumerate(self.conversation_history):
            if message["role"] == "system":
                # 保留原有角色预设和情绪修饰，添加风格模仿提示
                original_prompt = message["content"]
                # 移除旧的风格模仿提示
                if "请模仿以下文本的风格进行对话：" in original_prompt:
                    original_prompt = original_prompt.split("请模仿以下文本的风格进行对话：")[0].strip()
                # 添加新的风格模仿提示
                new_prompt = f"{original_prompt} {style_prompt} {self.emotion_modifiers[self.current_emotion]}"
                self.conversation_history[i]["content"] = new_prompt
                system_message_exists = True
                break
        
        # 如果没有系统消息，创建一个新的
        if not system_message_exists:
            system_message = {
                "id": f"msg_{self.message_counter}",
                "role": "system",
                "content": f"{style_prompt} {self.emotion_modifiers[self.current_emotion]}"
            }
            self.message_counter += 1
            self.conversation_history.insert(0, system_message)
        
        # 记录审计日志
        self.write_audit_log("用户", "应用风格模仿", f"风格文本：{style_text[:50]}...")
        
        # 添加风格模仿信息到聊天窗口
        self.add_message_to_history("系统", f"已应用风格模仿\n风格文本：{style_text[:100]}...")
        
        # 自动保存对话历史
        self.save_history_auto()
    
    def on_like(self):
        """处理用户点赞"""
        # 记录审计日志
        self.write_audit_log("用户", "点赞", "用户对AI回复表示满意")
        
        # 禁用反馈按钮
        self.like_button.setEnabled(False)
        self.dislike_button.setEnabled(False)
        
        # 显示感谢信息
        self.add_message_to_history("系统", "感谢您的认可！我会继续努力的。")
    
    def on_dislike(self):
        """处理用户点踩"""
        # 记录审计日志
        self.write_audit_log("用户", "点踩", "用户对AI回复表示不满意")
        
        # 禁用反馈按钮
        self.like_button.setEnabled(False)
        self.dislike_button.setEnabled(False)
        
        # 询问用户哪里不好
        from PyQt6.QtWidgets import QInputDialog
        feedback, ok = QInputDialog.getText(self, "反馈", "之前的回答哪里不好？")
        
        if ok and feedback.strip():
            # 记录反馈信息
            self.write_audit_log("用户", "反馈", f"用户反馈：{feedback}")
            
            # 更新对话历史中的系统消息，添加反馈信息
            for i, message in enumerate(self.conversation_history):
                if message["role"] == "system":
                    # 添加反馈信息到系统提示
                    feedback_prompt = f"\n\n用户反馈：{feedback}，请根据此反馈调整后续回答。"
                    if feedback_prompt not in message["content"]:
                        self.conversation_history[i]["content"] += feedback_prompt
                    break
            
            # 显示感谢反馈信息
            self.add_message_to_history("系统", f"感谢您的反馈：{feedback}\n我会根据您的反馈调整后续回答。")
            
            # 自动保存对话历史
            self.save_history_auto()
        else:
            # 显示默认感谢信息
            self.add_message_to_history("系统", "感谢您的反馈！我会继续改进的。")
    
    def import_config(self):
        """从文件导入配置"""
        from PyQt6.QtWidgets import QFileDialog
        
        # 打开文件选择对话框
        filename, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # 合并导入的配置
                self.config.update(imported_config)
                self.save_config()
                QMessageBox.information(self, "成功", f"配置已从 {filename} 导入并保存！")
            except FileNotFoundError:
                QMessageBox.critical(self, "错误", f"文件 {filename} 不存在！")
            except json.JSONDecodeError:
                QMessageBox.critical(self, "错误", f"文件 {filename} 格式错误！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入配置失败: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    chat = AIChatPyQt()
    sys.exit(app.exec())
