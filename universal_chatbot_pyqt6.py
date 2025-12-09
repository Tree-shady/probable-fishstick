import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox,
    QListWidget, QSplitter, QMenuBar, QMenu, QGroupBox, QScrollArea,
    QFormLayout, QMessageBox, QFileDialog, QStatusBar, QToolBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QDateTime, QObject
from PyQt6.QtGui import QFont, QIcon, QColor, QTextCursor, QAction

# 导入watchdog库用于监控配置文件变化
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import requests
import time
import os
import random
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import uuid
import re
import socket
import platform
import psutil
import subprocess
import base64
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 启用DPI感知，解决高缩放率显示器下显示不完全的问题
if sys.platform == 'win32':
    try:
        import ctypes
        # 设置进程为DPI感知
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

# 懒加载BeautifulSoup
def lazy_import_bs4():
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
            from bs4 import BeautifulSoup
            return BeautifulSoup
        except:
            return None



class NetworkMonitor:
    """本地网络监控类"""
    def __init__(self, parent=None):
        self.parent = parent
        self.running = False
        self.monitor_thread = None
        self.last_update_time = 0  # 记录上次更新时间
        self.update_interval = 180   # 更新间隔（秒）
        
        # 网络状态变量
        self.network_status = "未知"
        self.ip_address = "未知"
        self.ping_latency = "--ms"
        self.upload_speed = "--KB/s"
        self.download_speed = "--KB/s"
        
        # 图表数据
        self.download_history = [0] * 60
        self.upload_history = [0] * 60
        
        # 缓存结果，减少重复计算
        self._cached_ip = None
        self._cached_is_connected = None
        self._last_check_time = 0
    
    def get_ip_address(self):
        """获取本地IP地址（公共方法）"""
        # 优化：缓存IP地址，避免频繁获取
        current_time = time.time()
        if self._cached_ip and current_time - self._last_check_time < 30:  # 30秒缓存
            return self._cached_ip
        
        self._cached_ip = self._get_ip_address()
        self._last_check_time = current_time
        return self._cached_ip
    
    def get_network_speed(self):
        """获取网络上传下载速度（公共方法）"""
        upload_speed, download_speed = self._get_network_speed()
        # 格式化速度显示
        upload_speed_str = f"{upload_speed:.2f}KB/s" if upload_speed > 0 else "--KB/s"
        download_speed_str = f"{download_speed:.2f}KB/s" if download_speed > 0 else "--KB/s"
        return download_speed_str, upload_speed_str
    
    def start_monitoring(self):
        """开始监控网络状态"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_network, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控网络状态"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
    
    def _monitor_network(self):
        """网络监控实现"""
        while self.running:
            try:
                current_time = time.time()
                
                # 网络连接状态检查
                if current_time - self.last_update_time >= self.update_interval:
                    is_connected = self._check_internet_connection()
                    
                    if is_connected != self._cached_is_connected:
                        self._cached_is_connected = is_connected
                        
                        if is_connected:
                            self.network_status = "已连接"
                            ip = self._get_ip_address()
                            self.ip_address = ip
                            latency = self._get_ping_latency()
                            if latency is not None:
                                self.ping_latency = f"{latency}ms"
                        else:
                            self.network_status = "未连接"
                            self.ip_address = "未知"
                            self.ping_latency = "--ms"
                            self.upload_speed = "--KB/s"
                            self.download_speed = "--KB/s"
                    
                    # 更新速度
                    if is_connected:
                        upload_speed, download_speed = self._get_network_speed()
                        self.upload_speed = f"{upload_speed:.2f}KB/s"
                        self.download_speed = f"{download_speed:.2f}KB/s"
                    
                    self.last_update_time = current_time
                
            except Exception as e:
                if self.parent and hasattr(self.parent, 'add_debug_info'):
                    self.parent.add_debug_info(f"网络监控异常: {str(e)}", "ERROR")
            
            time.sleep(0.5)
    
    def _check_internet_connection(self):
        """检查网络连接状态"""
        try:
            with socket.create_connection(('8.8.8.8', 53), timeout=2):
                return True
        except (socket.timeout, socket.error):
            return False
    
    def _get_ip_address(self):
        """获取本地IP地址"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 53))
                ip = s.getsockname()[0]
                return ip
        except:
            return "127.0.0.1"
    
    def _get_ping_latency(self):
        """获取ping延迟"""
        try:
            if platform.system() == "Windows":
                command = ["ping", "-n", "1", "www.baidu.com"]
            else:
                command = ["ping", "-c", "1", "www.baidu.com"]
                
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            
            if result.returncode == 0:
                output = result.stdout
                if platform.system() == "Windows":
                    for line in output.split('\n'):
                        if "时间=" in line:
                            try:
                                latency = int(line.split("时间=")[-1].split("ms")[0])
                                return latency
                            except ValueError:
                                continue
                else:
                    for line in output.split('\n'):
                        if "time=" in line:
                            try:
                                latency = float(line.split("time=")[-1].split(" ")[0])
                                return int(latency)
                            except ValueError:
                                continue
            return None
        except Exception:
            return None
    
    def _get_network_speed(self):
        """获取网络上传下载速度"""
        try:
            current_time = time.time()
            if hasattr(self, '_last_speed_sample_time') and current_time - self._last_speed_sample_time < 1:
                return getattr(self, '_last_upload_speed', 0), getattr(self, '_last_download_speed', 0)
                
            net_io = psutil.net_io_counters()
            bytes_sent_before = net_io.bytes_sent
            bytes_recv_before = net_io.bytes_recv
            
            sample_time = 0.5
            time.sleep(sample_time)
            
            net_io = psutil.net_io_counters()
            bytes_sent_after = net_io.bytes_sent
            bytes_recv_after = net_io.bytes_recv
            
            upload_speed = (bytes_sent_after - bytes_sent_before) / 1024 / sample_time
            download_speed = (bytes_recv_after - bytes_recv_before) / 1024 / sample_time
            
            self._last_speed_sample_time = current_time
            self._last_upload_speed = upload_speed
            self._last_download_speed = download_speed
            
            return upload_speed, download_speed
        except Exception as e:
            if self.parent and hasattr(self.parent, 'add_debug_info'):
                self.parent.add_debug_info(f"获取网络速度失败: {str(e)}", "ERROR")
            return 0, 0

class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化事件处理器"""
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.last_modified = 0
        self.debounce_time = 1.0  # 防抖时间，防止短时间内多次触发
    
    def on_modified(self, event):
        """当文件被修改时触发"""
        if not event.is_directory and event.src_path == self.chatbot.config_file:
            current_time = time.time()
            # 防抖处理，避免短时间内多次触发
            if current_time - self.last_modified > self.debounce_time:
                self.last_modified = current_time
                # 在主线程中调用重新加载配置方法
                QTimer.singleShot(0, self.chatbot.reload_config_auto)

class ApiCallThread(QThread):
    """API调用线程类"""
    # 定义信号
    streaming_content = pyqtSignal(str)
    streaming_finished = pyqtSignal()
    api_error = pyqtSignal(str)
    non_streaming_response = pyqtSignal(str)
    debug_info = pyqtSignal(str, str)
    
    def __init__(self, api_url, api_key, model, message, is_streaming):
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.message = message
        self.is_streaming = is_streaming
    
    def run(self):
        """执行API调用"""
        try:
            # 创建API请求数据
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": self.message}
                ],
                "stream": self.is_streaming
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self.debug_info.emit(f"调用API: {self.api_url}", "INFO")
            self.debug_info.emit(f"使用模型: {self.model}", "INFO")
            self.debug_info.emit(f"流式输出: {self.is_streaming}", "INFO")
            
            if self.is_streaming:
                # 流式输出
                self._streaming_response()
            else:
                # 非流式输出
                self._non_streaming_response(payload, headers)
        
        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            self.api_error.emit(error_msg)
            self.debug_info.emit(error_msg, "ERROR")
    
    def _non_streaming_response(self, payload, headers):
        """非流式API响应处理"""
        try:
            # 发送API请求
            response = requests.post(self.api_url, json=payload, headers=headers, verify=False, timeout=30)
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                self.non_streaming_response.emit(ai_response)
            else:
                error_msg = f"API错误: {response.status_code} - {response.text}"
                self.api_error.emit(error_msg)
                self.debug_info.emit(error_msg, "ERROR")
        except Exception as e:
            error_msg = f"非流式响应处理失败: {str(e)}"
            self.api_error.emit(error_msg)
            self.debug_info.emit(error_msg, "ERROR")
    
    def _streaming_response(self):
        """流式API响应处理"""
        try:
            # 创建API请求数据
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": self.message}
                ],
                "stream": self.is_streaming
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送流式API请求
            with requests.post(self.api_url, json=payload, headers=headers, verify=False, stream=True, timeout=60) as response:
                if response.status_code == 200:
                    # 处理流式响应
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            # 解码响应块
                            chunk_str = chunk.decode('utf-8')
                            # 分割SSE事件
                            events = chunk_str.split('data: ')
                            
                            for event in events:
                                event = event.strip()
                                if event and event != '[DONE]':
                                    try:
                                        # 解析JSON
                                        data = json.loads(event)
                                        # 提取AI回复
                                        if 'choices' in data and data['choices']:
                                            delta = data['choices'][0].get('delta', {})
                                            if 'content' in delta:
                                                content = delta['content']
                                                # 通过信号更新UI
                                                self.streaming_content.emit(content)
                                    except json.JSONDecodeError:
                                        continue
                    
                    # 流式响应结束
                    self.streaming_finished.emit()
                else:
                    error_msg = f"API错误: {response.status_code} - {response.text}"
                    self.api_error.emit(error_msg)
                    self.debug_info.emit(error_msg, "ERROR")
        except Exception as e:
            error_msg = f"流式响应处理失败: {str(e)}"
            self.api_error.emit(error_msg)
            self.debug_info.emit(error_msg, "ERROR")


class UniversalChatBotPyQt6(QMainWindow):
    """PyQt6版本的多功能AI聊天助手"""
    # 定义信号用于在后台线程中更新UI
    update_streaming_response = pyqtSignal(str)
    streaming_response_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 连接信号槽
        self.update_streaming_response.connect(self.append_streaming_response)
        self.streaming_response_finished.connect(self.streaming_response_ended)
        
        # 初始化流式响应状态
        self.streaming_response_text = ""
        self.streaming_response_active = False
        
        # 初始化网络监控
        self.network_monitor = NetworkMonitor(self)
        self.network_monitor.start_monitoring()
        
        # 配置文件路径 - 优先使用工作目录的配置文件
        self.config_file = os.path.join(os.getcwd(), "chatbot_config.json")
        # 如果工作目录没有配置文件，使用用户目录的配置文件
        if not os.path.exists(self.config_file):
            self.config_file = os.path.join(os.path.expanduser("~"), ".universal_chatbot_config.json")
        
        # 初始化平台配置
        self.load_config()
        
        # 初始化配置文件监控
        self.setup_config_monitoring()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("🤖 多功能AI聊天助手")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部菜单栏
        self.create_menu()
        
        # 创建主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # 配置设置
        config_group = QGroupBox("⚙️ 配置设置")
        config_layout = QFormLayout(config_group)
        
        # AI平台选择
        self.platform_label = QLabel("AI平台:")
        self.platform_combo = QComboBox()
        # 添加信号连接，平台变化时更新模型列表
        self.platform_combo.currentTextChanged.connect(self.update_platform_config)
        config_layout.addRow(self.platform_label, self.platform_combo)
        
        # API地址
        self.api_url_label = QLabel("API地址:")
        self.api_url_edit = QLineEdit()
        config_layout.addRow(self.api_url_label, self.api_url_edit)
        
        # API密钥
        self.api_key_label = QLabel("API密钥:")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addRow(self.api_key_label, self.api_key_edit)
        
        # 模型选择
        self.model_label = QLabel("模型选择:")
        self.model_combo = QComboBox()
        config_layout.addRow(self.model_label, self.model_combo)
        
        # 平台管理按钮
        platform_buttons_layout = QHBoxLayout()
        self.add_platform_btn = QPushButton("添加平台")
        self.add_platform_btn.clicked.connect(self.show_add_platform_dialog)
        platform_buttons_layout.addWidget(self.add_platform_btn)
        
        self.edit_platform_btn = QPushButton("编辑平台")
        self.edit_platform_btn.clicked.connect(self.show_edit_platform_dialog)
        platform_buttons_layout.addWidget(self.edit_platform_btn)
        
        self.delete_platform_btn = QPushButton("删除平台")
        self.delete_platform_btn.clicked.connect(self.delete_platform)
        platform_buttons_layout.addWidget(self.delete_platform_btn)
        
        config_layout.addRow("平台管理:", platform_buttons_layout)
        
        left_layout.addWidget(config_group)
        
        # 调试控制
        debug_group = QGroupBox("🔍 调试控制")
        debug_layout = QVBoxLayout(debug_group)
        
        # 调试模式
        self.debug_mode_check = QCheckBox("启用调试模式")
        self.debug_mode_check.setChecked(True)
        debug_layout.addWidget(self.debug_mode_check)
        
        # 自动滚动
        self.auto_scroll_check = QCheckBox("自动滚动对话")
        self.auto_scroll_check.setChecked(True)
        debug_layout.addWidget(self.auto_scroll_check)
        
        # 自动保存
        self.auto_save_check = QCheckBox("自动保存对话")
        self.auto_save_check.setChecked(True)
        debug_layout.addWidget(self.auto_save_check)
        
        # 流式输出
        self.streaming_check = QCheckBox("AI流式输出")
        self.streaming_check.setChecked(True)
        debug_layout.addWidget(self.streaming_check)
        
        left_layout.addWidget(debug_group)
        
        # 调试信息
        debug_info_group = QGroupBox("📋 调试信息")
        debug_info_layout = QVBoxLayout(debug_info_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMaximumHeight(200)
        debug_info_layout.addWidget(self.debug_text)
        
        # 调试按钮
        debug_buttons_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_debug_log)
        debug_buttons_layout.addWidget(self.clear_log_btn)
        
        self.copy_log_btn = QPushButton("复制日志")
        self.copy_log_btn.clicked.connect(self.copy_debug_log)
        debug_buttons_layout.addWidget(self.copy_log_btn)
        
        debug_info_layout.addLayout(debug_buttons_layout)
        
        left_layout.addWidget(debug_info_group)
        left_layout.addStretch()
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 对话区域
        self.conversation_text = QTextEdit()
        self.conversation_text.setReadOnly(True)
        right_layout.addWidget(self.conversation_text)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("请输入您的问题...")
        self.input_text.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_text)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        right_layout.addLayout(input_layout)
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900])
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 导出对话
        export_action = QAction("导出对话历史", self)
        export_action.triggered.connect(self.export_conversation)
        file_menu.addAction(export_action)
        
        # 导入对话
        import_action = QAction("导入对话历史", self)
        import_action.triggered.connect(self.import_conversation)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 记忆菜单
        memory_menu = menubar.addMenu("记忆")
        
        # 个人信息
        personal_info_action = QAction("管理个人信息", self)
        personal_info_action.triggered.connect(self.show_personal_info_dialog)
        memory_menu.addAction(personal_info_action)
        
        # 任务管理
        task_manager_action = QAction("管理任务记录", self)
        task_manager_action.triggered.connect(self.show_task_manager)
        memory_menu.addAction(task_manager_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # 所有设置
        all_settings_action = QAction("所有设置...", self)
        all_settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(all_settings_action)
        
        # 重新加载配置
        reload_config_action = QAction("重新加载配置", self)
        reload_config_action.triggered.connect(self.reload_config)
        settings_menu.addAction(reload_config_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 使用帮助
        help_action = QAction("使用帮助", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.platforms = json.load(f)
            else:
                # 默认配置
                self.platforms = {
                    "心流AI": {
                        "name": "IFLOW(OpenAI兼容API)",
                        "api_key_hint": "sk-a61307e861a64d91b9752aec2c9682cd",
                        "base_url": "https://apis.iflow.cn",
                        "models": ["deepseek-v3.1"],
                        "enabled": True,
                        "api_type": "iflow"
                    }
                }
            
            # 更新平台下拉框
            available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
            self.platform_combo.addItems(available_platforms)
            if available_platforms:
                self.platform_combo.setCurrentText(available_platforms[0])
                self.update_platform_config(available_platforms[0])
        except Exception as e:
            self.add_debug_info(f"加载配置失败: {str(e)}", "ERROR")
    
    def update_platform_config(self, platform_name):
        """更新平台配置"""
        if platform_name in self.platforms:
            config = self.platforms[platform_name]
            self.api_url_edit.setText(config['base_url'])
            # 自动填充API密钥
            self.api_key_edit.setText(config['api_key_hint'])
            self.model_combo.clear()
            self.model_combo.addItems(config['models'])
            if config['models']:
                self.model_combo.setCurrentIndex(0)
    
    def show_add_platform_dialog(self):
        """显示添加平台对话框"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QCheckBox, QWidget
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("添加AI平台")
        dialog.setGeometry(200, 200, 500, 400)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 平台名称
        self.platform_name_edit = QLineEdit()
        self.platform_name_edit.setPlaceholderText("如：心流AI")
        form_layout.addRow("平台名称:", self.platform_name_edit)
        
        # 显示名称
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("如：IFLOW(OpenAI兼容API)")
        form_layout.addRow("显示名称:", self.display_name_edit)
        
        # API地址
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("如：https://apis.iflow.cn")
        form_layout.addRow("API地址:", self.base_url_edit)
        
        # API密钥
        self.api_key_edit_dialog = QLineEdit()
        self.api_key_edit_dialog.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit_dialog.setPlaceholderText("如：sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        form_layout.addRow("API密钥:", self.api_key_edit_dialog)
        
        # 模型列表
        self.models_edit = QLineEdit()
        self.models_edit.setPlaceholderText("多个模型用逗号分隔，如：deepseek-v3.1,deepseek-llm-7b-chat")
        form_layout.addRow("模型列表:", self.models_edit)
        
        # API类型
        self.api_type_edit = QLineEdit()
        self.api_type_edit.setPlaceholderText("如：openai, iflow, deepseek")
        form_layout.addRow("API类型:", self.api_type_edit)
        
        # 启用状态
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True)
        form_layout.addRow("启用:", self.enabled_check)
        
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.add_platform(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def add_platform(self, dialog):
        """添加新平台"""
        # 获取用户输入
        platform_name = self.platform_name_edit.text().strip()
        display_name = self.display_name_edit.text().strip()
        base_url = self.base_url_edit.text().strip()
        api_key = self.api_key_edit_dialog.text().strip()
        models_text = self.models_edit.text().strip()
        api_type = self.api_type_edit.text().strip()
        enabled = self.enabled_check.isChecked()
        
        # 验证输入
        if not platform_name or not display_name or not base_url or not models_text or not api_type:
            QMessageBox.critical(self, "错误", "平台名称、显示名称、API地址、模型列表和API类型不能为空")
            return
        
        # 解析模型列表
        models = [model.strip() for model in models_text.split(',') if model.strip()]
        if not models:
            QMessageBox.critical(self, "错误", "模型列表不能为空")
            return
        
        # 检查平台名称是否已存在
        if platform_name in self.platforms:
            QMessageBox.critical(self, "错误", "平台名称已存在")
            return
        
        # 创建新平台配置
        new_platform = {
            "name": display_name,
            "api_key_hint": api_key,
            "base_url": base_url,
            "models": models,
            "enabled": enabled,
            "api_type": api_type
        }
        
        # 添加到平台字典
        self.platforms[platform_name] = new_platform
        
        # 保存配置到文件
        self.save_config()
        
        # 更新平台下拉框
        self.platform_combo.clear()
        available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
        self.platform_combo.addItems(available_platforms)
        if available_platforms:
            self.platform_combo.setCurrentText(platform_name)
            self.update_platform_config(platform_name)
        
        # 关闭对话框
        dialog.accept()
        
        # 显示成功消息
        QMessageBox.information(self, "成功", f"平台 '{platform_name}' 已添加")
    
    def show_edit_platform_dialog(self):
        """显示编辑平台对话框"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QCheckBox
        
        # 获取当前选中的平台
        current_platform = self.platform_combo.currentText()
        if not current_platform or current_platform not in self.platforms:
            QMessageBox.warning(self, "警告", "请先选择一个平台")
            return
        
        # 获取当前平台配置
        config = self.platforms[current_platform]
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑AI平台")
        dialog.setGeometry(200, 200, 500, 400)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 平台名称（只读）
        self.platform_name_edit = QLineEdit(current_platform)
        self.platform_name_edit.setReadOnly(True)
        form_layout.addRow("平台名称:", self.platform_name_edit)
        
        # 显示名称
        self.display_name_edit = QLineEdit(config['name'])
        form_layout.addRow("显示名称:", self.display_name_edit)
        
        # API地址
        self.base_url_edit = QLineEdit(config['base_url'])
        form_layout.addRow("API地址:", self.base_url_edit)
        
        # API密钥
        self.api_key_edit_dialog = QLineEdit(config['api_key_hint'])
        self.api_key_edit_dialog.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API密钥:", self.api_key_edit_dialog)
        
        # 模型列表
        self.models_edit = QLineEdit(", ".join(config['models']))
        form_layout.addRow("模型列表:", self.models_edit)
        
        # API类型
        self.api_type_edit = QLineEdit(config['api_type'])
        form_layout.addRow("API类型:", self.api_type_edit)
        
        # 启用状态
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(config['enabled'])
        form_layout.addRow("启用:", self.enabled_check)
        
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.edit_platform(dialog, current_platform))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def edit_platform(self, dialog, platform_name):
        """编辑平台"""
        # 获取用户输入
        display_name = self.display_name_edit.text().strip()
        base_url = self.base_url_edit.text().strip()
        api_key = self.api_key_edit_dialog.text().strip()
        models_text = self.models_edit.text().strip()
        api_type = self.api_type_edit.text().strip()
        enabled = self.enabled_check.isChecked()
        
        # 验证输入
        if not display_name or not base_url or not models_text or not api_type:
            QMessageBox.critical(self, "错误", "显示名称、API地址、模型列表和API类型不能为空")
            return
        
        # 解析模型列表
        models = [model.strip() for model in models_text.split(',') if model.strip()]
        if not models:
            QMessageBox.critical(self, "错误", "模型列表不能为空")
            return
        
        # 更新平台配置
        self.platforms[platform_name] = {
            "name": display_name,
            "api_key_hint": api_key,
            "base_url": base_url,
            "models": models,
            "enabled": enabled,
            "api_type": api_type
        }
        
        # 保存配置到文件
        self.save_config()
        
        # 更新平台下拉框
        self.platform_combo.clear()
        available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
        self.platform_combo.addItems(available_platforms)
        if platform_name in available_platforms:
            self.platform_combo.setCurrentText(platform_name)
            self.update_platform_config(platform_name)
        
        # 关闭对话框
        dialog.accept()
        
        # 显示成功消息
        QMessageBox.information(self, "成功", f"平台 '{platform_name}' 已更新")
    
    def delete_platform(self):
        """删除当前选择的平台"""
        # 获取当前选中的平台
        current_platform = self.platform_combo.currentText()
        if not current_platform or current_platform not in self.platforms:
            QMessageBox.warning(self, "警告", "请先选择一个平台")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", f"确定要删除平台 '{current_platform}' 吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        
        # 删除平台
        del self.platforms[current_platform]
        
        # 保存配置到文件
        self.save_config()
        
        # 更新平台下拉框
        self.platform_combo.clear()
        available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
        self.platform_combo.addItems(available_platforms)
        if available_platforms:
            self.platform_combo.setCurrentText(available_platforms[0])
            self.update_platform_config(available_platforms[0])
        else:
            # 如果没有可用平台，清空输入框
            self.api_url_edit.clear()
            self.api_key_edit.clear()
            self.model_combo.clear()
        
        # 显示成功消息
        QMessageBox.information(self, "成功", f"平台 '{current_platform}' 已删除")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.platforms, f, ensure_ascii=False, indent=2)
            self.add_debug_info(f"配置已保存到: {self.config_file}", "INFO")
        except Exception as e:
            self.add_debug_info(f"保存配置失败: {str(e)}", "ERROR")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def send_message(self):
        """发送消息"""
        message = self.input_text.text().strip()
        if not message:
            return
        
        # 立即显示用户消息（不等待API响应）
        self.add_message("用户", message)
        self.input_text.clear()
        
        # 直接调用call_ai_api，内部会创建并启动ApiCallThread线程
        self.call_ai_api(message)
    
    def add_message(self, sender, message):
        """添加消息到对话区域"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation_text.append(f"[{timestamp}] {sender}:\n{message}\n")
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def add_ai_message_prefix(self):
        """添加AI消息前缀"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation_text.append(f"[{timestamp}] AI:\n")
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def append_streaming_response(self, content):
        """追加流式响应内容（在主线程中执行）"""
        self.conversation_text.insertPlainText(content)
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def streaming_response_ended(self):
        """流式响应结束（在主线程中执行）"""
        self.conversation_text.append("\n\n")
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # 重置流式响应状态
        self.streaming_response_active = False
    
    def call_ai_api(self, message):
        """调用AI API获取响应"""
        try:
            # 直接在主线程中获取UI状态
            platform_name = self.platform_combo.currentText()
            base_url = self.api_url_edit.text().strip()
            api_key = self.api_key_edit.text().strip()
            model = self.model_combo.currentText()
            is_streaming = self.streaming_check.isChecked()
            
            # 添加调试信息
            self.add_debug_info(f"获取API配置成功: platform={platform_name}, base_url={base_url}, model={model}, streaming={is_streaming}", "INFO")
            
            # 检查平台配置是否存在
            if platform_name not in self.platforms:
                raise Exception(f"平台配置不存在: {platform_name}")
            
            # 检查base_url是否已经包含了完整路径
            if "/chat/completions" in base_url:
                api_url = base_url
            else:
                api_url = f"{base_url}/chat/completions"  # OpenAI兼容API格式
            
            if not api_url or not api_key:
                QMessageBox.critical(self, "错误", "API地址和API密钥不能为空")
                return
            
            # 添加AI消息前缀
            self.add_ai_message_prefix()
            
            # 创建并启动API调用线程
            self.api_thread = ApiCallThread(api_url, api_key, model, message, is_streaming)
            
            # 连接信号槽
            self.api_thread.streaming_content.connect(self.append_streaming_response)
            self.api_thread.streaming_finished.connect(self.streaming_response_ended)
            self.api_thread.non_streaming_response.connect(self.handle_non_streaming_response)
            self.api_thread.api_error.connect(self.handle_api_error)
            self.api_thread.debug_info.connect(self.add_debug_info)
            
            # 启动线程
            self.api_thread.start()
        
        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            self.add_debug_info(error_msg, "ERROR")
            self.add_message("AI", error_msg)
    
    def handle_non_streaming_response(self, ai_response):
        """处理非流式响应"""
        self.conversation_text.insertPlainText(ai_response + "\n\n")
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def handle_api_error(self, error_msg):
        """处理API错误"""
        self.conversation_text.insertPlainText(f"\n{error_msg}\n\n")
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def add_debug_info(self, message, level="INFO"):
        """添加调试信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.debug_text.append(f"[{timestamp}] [{level}] {message}")
        self.debug_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def clear_debug_log(self):
        """清空调试日志"""
        self.debug_text.clear()
    
    def copy_debug_log(self):
        """复制调试日志"""
        self.debug_text.selectAll()
        self.debug_text.copy()
    
    def setup_config_monitoring(self):
        """设置配置文件监控"""
        try:
            # 创建事件处理器和观察者
            self.config_handler = ConfigFileHandler(self)
            self.config_observer = Observer()
            # 监控配置文件所在目录
            config_dir = os.path.dirname(self.config_file)
            # 如果目录不存在，先创建
            os.makedirs(config_dir, exist_ok=True)
            # 启动监控
            self.config_observer.schedule(self.config_handler, config_dir, recursive=False)
            self.config_observer.start()
            self.add_debug_info(f"已启动配置文件监控: {self.config_file}", "INFO")
        except Exception as e:
            self.add_debug_info(f"启动配置文件监控失败: {str(e)}", "ERROR")
    
    def reload_config(self):
        """手动重新加载配置"""
        try:
            self.load_config()
            # 更新平台下拉框
            available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
            self.platform_combo.clear()
            self.platform_combo.addItems(available_platforms)
            if available_platforms:
                self.platform_combo.setCurrentText(available_platforms[0])
                self.update_platform_config(available_platforms[0])
            self.add_debug_info("配置已重新加载", "INFO")
            QMessageBox.information(self, "提示", "配置已重新加载")
        except Exception as e:
            self.add_debug_info(f"重新加载配置失败: {str(e)}", "ERROR")
            QMessageBox.critical(self, "错误", f"重新加载配置失败: {str(e)}")
    
    def reload_config_auto(self):
        """自动重新加载配置（不显示弹窗）"""
        try:
            self.load_config()
            # 更新平台下拉框
            available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
            current_platform = self.platform_combo.currentText()
            self.platform_combo.clear()
            self.platform_combo.addItems(available_platforms)
            # 保持当前选择的平台（如果仍然存在）
            if current_platform in available_platforms:
                self.platform_combo.setCurrentText(current_platform)
            elif available_platforms:
                self.platform_combo.setCurrentText(available_platforms[0])
            self.update_platform_config(self.platform_combo.currentText())
            self.add_debug_info("配置文件已更新，自动重新加载", "INFO")
            self.status_bar.showMessage("配置文件已自动更新", 3000)  # 显示3秒
        except Exception as e:
            self.add_debug_info(f"自动重新加载配置失败: {str(e)}", "ERROR")
            self.status_bar.showMessage(f"配置更新失败: {str(e)}", 3000)
    
    def export_conversation(self):
        """导出对话历史"""
        QMessageBox.information(self, "提示", "导出对话功能开发中...")
    
    def import_conversation(self):
        """导入对话历史"""
        QMessageBox.information(self, "提示", "导入对话功能开发中...")
    
    def show_personal_info_dialog(self):
        """显示个人信息对话框"""
        QMessageBox.information(self, "提示", "个人信息管理功能开发中...")
    
    def show_task_manager(self):
        """显示任务管理器"""
        QMessageBox.information(self, "提示", "任务管理器功能开发中...")
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        QMessageBox.information(self, "提示", "设置对话框功能开发中...")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", "🤖 多功能AI聊天助手\n\n版本: 1.0.0\n作者: AI助手\n\n一个功能丰富、界面美观的AI聊天助手，支持多种AI平台集成。")
    
    def show_help(self):
        """显示帮助对话框"""
        QMessageBox.information(self, "使用帮助", "使用帮助功能开发中...")
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        # 停止网络监控
        self.network_monitor.stop_monitoring()
        # 停止配置文件监控
        if hasattr(self, 'config_observer'):
            self.config_observer.stop()
            self.config_observer.join(timeout=1)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，跨平台一致性更好
    window = UniversalChatBotPyQt6()
    window.show()
    sys.exit(app.exec())
