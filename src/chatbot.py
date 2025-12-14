import os
import sys
import time
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from .core.chat_core import ChatCore
from .ui.ui_manager import UIManager
from .data.settings import SettingsManager
from .data.database import DatabaseManager
from .data.statistics import StatisticsManager
from .data.memory import MemoryManager
from .utils.network import NetworkMonitor
from .utils.helpers import load_json_file, save_json_file, get_current_timestamp

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
        
        # 初始化设置管理器
        self.settings_manager = SettingsManager(self.config_file)
        self.settings = self.settings_manager.settings
        self.platforms = self.settings_manager.platforms
        
        # 初始化对话历史
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_platform: str = ""
        self.current_platform_config: Dict[str, Any] = {}
        
        # 初始化主题管理器
        self.theme_manager = self._init_theme_manager()
        
        # 初始化统计管理器
        self.stats_manager = StatisticsManager()
        
        # 初始化数据库管理器
        self.db_manager = None
        
        # 初始化网络监控
        self.network_monitor = NetworkMonitor(self)
        self.network_monitor.start_monitoring()
        
        # 初始化记忆管理器
        self.memories_dir = os.path.join(os.getcwd(), "memories")
        self.memory_manager = MemoryManager(self, self.memories_dir)
        
        # 初始化UI
        self.ui_manager = UIManager(self)
        
        # 初始化聊天核心
        self.chat_core = ChatCore(self)
        
        # 连接信号槽
        self.update_streaming_response.connect(self.append_streaming_response)
        self.streaming_response_finished.connect(self.streaming_response_ended)
        
        # 初始化配置文件监控
        self.setup_config_monitoring()
        
        # 初始化定期同步定时器
        self.setup_sync_timer()
        
        # 初始化平台下拉框
        available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
        self.platform_combo.clear()
        self.platform_combo.addItems(available_platforms)
        if available_platforms:
            self.current_platform = available_platforms[0]
            self.current_platform_config = self.platforms[available_platforms[0]]
            self.platform_combo.setCurrentText(available_platforms[0])
        
        # 加载对话历史
        self.load_conversation()
        
        # 更新统计管理器的对话历史
        self.stats_manager.update_conversation_history(self.conversation_history)
        
        # 延迟初始化数据库，在主窗口显示后再尝试
        QTimer.singleShot(2000, self.delayed_init_db)
    
    def _init_theme_manager(self):
        """初始化主题管理器"""
        # 简单的主题管理器实现
        class SimpleThemeManager:
            def get_available_themes(self):
                return ["默认主题", "深色主题", "浅色主题"]
            
            def get_theme_stylesheet(self, theme_name):
                if theme_name == "深色主题":
                    return """QMainWindow { background-color: #2b2b2b; color: #ffffff; }"""
                elif theme_name == "浅色主题":
                    return """QMainWindow { background-color: #ffffff; color: #000000; }"""
                else:
                    return ""
        return SimpleThemeManager()
    
    def delayed_init_db(self):
        """延迟初始化数据库"""
        try:
            # 不强制禁用数据库功能，使用用户配置的状态
            # 初始化数据库管理器
            self.db_manager = DatabaseManager(self, self.settings)
            # 不自动连接，让用户手动测试连接
            self.add_debug_info("数据库管理器已初始化，等待用户手动连接", "INFO")
        except Exception as e:
            self.add_debug_info(f"延迟初始化数据库失败: {str(e)}", "ERROR")
    
    def setup_config_monitoring(self):
        """设置配置文件监控"""
        # 配置监控功能可以在这里实现
        pass
    
    def setup_sync_timer(self):
        """设置定期同步定时器"""
        # 同步定时器功能已集成到database.py模块中
        pass
    
    def display_message(self, sender: str, content: str) -> None:
        """在聊天窗口中显示消息"""
        self.ui_manager.display_message(sender, content)
    
    def update_platform_config(self, platform_name: str) -> None:
        """更新平台配置"""
        self.ui_manager.update_platform_config(platform_name)
    
    def send_message(self):
        """发送消息"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        self.chat_core.send_message(message)
        # 发送消息后清空输入框
        self.clear_input()
    
    def send_to_ai(self, message: str):
        """发送消息到AI"""
        self.chat_core.send_to_ai(message)
    
    def append_streaming_response(self, text: str):
        """追加流式响应到聊天窗口"""
        self.chat_core.append_streaming_response(text)
    
    def streaming_response_ended(self):
        """流式响应结束处理"""
        self.chat_core.streaming_response_ended()
    
    def flush_streaming_buffer(self):
        """刷新流式响应缓冲区，更新UI"""
        self.chat_core.flush_streaming_buffer()
    
    def load_conversation(self):
        """加载对话历史，确保每条消息都包含所有必需的字段"""
        conversation_file = os.path.join(os.getcwd(), "conversation_history.json")
        history = load_json_file(conversation_file, [])
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
    
    def save_conversation(self):
        """保存对话历史"""
        conversation_file = os.path.join(os.getcwd(), "conversation_history.json")
        save_json_file(conversation_file, self.conversation_history)
    
    def load_conversation_from_file(self):
        """从文件加载对话历史"""
        file_path, _ = QFileDialog.getOpenFileName(self, "加载对话历史", ".", "JSON Files (*.json)")
        if file_path:
            self.chat_core.load_conversation_from_file(file_path)
    
    def refresh_chat_display(self):
        """刷新聊天显示"""
        self.chat_core.refresh_chat_display()
    
    def new_conversation(self):
        """开始新对话"""
        reply = QMessageBox.question(self, "确认新对话", "确定要开始新对话吗？当前对话历史将被保存。",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 保存当前对话历史
            self.save_conversation()
            # 清空对话历史和聊天显示
            self.conversation_history = []
            self.chat_display.clear()
    
    def clear_chat_display(self):
        """清空聊天显示"""
        self.chat_display.clear()
    
    def clear_input(self):
        """清空输入框"""
        self.message_input.clear()
    
    def search_conversation(self):
        """搜索对话历史"""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.information(self, "提示", "请输入搜索关键词")
            return
        
        # 执行搜索
        search_results = self.chat_core.search_conversation(search_text)
        
        # 显示搜索结果
        if search_results:
            self.display_search_results(search_results, search_text)
        else:
            QMessageBox.information(self, "搜索结果", f"未找到包含 '{search_text}' 的消息")
    
    def clear_search(self):
        """清除搜索结果，恢复显示全部对话"""
        self.search_input.clear()
        self.chat_core.refresh_chat_display()
    
    def display_search_results(self, results, search_text):
        """显示搜索结果"""
        self.chat_display.clear()
        
        # 显示搜索提示
        search_info = f"<div style='text-align: center; margin: 10px 0; font-style: italic; color: #666;'>"
        search_info += f"搜索结果: 找到 {len(results)} 条包含 '{search_text}' 的消息</div><br>"
        self.chat_display.append(search_info)
        
        # 显示搜索结果
        for entry in results:
            sender = entry['sender']
            content = entry['content']
            created_at = entry['created_at']
            
            # 高亮搜索关键词
            highlighted_content = content.replace(search_text, f"<span style='background-color: #ffff00; color: #000;'>{search_text}</span>")
            
            # 用户和AI消息有不同的样式区分
            if sender == "用户":
                sender_name = "你"
                message_style = """style='margin: 10px 0; padding: 10px; border-radius: 10px; max-width: 70%; align-self: flex-end; text-align: right; float: right;'"""
            else:
                sender_name = "AI"
                message_style = """style='margin: 10px 0; padding: 10px; border-radius: 10px; max-width: 70%; align-self: flex-start; text-align: left;'"""
            
            # 根据设置决定是否显示时间戳
            show_timestamp = self.settings.get('chat', {}).get('show_timestamp', True)
            timestamp_text = f" ({created_at})" if show_timestamp else ""
            
            # 构建消息HTML
            message_html = f"<div class='message-container' style='display: flex; flex-direction: column; margin: 5px 0;'>"
            if sender == "用户":
                message_html += f"<div class='user-message' {message_style}><strong style='color: #1976d2;'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px;'>{highlighted_content}</div></div>"
            else:
                message_html += f"<div class='ai-message' {message_style}><strong style='color: #4caf50;'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px;'>{highlighted_content}</div></div>"
            message_html += "</div><div style='clear: both;'></div>"
            
            # 显示消息
            self.chat_display.append(message_html)
    
    def copy_selected_text(self):
        """复制选中的文本"""
        self.chat_display.copy()
    
    def paste_text(self):
        """粘贴文本到输入框"""
        self.message_input.paste()
    
    def edit_message(self, message_id):
        """编辑消息"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QMessageBox
        
        # 查找要编辑的消息
        message_index = -1
        for i, message in enumerate(self.conversation_history):
            if message['id'] == message_id:
                message_index = i
                break
        
        if message_index == -1:
            QMessageBox.warning(self, "错误", "未找到要编辑的消息")
            return
        
        message = self.conversation_history[message_index]
        
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑消息")
        dialog.resize(500, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 消息编辑框
        edit_text = QTextEdit()
        edit_text.setPlainText(message['content'])
        layout.addWidget(edit_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self._save_edited_message(dialog, message_index, edit_text.toPlainText()))
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _save_edited_message(self, dialog, message_index, new_content):
        """保存编辑后的消息"""
        if not new_content.strip():
            QMessageBox.warning(self, "提示", "消息内容不能为空")
            return
        
        # 更新消息内容
        self.conversation_history[message_index]['content'] = new_content.strip()
        
        # 保存到文件
        self.save_conversation()
        
        # 刷新聊天显示
        self.chat_core.refresh_chat_display()
        
        QMessageBox.information(self, "成功", "消息已成功编辑")
        dialog.close()
    
    def delete_message(self, message_id):
        """删除消息"""
        from PyQt6.QtWidgets import QMessageBox
        
        # 查找要删除的消息
        message_index = -1
        for i, message in enumerate(self.conversation_history):
            if message['id'] == message_id:
                message_index = i
                break
        
        if message_index == -1:
            QMessageBox.warning(self, "错误", "未找到要删除的消息")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", "确定要删除这条消息吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 删除消息
        del self.conversation_history[message_index]
        
        # 保存到文件
        self.save_conversation()
        
        # 刷新聊天显示
        self.chat_core.refresh_chat_display()
        
        QMessageBox.information(self, "成功", "消息已成功删除")
    
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
    
    def toggle_database_enabled(self):
        """切换数据库启用状态"""
        self.settings['database']['enabled'] = not self.settings['database']['enabled']
        self.settings_manager.update_settings(self.settings)
        self.enable_db_btn.setText("禁用数据库" if self.settings['database']['enabled'] else "启用数据库")
    
    def load_quick_replies(self):
        """加载快捷回复列表"""
        # 默认快捷回复
        default_replies = [
            "你好，能帮我解答一个问题吗？",
            "请详细解释一下这个概念。",
            "可以提供更多相关信息吗？",
            "这个问题的解决方案是什么？",
            "感谢你的帮助！",
            "请举个例子说明。",
            "我不太明白，能再解释一遍吗？",
            "这个功能是如何工作的？"
        ]
        
        # 从设置中加载快捷回复，如果没有则使用默认值
        if 'quick_replies' not in self.settings:
            self.settings['quick_replies'] = default_replies
            self.settings_manager.update_settings(self.settings)
        
        return self.settings['quick_replies']
    
    def show_quick_replies(self):
        """显示快捷回复菜单"""
        from PyQt6.QtWidgets import QMenu, QAction
        
        quick_replies = self.load_quick_replies()
        
        # 创建快捷回复菜单
        menu = QMenu("快捷回复", self)
        
        # 添加快捷回复选项
        for reply in quick_replies:
            action = QAction(reply, self)
            action.triggered.connect(lambda checked, r=reply: self.use_quick_reply(r))
            menu.addAction(action)
        
        # 添加编辑快捷回复选项
        menu.addSeparator()
        edit_action = QAction("编辑快捷回复", self)
        edit_action.triggered.connect(self.edit_quick_replies)
        menu.addAction(edit_action)
        
        # 显示菜单
        menu.exec(self.quick_reply_btn.mapToGlobal(self.quick_reply_btn.rect().bottomLeft()))
    
    def use_quick_reply(self, reply_text):
        """使用快捷回复"""
        self.message_input.setPlainText(reply_text)
        self.message_input.setFocus()
    
    def take_screenshot(self):
        """截图功能"""
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtGui import QScreen, QPixmap
        import os
        import time
        
        try:
            # 获取屏幕截图
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0)  # 0表示整个屏幕
            
            # 生成截图文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_dir = os.path.join(os.getcwd(), "screenshots")
            
            # 创建截图目录
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # 保存截图
            screenshot_path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
            pixmap.save(screenshot_path)
            
            # 将截图路径添加到输入框
            self.message_input.append(f"[截图: {os.path.basename(screenshot_path)}]\n{screenshot_path}")
            
            self.add_debug_info(f"截图已保存: {screenshot_path}", "INFO")
        except Exception as e:
            self.add_debug_info(f"截图失败: {str(e)}", "ERROR")
            QMessageBox.critical(self, "错误", f"截图失败: {str(e)}")
    
    def edit_quick_replies(self):
        """编辑快捷回复列表"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QMessageBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑快捷回复")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 快捷回复列表
        reply_list = QListWidget()
        reply_list.addItems(self.load_quick_replies())
        layout.addWidget(reply_list)
        
        # 输入框
        input_layout = QHBoxLayout()
        new_reply_input = QLineEdit()
        new_reply_input.setPlaceholderText("输入新的快捷回复...")
        input_layout.addWidget(new_reply_input)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(lambda: self._add_quick_reply(new_reply_input, reply_list))
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(lambda: self._remove_quick_reply(reply_list))
        button_layout.addWidget(remove_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self._save_quick_replies(dialog, reply_list))
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.close)
        button_layout.addWidget(cancel_btn)
        
        input_layout.addLayout(button_layout)
        layout.addLayout(input_layout)
        
        dialog.exec()
    
    def _add_quick_reply(self, input_field, reply_list):
        """添加快捷回复"""
        new_reply = input_field.text().strip()
        if new_reply:
            reply_list.addItem(new_reply)
            input_field.clear()
    
    def _remove_quick_reply(self, reply_list):
        """删除选中的快捷回复"""
        selected_items = reply_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请选择要删除的快捷回复")
            return
        
        for item in selected_items:
            reply_list.takeItem(reply_list.row(item))
    
    def _save_quick_replies(self, dialog, reply_list):
        """保存快捷回复列表"""
        quick_replies = [reply_list.item(i).text() for i in range(reply_list.count())]
        self.settings['quick_replies'] = quick_replies
        self.settings_manager.update_settings(self.settings)
        QMessageBox.information(self, "成功", "快捷回复已保存")
        dialog.close()
    
    def connect_database(self):
        """连接数据库"""
        if self.db_manager:
            if self.db_manager.connect():
                self.add_debug_info("数据库连接成功", "INFO")
            else:
                self.add_debug_info("数据库连接失败", "ERROR")
    
    def sync_database_now(self):
        """立即同步数据库"""
        if self.db_manager:
            self.db_manager.sync_all()
    
    def export_statistics(self, file_path: Optional[str] = None):
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
    
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.information(self, "关于", "多功能AI聊天助手\n版本: 1.0.0\n基于PyQt6开发")
    
    def open_help_dialog(self):
        """打开帮助文档"""
        QMessageBox.information(self, "帮助", "这是一个多功能AI聊天助手，支持多种AI平台和功能。\n\n主要功能:\n- 支持多种AI平台\n- 流式响应\n- 对话历史保存\n- 统计报告\n- 个人信息管理\n- 任务管理\n- 数据库同步")
    
    def add_debug_info(self, info: str, level: str = "INFO"):
        """添加调试信息"""
        timestamp = get_current_timestamp()
        debug_text = f"[{timestamp}] [{level}] {info}\n"
        self.debug_display.append(debug_text)
        self.debug_output.append(debug_text)
    
    def clear_debug_info(self):
        """清除调试信息"""
        self.debug_display.clear()
    
    def export_debug_info(self):
        """导出调试信息"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出调试信息", ".", "Text Files (*.txt)")
        if file_path:
            debug_text = self.debug_display.toPlainText()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(debug_text)
            QMessageBox.information(self, "成功", "调试信息已成功导出！")
    
    def export_conversation_history(self):
        """导出对话历史"""
        self.chat_core.export_conversation_history()
    
    def _handle_non_streaming_response(self, response: str):
        """处理非流式API响应"""
        self.display_message("AI", response)
        
        # 检查是否需要在AI回答后自动同步数据库
        if self.settings['database']['enabled'] and self.settings['database']['sync_after_ai_response']:
            # 启用自动同步后，暂时休眠自动上传功能
            self.auto_upload_paused = True
            # 立即同步数据库
            self.sync_database_now()
    
    def _handle_api_error(self, error_msg: str):
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
    
    # 记忆管理相关方法
    def load_personal_info(self):
        """加载个人信息"""
        return self.memory_manager.load_personal_info()
    
    def save_personal_info(self, personal_info):
        """保存个人信息"""
        return self.memory_manager.save_personal_info(personal_info)
    
    def load_task_records(self):
        """加载任务记录"""
        return self.memory_manager.load_task_records()
    
    def save_task_records(self, task_records):
        """保存任务记录"""
        return self.memory_manager.save_task_records(task_records)
    
    def get_current_timestamp(self):
        """获取当前时间戳"""
        return get_current_timestamp()
    
    def show_message(self, title: str, message: str, is_error: bool = False):
        """在UI线程中显示消息框"""
        if is_error:
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
