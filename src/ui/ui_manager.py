import os
import time
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QListWidget, 
    QTextEdit, QLineEdit, QPushButton, QSplitter, QLabel, QComboBox, 
    QMenuBar, QMenu, QStatusBar, QProgressBar, QCheckBox, QGroupBox, QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction

from ..utils.helpers import load_json_file, save_json_file
from .dialogs import SettingsDialog, StatisticsDialog, PersonalInfoDialog, TaskManagementDialog

class UIManager:
    """UI管理类，负责UI组件的初始化和事件处理"""
    
    def __init__(self, parent: QMainWindow):
        self.parent = parent
        self.init_ui()
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 设置窗口标题和大小
        self.parent.setWindowTitle("多功能AI聊天助手")
        self.parent.resize(self.parent.settings['window']['width'], self.parent.settings['window']['height'])
        
        # 创建中央部件
        central_widget = QWidget()
        self.parent.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.parent.status_bar = QStatusBar()
        self.parent.setStatusBar(self.parent.status_bar)
        
        # 创建分割器，用于左右布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板：包含调试信息和监控面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(300)
        
        # 创建左侧面板的标签页
        left_tab_widget = QTabWidget()
        left_layout.addWidget(left_tab_widget)
        
        # 调试信息标签页
        debug_tab = QWidget()
        debug_layout = QVBoxLayout(debug_tab)
        
        # 调试信息标题
        debug_title = QLabel("调试信息")
        debug_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        debug_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        debug_layout.addWidget(debug_title)
        
        # 调试信息文本框
        self.parent.debug_display = QTextEdit()
        self.parent.debug_display.setReadOnly(True)
        debug_layout.addWidget(self.parent.debug_display)
        
        # 调试操作按钮
        debug_buttons = QHBoxLayout()
        
        clear_debug_btn = QPushButton("清除调试")
        clear_debug_btn.clicked.connect(self.parent.clear_debug_info)
        debug_buttons.addWidget(clear_debug_btn)
        
        export_debug_btn = QPushButton("导出调试")
        export_debug_btn.clicked.connect(self.parent.export_debug_info)
        debug_buttons.addWidget(export_debug_btn)
        
        debug_layout.addLayout(debug_buttons)
        
        # 数据库操作按钮
        db_buttons = QHBoxLayout()
        
        # 启用数据库按钮
        self.parent.enable_db_btn = QPushButton("启用数据库")
        if self.parent.settings['database']['enabled']:
            self.parent.enable_db_btn.setText("禁用数据库")
        self.parent.enable_db_btn.clicked.connect(self.parent.toggle_database_enabled)
        db_buttons.addWidget(self.parent.enable_db_btn)
        
        sync_now_btn = QPushButton("立即同步")
        sync_now_btn.clicked.connect(self.parent.sync_database_now)
        db_buttons.addWidget(sync_now_btn)
        
        connect_db_btn = QPushButton("连接数据库")
        connect_db_btn.clicked.connect(self.parent.connect_database)
        db_buttons.addWidget(connect_db_btn)
        
        debug_layout.addLayout(db_buttons)
        
        left_tab_widget.addTab(debug_tab, "调试")
        
        # 监控面板标签页
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        
        # 监控面板标题
        monitor_title = QLabel("系统监控")
        monitor_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        monitor_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        monitor_layout.addWidget(monitor_title)
        
        # 网络状态监控
        network_group = QGroupBox("网络状态")
        network_layout = QVBoxLayout(network_group)
        
        # 网络连接状态
        self.parent.network_status_label = QLabel("网络状态: 未连接")
        network_layout.addWidget(self.parent.network_status_label)
        
        # IP地址
        self.parent.ip_address_label = QLabel("IP地址: - - - - - - - - - - ")
        network_layout.addWidget(self.parent.ip_address_label)
        
        # 网络延迟
        self.parent.network_latency_label = QLabel("延迟: - - ms")
        network_layout.addWidget(self.parent.network_latency_label)
        
        monitor_layout.addWidget(network_group)
        
        # 数据库状态监控
        db_group = QGroupBox("数据库状态")
        db_layout = QVBoxLayout(db_group)
        
        # 数据库连接状态
        self.parent.db_status_label = QLabel("数据库状态: 未连接")
        db_layout.addWidget(self.parent.db_status_label)
        
        # 数据库类型
        db_type = self.parent.settings.get('database', {}).get('type', 'unknown')
        self.parent.db_type_label = QLabel(f"数据库类型: {db_type}")
        db_layout.addWidget(self.parent.db_type_label)
        
        # 同步状态
        self.parent.sync_status_label = QLabel("同步状态: 未同步")
        db_layout.addWidget(self.parent.sync_status_label)
        
        monitor_layout.addWidget(db_group)
        
        # 系统资源监控
        system_group = QGroupBox("系统资源")
        system_layout = QVBoxLayout(system_group)
        
        # 内存使用情况
        self.parent.memory_usage_label = QLabel("内存使用: - -%")
        system_layout.addWidget(self.parent.memory_usage_label)
        
        monitor_layout.addWidget(system_group)
        
        left_tab_widget.addTab(monitor_tab, "监控")
        
        # 添加左侧面板到分割器
        splitter.addWidget(left_panel)
        
        # 右侧面板：聊天区域和输入区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 创建标签页
        self.parent.tab_widget = QTabWidget()
        right_layout.addWidget(self.parent.tab_widget)
        
        # 聊天标签页
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 10)
        
        search_label = QLabel("搜索:")
        search_layout.addWidget(search_label)
        
        self.parent.search_input = QLineEdit()
        self.parent.search_input.setPlaceholderText("输入关键词搜索对话历史...")
        search_layout.addWidget(self.parent.search_input)
        
        self.parent.search_button = QPushButton("搜索")
        self.parent.search_button.clicked.connect(self.parent.search_conversation)
        search_layout.addWidget(self.parent.search_button)
        
        self.parent.clear_search_button = QPushButton("清除搜索")
        self.parent.clear_search_button.clicked.connect(self.parent.clear_search)
        search_layout.addWidget(self.parent.clear_search_button)
        
        chat_layout.addLayout(search_layout)
        
        # 聊天显示区域
        self.parent.chat_display = QTextEdit()
        self.parent.chat_display.setReadOnly(True)
        self.parent.chat_display.setMinimumHeight(400)
        chat_layout.addWidget(self.parent.chat_display)
        
        # 平台选择和状态区域
        platform_layout = QHBoxLayout()
        
        # AI平台选择
        platform_label = QLabel("AI平台:")
        platform_layout.addWidget(platform_label)
        
        self.parent.platform_combo = QComboBox()
        self.parent.platform_combo.currentTextChanged.connect(self.parent.update_platform_config)
        platform_layout.addWidget(self.parent.platform_combo)
        
        # 主题选择
        theme_label = QLabel("主题:")
        platform_layout.addWidget(theme_label)
        
        self.parent.theme_combo = QComboBox()
        # 获取可用主题列表
        themes = self.parent.theme_manager.get_available_themes()
        self.parent.theme_combo.addItems(themes)
        # 设置当前主题
        current_theme = self.parent.settings.get('appearance', {}).get('theme', '默认主题')
        if current_theme in themes:
            self.parent.theme_combo.setCurrentText(current_theme)
        # 连接主题切换信号
        self.parent.theme_combo.currentTextChanged.connect(self.parent.change_theme)
        platform_layout.addWidget(self.parent.theme_combo)
        
        # 状态指示器
        self.parent.status_indicator = QLabel("●")
        self.parent.status_indicator.setStyleSheet("color: #ff0000; font-size: 16px;")
        platform_layout.addWidget(self.parent.status_indicator)
        
        self.parent.status_label = QLabel("未连接")
        platform_layout.addWidget(self.parent.status_label)
        
        platform_layout.addStretch()
        
        chat_layout.addLayout(platform_layout)
        
        # 消息输入区域
        input_layout = QVBoxLayout()
        
        self.parent.message_input = QTextEdit()
        self.parent.message_input.setMinimumHeight(75)
        self.parent.message_input.setMaximumHeight(150)
        self.parent.message_input.setPlaceholderText("输入消息...")
        self.parent.message_input.setFocus()
        self.parent.message_input.setAcceptRichText(False)  # 只接受纯文本
        # 安装事件过滤器，以便捕获键盘事件
        self.parent.message_input.installEventFilter(self.parent)
        # 连接textChanged信号，实现自动调整高度
        self.parent.message_input.textChanged.connect(self.auto_resize_input)
        input_layout.addWidget(self.parent.message_input)
        
        # 输入辅助按钮
        input_buttons = QHBoxLayout()
        
        self.parent.attach_file_btn = QPushButton("附件")
        self.parent.attach_file_btn.clicked.connect(self.parent.attach_file)
        input_buttons.addWidget(self.parent.attach_file_btn)
        
        self.parent.insert_image_btn = QPushButton("图片")
        self.parent.insert_image_btn.clicked.connect(self.parent.insert_image)
        input_buttons.addWidget(self.parent.insert_image_btn)
        
        # 截图按钮
        self.parent.screenshot_btn = QPushButton("截图")
        self.parent.screenshot_btn.clicked.connect(self.parent.take_screenshot)
        input_buttons.addWidget(self.parent.screenshot_btn)
        
        # 快捷回复按钮
        self.parent.quick_reply_btn = QPushButton("快捷回复")
        self.parent.quick_reply_btn.clicked.connect(self.parent.show_quick_replies)
        input_buttons.addWidget(self.parent.quick_reply_btn)
        
        input_buttons.addStretch()
        
        self.parent.clear_input_btn = QPushButton("清空")
        self.parent.clear_input_btn.clicked.connect(self.parent.clear_input)
        input_buttons.addWidget(self.parent.clear_input_btn)
        
        input_layout.addLayout(input_buttons)
        
        # 发送按钮和设置
        send_layout = QHBoxLayout()
        
        self.parent.send_button = QPushButton("发送 (Enter)")
        self.parent.send_button.clicked.connect(self.parent.send_message)
        send_button_font = QFont()
        send_button_font.setBold(True)
        self.parent.send_button.setFont(send_button_font)
        send_layout.addWidget(self.parent.send_button)
        
        # 流式响应开关
        self.parent.streaming_checkbox = QCheckBox("流式响应")
        self.parent.streaming_checkbox.setChecked(self.parent.settings['chat']['streaming'])
        send_layout.addWidget(self.parent.streaming_checkbox)
        
        chat_layout.addLayout(input_layout)
        chat_layout.addLayout(send_layout)
        
        # 添加聊天标签页
        self.parent.tab_widget.addTab(chat_tab, "聊天")
        
        # 调试标签页
        debug_tab = QWidget()
        debug_layout = QVBoxLayout(debug_tab)
        
        self.parent.debug_output = QTextEdit()
        self.parent.debug_output.setReadOnly(True)
        debug_layout.addWidget(self.parent.debug_output)
        
        self.parent.tab_widget.addTab(debug_tab, "调试")
        
        # 添加右侧面板到分割器
        splitter.addWidget(right_panel)
        
        # 设置分割器初始比例
        splitter.setSizes([250, 750])
        
        # 应用主题样式
        self.apply_theme(self.parent.settings['appearance']['theme'])
    
    def create_menu_bar(self) -> None:
        """创建菜单栏"""
        menu_bar = self.parent.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_conversation_action = QAction("新对话", self.parent)
        new_conversation_action.triggered.connect(self.parent.new_conversation)
        file_menu.addAction(new_conversation_action)
        
        save_conversation_action = QAction("保存对话", self.parent)
        save_conversation_action.triggered.connect(self.parent.save_conversation)
        file_menu.addAction(save_conversation_action)
        
        load_conversation_action = QAction("加载对话", self.parent)
        load_conversation_action.triggered.connect(self.parent.load_conversation_from_file)
        file_menu.addAction(load_conversation_action)
        
        file_menu.addSeparator()
        
        export_conversation_action = QAction("导出对话", self.parent)
        export_conversation_action.triggered.connect(self.parent.export_conversation_history)
        file_menu.addAction(export_conversation_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("设置", self.parent)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self.parent)
        exit_action.triggered.connect(self.parent.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menu_bar.addMenu("编辑")
        
        copy_action = QAction("复制", self.parent)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.parent.copy_selected_text)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self.parent)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.parent.paste_text)
        edit_menu.addAction(paste_action)
        
        clear_chat_action = QAction("清除聊天", self.parent)
        clear_chat_action.setShortcut("Ctrl+L")
        clear_chat_action.triggered.connect(self.parent.clear_chat_display)
        edit_menu.addAction(clear_chat_action)
        
        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        
        # 统计报告
        statistics_action = QAction("统计报告...", self.parent)
        statistics_action.triggered.connect(self.show_statistics_dialog)
        settings_menu.addAction(statistics_action)
        
        # 个人信息
        personal_info_action = QAction("个人信息", self.parent)
        personal_info_action.triggered.connect(self.show_personal_info_dialog)
        settings_menu.addAction(personal_info_action)
        
        # 任务管理
        task_management_action = QAction("任务管理", self.parent)
        task_management_action.triggered.connect(self.show_task_management_dialog)
        settings_menu.addAction(task_management_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self.parent)
        about_action.triggered.connect(self.parent.show_about_dialog)
        help_menu.addAction(about_action)
        
        help_action = QAction("帮助文档", self.parent)
        help_action.triggered.connect(self.parent.open_help_dialog)
        help_menu.addAction(help_action)
    
    def apply_theme(self, theme_name: str) -> None:
        """应用主题样式"""
        # 获取自定义主题设置
        custom_theme = self.parent.settings.get('appearance', {}).get('custom_theme', {})
        
        # 获取主题样式表
        stylesheet = self.parent.theme_manager.get_theme_stylesheet(theme_name, custom_theme)
        self.parent.setStyleSheet(stylesheet)
        
        # 更新设置中的主题
        self.parent.settings['appearance']['theme'] = theme_name
        self.parent.settings_manager.update_settings(self.parent.settings)
        
        # 更新UI组件样式
        self.update_ui_components()
        
        # 刷新聊天显示以应用新主题
        self.parent.refresh_chat_display()
    
    def update_ui_components(self) -> None:
        """更新UI组件样式"""
        # 可以在这里添加特定组件的样式更新
        pass
    
    def show_settings_dialog(self) -> None:
        """显示设置对话框"""
        dialog = SettingsDialog(self.parent)
        dialog.exec()
    
    def show_statistics_dialog(self) -> None:
        """显示统计报告对话框"""
        dialog = StatisticsDialog(self.parent)
        dialog.exec()
    
    def show_personal_info_dialog(self) -> None:
        """显示个人信息对话框"""
        dialog = PersonalInfoDialog(self.parent)
        dialog.exec()
    
    def show_task_management_dialog(self) -> None:
        """显示任务管理对话框"""
        dialog = TaskManagementDialog(self.parent)
        dialog.exec()
    
    def display_message(self, sender: str, content: str) -> None:
        """在聊天窗口中显示消息，优化样式和交互"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 获取当前主题
        current_theme = self.parent.settings.get('appearance', {}).get('theme', '默认主题')
        custom_theme = self.parent.settings.get('appearance', {}).get('custom_theme', {})
        
        # 获取消息样式
        message_style_data = self.parent.theme_manager.get_message_style(sender, current_theme, custom_theme)
        sender_name = message_style_data['sender_name']
        message_style = message_style_data['message_style']
        name_color = message_style_data['name_color']
        
        # 根据设置决定是否显示时间戳
        show_timestamp = self.parent.settings.get('chat', {}).get('show_timestamp', True)
        timestamp_text = f" ({timestamp})" if show_timestamp else ""
        
        # 生成唯一ID
        message_id = f"{time.time()}-{id(content)}"
        
        # 构建消息HTML
        message_html = f"<div class='message-container' style='display: flex; flex-direction: column; margin: 5px 0;' id='message_{message_id}'>"
        
        # 消息内容
        if sender == "用户":
            message_html += f"<div class='user-message' {message_style}><strong style='color: {name_color};'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px; color: {message_style_data['content_color']};'>{content}</div>"
        else:
            message_html += f"<div class='ai-message' {message_style}><strong style='color: {name_color};'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px; color: {message_style_data['content_color']};'>{content}</div>"
        

        
        message_html += "</div></div><div style='clear: both;'></div>"
        
        # 显示消息
        self.parent.chat_display.append(message_html)
        
        # 自动滚动到底部
        if self.parent.settings['chat']['auto_scroll']:
            self.parent.chat_display.verticalScrollBar().setValue(self.parent.chat_display.verticalScrollBar().maximum())
        
        # 生成唯一ID
        message_id = f"{time.time()}-{id(content)}"
        
        # 更新对话历史
        self.parent.conversation_history.append({
            'id': message_id,  # 添加唯一ID
            'sender': sender,
            'content': content,
            'timestamp': timestamp,  # 添加timestamp字段
            'created_at': timestamp,  # 保持向后兼容
            'response_time': None  # 添加response_time字段
        })
        
        # 触发自动保存
        self.parent.chat_core.schedule_auto_save()
        
        # 更新统计
        self.parent.stats_manager.update_conversation_history(self.parent.conversation_history)
    
    def auto_resize_input(self) -> None:
        """自动调整输入框高度，根据内容多少动态调整"""
        # 计算文本内容的高度
        text_height = self.parent.message_input.document().size().height()
        # 确保高度在合理范围内
        min_height = 75
        max_height = 150
        new_height = min(max_height, max(min_height, text_height + 10))
        # 设置新高度
        self.parent.message_input.setFixedHeight(int(new_height))
    
    def update_platform_config(self, platform_name: str) -> None:
        """更新平台配置"""
        if platform_name in self.parent.platforms:
            self.parent.current_platform = platform_name
            self.parent.current_platform_config = self.parent.platforms[platform_name]
            self.parent.status_label.setText(f"已连接到 {platform_name}")
            self.parent.status_indicator.setStyleSheet("color: #00ff00; font-size: 16px;")
        else:
            self.parent.status_label.setText("平台配置错误")
            self.parent.status_indicator.setStyleSheet("color: #ff0000; font-size: 16px;")
