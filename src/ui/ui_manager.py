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
        self.parent.debug_display = QTextEdit()
        self.parent.debug_display.setReadOnly(True)
        left_layout.addWidget(self.parent.debug_display)
        
        # 调试操作按钮
        debug_buttons = QHBoxLayout()
        
        clear_debug_btn = QPushButton("清除调试")
        clear_debug_btn.clicked.connect(self.parent.clear_debug_info)
        debug_buttons.addWidget(clear_debug_btn)
        
        export_debug_btn = QPushButton("导出调试")
        export_debug_btn.clicked.connect(self.parent.export_debug_info)
        debug_buttons.addWidget(export_debug_btn)
        
        left_layout.addLayout(debug_buttons)
        
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
        
        left_layout.addLayout(db_buttons)
        
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
        
        # 聊天显示区域
        self.parent.chat_display = QTextEdit()
        self.parent.chat_display.setReadOnly(True)
        self.parent.chat_display.setMinimumHeight(400)
        chat_layout.addWidget(self.parent.chat_display)
        
        # 平台选择和状态区域
        platform_layout = QHBoxLayout()
        
        platform_label = QLabel("AI平台:")
        platform_layout.addWidget(platform_label)
        
        self.parent.platform_combo = QComboBox()
        self.parent.platform_combo.currentTextChanged.connect(self.parent.update_platform_config)
        platform_layout.addWidget(self.parent.platform_combo)
        
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
        stylesheet = self.parent.theme_manager.get_theme_stylesheet(theme_name)
        self.parent.setStyleSheet(stylesheet)
        
        # 更新设置中的主题
        self.parent.settings['appearance']['theme'] = theme_name
        self.parent.settings_manager.update_settings(self.parent.settings)
        
        # 更新UI组件样式
        self.update_ui_components()
    
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
        
        # 用户和AI消息有不同的样式区分，取消白底
        if sender == "用户":
            sender_name = "你"
            message_style = """style='margin: 10px 0; padding: 10px; border-radius: 10px; max-width: 70%; align-self: flex-end; text-align: right; float: right;'"""
        else:
            sender_name = "AI"
            message_style = """style='margin: 10px 0; padding: 10px; border-radius: 10px; max-width: 70%; align-self: flex-start; text-align: left;'"""
        
        # 根据设置决定是否显示时间戳
        show_timestamp = self.parent.settings.get('chat', {}).get('show_timestamp', True)
        timestamp_text = f" ({timestamp})" if show_timestamp else ""
        
        # 构建消息HTML
        message_html = "<div class='message-container' style='display: flex; flex-direction: column; margin: 5px 0;'>"
        if sender == "用户":
            message_html += f"<div class='user-message' {message_style}><strong style='color: #1976d2;'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px;'>{content}</div></div>"
        else:
            message_html += f"<div class='ai-message' {message_style}><strong style='color: #4caf50;'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px;'>{content}</div></div>"
        message_html += "</div><div style='clear: both;'></div>"
        
        # 显示消息
        self.parent.chat_display.append(message_html)
        
        # 自动滚动到底部
        if self.parent.settings['chat']['auto_scroll']:
            self.parent.chat_display.verticalScrollBar().setValue(self.parent.chat_display.verticalScrollBar().maximum())
        
        # 更新对话历史
        self.parent.conversation_history.append({
            'id': f"{time.time()}-{id(content)}",  # 添加唯一ID
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
