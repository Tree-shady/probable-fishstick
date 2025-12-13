import os
import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QListWidget, QTextEdit, QLineEdit, QPushButton, QSplitter, QLabel,
    QComboBox, QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QProgressBar, QCheckBox, QGroupBox, QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QFont, QDesktopServices, QAction

from .utils import load_json_file, save_json_file
from .network import NetworkMonitor
from .settings import SettingsManager
from .statistics import StatisticsManager
from .database import DatabaseManager
from .ui import SplashScreen, ThemeManager


class UniversalChatBotPyQt6(QMainWindow):
    """PyQt6版本的多功能AI聊天助手"""
    # 定义信号用于在后台线程中更新UI
    update_streaming_response = pyqtSignal(str)
    streaming_response_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 配置文件路径 - 优先使用工作目录的配置文件
        self.config_file = os.path.join(os.getcwd(), "chatbot_config.json")
        # 如果工作目录没有配置文件，使用用户目录的配置文件
        if not os.path.exists(self.config_file):
            self.config_file = os.path.join(os.path.expanduser("~"), ".universal_chatbot_config.json")
        
        # 初始化主题管理器
        self.theme_manager = ThemeManager()
        
        # 初始化设置管理器
        self.settings_manager = SettingsManager(self.config_file)
        self.settings_manager.load_settings()
        self.settings = self.settings_manager.settings
        self.platforms = self.settings_manager.platforms
        
        # 初始化对话历史
        self.conversation_history = []
        self.conversation_file = os.path.join(os.getcwd(), "conversation_history.json")
        self.auto_save_timer = None  # 自动保存定时器
        self.auto_save_delay = 5000  # 自动保存延迟（毫秒）
        
        # 初始化记忆存储目录
        self.memories_dir = os.path.join(os.getcwd(), "memories")
        # 创建memories文件夹（如果不存在）
        os.makedirs(self.memories_dir, exist_ok=True)
        # 个人信息和任务记录文件路径
        self.personal_info_file = os.path.join(self.memories_dir, "personal_info.json")
        self.task_records_file = os.path.join(self.memories_dir, "task_records.json")
        
        # 初始化UI
        self.init_ui()
        
        # 连接信号槽
        self.update_streaming_response.connect(self.append_streaming_response)
        self.streaming_response_finished.connect(self.streaming_response_ended)
        
        # 初始化流式响应状态
        self.streaming_response_text = ""
        self.streaming_response_active = False
        self.current_ai_message_timestamp = None
        self.current_ai_message_prefix = ""
        self.streaming_buffer = ""  # 流式响应缓冲区
        self.streaming_update_timer = None  # 流式更新定时器
        
        # 初始化响应时间记录
        self.message_start_time = None
        self.response_times = []
        
        # 初始化统计管理器
        self.stats_manager = StatisticsManager()
        
        # 初始化数据库管理器
        self.db_manager = None
        
        # 修复DPI设置错误
        if sys.platform == 'win32':
            try:
                import ctypes
                # 尝试不同的DPI设置方式
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        
        # 延迟初始化数据库，在主窗口显示后再尝试
        def delayed_init_db():
            try:
                # 不强制禁用数据库功能，使用用户配置的状态
                # 初始化数据库管理器
                self.db_manager = DatabaseManager(self, self.settings)
                # 不自动连接，让用户手动测试连接
                self.add_debug_info("数据库管理器已初始化，等待用户手动连接", "INFO")
            except Exception as e:
                self.add_debug_info(f"延迟初始化数据库失败: {str(e)}", "ERROR")
        
        QTimer.singleShot(2000, delayed_init_db)
        
        # 初始化网络监控
        self.network_monitor = NetworkMonitor(self)
        self.network_monitor.start_monitoring()
        
        # 初始化配置文件监控
        self.setup_config_monitoring()
        
        # 初始化定期同步定时器
        self.setup_sync_timer()
        
        # 初始化平台下拉框
        available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
        self.platform_combo.clear()
        self.platform_combo.addItems(available_platforms)
        if available_platforms:
            self.platform_combo.setCurrentText(available_platforms[0])
            self.update_platform_config(available_platforms[0])
        
        # 加载对话历史
        self.load_conversation()
        
        # 更新统计管理器的对话历史
        self.stats_manager.update_conversation_history(self.conversation_history)
    
    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle("多功能AI聊天助手")
        self.resize(self.settings['window']['width'], self.settings['window']['height'])
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建主题切换菜单
        self.create_theme_menu()
        
        # 创建分割器，用于左右布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板：调试信息框
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(300)
        
        # 调试信息标题
        debug_title = QLabel("调试信息")
        debug_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        debug_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(debug_title)
        
        # 调试信息文本框
        self.debug_display = QTextEdit()
        self.debug_display.setReadOnly(True)
        left_layout.addWidget(self.debug_display)
        
        # 调试操作按钮
        debug_buttons = QHBoxLayout()
        
        clear_debug_btn = QPushButton("清除调试")
        clear_debug_btn.clicked.connect(self.clear_debug_info)
        debug_buttons.addWidget(clear_debug_btn)
        
        export_debug_btn = QPushButton("导出调试")
        export_debug_btn.clicked.connect(self.export_debug_info)
        debug_buttons.addWidget(export_debug_btn)
        
        left_layout.addLayout(debug_buttons)
        
        # 数据库操作按钮
        db_buttons = QHBoxLayout()
        
        # 启用数据库按钮
        self.enable_db_btn = QPushButton("启用数据库")
        if self.settings['database']['enabled']:
            self.enable_db_btn.setText("禁用数据库")
        self.enable_db_btn.clicked.connect(self.toggle_database_enabled)
        db_buttons.addWidget(self.enable_db_btn)
        
        sync_now_btn = QPushButton("立即同步")
        sync_now_btn.clicked.connect(self.sync_database_now)
        db_buttons.addWidget(sync_now_btn)
        
        connect_db_btn = QPushButton("连接数据库")
        connect_db_btn.clicked.connect(self.connect_database)
        db_buttons.addWidget(connect_db_btn)
        
        left_layout.addLayout(db_buttons)
        
        # 添加左侧面板到分割器
        splitter.addWidget(left_panel)
        
        # 右侧面板：聊天区域和输入区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        right_layout.addWidget(self.tab_widget)
        
        # 聊天标签页
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        
        # 聊天显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(400)
        chat_layout.addWidget(self.chat_display)
        
        # 平台选择和状态区域
        platform_layout = QHBoxLayout()
        
        platform_label = QLabel("AI平台:")
        platform_layout.addWidget(platform_label)
        
        self.platform_combo = QComboBox()
        self.platform_combo.currentTextChanged.connect(self.update_platform_config)
        platform_layout.addWidget(self.platform_combo)
        
        # 状态指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ff0000; font-size: 16px;")
        platform_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("未连接")
        platform_layout.addWidget(self.status_label)
        
        platform_layout.addStretch()
        
        chat_layout.addLayout(platform_layout)
        
        # 消息输入区域
        input_layout = QVBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(75)
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setFocus()
        # 安装事件过滤器，以便捕获键盘事件
        self.message_input.installEventFilter(self)
        input_layout.addWidget(self.message_input)
        
        # 输入辅助按钮
        input_buttons = QHBoxLayout()
        
        self.attach_file_btn = QPushButton("附件")
        self.attach_file_btn.clicked.connect(self.attach_file)
        input_buttons.addWidget(self.attach_file_btn)
        
        self.insert_image_btn = QPushButton("图片")
        self.insert_image_btn.clicked.connect(self.insert_image)
        input_buttons.addWidget(self.insert_image_btn)
        
        input_buttons.addStretch()
        
        self.clear_input_btn = QPushButton("清空")
        self.clear_input_btn.clicked.connect(self.clear_input)
        input_buttons.addWidget(self.clear_input_btn)
        
        input_layout.addLayout(input_buttons)
        
        # 发送按钮和设置
        send_layout = QHBoxLayout()
        
        self.send_button = QPushButton("发送 (Enter)")
        self.send_button.clicked.connect(self.send_message)
        send_button_font = QFont()
        send_button_font.setBold(True)
        self.send_button.setFont(send_button_font)
        send_layout.addWidget(self.send_button)
        
        # 流式响应开关
        self.streaming_checkbox = QCheckBox("流式响应")
        self.streaming_checkbox.setChecked(self.settings['chat']['streaming'])
        send_layout.addWidget(self.streaming_checkbox)
        
        chat_layout.addLayout(input_layout)
        chat_layout.addLayout(send_layout)
        
        # 添加聊天标签页
        self.tab_widget.addTab(chat_tab, "聊天")
        
        # 调试标签页
        debug_tab = QWidget()
        debug_layout = QVBoxLayout(debug_tab)
        
        self.debug_output = QTextEdit()
        self.debug_output.setReadOnly(True)
        debug_layout.addWidget(self.debug_output)
        
        self.tab_widget.addTab(debug_tab, "调试")
        
        # 添加右侧面板到分割器
        splitter.addWidget(right_panel)
        
        # 设置分割器初始比例
        splitter.setSizes([250, 750])
        
        # 应用主题样式
        self.apply_theme(self.settings['appearance']['theme'])
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_conversation_action = QAction("新对话", self)
        new_conversation_action.triggered.connect(self.new_conversation)
        file_menu.addAction(new_conversation_action)
        
        save_conversation_action = QAction("保存对话", self)
        save_conversation_action.triggered.connect(self.save_conversation)
        file_menu.addAction(save_conversation_action)
        
        load_conversation_action = QAction("加载对话", self)
        load_conversation_action.triggered.connect(self.load_conversation_from_file)
        file_menu.addAction(load_conversation_action)
        
        file_menu.addSeparator()
        
        export_conversation_action = QAction("导出对话", self)
        export_conversation_action.triggered.connect(self.export_conversation_history)
        file_menu.addAction(export_conversation_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menu_bar.addMenu("编辑")
        
        copy_action = QAction("复制", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selected_text)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_text)
        edit_menu.addAction(paste_action)
        
        clear_chat_action = QAction("清除聊天", self)
        clear_chat_action.setShortcut("Ctrl+L")
        clear_chat_action.triggered.connect(self.clear_chat_display)
        edit_menu.addAction(clear_chat_action)
        
        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        
        # 统计报告
        statistics_action = QAction("统计报告...", self)
        statistics_action.triggered.connect(self.show_statistics_dialog)
        settings_menu.addAction(statistics_action)
        
        # 个人信息
        personal_info_action = QAction("个人信息", self)
        personal_info_action.triggered.connect(self.show_personal_info_dialog)
        settings_menu.addAction(personal_info_action)
        
        # 任务管理
        task_management_action = QAction("任务管理", self)
        task_management_action.triggered.connect(self.show_task_management_dialog)
        settings_menu.addAction(task_management_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        help_action = QAction("帮助文档", self)
        help_action.triggered.connect(self.open_help_dialog)
        help_menu.addAction(help_action)
    
    def create_theme_menu(self):
        """创建主题切换菜单"""
        # 主题切换功能已集成到设置对话框中
        pass
    
    def apply_theme(self, theme_name):
        """应用主题样式"""
        stylesheet = self.theme_manager.get_theme_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        
        # 更新设置中的主题
        self.settings['appearance']['theme'] = theme_name
        self.settings_manager.update_settings(self.settings)
        
        # 更新UI组件样式
        self.update_ui_components()
    
    def update_ui_components(self):
        """更新UI组件样式"""
        # 可以在这里添加特定组件的样式更新
        pass
    
    def show_splash_screen(self):
        """显示启动动画"""
        # 创建启动动画窗口
        splash = SplashScreen()
        splash.show()
        
        # 更新进度
        splash.update_progress(10, "加载配置文件...")
        QApplication.processEvents()
        
        # 模拟一些耗时初始化
        time.sleep(0.5)
        
        splash.update_progress(30, "初始化UI组件...")
        QApplication.processEvents()
        time.sleep(0.5)
        
        splash.update_progress(50, "加载平台配置...")
        QApplication.processEvents()
        time.sleep(0.5)
        
        splash.update_progress(70, "初始化数据库连接...")
        QApplication.processEvents()
        time.sleep(0.5)
        
        splash.update_progress(90, "加载对话历史...")
        QApplication.processEvents()
        time.sleep(0.5)
        
        splash.update_progress(100, "初始化完成！")
        QApplication.processEvents()
        time.sleep(0.3)
        
        # 关闭启动动画
        splash.fade_out(duration=500)
        QApplication.processEvents()
        time.sleep(0.6)  # 等待渐变效果完成
        splash.close()
        splash.deleteLater()
        QApplication.processEvents()
    
    def setup_config_monitoring(self):
        """设置配置文件监控"""
        # 配置监控功能已集成到config.py模块中
        pass
    
    def setup_sync_timer(self):
        """设置定期同步定时器"""
        # 同步定时器功能已集成到database.py模块中
        pass
    
    def update_platform_config(self, platform_name):
        """更新平台配置"""
        if platform_name in self.platforms:
            self.current_platform = platform_name
            self.current_platform_config = self.platforms[platform_name]
            self.status_label.setText(f"已连接到 {platform_name}")
            self.status_indicator.setStyleSheet("color: #00ff00; font-size: 16px;")
        else:
            self.status_label.setText("平台配置错误")
            self.status_indicator.setStyleSheet("color: #ff0000; font-size: 16px;")
    
    def send_message(self):
        """发送消息"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        
        # 记录发送时间
        self.message_start_time = time.time()
        
        # 显示用户消息
        self.display_message("用户", message)
        
        # 清空输入框
        self.message_input.clear()
        
        # 发送消息到AI
        self.send_to_ai(message)
    
    def display_message(self, sender, content):
        """在聊天窗口中显示消息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 所有消息都靠左显示
        sender_name = "你" if sender == "用户" else "AI"
        
        # 根据设置决定是否显示时间戳
        show_timestamp = self.settings.get('chat', {}).get('show_timestamp', True)
        if show_timestamp:
            self.chat_display.append(f"<div style='text-align: left; margin: 10px 0;'><strong>{sender_name} ({timestamp}):</strong><br>{content}</div>")
        else:
            self.chat_display.append(f"<div style='text-align: left; margin: 10px 0;'><strong>{sender_name}:</strong><br>{content}</div>")
        
        # 自动滚动到底部
        if self.settings['chat']['auto_scroll']:
            self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
        
        # 更新对话历史
        self.conversation_history.append({
            'id': f"{time.time()}-{id(content)}",  # 添加唯一ID
            'sender': sender,
            'content': content,
            'timestamp': timestamp,  # 添加timestamp字段
            'created_at': timestamp,  # 保持向后兼容
            'response_time': None  # 添加response_time字段
        })
        
        # 触发自动保存
        self.schedule_auto_save()
        
        # 更新统计
        self.stats_manager.update_conversation_history(self.conversation_history)
    
    def send_to_ai(self, message):
        """发送消息到AI"""
        from .api import ApiCallThread
        
        # 获取当前平台配置
        platform_config = self.platforms.get(self.current_platform, {})
        if not platform_config:
            self.add_debug_info("未找到当前平台配置", "ERROR")
            return
        
        # 检查API密钥
        api_key = platform_config.get('api_key', '')
        if not api_key:
            self.add_debug_info("API密钥未设置", "ERROR")
            return
        
        # 获取API URL和模型
        base_url = platform_config.get('base_url', '')
        # 确保base_url以斜杠结尾，并且不会重复添加路径
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        # 检查base_url是否已经包含/v1/chat/completions路径
        if base_url.endswith('/v1/chat/completions'):
            api_url = base_url
        else:
            # 构建API URL，确保路径正确
            api_url = f"{base_url}/v1/chat/completions"
        
        model = platform_config.get('models', ['deepseek-v3.1'])[0]
        is_streaming = self.streaming_checkbox.isChecked()
        
        # 获取响应速度设置
        response_speed = self.settings.get('chat', {}).get('response_speed', 5)
        # 获取SSL验证设置
        verify_ssl = self.settings.get('network', {}).get('verify_ssl', False)
        
        # 创建API调用线程
        self.api_thread = ApiCallThread(api_url, api_key, model, message, is_streaming, response_speed, verify_ssl)
        
        # 连接信号
        self.api_thread.streaming_content.connect(self.append_streaming_response)
        self.api_thread.streaming_finished.connect(self.streaming_response_ended)
        self.api_thread.non_streaming_response.connect(self._handle_non_streaming_response)
        self.api_thread.api_error.connect(self._handle_api_error)
        self.api_thread.debug_info.connect(self.add_debug_info)
        
        # 启动线程
        self.api_thread.start()
    
    def _handle_non_streaming_response(self, response):
        """处理非流式API响应"""
        self.display_message("AI", response)
        
    def _handle_api_error(self, error_msg):
        """处理API错误"""
        self.display_message("系统", f"API调用失败: {error_msg}")
    
    def eventFilter(self, obj, event):
        """事件过滤器：处理消息输入框的键盘事件"""
        if obj == self.message_input:
            if event.type() == event.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                        # SHIFT+ENTER：换行
                        return False  # 让默认处理继续，实现换行
                    else:
                        # ENTER：发送消息
                        self.send_message()
                        return True  # 阻止默认处理
        return super().eventFilter(obj, event)
    
    def append_streaming_response(self, text):
        """追加流式响应到聊天窗口"""
        self.streaming_buffer += text
        
        # 如果没有启动定时器，创建一个
        if not self.streaming_update_timer:
            self.streaming_update_timer = QTimer(self)
            self.streaming_update_timer.timeout.connect(self.flush_streaming_buffer)
            self.streaming_update_timer.start(100)  # 每100毫秒更新一次UI
    
    def flush_streaming_buffer(self):
        """刷新流式响应缓冲区，更新UI"""
        if self.streaming_buffer:
            # 如果是第一次更新，添加AI消息前缀
            if not self.streaming_response_active:
                self.streaming_response_active = True
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.current_ai_message_timestamp = timestamp
                self.current_ai_message_prefix = f"<div style='text-align: left; margin: 10px 0;'><strong>AI ({timestamp}):</strong><br>"
                self.chat_display.append(self.current_ai_message_prefix)
            
            # 更新聊天显示
            self.chat_display.insertPlainText(self.streaming_buffer)
            self.streaming_response_text += self.streaming_buffer
            self.streaming_buffer = ""
            
            # 自动滚动到底部
            if self.settings['chat']['auto_scroll']:
                self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())
    
    def streaming_response_ended(self):
        """流式响应结束处理"""
        # 停止定时器
        if self.streaming_update_timer:
            self.streaming_update_timer.stop()
            self.streaming_update_timer = None
        
        # 确保缓冲区中的内容都被显示
        self.flush_streaming_buffer()
        
        # 完成AI消息
        if self.streaming_response_active:
            self.streaming_response_active = False
            self.chat_display.append("</div>")
            
            # 计算响应时间
            if self.message_start_time:
                response_time = time.time() - self.message_start_time
                self.response_times.append(response_time)
            else:
                response_time = 0
            
            # 更新对话历史
            self.conversation_history.append({
                'sender': 'AI',
                'content': self.streaming_response_text,
                'created_at': self.current_ai_message_timestamp,
                'response_time': response_time
            })
            
            # 重置流式响应状态
            self.streaming_response_text = ""
            self.current_ai_message_timestamp = None
            self.current_ai_message_prefix = ""
            
            # 触发自动保存
            self.schedule_auto_save()
            
            # 更新统计
            self.stats_manager.update_conversation_history(self.conversation_history)
    
    def schedule_auto_save(self):
        """安排自动保存"""
        if self.auto_save_timer:
            self.auto_save_timer.stop()
        
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_conversation)
        self.auto_save_timer.start(self.auto_save_delay)
    
    def auto_save_conversation(self):
        """自动保存对话历史"""
        if self.settings['chat']['auto_save']:
            self.save_conversation()
    
    def save_conversation(self):
        """保存对话历史"""
        save_json_file(self.conversation_file, self.conversation_history)
    
    def load_conversation(self):
        """加载对话历史，确保每条消息都包含所有必需的字段"""
        history = load_json_file(self.conversation_file, [])
        # 确保每条消息都包含所有必需的字段
        for message in history:
            if 'id' not in message:
                message['id'] = f"{time.time()}-{id(message)}"
            if 'content' not in message:
                message['content'] = message.get('message', '')
            if 'timestamp' not in message:
                message['timestamp'] = message.get('created_at', time.strftime("%Y-%m-%d %H:%M:%S"))
            if 'created_at' not in message:
                message['created_at'] = message['timestamp']
            if 'response_time' not in message:
                message['response_time'] = None
        self.conversation_history = history
    
    def load_conversation_from_file(self):
        """从文件加载对话历史，确保每条消息都包含所有必需的字段"""
        file_path, _ = QFileDialog.getOpenFileName(self, "加载对话历史", ".", "JSON Files (*.json)")
        if file_path:
            history = load_json_file(file_path, [])
            # 确保每条消息都包含所有必需的字段
            for message in history:
                if 'id' not in message:
                    message['id'] = f"{time.time()}-{id(message)}"
                if 'content' not in message:
                    message['content'] = message.get('message', '')
                if 'timestamp' not in message:
                    message['timestamp'] = message.get('created_at', time.strftime("%Y-%m-%d %H:%M:%S"))
                if 'created_at' not in message:
                    message['created_at'] = message['timestamp']
                if 'response_time' not in message:
                    message['response_time'] = None
            self.conversation_history = history
            self.refresh_chat_display()
    
    def refresh_chat_display(self):
        """刷新聊天显示"""
        self.chat_display.clear()
        for entry in self.conversation_history:
            if entry['sender'] == "用户":
                self.chat_display.append(f"<div style='text-align: right; margin: 10px 0;'><strong>你 ({entry['created_at']}):</strong><br>{entry['content']}</div>")
            else:
                self.chat_display.append(f"<div style='text-align: left; margin: 10px 0;'><strong>AI ({entry['created_at']}):</strong><br>{entry['content']}</div>")
    
    def clear_conversation_history(self):
        """清除对话历史"""
        reply = QMessageBox.question(self, "确认清除", "确定要清除所有对话历史吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_history = []
            self.chat_display.clear()
            self.save_conversation()
    
    def export_conversation_history(self):
        """导出对话历史"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出对话历史", ".", "JSON Files (*.json);;Text Files (*.txt)")
        if file_path:
            if file_path.endswith('.json'):
                save_json_file(file_path, self.conversation_history)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for entry in self.conversation_history:
                        f.write(f"{entry['sender']} ({entry['created_at']}):\n{entry['content']}\n\n")
            
            QMessageBox.information(self, "成功", "对话历史已成功导出！")
    
    def export_statistics(self, file_path=None):
        """导出统计报告"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, "导出统计报告", ".", "JSON Files (*.json);;Text Files (*.txt)")
        
        if file_path:
            success, result = self.stats_manager.export_statistics(file_path)
            if success:
                QMessageBox.information(self, "成功", f"统计报告已成功导出到: {result}")
            else:
                QMessageBox.critical(self, "错误", f"导出统计报告失败: {result}")
    
    def clear_input(self):
        """清空输入框"""
        self.message_input.clear()
    
    def clear_chat_display(self):
        """清空聊天显示"""
        self.chat_display.clear()
    
    def copy_selected_text(self):
        """复制选中的文本"""
        self.chat_display.copy()
    
    def paste_text(self):
        """粘贴文本到输入框"""
        self.message_input.paste()
    
    def attach_file(self):
        """附加文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", ".", "All Files (*)")
        if file_path:
            self.message_input.append(f"[附件: {os.path.basename(file_path)}]\n{file_path}")
    
    def insert_image(self):
        """插入图片"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", ".", "Image Files (*.png *.jpg *.jpeg *.gif)")
        if file_path:
            self.message_input.append(f"[图片: {os.path.basename(file_path)}]\n{file_path}")
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox,
            QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QTabWidget, QLineEdit
        )
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setMinimumWidth(500)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 基本设置标签页
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        # 主题选择
        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_available_themes())
        self.theme_combo.setCurrentText(self.settings['appearance']['theme'])
        basic_layout.addRow(theme_label, self.theme_combo)
        
        # 字体大小
        font_size_label = QLabel("字体大小:")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings['appearance']['font_size'])
        basic_layout.addRow(font_size_label, self.font_size_spin)
        
        tab_widget.addTab(basic_tab, "外观")
        
        # 聊天设置标签页
        chat_tab = QWidget()
        chat_layout = QFormLayout(chat_tab)
        
        # 自动滚动
        auto_scroll_check = QCheckBox("自动滚动")
        auto_scroll_check.setChecked(self.settings['chat']['auto_scroll'])
        chat_layout.addRow(auto_scroll_check)
        
        # 自动保存
        auto_save_check = QCheckBox("自动保存")
        auto_save_check.setChecked(self.settings['chat']['auto_save'])
        chat_layout.addRow(auto_save_check)
        
        # 显示时间戳
        show_timestamp_check = QCheckBox("显示时间戳")
        show_timestamp_check.setChecked(self.settings['chat']['show_timestamp'])
        chat_layout.addRow(show_timestamp_check)
        
        # 流式响应
        streaming_check = QCheckBox("流式响应")
        streaming_check.setChecked(self.settings['chat']['streaming'])
        chat_layout.addRow(streaming_check)
        
        # 最大历史记录
        max_history_label = QLabel("最大历史记录:")
        max_history_spin = QSpinBox()
        max_history_spin.setRange(10, 1000)
        max_history_spin.setValue(self.settings['chat']['max_history'])
        chat_layout.addRow(max_history_label, max_history_spin)
        
        tab_widget.addTab(chat_tab, "聊天")
        
        # 网络设置标签页
        network_tab = QWidget()
        network_layout = QFormLayout(network_tab)
        
        # 超时设置
        timeout_label = QLabel("超时时间(秒):")
        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 120)
        timeout_spin.setValue(self.settings['network']['timeout'])
        network_layout.addRow(timeout_label, timeout_spin)
        
        # 重试次数
        retry_label = QLabel("重试次数:")
        retry_spin = QSpinBox()
        retry_spin.setRange(0, 5)
        retry_spin.setValue(self.settings['network']['retry_count'])
        network_layout.addRow(retry_label, retry_spin)
        
        # 使用代理
        use_proxy_check = QCheckBox("使用代理")
        use_proxy_check.setChecked(self.settings['network']['use_proxy'])
        network_layout.addRow(use_proxy_check)
        
        tab_widget.addTab(network_tab, "网络")
        
        # 数据库设置标签页
        database_tab = QWidget()
        database_layout = QFormLayout(database_tab)
        
        # 启用数据库
        enable_db_check = QCheckBox("启用数据库")
        enable_db_check.setChecked(self.settings['database']['enabled'])
        database_layout.addRow(enable_db_check)
        
        # 数据库类型
        db_type_label = QLabel("数据库类型:")
        db_type_combo = QComboBox()
        db_type_combo.addItems(['mysql', 'postgresql', 'sqlite'])
        db_type_combo.setCurrentText(self.settings['database']['type'])
        database_layout.addRow(db_type_label, db_type_combo)
        
        # 数据库主机
        db_host_label = QLabel("主机:")
        db_host_edit = QLineEdit()
        db_host_edit.setText(self.settings['database']['host'])
        database_layout.addRow(db_host_label, db_host_edit)
        
        # 数据库端口
        db_port_label = QLabel("端口:")
        db_port_spin = QSpinBox()
        db_port_spin.setRange(1, 65535)
        db_port_spin.setValue(self.settings['database']['port'])
        database_layout.addRow(db_port_label, db_port_spin)
        
        # 数据库名称
        db_name_label = QLabel("数据库名称:")
        db_name_edit = QLineEdit()
        db_name_edit.setText(self.settings['database']['database'])
        database_layout.addRow(db_name_label, db_name_edit)
        
        # 数据库用户名
        db_user_label = QLabel("用户名:")
        db_user_edit = QLineEdit()
        db_user_edit.setText(self.settings['database']['username'])
        database_layout.addRow(db_user_label, db_user_edit)
        
        # 数据库密码
        db_pass_label = QLabel("密码:")
        db_pass_edit = QLineEdit()
        db_pass_edit.setText(self.settings['database']['password'])
        db_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        database_layout.addRow(db_pass_label, db_pass_edit)
        
        # 同步选项
        sync_on_startup_check = QCheckBox("启动时同步")
        sync_on_startup_check.setChecked(self.settings['database']['sync_on_startup'])
        database_layout.addRow(sync_on_startup_check)
        
        # 同步间隔
        sync_interval_label = QLabel("同步间隔 (秒):")
        sync_interval_spin = QSpinBox()
        sync_interval_spin.setRange(60, 3600)  # 60-3600秒
        sync_interval_spin.setValue(self.settings['database']['sync_interval'])
        database_layout.addRow(sync_interval_label, sync_interval_spin)
        
        # 选择性同步
        sync_config_check = QCheckBox("同步配置")
        sync_config_check.setChecked(self.settings['database']['sync_config'])
        database_layout.addRow(sync_config_check)
        
        sync_conversations_check = QCheckBox("同步对话历史")
        sync_conversations_check.setChecked(self.settings['database']['sync_conversations'])
        database_layout.addRow(sync_conversations_check)
        
        sync_memories_check = QCheckBox("同步记忆数据")
        sync_memories_check.setChecked(self.settings['database']['sync_memories'])
        database_layout.addRow(sync_memories_check)
        
        # 测试连接按钮
        test_conn_btn = QPushButton("测试连接")
        test_conn_btn.clicked.connect(lambda: self._test_database_connection(
            db_type_combo.currentText(),
            db_host_edit.text(),
            db_port_spin.value(),
            db_name_edit.text(),
            db_user_edit.text(),
            db_pass_edit.text()
        ))
        database_layout.addRow(test_conn_btn)
        
        # 立即同步按钮
        sync_now_btn = QPushButton("立即同步")
        sync_now_btn.clicked.connect(self.sync_database_now)
        database_layout.addRow(sync_now_btn)
        
        tab_widget.addTab(database_tab, "数据库")
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        # 重置按钮
        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self.settings_manager.reset_settings)
        button_layout.addWidget(reset_button)
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(button_layout)
        
        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 应用设置
            new_settings = {
                'appearance': {
                    'theme': self.theme_combo.currentText(),
                    'font_size': self.font_size_spin.value()
                },
                'chat': {
                    'auto_scroll': auto_scroll_check.isChecked(),
                    'auto_save': auto_save_check.isChecked(),
                    'show_timestamp': show_timestamp_check.isChecked(),
                    'streaming': streaming_check.isChecked(),
                    'max_history': max_history_spin.value()
                },
                'network': {
                    'timeout': timeout_spin.value(),
                    'retry_count': retry_spin.value(),
                    'use_proxy': use_proxy_check.isChecked()
                },
                'database': {
                    'enabled': enable_db_check.isChecked(),
                    'type': db_type_combo.currentText(),
                    'host': db_host_edit.text(),
                    'port': db_port_spin.value(),
                    'database': db_name_edit.text(),
                    'username': db_user_edit.text(),
                    'password': db_pass_edit.text(),
                    'sync_on_startup': sync_on_startup_check.isChecked(),
                    'sync_interval': sync_interval_spin.value(),
                    'sync_config': sync_config_check.isChecked(),
                    'sync_conversations': sync_conversations_check.isChecked(),
                    'sync_memories': sync_memories_check.isChecked()
                }
            }
            
            # 更新设置
            self.settings_manager.update_settings(new_settings)
            self.settings = self.settings_manager.settings
            
            # 应用主题
            self.apply_theme(self.settings['appearance']['theme'])
            
            # 更新流式响应复选框
            self.streaming_checkbox.setChecked(self.settings['chat']['streaming'])
            
            # 更新数据库管理器设置
            if self.db_manager:
                self.db_manager.settings = self.settings
                self.db_manager.db_config = self.settings['database']
        
    def _test_database_connection(self, db_type, host, port, database, username, password):
        """测试数据库连接"""
        from PyQt6.QtWidgets import QMessageBox
        
        # 创建临时数据库配置
        temp_db_config = {
            'enabled': True,
            'type': db_type,
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password
        }
        
        # 创建临时数据库管理器测试连接
        temp_db_manager = DatabaseManager(self, {'database': temp_db_config})
        
        # 测试连接
        if temp_db_manager.connect():
            QMessageBox.information(self, "成功", "数据库连接成功！")
            temp_db_manager.disconnect()
        else:
            QMessageBox.critical(self, "错误", "数据库连接失败！")
    
    def show_statistics_dialog(self):
        """显示统计报告对话框"""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
            QTabWidget, QFormLayout
        )
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("统计报告")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 统计概览标签页
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        # 获取统计数据
        stats_summary = self.stats_manager.get_statistics_summary()
        
        # 创建统计概览区域
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        
        # 格式化统计数据
        stats_content = "统计概览\n\n"
        stats_content += f"总对话数: {stats_summary['total_conversations']}\n"
        stats_content += f"总消息数: {stats_summary['total_messages']}\n"
        stats_content += f"用户消息数: {stats_summary['user_messages']}\n"
        stats_content += f"AI消息数: {stats_summary['ai_messages']}\n"
        stats_content += f"平均响应时间: {stats_summary['average_response_time']}秒\n"
        stats_content += f"最小响应时间: {stats_summary['min_response_time']}秒\n"
        stats_content += f"最大响应时间: {stats_summary['max_response_time']}秒\n"
        stats_content += f"总对话时长: {stats_summary['total_duration']}分钟\n\n"
        
        # 添加响应时间分布
        stats_content += "响应时间分布:\n"
        distribution = stats_summary['response_time_distribution']
        stats_content += f"  - 快速 (< 1秒): {distribution['fast']}次\n"
        stats_content += f"  - 正常 (1-5秒): {distribution['normal']}次\n"
        stats_content += f"  - 较慢 (5-10秒): {distribution['slow']}次\n"
        stats_content += f"  - 很慢 (> 10秒): {distribution['very_slow']}次\n"
        
        stats_text.setPlainText(stats_content)
        summary_layout.addWidget(stats_text)
        
        tab_widget.addTab(summary_tab, "统计概览")
        
        # 每日统计标签页
        daily_tab = QWidget()
        daily_layout = QVBoxLayout(daily_tab)
        
        daily_stats_text = QTextEdit()
        daily_stats_text.setReadOnly(True)
        
        daily_stats = self.stats_manager.get_daily_statistics()
        daily_content = "每日统计\n\n"
        
        if daily_stats:
            for date in sorted(daily_stats.keys()):
                stats = daily_stats[date]
                daily_content += f"日期: {date}\n"
                daily_content += f"  - 消息总数: {stats['messages']}\n"
                daily_content += f"  - 用户消息: {stats['user_messages']}\n"
                daily_content += f"  - AI消息: {stats['ai_messages']}\n"
                daily_content += f"  - 平均响应时间: {stats['average_response_time']}秒\n\n"
        else:
            daily_content += "暂无每日统计数据\n"
        
        daily_stats_text.setPlainText(daily_content)
        daily_layout.addWidget(daily_stats_text)
        
        tab_widget.addTab(daily_tab, "每日统计")
        
        # 导出按钮
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        export_button = QPushButton("导出统计数据")
        export_button.clicked.connect(lambda: self.export_statistics())
        export_layout.addWidget(export_button)
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(export_layout)
        
        # 显示对话框
        dialog.exec()
    
    def show_personal_info_dialog(self):
        """显示个人信息对话框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
        from PyQt6.QtCore import Qt
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("个人信息")
        dialog.setMinimumWidth(400)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 加载现有个人信息
        personal_info = self.load_personal_info()
        
        # 创建输入框
        name_edit = QLineEdit(personal_info.get("name", ""))
        email_edit = QLineEdit(personal_info.get("email", ""))
        phone_edit = QLineEdit(personal_info.get("phone", ""))
        address_edit = QLineEdit(personal_info.get("address", ""))
        
        # 添加到表单
        form_layout.addRow("姓名", name_edit)
        form_layout.addRow("邮箱", email_edit)
        form_layout.addRow("电话", phone_edit)
        form_layout.addRow("地址", address_edit)
        
        # 添加表单到主布局
        layout.addLayout(form_layout)
        
        # 按钮布局
        button_layout = QVBoxLayout()
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self._save_personal_info(
            dialog, name_edit.text(), email_edit.text(), phone_edit.text(), address_edit.text()
        ))
        button_layout.addWidget(save_btn)
        
        # 添加按钮布局到主布局
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec()
    
    def _save_personal_info(self, dialog, name, email, phone, address):
        """保存个人信息"""
        personal_info = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address
        }
        
        if self.save_personal_info(personal_info):
            QMessageBox.information(self, "成功", "个人信息已保存！")
            dialog.accept()
        else:
            QMessageBox.error(self, "错误", "保存个人信息失败！")
    
    def show_task_management_dialog(self):
        """显示任务管理对话框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QPushButton, QMessageBox
        from PyQt6.QtCore import Qt
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("任务管理")
        dialog.setMinimumSize(500, 400)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # 主布局
        layout = QVBoxLayout(dialog)
        
        # 任务输入布局
        input_layout = QHBoxLayout()
        
        task_input = QLineEdit()
        task_input.setPlaceholderText("输入新任务...")
        input_layout.addWidget(task_input)
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(lambda: self._add_task(task_list, task_input))
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        # 任务列表
        task_list = QListWidget()
        # 加载现有任务
        self._load_tasks(task_list)
        layout.addWidget(task_list)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self._delete_task(task_list))
        button_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(lambda: self._clear_tasks(task_list))
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec()
    
    def _load_tasks(self, task_list):
        """加载任务到列表"""
        task_list.clear()
        tasks = self.load_task_records()
        for task in tasks:
            # 处理任务可能是字符串或字典的情况
            if isinstance(task, str):
                task_list.addItem(task)
            else:
                task_list.addItem(task.get("content", ""))
    
    def _add_task(self, task_list, task_input):
        """添加任务"""
        task_content = task_input.text().strip()
        if task_content:
            tasks = self.load_task_records()
            
            # 确保所有现有任务都是字典格式
            formatted_tasks = []
            for task in tasks:
                if isinstance(task, str):
                    formatted_tasks.append({
                        "id": f"{time.time()}-{id(task)}",
                        "content": task,
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "completed": False
                    })
                else:
                    formatted_tasks.append(task)
            
            # 添加新任务
            formatted_tasks.append({
                "id": f"{time.time()}-{id(task_content)}",
                "content": task_content,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "completed": False
            })
            
            if self.save_task_records(formatted_tasks):
                task_list.addItem(task_content)
                task_input.clear()
                # 更新任务列表
                self._load_tasks(task_list)
    
    def _delete_task(self, task_list):
        """删除选中的任务"""
        current_row = task_list.currentRow()
        if current_row >= 0:
            # 获取当前选中的任务文本
            selected_item = task_list.item(current_row)
            if not selected_item:
                return
            selected_text = selected_item.text()
            
            # 加载并格式化任务记录
            tasks = self.load_task_records()
            formatted_tasks = []
            for task in tasks:
                if isinstance(task, str):
                    formatted_tasks.append({
                        "id": f"{time.time()}-{id(task)}",
                        "content": task,
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "completed": False
                    })
                else:
                    formatted_tasks.append(task)
            
            # 查找并删除匹配的任务
            updated_tasks = []
            for task in formatted_tasks:
                if task.get("content", "") != selected_text:
                    updated_tasks.append(task)
            
            # 保存更新后的任务列表
            if self.save_task_records(updated_tasks):
                # 更新界面
                task_list.takeItem(current_row)
                # 重新加载任务列表以确保一致性
                self._load_tasks(task_list)
    
    def _clear_tasks(self, task_list):
        """清空所有任务"""
        from PyQt6.QtWidgets import QMessageBox
        if QMessageBox.question(self, "确认", "确定要清空所有任务吗？") == QMessageBox.StandardButton.Yes:
            # 保存空的任务列表
            if self.save_task_records([]):
                # 清空界面上的任务列表
                task_list.clear()
                # 重新加载任务列表以确保一致性
                self._load_tasks(task_list)
    
    def load_personal_info(self):
        """加载个人信息"""
        from .utils import load_json_file
        return load_json_file(self.personal_info_file, {})
    
    def save_personal_info(self, info):
        """保存个人信息"""
        from .utils import save_json_file
        return save_json_file(self.personal_info_file, info)
    
    def load_task_records(self):
        """加载任务记录"""
        from .utils import load_json_file
        return load_json_file(self.task_records_file, [])
    
    def save_task_records(self, records):
        """保存任务记录"""
        from .utils import save_json_file
        return save_json_file(self.task_records_file, records)
    
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于多功能AI聊天助手",
                        "多功能AI聊天助手\n\n" "版本: 1.0.0\n\n" "一个功能丰富、界面美观的AI聊天助手")
    
    def open_help_dialog(self):
        """打开帮助文档"""
        QMessageBox.information(self, "帮助文档",
                              "帮助文档功能正在开发中...\n\n" "请访问我们的官方网站获取更多帮助。")
    
    def add_debug_info(self, info, level="INFO"):
        """添加调试信息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        debug_line = f"[{timestamp}] [{level}] {info}"
        
        # 更新调试输出标签页
        if hasattr(self, 'debug_output'):
            self.debug_output.append(debug_line)
            self.debug_output.verticalScrollBar().setValue(self.debug_output.verticalScrollBar().maximum())
        
        # 更新左侧调试信息框
        if hasattr(self, 'debug_display'):
            self.debug_display.append(debug_line)
            self.debug_display.verticalScrollBar().setValue(self.debug_display.verticalScrollBar().maximum())
    
    def clear_debug_info(self):
        """清除调试信息"""
        if hasattr(self, 'debug_display'):
            self.debug_display.clear()
        if hasattr(self, 'debug_output'):
            self.debug_output.clear()
    
    def export_debug_info(self):
        """导出调试信息"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getSaveFileName(self, "导出调试信息", ".", "Text Files (*.txt);;All Files (*)")
        if file_path:
            # 获取调试信息文本
            if hasattr(self, 'debug_display'):
                debug_text = self.debug_display.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(debug_text)
                QMessageBox.information(self, "成功", "调试信息已成功导出！")
    
    def sync_database_now(self):
        """立即同步数据库"""
        if self.db_manager:
            self.add_debug_info("开始立即同步数据库...", "INFO")
            self.db_manager.sync_all()
        else:
            self.add_debug_info("数据库管理器未初始化", "WARNING")
    
    def connect_database(self):
        """连接数据库"""
        if self.db_manager:
            self.add_debug_info("正在连接数据库...", "INFO")
            if self.db_manager.connect():
                self.add_debug_info("数据库连接成功", "INFO")
            else:
                self.add_debug_info("数据库连接失败", "ERROR")
        else:
            self.add_debug_info("数据库管理器未初始化", "WARNING")
    
    def toggle_database_enabled(self):
        """切换数据库启用状态"""
        # 切换启用状态
        current_state = self.settings['database']['enabled']
        new_state = not current_state
        
        # 更新设置
        new_settings = {
            'database': {
                'enabled': new_state
            }
        }
        self.settings_manager.update_settings(new_settings)
        self.settings = self.settings_manager.settings
        
        # 更新按钮文本
        if new_state:
            self.enable_db_btn.setText("禁用数据库")
            self.add_debug_info("数据库已启用", "INFO")
            # 重启自动同步定时器
            if self.db_manager:
                self.db_manager.setup_sync_timer()
        else:
            self.enable_db_btn.setText("启用数据库")
            self.add_debug_info("数据库已禁用", "INFO")
            # 停止自动同步定时器
            if self.db_manager and hasattr(self.db_manager, 'sync_timer') and self.db_manager.sync_timer:
                self.db_manager.sync_timer.stop()
                self.db_manager.sync_timer = None
    
    def new_conversation(self):
        """创建新对话"""
        reply = QMessageBox.question(self, "确认新建", "确定要开始新对话吗？当前对话将被保存。",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.save_conversation()
            self.conversation_history = []
            self.chat_display.clear()
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        # 保存对话历史
        self.save_conversation()
        
        # 停止网络监控
        self.network_monitor.stop_monitoring()
        
        # 断开数据库连接
        if self.db_manager:
            self.db_manager.disconnect()
        
        event.accept()
