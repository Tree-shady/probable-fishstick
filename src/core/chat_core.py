import os
import time
import asyncio
import aiofiles
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEventLoop
from PyQt6.QtWidgets import QMessageBox, QFileDialog

from ..utils.helpers import load_json_file, save_json_file
from ..utils.async_helpers import AsyncFileManager
from .api import ApiCallThread

class ChatCore:
    """聊天核心功能类"""
    
    def __init__(self, parent):
        self.parent = parent
        self.conversation_history: List[Dict[str, Any]] = []
        self.conversation_file = os.path.join(os.getcwd(), "conversation_history.json")
        self.auto_save_timer: Optional[QTimer] = None  # 自动保存定时器
        self.auto_save_delay = 5000  # 自动保存延迟（毫秒）
        
        # 流式响应状态
        self.streaming_response_text = ""
        self.streaming_response_active = False
        self.current_ai_message_timestamp = None
        self.current_ai_message_prefix = ""
        self.streaming_buffer = ""  # 流式响应缓冲区
        self.streaming_update_timer: Optional[QTimer] = None  # 流式更新定时器
        
        # 响应时间记录
        self.message_start_time: Optional[float] = None
        self.response_times: List[float] = []
    
    def send_message(self, message: str) -> None:
        """发送消息"""
        if not message:
            return
        
        # 记录发送时间
        self.message_start_time = time.time()
        
        # 重置流式响应状态
        self.streaming_response_active = False
        self.streaming_response_text = ""
        self.streaming_buffer = ""
        
        # 显示用户消息
        self.parent.display_message("用户", message)
        
        # 发送消息到AI
        self.send_to_ai(message)
    
    def send_to_ai(self, message: str) -> None:
        """发送消息到AI"""
        # 获取当前平台配置
        platform_config = self.parent.platforms.get(self.parent.current_platform, {})
        if not platform_config:
            self.parent.add_debug_info("未找到当前平台配置", "ERROR")
            return
        
        # 检查API密钥
        api_key = platform_config.get('api_key', '')
        if not api_key:
            self.parent.add_debug_info("API密钥未设置", "ERROR")
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
        is_streaming = self.parent.streaming_checkbox.isChecked()
        
        # 获取响应速度设置
        response_speed = self.parent.settings.get('chat', {}).get('response_speed', 5)
        # 获取SSL验证设置
        verify_ssl = self.parent.settings.get('network', {}).get('verify_ssl', False)
        
        # 创建API调用线程
        self.parent.api_thread = ApiCallThread(api_url, api_key, model, message, is_streaming, response_speed, verify_ssl)
        
        # 连接信号
        self.parent.api_thread.streaming_content.connect(self.parent.append_streaming_response)
        self.parent.api_thread.streaming_finished.connect(self.parent.streaming_response_ended)
        self.parent.api_thread.non_streaming_response.connect(self.parent._handle_non_streaming_response)
        self.parent.api_thread.api_error.connect(self.parent._handle_api_error)
        self.parent.api_thread.debug_info.connect(self.parent.add_debug_info)
        
        # 启动线程
        self.parent.api_thread.start()
    
    def schedule_auto_save(self) -> None:
        """安排自动保存"""
        if self.auto_save_timer:
            self.auto_save_timer.stop()
        
        self.auto_save_timer = QTimer(self.parent)
        self.auto_save_timer.timeout.connect(self.auto_save_conversation)
        self.auto_save_timer.start(self.auto_save_delay)
    
    def auto_save_conversation(self) -> None:
        """自动保存对话历史"""
        if self.parent.settings['chat']['auto_save']:
            self.save_conversation()
    
    def save_conversation(self) -> None:
        """保存对话历史"""
        # 使用异步文件IO保存对话历史，避免阻塞UI线程
        async def async_save():
            await AsyncFileManager.async_save_json_file(self.conversation_file, self.parent.conversation_history)
        
        # 使用线程池执行异步保存，避免阻塞UI线程
        asyncio.run_coroutine_threadsafe(async_save(), asyncio.get_event_loop())
    
    def load_conversation(self) -> None:
        """加载对话历史，确保每条消息都包含所有必需的字段"""
        # 使用异步文件IO加载对话历史，避免阻塞UI线程
        async def async_load():
            history = await AsyncFileManager.async_load_json_file(self.conversation_file, [])
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
            self.parent.conversation_history = history
        
        # 使用线程池执行异步加载，避免阻塞UI线程
        asyncio.run_coroutine_threadsafe(async_load(), asyncio.get_event_loop())
    
    def load_conversation_from_file(self, file_path: str) -> None:
        """从文件加载对话历史，确保每条消息都包含所有必需的字段"""
        # 使用异步文件IO加载对话历史，避免阻塞UI线程
        async def async_load():
            history = await AsyncFileManager.async_load_json_file(file_path, [])
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
            self.parent.conversation_history = history
            # 刷新聊天显示，确保在UI线程中执行
            self.parent.refresh_chat_display()
        
        # 使用线程池执行异步加载，避免阻塞UI线程
        asyncio.run_coroutine_threadsafe(async_load(), asyncio.get_event_loop())
    
    def refresh_chat_display(self) -> None:
        """刷新聊天显示，使用优化的消息样式和批量加载"""
        self.parent.chat_display.clear()
        
        # 获取当前主题和自定义主题设置
        current_theme = self.parent.settings.get('appearance', {}).get('theme', '默认主题')
        custom_theme = self.parent.settings.get('appearance', {}).get('custom_theme', {})
        show_timestamp = self.parent.settings.get('chat', {}).get('show_timestamp', True)
        
        # 批量构建HTML内容，减少UI更新次数
        html_content = []
        for entry in self.parent.conversation_history:
            sender = entry['sender']
            content = entry['content']
            created_at = entry['created_at']
            
            # 获取消息样式
            message_style_data = self.parent.theme_manager.get_message_style(sender, current_theme, custom_theme)
            sender_name = message_style_data['sender_name']
            message_style = message_style_data['message_style']
            name_color = message_style_data['name_color']
            content_color = message_style_data['content_color']
            
            timestamp_text = f" ({created_at})" if show_timestamp else ""
            
            # 构建消息HTML
            message_html = f"<div class='message-container' style='display: flex; flex-direction: column; margin: 5px 0;'>"
            if sender == "用户":
                message_html += f"<div class='user-message' {message_style}><strong style='color: {name_color};'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px; color: {content_color};'>{content}</div></div>"
            else:
                message_html += f"<div class='ai-message' {message_style}><strong style='color: {name_color};'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px; color: {content_color};'>{content}</div></div>"
            message_html += "</div><div style='clear: both;'></div>"
            
            html_content.append(message_html)
        
        # 一次性设置HTML内容，减少UI更新次数
        self.parent.chat_display.setHtml(''.join(html_content))
        
        # 自动滚动到底部
        if self.parent.settings['chat']['auto_scroll']:
            self.parent.chat_display.verticalScrollBar().setValue(self.parent.chat_display.verticalScrollBar().maximum())
    
    def clear_conversation_history(self) -> None:
        """清除对话历史"""
        reply = QMessageBox.question(self.parent, "确认清除", "确定要清除所有对话历史吗？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.parent.conversation_history = []
            self.parent.chat_display.clear()
            self.save_conversation()
    
    def search_conversation(self, search_text: str) -> list:
        """搜索对话历史
        
        Args:
            search_text: 搜索关键词
            
        Returns:
            list: 包含搜索结果的对话历史列表
        """
        if not search_text:
            return []
        
        search_results = []
        for message in self.parent.conversation_history:
            content = message.get('content', '')
            if search_text.lower() in content.lower():
                search_results.append(message)
        
        return search_results
    
    def export_conversation_history(self) -> None:
        """导出对话历史"""
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "导出对话历史", ".", "JSON Files (*.json);;Text Files (*.txt)")
        if file_path:
            # 使用异步文件IO导出对话历史，避免阻塞UI线程
            async def async_export():
                success = False
                try:
                    if file_path.endswith('.json'):
                        success = await AsyncFileManager.async_save_json_file(file_path, self.parent.conversation_history)
                    else:
                        # 异步写入文本文件
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                            for entry in self.parent.conversation_history:
                                await f.write(f"{entry['sender']} ({entry['created_at']}):\n{entry['content']}\n\n")
                        success = True
                except Exception as e:
                    print(f"导出对话历史失败: {str(e)}")
                    success = False
                
                # 显示结果消息，确保在UI线程中执行
                if success:
                    self.parent.show_message("成功", "对话历史已成功导出！")
                else:
                    self.parent.show_message("错误", "导出对话历史失败！", is_error=True)
            
            # 使用线程池执行异步导出，避免阻塞UI线程
            asyncio.run_coroutine_threadsafe(async_export(), asyncio.get_event_loop())
    
    def append_streaming_response(self, text: str) -> None:
        """追加流式响应到聊天窗口"""
        self.streaming_buffer += text
        
        # 如果没有启动定时器，创建一个
        if not self.streaming_update_timer:
            self.streaming_update_timer = QTimer(self.parent)
            self.streaming_update_timer.timeout.connect(self.flush_streaming_buffer)
            self.streaming_update_timer.start(100)  # 每100毫秒更新一次UI
    
    def flush_streaming_buffer(self) -> None:
        """刷新流式响应缓冲区，更新UI"""
        if self.streaming_buffer and self.parent.chat_display:
            # 确保chat_display对象存在
            if not self.streaming_response_active:
                # 首次更新时，添加AI消息前缀
                self.streaming_response_active = True
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.current_ai_message_timestamp = timestamp
                
                # 获取当前主题
                current_theme = self.parent.settings.get('appearance', {}).get('theme', '默认主题')
                custom_theme = self.parent.settings.get('appearance', {}).get('custom_theme', {})
                
                # 获取消息样式
                message_style_data = self.parent.theme_manager.get_message_style('AI', current_theme, custom_theme)
                sender_name = message_style_data['sender_name']
                message_style = message_style_data['message_style']
                name_color = message_style_data['name_color']
                
                # 显示时间戳设置
                show_timestamp = self.parent.settings.get('chat', {}).get('show_timestamp', True)
                timestamp_text = f" ({timestamp})" if show_timestamp else ""
                
                # 显示AI消息前缀
                message_prefix = f"<div class='message-container' style='display: flex; flex-direction: column; margin: 5px 0;'><div class='ai-message' {message_style}><strong style='color: {name_color};'>{sender_name}{timestamp_text}:</strong><br><div style='word-wrap: break-word; margin-top: 5px; color: {message_style_data['content_color']};'>"
                self.parent.chat_display.append(message_prefix)
            
            # 实时显示响应内容
            self.parent.chat_display.insertPlainText(self.streaming_buffer)
            
            # 更新响应文本
            self.streaming_response_text += self.streaming_buffer
            self.streaming_buffer = ""
            
            # 自动滚动到底部
            if self.parent.settings['chat']['auto_scroll']:
                self.parent.chat_display.verticalScrollBar().setValue(self.parent.chat_display.verticalScrollBar().maximum())
    
    def streaming_response_ended(self) -> None:
        """流式响应结束处理"""
        # 停止定时器
        if self.streaming_update_timer:
            self.streaming_update_timer.stop()
            self.streaming_update_timer = None
        
        # 确保缓冲区中的内容都被处理
        self.flush_streaming_buffer()
        
        # 完成AI消息
        if self.streaming_response_active:
            self.streaming_response_active = False
            
            # 关闭HTML标签
            if self.parent.chat_display:
                self.parent.chat_display.append("</div></div><div style='clear: both;'></div>")
                
                # 自动滚动到底部
                if self.parent.settings['chat']['auto_scroll']:
                    self.parent.chat_display.verticalScrollBar().setValue(self.parent.chat_display.verticalScrollBar().maximum())
            
            # 计算响应时间
            if self.message_start_time:
                response_time = time.time() - self.message_start_time
                self.response_times.append(response_time)
            else:
                response_time = 0
            
            # 直接更新对话历史，不通过display_message方法，避免重复
            self.parent.conversation_history.append({
                'id': f"{time.time()}-{id(self.streaming_response_text)}",
                'sender': 'AI',
                'content': self.streaming_response_text,
                'timestamp': self.current_ai_message_timestamp,
                'created_at': self.current_ai_message_timestamp,
                'response_time': response_time
            })
            
            # 触发自动保存
            self.schedule_auto_save()
            
            # 更新统计
            self.parent.stats_manager.update_conversation_history(self.parent.conversation_history)
            
            # 检查是否需要在AI回答后自动同步数据库
            if hasattr(self.parent, 'settings') and self.parent.settings['database']['enabled'] and self.parent.settings['database']['sync_after_ai_response']:
                # 启用自动同步后，暂时休眠自动上传功能
                if not hasattr(self.parent, 'auto_upload_paused'):
                    self.parent.auto_upload_paused = True
                else:
                    self.parent.auto_upload_paused = True
                # 立即同步数据库
                if hasattr(self.parent, 'sync_database_now'):
                    self.parent.sync_database_now()
            
            # 重置流式响应状态
            self.streaming_response_text = ""
            self.current_ai_message_timestamp = None
