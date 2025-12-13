import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox,
    QListWidget, QSplitter, QMenuBar, QMenu, QGroupBox, QScrollArea,
    QFormLayout, QMessageBox, QFileDialog, QStatusBar, QToolBar, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QDateTime, QObject, QPropertyAnimation
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

class ConfigReloader(QObject):
    """配置重新加载器，用于在主线程中处理配置文件变化"""
    config_changed = pyqtSignal()
    
    def __init__(self, chatbot):
        super().__init__(chatbot)
        self.chatbot = chatbot
        self.config_changed.connect(self.reload_config)
    
    def reload_config(self):
        """在主线程中重新加载配置"""
        QTimer.singleShot(0, self.chatbot.reload_config_auto)

class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变化事件处理器"""
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.last_modified = 0
        self.debounce_time = 1.0  # 防抖时间，防止短时间内多次触发
        self.last_file_hash = None  # 记录上次文件内容的哈希值
        # 创建配置重新加载器，用于在主线程中处理配置变化
        self.config_reloader = ConfigReloader(chatbot)
        # 计算初始文件哈希
        self._compute_file_hash()
    
    def _compute_file_hash(self):
        """计算配置文件的哈希值"""
        try:
            import hashlib
            with open(self.chatbot.config_file, 'rb') as f:
                self.last_file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            self.last_file_hash = None
    
    def on_modified(self, event):
        """当文件被修改时触发"""
        if not event.is_directory and event.src_path == self.chatbot.config_file:
            current_time = time.time()
            # 防抖处理，避免短时间内多次触发
            if current_time - self.last_modified > self.debounce_time:
                # 计算当前文件哈希
                try:
                    import hashlib
                    with open(self.chatbot.config_file, 'rb') as f:
                        current_hash = hashlib.md5(f.read()).hexdigest()
                    
                    # 只有当文件内容真正改变时才重新加载
                    if current_hash != self.last_file_hash:
                        self.last_modified = current_time
                        self.last_file_hash = current_hash
                        # 触发配置变化信号，在主线程中处理
                        self.config_reloader.config_changed.emit()
                        self.chatbot.add_debug_info(f"配置文件已更新，哈希值变化: {current_hash}", "INFO")
                except Exception as e:
                    # 如果读取文件失败，仍然重新加载
                    self.last_modified = current_time
                    self.config_reloader.config_changed.emit()
                    self.chatbot.add_debug_info(f"配置文件监控异常: {str(e)}", "ERROR")

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
            # 显示完整的JSON格式请求信息
            self.debug_info.emit(f"请求头: {json.dumps(headers, indent=2)}", "DEBUG")
            self.debug_info.emit(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}", "DEBUG")
            
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
            
            # 显示完整的JSON格式请求信息
            self.debug_info.emit(f"请求头: {json.dumps(headers, indent=2)}", "DEBUG")
            self.debug_info.emit(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}", "DEBUG")
            
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


class BackgroundTaskThread(QThread):
    """通用后台任务线程类"""
    task_complete = pyqtSignal(bool, str, object)
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.abort = False
        self.setObjectName(f"BackgroundTask-{id(self)}")  # 设置线程名称，便于调试
    
    def run(self):
        """执行任务"""
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.task_complete.emit(True, "任务完成", result)
        except Exception as e:
            self.task_complete.emit(False, f"任务失败: {str(e)}", None)
        finally:
            # 确保线程资源被正确清理
            self.quit()
    
    def stop(self):
        """停止任务"""
        self.abort = True
        self.quit()

class DatabaseSyncThread(BackgroundTaskThread):
    """数据库同步后台线程类"""
    def __init__(self, db_manager, upload=True, download=False):
        # 使用BackgroundTaskThread的构造函数，将_sync_all作为任务函数
        super().__init__(db_manager._sync_all, upload=upload, download=download)
        self.db_manager = db_manager
        self.setObjectName(f"DatabaseSyncThread-{id(self)}")  # 设置线程名称
    
    def run(self):
        """执行同步操作"""
        try:
            if not self.db_manager.is_connected:
                if not self.db_manager.connect():
                    self.task_complete.emit(False, "数据库连接失败", None)
                    return
            
            # 执行同步
            success = self.task_func(*self.args, **self.kwargs)
            self.task_complete.emit(success, "同步完成" if success else "同步失败", None)
        except Exception as e:
            if hasattr(self.db_manager, 'chatbot') and hasattr(self.db_manager.chatbot, 'add_debug_info'):
                self.db_manager.chatbot.add_debug_info(f"后台同步异常: {str(e)}", "ERROR")
            self.task_complete.emit(False, f"同步异常: {str(e)}", None)
        finally:
            self.quit()


class DatabaseManager:
    """数据库管理类，负责处理与远程数据库的连接和数据同步"""
    
    def __init__(self, chatbot, settings):
        self.chatbot = chatbot
        self.settings = settings
        self.db_config = self.settings.get('database', {})
        self.connection = None
        self.cursor = None
        self.is_connected = False
        self.sync_thread = None
        self.sync_timer = None
    
    def connect(self):
        """连接到数据库"""
        if not self.db_config.get('enabled', False):
            return False
        
        try:
            db_type = self.db_config.get('type', 'mysql')
            
            # 确保导入失败时不会导致整个程序崩溃
            if db_type == 'mysql':
                # 尝试导入MySQL驱动
                try:
                    import mysql.connector
                except ImportError:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"缺少MySQL驱动: mysql-connector-python", "ERROR")
                        self.chatbot.add_debug_info(f"安装命令: pip install mysql-connector-python", "INFO")
                    return False
                
                try:
                    # 设置连接超时，避免无限等待
                    self.connection = mysql.connector.connect(
                        host=self.db_config.get('host', 'localhost'),
                        port=self.db_config.get('port', 3306),
                        database=self.db_config.get('database', 'chatbot'),
                        user=self.db_config.get('username', 'root'),
                        password=self.db_config.get('password', ''),
                        connect_timeout=5  # 5秒超时
                    )
                except Exception as e:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"连接MySQL数据库失败: {str(e)}", "ERROR")
                    return False
            elif db_type == 'postgresql':
                # 尝试导入PostgreSQL驱动
                try:
                    import psycopg2
                except ImportError:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"缺少PostgreSQL驱动: psycopg2", "ERROR")
                        self.chatbot.add_debug_info(f"安装命令: pip install psycopg2", "INFO")
                    return False
                
                try:
                    self.connection = psycopg2.connect(
                        host=self.db_config.get('host', 'localhost'),
                        port=self.db_config.get('port', 5432),
                        dbname=self.db_config.get('database', 'chatbot'),
                        user=self.db_config.get('username', 'postgres'),
                        password=self.db_config.get('password', ''),
                        connect_timeout=5  # 5秒超时
                    )
                except Exception as e:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"连接PostgreSQL数据库失败: {str(e)}", "ERROR")
                    return False
            elif db_type == 'sqlite':
                # 尝试导入SQLite驱动（Python标准库，通常不需要安装）
                try:
                    import sqlite3
                except ImportError:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"缺少SQLite驱动", "ERROR")
                    return False
                
                try:
                    db_path = self.db_config.get('database', ':memory:')
                    self.connection = sqlite3.connect(db_path)
                except Exception as e:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"连接SQLite数据库失败: {str(e)}", "ERROR")
                    return False
            else:
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info(f"不支持的数据库类型: {db_type}", "ERROR")
                return False
            
            try:
                # 创建游标
                self.cursor = self.connection.cursor()
                self.is_connected = True
                
                # 初始化数据库表
                self.init_database()
                
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info(f"成功连接到{db_type}数据库", "INFO")
                return True
            except Exception as e:
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info(f"初始化数据库失败: {str(e)}", "ERROR")
                return False
        
        except Exception as e:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"连接数据库失败: {str(e)}", "ERROR")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.is_connected:
            try:
                if self.cursor:
                    self.cursor.close()
                if self.connection:
                    self.connection.close()
                self.is_connected = False
                self.chatbot.add_debug_info("已断开数据库连接", "INFO")
            except Exception as e:
                self.chatbot.add_debug_info(f"断开数据库连接失败: {str(e)}", "ERROR")
    
    def init_database(self):
        """初始化数据库表"""
        try:
            # 创建配置表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS chatbot_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    config_key VARCHAR(255) UNIQUE NOT NULL,
                    config_value JSON NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建对话历史表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id VARCHAR(36) PRIMARY KEY,
                    sender VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp VARCHAR(50) NOT NULL,
                    created_at DATETIME NOT NULL,
                    response_time FLOAT,
                    session_id VARCHAR(36) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_created_at (created_at) 
                )
            ''')
            
            # 创建记忆表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id VARCHAR(36) PRIMARY KEY,
                    memory_type VARCHAR(50) NOT NULL,
                    memory_data JSON NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建平台配置表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_configs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    platform_name VARCHAR(255) UNIQUE NOT NULL,
                    config JSON NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            self.chatbot.add_debug_info("数据库表初始化成功", "INFO")
        
        except Exception as e:
            self.chatbot.add_debug_info(f"初始化数据库表失败: {str(e)}", "ERROR")
            self.connection.rollback()
    
    def sync_config(self, upload=True, download=False):
        """同步配置数据"""
        if not self.is_connected:
            self.chatbot.add_debug_info("未连接到数据库，无法同步配置", "WARNING")
            return False
        
        try:
            if upload:
                # 上传配置
                config_data = {
                    'settings': self.settings,
                    'platforms': self.chatbot.platforms
                }
                
                # 检查是否已存在配置
                self.cursor.execute("SELECT COUNT(*) FROM chatbot_config WHERE config_key = %s", ('global_config',))
                count = self.cursor.fetchone()[0]
                
                if count > 0:
                    # 更新配置
                    self.cursor.execute(
                        "UPDATE chatbot_config SET config_value = %s WHERE config_key = %s",
                        (json.dumps(config_data, ensure_ascii=False), 'global_config')
                    )
                else:
                    # 插入新配置
                    self.cursor.execute(
                        "INSERT INTO chatbot_config (config_key, config_value) VALUES (%s, %s)",
                        ('global_config', json.dumps(config_data, ensure_ascii=False))
                    )
                
                self.connection.commit()
                self.chatbot.add_debug_info("配置已上传到数据库", "INFO")
            
            if download:
                # 下载配置
                self.cursor.execute("SELECT config_value FROM chatbot_config WHERE config_key = %s", ('global_config',))
                result = self.cursor.fetchone()
                
                if result:
                    config_data = json.loads(result[0])
                    # 应用下载的配置
                    self.settings.update(config_data.get('settings', {}))
                    self.chatbot.platforms.update(config_data.get('platforms', {}))
                    self.chatbot.add_debug_info("已从数据库下载配置", "INFO")
                    return True
        
        except Exception as e:
            self.chatbot.add_debug_info(f"同步配置失败: {str(e)}", "ERROR")
            self.connection.rollback()
            return False
    
    def sync_conversations(self, upload=True, download=False):
        """同步对话历史"""
        if not self.is_connected:
            self.chatbot.add_debug_info("未连接到数据库，无法同步对话历史", "WARNING")
            return False
        
        try:
            if upload:
                # 上传对话历史 - 优化：只上传新增或修改的消息
                local_history = self.chatbot.conversation_history
                if not local_history:
                    self.chatbot.add_debug_info("本地对话历史为空，无需上传", "INFO")
                    return True
                
                # 获取会话ID
                session_id = getattr(self.chatbot, 'session_id', 'default')
                
                # 优化：只处理最近的100条消息，避免处理过多数据
                recent_history = local_history[-100:]
                local_count = len(recent_history)
                self.chatbot.add_debug_info(f"开始上传对话历史，共{local_count}条消息", "INFO")
                
                # 收集所有需要处理的消息ID
                message_ids = [msg['id'] for msg in recent_history]
                
                # 批量查询已存在的消息，减少数据库查询次数
                if message_ids:
                    # 构建IN查询语句
                    placeholders = ','.join(['%s'] * len(message_ids))
                    query = f"SELECT id FROM conversation_history WHERE id IN ({placeholders})"
                    self.cursor.execute(query, tuple(message_ids))
                    existing_ids = {row[0] for row in self.cursor.fetchall()}
                else:
                    existing_ids = set()
                
                # 准备插入和更新的数据
                insert_data = []
                update_data = []
                
                # 收集需要处理的消息
                for message in recent_history:
                    msg_id = message['id']
                    sender = message['sender']
                    msg_content = message['message']
                    timestamp = message['timestamp']
                    
                    # 确保created_at是正确的ISO格式
                    created_at = message['created_at']
                    created_at_str = created_at.isoformat() if isinstance(created_at, datetime) else created_at
                    
                    response_time = message.get('response_time')
                    
                    if msg_id in existing_ids:
                        # 添加到更新列表
                        update_data.append((sender, msg_content, timestamp, created_at_str, response_time, msg_id))
                    else:
                        # 添加到插入列表
                        insert_data.append((msg_id, sender, msg_content, timestamp, created_at_str, response_time, session_id))
                
                # 执行批量更新 - 优化：减少数据库交互次数
                if update_data:
                    update_count = len(update_data)
                    # 使用批量更新，减少数据库交互次数
                    self.cursor.executemany(
                        "UPDATE conversation_history SET sender = %s, message = %s, timestamp = %s, "
                        "created_at = %s, response_time = %s WHERE id = %s",
                        update_data
                    )
                    self.chatbot.add_debug_info(f"已更新{update_count}条现有消息", "INFO")
                
                # 执行批量插入 - 优化：减少数据库交互次数
                if insert_data:
                    insert_count = len(insert_data)
                    self.cursor.executemany(
                        "INSERT INTO conversation_history (id, sender, message, timestamp, "
                        "created_at, response_time, session_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        insert_data
                    )
                    self.chatbot.add_debug_info(f"已插入{insert_count}条新消息", "INFO")
                
                # 提交事务
                self.connection.commit()
            
            if download:
                # 下载对话历史 - 优化：只下载新消息
                # 获取本地最新消息的时间戳
                if self.chatbot.conversation_history:
                    latest_local = max(msg['created_at'] for msg in self.chatbot.conversation_history)
                    # 查询数据库中比本地最新消息更新的记录
                    self.cursor.execute(
                        "SELECT * FROM conversation_history WHERE created_at > %s ORDER BY created_at ASC",
                        (latest_local,)
                    )
                else:
                    # 本地没有历史记录，下载所有消息
                    self.cursor.execute("SELECT * FROM conversation_history ORDER BY created_at ASC")
                
                rows = self.cursor.fetchall()
                
                if rows:
                    downloaded_history = []
                    for row in rows:
                        message = {
                            'id': row[0],
                            'sender': row[1],
                            'message': row[2],
                            'timestamp': row[3],
                            'created_at': row[4],
                            'response_time': row[5]
                        }
                        downloaded_history.append(message)
                    
                    # 更新本地对话历史
                    self.chatbot.conversation_history.extend(downloaded_history)
                    # 限制历史记录数量
                    max_history = self.chatbot.settings.get('chat', {}).get('max_history', 100)
                    if len(self.chatbot.conversation_history) > max_history:
                        self.chatbot.conversation_history = self.chatbot.conversation_history[-max_history:]
                    
                    self.chatbot.add_debug_info(f"已从数据库下载{len(downloaded_history)}条对话历史", "INFO")
            
            return True
        
        except Exception as e:
            self.connection.rollback()
            self.chatbot.add_debug_info(f"同步对话历史失败: {str(e)}", "ERROR")
            return False
    
    def sync_memories(self, upload=True, download=False):
        """同步记忆数据"""
        if not self.is_connected:
            self.chatbot.add_debug_info("未连接到数据库，无法同步记忆数据", "WARNING")
            return False
        
        try:
            if upload:
                # 上传个人信息
                personal_info = self.chatbot.load_personal_info()
                self.cursor.execute(
                    "INSERT INTO memories (id, memory_type, memory_data) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE memory_data = %s",
                    ('personal_info', 'personal', json.dumps(personal_info, ensure_ascii=False), 
                     json.dumps(personal_info, ensure_ascii=False))
                )
                
                # 上传任务记录
                task_records = self.chatbot.load_task_records()
                self.cursor.execute(
                    "INSERT INTO memories (id, memory_type, memory_data) VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE memory_data = %s",
                    ('task_records', 'tasks', json.dumps(task_records, ensure_ascii=False), 
                     json.dumps(task_records, ensure_ascii=False))
                )
                
                self.connection.commit()
                self.chatbot.add_debug_info("记忆数据已上传到数据库", "INFO")
            
            if download:
                # 下载记忆数据
                self.cursor.execute("SELECT id, memory_type, memory_data FROM memories")
                rows = self.cursor.fetchall()
                
                for row in rows:
                    memory_id, memory_type, memory_data = row
                    if memory_id == 'personal_info':
                        # 保存个人信息
                        self.chatbot.save_personal_info(json.loads(memory_data))
                    elif memory_id == 'task_records':
                        # 保存任务记录
                        self.chatbot.save_task_records(json.loads(memory_data))
                
                self.chatbot.add_debug_info(f"已从数据库下载{len(rows)}条记忆数据", "INFO")
            
            return True
        
        except Exception as e:
            self.connection.rollback()
            self.chatbot.add_debug_info(f"同步记忆数据失败: {str(e)}", "ERROR")
            return False
    
    def _sync_all(self, upload=True, download=False):
        """内部同步所有数据方法，在后台线程中执行"""
        success = True
        
        # 检查是否需要中断
        if hasattr(self, 'sync_thread') and hasattr(self.sync_thread, 'abort') and self.sync_thread.abort:
            self.chatbot.add_debug_info("同步操作已被中断", "INFO")
            return False
        
        try:
            # 同步配置
            if self.db_config.get('sync_config', True):
                if not self.sync_config(upload=upload, download=download):
                    success = False
            
            # 同步对话历史
            if self.db_config.get('sync_conversations', True):
                if not self.sync_conversations(upload=upload, download=download):
                    success = False
            
            # 同步记忆数据
            if self.db_config.get('sync_memories', True):
                if not self.sync_memories(upload=upload, download=download):
                    success = False
            
            return success
        
        except Exception as e:
            self.chatbot.add_debug_info(f"同步所有数据失败: {str(e)}", "ERROR")
            return False
    
    def sync_all(self, upload=True, download=False):
        """同步所有数据，在后台线程中执行"""
        # 检查是否已有同步线程在运行
        if self.sync_thread and self.sync_thread.isRunning():
            self.chatbot.add_debug_info("已有同步线程在运行，请勿重复启动", "WARNING")
            return False
        
        # 创建并启动后台同步线程
        self.sync_thread = DatabaseSyncThread(self, upload, download)
        
        # 连接信号槽处理同步完成
        def on_sync_complete(success, message, result):
            self.chatbot.add_debug_info(f"后台同步{message}", "INFO" if success else "ERROR")
            # 清除线程引用
            self.sync_thread = None
        
        self.sync_thread.task_complete.connect(on_sync_complete)
        self.sync_thread.start()
        
        self.chatbot.add_debug_info(f"已启动后台同步线程，上传: {upload}, 下载: {download}", "INFO")
        return True
    
    def check_connection(self):
        """检查数据库连接状态"""
        if not self.is_connected:
            return False
        
        try:
            # 执行一个简单的查询来检查连接
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
            return True
        except Exception as e:
            self.chatbot.add_debug_info(f"数据库连接已断开: {str(e)}", "WARNING")
            self.is_connected = False
            return False

class SettingsManager:
    """设置管理类，负责处理应用程序的所有设置"""
    
    def __init__(self, config_file):
        self.config_file = config_file
        self.default_settings = {
            'window': {
                'width': 1200,
                'height': 800,
                'auto_save': True
            },
            'appearance': {
                'theme': '默认主题',
                'font': None,
                'font_size': 12
            },
            'network': {
                'timeout': 30,
                'retry_count': 1,
                'use_proxy': False,
                'proxy_type': 'HTTP',
                'proxy_host': '',
                'proxy_port': 8080,
                'verify_ssl': False
            },
            'chat': {
                'auto_scroll': True,
                'auto_save': True,
                'show_timestamp': True,
                'streaming': True,
                'response_speed': 5,
                'max_history': 100
            },
            'memory': {
                'enabled': True,
                'memory_type': 'short_term',  # short_term, long_term, none
                'max_memory_length': 10,
                'max_tokens': 8192,
                'memory_persistence': True,
                'memory_retention_days': 7
            },
            'database': {
                'enabled': False,
                'type': 'mysql',  # mysql, postgresql, sqlite
                'host': 'localhost',
                'port': 3306,
                'database': 'chatbot',
                'username': 'root',
                'password': '',
                'sync_interval': 300,  # 自动同步间隔（秒）
                'sync_on_startup': True,  # 启动时同步
                'sync_config': True,  # 同步配置
                'sync_conversations': True,  # 同步对话历史
                'sync_memories': True  # 同步记忆数据
            },
            'debug': {
                'enabled': True,
                'verbose': False,
                'log_level': 'INFO'
            },
            'shortcuts': {
                'send_message': 'Enter',
                'clear_chat': 'Ctrl+L',
                'copy_selected': 'Ctrl+C',
                'paste_text': 'Ctrl+V',
                'show_settings': 'Ctrl+S'
            }
        }
        self.settings = self.default_settings.copy()
        self.platforms = {}
        
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # 检查配置格式，兼容旧格式
                if 'platforms' in config_data:
                    # 新格式：包含platforms和settings字段
                    self.platforms = config_data.get('platforms', {
                        "心流AI": {
                            "name": "IFLOW(OpenAI兼容API)",
                            "api_key_hint": "sk-a61307e861a64d91b9752aec2c9682cd",
                            "base_url": "https://apis.iflow.cn",
                            "models": ["deepseek-v3.1"],
                            "enabled": True,
                            "api_type": "iflow"
                        }
                    })
                    # 处理应用设置，使用递归合并确保所有默认设置都被包含
                    self.settings = self._merge_settings(self.default_settings, config_data.get('settings', {}))
                else:
                    # 旧格式：直接包含平台配置
                    self.platforms = config_data
                    # 使用默认设置
                    self.settings = self.default_settings.copy()
                    # 转换为新格式并保存
                    self.save_settings()
            else:
                # 默认平台配置
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
        except Exception as e:
            # 如果加载失败，使用默认设置
            self.settings = self.default_settings.copy()
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
            # 直接打印错误信息，因为调试信息方法是主窗口类的方法
            print(f"加载配置失败: {str(e)}")
    
    def _merge_settings(self, default, custom):
        """递归合并设置"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_settings(self):
        """保存设置"""
        try:
            # 构建完整的配置数据
            config_data = {
                'platforms': self.platforms,
                'settings': self.settings
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise e
    
    def update_settings(self, new_settings):
        """更新设置"""
        self.settings = self._merge_settings(self.settings, new_settings)
        self.save_settings()
    
    def reset_settings(self):
        """重置为默认设置"""
        self.settings = self.default_settings.copy()
        self.save_settings()

class StatisticsManager:
    """统计管理类，负责计算和管理各种统计指标"""
    
    def __init__(self, conversation_history=None):
        self.conversation_history = conversation_history or []
        self._cached_stats = None  # 统计数据缓存
        self._cached_daily_stats = None  # 每日统计数据缓存
        self._cache_valid = False  # 缓存是否有效
    
    def update_conversation_history(self, history):
        """更新对话历史"""
        self.conversation_history = history
        self._cache_valid = False  # 缓存失效
    
    def get_total_conversations(self):
        """获取对话数量"""
        # 每个完整对话包含用户消息和AI回复，所以对话数量是AI消息数量
        return len([entry for entry in self.conversation_history if entry['sender'] == 'AI'])
    
    def get_total_messages(self):
        """获取总消息数量"""
        return len(self.conversation_history)
    
    def get_user_message_count(self):
        """获取用户消息数量"""
        return len([entry for entry in self.conversation_history if entry['sender'] == '用户'])
    
    def get_ai_message_count(self):
        """获取AI消息数量"""
        return len([entry for entry in self.conversation_history if entry['sender'] == 'AI'])
    
    def get_response_times(self):
        """获取所有有效响应时间"""
        return [entry.get('response_time') for entry in self.conversation_history 
                if entry['sender'] == 'AI' and entry.get('response_time') is not None]
    
    def get_average_response_time(self):
        """获取平均响应时间（秒）"""
        response_times = self.get_response_times()
        if not response_times:
            return 0
        return sum(response_times) / len(response_times)
    
    def get_min_response_time(self):
        """获取最小响应时间（秒）"""
        response_times = self.get_response_times()
        if not response_times:
            return 0
        return min(response_times)
    
    def get_max_response_time(self):
        """获取最大响应时间（秒）"""
        response_times = self.get_response_times()
        if not response_times:
            return 0
        return max(response_times)
    
    def get_response_time_distribution(self):
        """获取响应时间分布"""
        response_times = self.get_response_times()
        if not response_times:
            return {
                'fast': 0,    # < 1秒
                'normal': 0,  # 1-5秒
                'slow': 0,    # 5-10秒
                'very_slow': 0  # > 10秒
            }
        
        distribution = {
            'fast': 0,
            'normal': 0,
            'slow': 0,
            'very_slow': 0
        }
        
        for rt in response_times:
            if rt < 1:
                distribution['fast'] += 1
            elif rt < 5:
                distribution['normal'] += 1
            elif rt < 10:
                distribution['slow'] += 1
            else:
                distribution['very_slow'] += 1
        
        return distribution
    
    def get_total_conversation_duration(self):
        """获取总对话时长（分钟）"""
        if not self.conversation_history:
            return 0
        
        try:
            first_message = datetime.fromisoformat(self.conversation_history[0]['created_at'])
            last_message = datetime.fromisoformat(self.conversation_history[-1]['created_at'])
            duration = (last_message - first_message).total_seconds() / 60
            return duration
        except:
            return 0
    
    def get_statistics_summary(self):
        """获取统计摘要 - 使用缓存优化"""
        # 如果缓存有效，直接返回缓存数据
        if self._cache_valid and self._cached_stats:
            return self._cached_stats
        
        # 计算统计数据
        stats = {
            'total_conversations': self.get_total_conversations(),
            'total_messages': self.get_total_messages(),
            'user_messages': self.get_user_message_count(),
            'ai_messages': self.get_ai_message_count(),
            'average_response_time': round(self.get_average_response_time(), 2),
            'min_response_time': round(self.get_min_response_time(), 2),
            'max_response_time': round(self.get_max_response_time(), 2),
            'response_time_distribution': self.get_response_time_distribution(),
            'total_duration': round(self.get_total_conversation_duration(), 2)
        }
        
        # 更新缓存
        self._cached_stats = stats
        self._cache_valid = True
        
        return stats
    
    def get_daily_statistics(self):
        """获取每日统计数据 - 使用缓存优化"""
        # 如果缓存有效，直接返回缓存数据
        if self._cache_valid and self._cached_daily_stats:
            return self._cached_daily_stats
        
        # 计算每日统计数据
        daily_stats = {}
        
        for entry in self.conversation_history:
            try:
                date = datetime.fromisoformat(entry['created_at']).strftime('%Y-%m-%d')
                if date not in daily_stats:
                    daily_stats[date] = {
                        'messages': 0,
                        'user_messages': 0,
                        'ai_messages': 0,
                        'response_times': []
                    }
                
                daily_stats[date]['messages'] += 1
                if entry['sender'] == '用户':
                    daily_stats[date]['user_messages'] += 1
                elif entry['sender'] == 'AI':
                    daily_stats[date]['ai_messages'] += 1
                    if entry['response_time'] is not None:
                        daily_stats[date]['response_times'].append(entry['response_time'])
            except:
                continue
        
        # 计算每日平均响应时间
        for date, stats in daily_stats.items():
            if stats['response_times']:
                stats['average_response_time'] = round(sum(stats['response_times']) / len(stats['response_times']), 2)
            else:
                stats['average_response_time'] = 0
        
        # 更新缓存
        self._cached_daily_stats = daily_stats
        self._cache_valid = True
        
        return daily_stats
    
    def export_statistics(self, file_path=None, format='json'):
        """导出统计数据"""
        stats = {
            'summary': self.get_statistics_summary(),
            'daily_stats': self.get_daily_statistics(),
            'export_time': datetime.now().isoformat()
        }
        
        if not file_path:
            file_path = os.path.join(os.getcwd(), f"chat_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}")
        
        try:
            if format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                import csv
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['日期', '消息总数', '用户消息', 'AI消息', '平均响应时间'])
                    for date, data in stats['daily_stats'].items():
                        writer.writerow([
                            date,
                            data['messages'],
                            data['user_messages'],
                            data['ai_messages'],
                            data['average_response_time']
                        ])
            return True, file_path
        except Exception as e:
            return False, str(e)

class SplashScreen(QWidget):
    """启动动画窗口类"""
    def __init__(self):
        super().__init__()
        self.opacity = 1.0  # 初始透明度
        self.init_ui()
    
    def init_ui(self):
        """初始化启动动画UI"""
        # 设置窗口属性
        self.setWindowTitle("多功能AI聊天助手")
        self.setFixedSize(400, 300)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # 无边框
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 模态窗口
        
        # 设置窗口透明度
        self.setWindowOpacity(self.opacity)
        
        # 主布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title_label = QLabel("🤖 多功能AI聊天助手")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("版本: 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        layout.addWidget(version_label)
        
        # 描述
        desc_label = QLabel("一个功能丰富、界面美观的AI聊天助手")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # 加载动画（使用QLabel模拟进度）
        self.progress_label = QLabel("正在初始化...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 居中显示
        self.center()
    
    def center(self):
        """将窗口居中显示"""
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def update_progress(self, value, message=None):
        """更新进度条值"""
        self.progress_bar.setValue(value)
        if message:
            self.progress_label.setText(message)
        self.repaint()  # 强制重绘，确保进度条更新
    
    def fade_out(self, duration=500):
        """淡出效果"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()
    
    def fade_in(self, duration=500):
        """淡入效果"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

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
        
        # 暂时禁用数据库功能，避免启动时崩溃
        self.settings['database']['enabled'] = False
        self.status_bar.showMessage("数据库功能已暂时禁用", 3000)
        self.add_debug_info("数据库功能已暂时禁用，避免启动崩溃", "WARNING")
        
        # 延迟初始化数据库，在主窗口显示后再尝试
        def delayed_init_db():
            try:
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
    

    
    def apply_theme(self, theme_name):
        """应用主题"""
        # 定义主题样式表
        themes = {
            '默认主题': '',  # 使用系统默认主题
            '浅色主题': """QWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLineEdit, QComboBox, QTextEdit, QSpinBox, QCheckBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }""",
            '深色主题': """QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px 10px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLineEdit, QComboBox, QTextEdit, QSpinBox, QCheckBox {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QTextEdit {
                selection-background-color: #606060;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 8px 16px;
                margin-right: 2px;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                border-bottom-color: #2d2d2d;
            }"""
        }
        
        # 应用主题样式表
        style_sheet = themes.get(theme_name, '')
        self.setStyleSheet(style_sheet)
        
        # 保存主题设置
        self.settings['appearance']['theme'] = theme_name
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("🤖 多功能AI聊天助手")
        self.setGeometry(100, 100, self.settings['window']['width'], self.settings['window']['height'])
        
        # 应用主题
        self.apply_theme(self.settings['appearance']['theme'])
        
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
        self.debug_mode_check.setChecked(self.settings['debug']['enabled'])
        debug_layout.addWidget(self.debug_mode_check)
        
        # 自动滚动
        self.auto_scroll_check = QCheckBox("自动滚动对话")
        self.auto_scroll_check.setChecked(self.settings['chat']['auto_scroll'])
        debug_layout.addWidget(self.auto_scroll_check)
        
        # 自动保存
        self.auto_save_check = QCheckBox("自动保存对话")
        self.auto_save_check.setChecked(self.settings['chat']['auto_save'])
        debug_layout.addWidget(self.auto_save_check)
        
        # 流式输出
        self.streaming_check = QCheckBox("AI流式输出")
        self.streaming_check.setChecked(self.settings['chat']['streaming'])
        debug_layout.addWidget(self.streaming_check)
        
        left_layout.addWidget(debug_group)
        
        # 调试信息
        debug_info_group = QGroupBox("📋 调试信息")
        debug_info_layout = QVBoxLayout(debug_info_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        # 移除最大高度限制，让调试信息框可以自由扩展
        # self.debug_text.setMaximumHeight(200)
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
        
        # 将调试信息组放在最后，并使用拉伸因子让它占据剩余空间
        left_layout.addWidget(debug_info_group, 1)  # 设置拉伸因子为1
        # 移除最后的拉伸，让调试信息框占据所有剩余空间
        # left_layout.addStretch()
        
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
        # 加大输入框：设置最小高度、增大字体、设置布局拉伸因子
        self.input_text.setMinimumHeight(40)
        font = self.input_text.font()
        font.setPointSize(10)
        self.input_text.setFont(font)
        input_layout.addWidget(self.input_text, 1)  # 设置拉伸因子为1，让输入框占据更多空间
        
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setMinimumHeight(40)  # 让发送按钮高度与输入框匹配
        input_layout.addWidget(self.send_btn)
        
        # 对话状态标志
        self.is_in_conversation = False
        
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
        
        # 统计报告
        statistics_action = QAction("统计报告...", self)
        statistics_action.triggered.connect(self.show_statistics_dialog)
        settings_menu.addAction(statistics_action)
        
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
        platform_name_edit = QLineEdit()
        platform_name_edit.setPlaceholderText("如：心流AI")
        form_layout.addRow("平台名称:", platform_name_edit)
        
        # 显示名称
        display_name_edit = QLineEdit()
        display_name_edit.setPlaceholderText("如：IFLOW(OpenAI兼容API)")
        form_layout.addRow("显示名称:", display_name_edit)
        
        # API地址
        base_url_edit = QLineEdit()
        base_url_edit.setPlaceholderText("如：https://apis.iflow.cn")
        form_layout.addRow("API地址:", base_url_edit)
        
        # API密钥
        api_key_edit_dialog = QLineEdit()
        api_key_edit_dialog.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_edit_dialog.setPlaceholderText("如：sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        form_layout.addRow("API密钥:", api_key_edit_dialog)
        
        # 模型列表
        models_edit = QLineEdit()
        models_edit.setPlaceholderText("多个模型用逗号分隔，如：deepseek-v3.1,deepseek-llm-7b-chat")
        form_layout.addRow("模型列表:", models_edit)
        
        # API类型
        api_type_edit = QLineEdit()
        api_type_edit.setPlaceholderText("如：openai, iflow, deepseek")
        form_layout.addRow("API类型:", api_type_edit)
        
        # 启用状态
        enabled_check = QCheckBox()
        enabled_check.setChecked(True)
        form_layout.addRow("启用:", enabled_check)
        
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        def accept_dialog():
            """接受对话框"""
            # 获取用户输入
            platform_name = platform_name_edit.text().strip()
            display_name = display_name_edit.text().strip()
            base_url = base_url_edit.text().strip()
            api_key = api_key_edit_dialog.text().strip()
            models_text = models_edit.text().strip()
            api_type = api_type_edit.text().strip()
            enabled = enabled_check.isChecked()
            
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
            self.settings_manager.save_settings()
            
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
        
        button_box.accepted.connect(accept_dialog)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
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
        platform_name_edit = QLineEdit(current_platform)
        platform_name_edit.setReadOnly(True)
        form_layout.addRow("平台名称:", platform_name_edit)
        
        # 显示名称
        display_name_edit = QLineEdit(config['name'])
        form_layout.addRow("显示名称:", display_name_edit)
        
        # API地址
        base_url_edit = QLineEdit(config['base_url'])
        form_layout.addRow("API地址:", base_url_edit)
        
        # API密钥
        api_key_edit_dialog = QLineEdit(config['api_key_hint'])
        api_key_edit_dialog.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API密钥:", api_key_edit_dialog)
        
        # 模型列表
        models_edit = QLineEdit(", ".join(config['models']))
        form_layout.addRow("模型列表:", models_edit)
        
        # API类型
        api_type_edit = QLineEdit(config['api_type'])
        form_layout.addRow("API类型:", api_type_edit)
        
        # 启用状态
        enabled_check = QCheckBox()
        enabled_check.setChecked(config['enabled'])
        form_layout.addRow("启用:", enabled_check)
        
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        def accept_dialog():
            """接受对话框"""
            # 获取用户输入
            display_name = display_name_edit.text().strip()
            base_url = base_url_edit.text().strip()
            api_key = api_key_edit_dialog.text().strip()
            models_text = models_edit.text().strip()
            api_type = api_type_edit.text().strip()
            enabled = enabled_check.isChecked()
            
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
            self.platforms[current_platform] = {
                "name": display_name,
                "api_key_hint": api_key,
                "base_url": base_url,
                "models": models,
                "enabled": enabled,
                "api_type": api_type
            }
            
            # 保存配置到文件
            self.settings_manager.save_settings()
            
            # 更新平台下拉框
            self.platform_combo.clear()
            available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
            self.platform_combo.addItems(available_platforms)
            if current_platform in available_platforms:
                self.platform_combo.setCurrentText(current_platform)
                self.update_platform_config(current_platform)
            
            # 关闭对话框
            dialog.accept()
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"平台 '{current_platform}' 已更新")
        
        button_box.accepted.connect(accept_dialog)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
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
        self.settings_manager.save_settings()
        
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
    
    def send_message(self):
        """发送消息"""
        message = self.input_text.text().strip()
        if not message:
            return
        
        # 设置对话中标志
        self.is_in_conversation = True
        
        # 记录消息发送时间，用于计算响应时间
        self.message_start_time = datetime.now()
        
        # 立即显示用户消息（不等待API响应）
        self.add_message("用户", message)
        self.input_text.clear()
        
        # 直接调用call_ai_api，内部会创建并启动ApiCallThread线程
        self.call_ai_api(message)
    
    def add_message(self, sender, message):
        """添加消息到对话区域"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation_text.append(f"[{timestamp}] {sender}:\n{message}\n")
        
        # 添加到对话历史
        self.add_conversation_entry(sender, message, timestamp)
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def add_conversation_entry(self, sender, message, timestamp=None, response_time=None):
        """添加对话条目到历史记录"""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = {
            'id': str(uuid.uuid4()),
            'sender': sender,
            'message': message,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'response_time': response_time  # 响应时间（秒）
        }
        
        self.conversation_history.append(entry)
        
        # 限制历史记录数量
        max_history = self.settings.get('chat', {}).get('max_history', 100)
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]
        
        # 自动保存对话 - 优化：使用延迟保存，避免频繁写入磁盘
        if self.settings.get('chat', {}).get('auto_save', False):
            self.schedule_auto_save()
    
    def schedule_auto_save(self):
        """安排自动保存，延迟执行"""
        # 如果定时器已存在，先取消
        if self.auto_save_timer and self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
        
        # 创建新的定时器，延迟保存
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)  # 只执行一次
        self.auto_save_timer.setInterval(self.auto_save_delay)
        self.auto_save_timer.timeout.connect(self.save_conversation)
        self.auto_save_timer.start()
    
    def streaming_response_ended(self):
        """流式响应结束（在主线程中执行）"""
        self.conversation_text.append("\n\n")
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # 计算响应时间
        response_time = None
        if self.message_start_time:
            response_time = (datetime.now() - self.message_start_time).total_seconds()
            self.response_times.append(response_time)
            # 限制响应时间记录数量
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
        
        # 将完整的AI响应添加到对话历史
        if self.streaming_response_text:
            self.add_conversation_entry("AI", self.streaming_response_text, self.current_ai_message_timestamp, response_time)
            # 保存对话历史
            self.save_conversation()
        
        # 重置流式响应状态
        self.streaming_response_active = False
        self.streaming_response_text = ""
        self.current_ai_message_timestamp = None
        self.message_start_time = None
        
        # 对话结束，设置对话结束标志
        self.is_in_conversation = False
        
        # 对话完成后，同步数据到数据库
        if self.settings['database']['enabled'] and self.db_manager:
            self.db_manager.sync_all(upload=True, download=False)
    
    def _save_conversation_file(self, file_path, conversation_history):
        """在后台线程中保存对话历史文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
        return file_path
    
    def save_conversation(self):
        """保存对话历史到文件"""
        # 在后台线程中保存对话历史
        def on_conversation_saved(success, result):
            if success:
                self.add_debug_info(f"对话历史已保存到: {result}", "INFO")
                
                # 同步到数据库
                if self.settings['database']['enabled'] and self.db_manager:
                    self.db_manager.sync_conversations(upload=True, download=False)
            else:
                self.add_debug_info(f"保存对话历史失败", "ERROR")
        
        # 传递当前对话历史的副本，避免线程安全问题
        self.run_background_task(self._save_conversation_file, on_conversation_saved, 
                               self.conversation_file, self.conversation_history.copy())
    
    def setup_sync_timer(self):
        """设置定期同步定时器"""
        if not self.settings['database']['enabled']:
            return
        
        try:
            from PyQt6.QtCore import QTimer
            
            # 创建定时器
            self.sync_timer = QTimer(self)
            # 设置同步间隔（秒）
            sync_interval = self.settings['database'].get('sync_interval', 300) * 1000
            self.sync_timer.setInterval(sync_interval)
            # 连接信号槽
            self.sync_timer.timeout.connect(self.perform_auto_sync)
            # 启动定时器
            self.sync_timer.start()
            
            self.add_debug_info(f"已启动自动同步定时器，间隔: {sync_interval//1000}秒", "INFO")
        except Exception as e:
            self.add_debug_info(f"启动自动同步定时器失败: {str(e)}", "ERROR")
    
    def perform_auto_sync(self):
        """执行自动同步"""
        # 如果正在对话中，跳过自动同步
        if self.is_in_conversation:
            self.add_debug_info("正在对话中，跳过自动同步", "INFO")
            return
        
        if self.settings['database']['enabled'] and self.db_manager:
            self.add_debug_info("开始自动同步数据到数据库", "INFO")
            self.db_manager.sync_all(upload=True, download=False)
            self.add_debug_info("自动同步完成", "INFO")
    
    def run_background_task(self, task_func, on_complete=None, *args, **kwargs):
        """运行后台任务"""
        # 创建后台任务线程
        task_thread = BackgroundTaskThread(task_func, *args, **kwargs)
        
        # 连接信号槽处理任务完成
        def task_complete_handler(success, message, result):
            if success:
                self.add_debug_info(f"后台任务完成: {message}", "INFO")
            else:
                self.add_debug_info(f"后台任务失败: {message}", "ERROR")
            
            if on_complete:
                on_complete(success, result)
            
            # 确保线程被正确清理
            QTimer.singleShot(0, lambda: task_thread.deleteLater())
        
        task_thread.task_complete.connect(task_complete_handler)
        # 连接finished信号，确保线程资源被释放
        task_thread.finished.connect(lambda: task_thread.deleteLater())
        task_thread.start()
        return task_thread
    
    def _load_conversation_file(self, file_path):
        """在后台线程中加载对话历史文件"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_conversation(self):
        """从文件加载对话历史"""
        # 在后台线程中加载对话历史
        def on_conversation_loaded(success, history):
            if success:
                self.conversation_history = history
                
                # 显示历史对话
                self.conversation_text.clear()
                for entry in self.conversation_history:
                    self.conversation_text.append(f"[{entry['timestamp']}] {entry['sender']}:\n{entry['message']}\n")
                
                # 滚动到底部
                self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
                self.add_debug_info(f"从文件加载对话历史: {self.conversation_file}", "INFO")
                
                # 更新统计管理器
                self.stats_manager.update_conversation_history(self.conversation_history)
            else:
                self.add_debug_info(f"加载对话历史失败", "ERROR")
                self.conversation_history = []
                self.stats_manager.update_conversation_history([])
        
        self.run_background_task(self._load_conversation_file, on_conversation_loaded, self.conversation_file)
    
    def add_ai_message_prefix(self):
        """添加AI消息前缀"""
        self.current_ai_message_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conversation_text.append(f"[{self.current_ai_message_timestamp}] AI:\n")
        self.streaming_response_text = ""
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def append_streaming_response(self, content):
        """追加流式响应内容（在主线程中执行）"""
        # 将内容添加到缓冲区
        self.streaming_buffer += content
        self.streaming_response_text += content
        
        # 初始化定时器，每100毫秒更新一次UI，减少UI更新频率
        if not self.streaming_update_timer or not self.streaming_update_timer.isActive():
            self.streaming_update_timer = QTimer(self)
            self.streaming_update_timer.setInterval(100)  # 100毫秒更新一次
            self.streaming_update_timer.timeout.connect(self.flush_streaming_buffer)
            self.streaming_update_timer.start()
    
    def flush_streaming_buffer(self):
        """刷新流式响应缓冲区，更新UI"""
        if self.streaming_buffer:
            # 更新UI
            self.conversation_text.insertPlainText(self.streaming_buffer)
            
            # 自动滚动
            if self.auto_scroll_check.isChecked():
                self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
            
            # 清空缓冲区
            self.streaming_buffer = ""
    
    def streaming_response_ended(self):
        """流式响应结束（在主线程中执行）"""
        # 确保刷新所有缓冲内容
        self.flush_streaming_buffer()
        
        # 停止定时器
        if self.streaming_update_timer and self.streaming_update_timer.isActive():
            self.streaming_update_timer.stop()
        
        # 添加结束换行
        self.conversation_text.append("\n\n")
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # 将完整的AI响应添加到对话历史
        if self.streaming_response_text:
            self.add_conversation_entry("AI", self.streaming_response_text, self.current_ai_message_timestamp)
        
        # 重置流式响应状态
        self.streaming_response_active = False
        self.streaming_response_text = ""
        self.current_ai_message_timestamp = None
        self.streaming_buffer = ""
    
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
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # 计算响应时间
        response_time = None
        if self.message_start_time:
            response_time = (datetime.now() - self.message_start_time).total_seconds()
            self.response_times.append(response_time)
            # 限制响应时间记录数量
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
        
        # 将AI响应添加到对话历史
        if ai_response:
            self.add_conversation_entry("AI", ai_response, self.current_ai_message_timestamp, response_time)
        
        # 确保保存对话历史，无论是否启用自动保存
        self.save_conversation()
        
        # 重置相关状态
        self.streaming_response_text = ""
        self.current_ai_message_timestamp = None
        self.message_start_time = None

    def handle_api_error(self, error_msg):
        """处理API错误"""
        self.conversation_text.insertPlainText(f"\n{error_msg}\n\n")
        
        # 自动滚动
        if self.auto_scroll_check.isChecked():
            self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # 将错误信息添加到对话历史
        error_entry = {
            "id": str(uuid.uuid4()),
            "sender": "系统",
            "message": error_msg,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": datetime.now().isoformat()
        }
        self.conversation_history.append(error_entry)
        self.save_conversation()
        
        # 重置相关状态
        self.streaming_response_text = ""
        self.current_ai_message_timestamp = None
    
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
            self.settings_manager.load_settings()
            self.settings = self.settings_manager.settings
            self.platforms = self.settings_manager.platforms
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
            self.settings_manager.load_settings()
            self.settings = self.settings_manager.settings
            self.platforms = self.settings_manager.platforms
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
        from PyQt6.QtWidgets import QFileDialog
        
        # 打开文件对话框，选择导出文件
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出对话历史", 
            os.path.join(os.getcwd(), f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"), 
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.json'):
                # 以JSON格式导出
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            elif file_path.endswith('.txt'):
                # 以文本格式导出
                with open(file_path, 'w', encoding='utf-8') as f:
                    for entry in self.conversation_history:
                        f.write(f"[{entry['timestamp']}] {entry['sender']}:\n{entry['message']}\n\n")
            else:
                # 默认以JSON格式导出
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            self.add_debug_info(f"对话历史已导出到: {file_path}", "INFO")
            QMessageBox.information(self, "成功", f"对话历史已成功导出到: {file_path}")
        except Exception as e:
            self.add_debug_info(f"导出对话历史失败: {str(e)}", "ERROR")
            QMessageBox.critical(self, "错误", f"导出对话历史失败: {str(e)}")
    
    def import_conversation(self):
        """导入对话历史"""
        from PyQt6.QtWidgets import QFileDialog
        
        # 打开文件对话框，选择导入文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "导入对话历史", 
            os.getcwd(), 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_history = json.load(f)
            
            # 检查导入数据的格式
            if isinstance(imported_history, list):
                # 清空当前对话
                self.conversation_text.clear()
                
                # 加载导入的对话
                self.conversation_history = imported_history
                
                # 显示导入的对话
                for entry in self.conversation_history:
                    self.conversation_text.append(f"[{entry['timestamp']}] {entry['sender']}:\n{entry['message']}\n")
                
                # 滚动到底部
                self.conversation_text.moveCursor(QTextCursor.MoveOperation.End)
                
                # 保存到当前对话文件
                self.save_conversation()
                
                self.add_debug_info(f"对话历史已从: {file_path} 导入", "INFO")
                QMessageBox.information(self, "成功", f"对话历史已成功导入")
            else:
                raise ValueError("导入文件格式不正确，应为JSON数组")
        except Exception as e:
            self.add_debug_info(f"导入对话历史失败: {str(e)}", "ERROR")
            QMessageBox.critical(self, "错误", f"导入对话历史失败: {str(e)}")
    
    def _load_json_file(self, file_path, default=None):
        """在后台线程中加载JSON文件"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default if default is not None else {}
    
    def _save_json_file(self, file_path, data):
        """在后台线程中保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    
    def load_personal_info(self):
        """加载个人信息"""
        default_info = {
            "name": "",
            "email": "",
            "phone": "",
            "birthday": "",
            "gender": "",
            "occupation": "",
            "interests": [],
            "personality": "",
            "background": "",
            "custom_fields": {}
        }
        try:
            return self._load_json_file(self.personal_info_file, default_info)
        except Exception as e:
            self.add_debug_info(f"加载个人信息失败: {str(e)}", "ERROR")
            return default_info
    
    def save_personal_info(self, personal_info):
        """保存个人信息"""
        def on_personal_info_saved(success, result):
            if success:
                self.add_debug_info(f"个人信息已保存到: {result}", "INFO")
            else:
                self.add_debug_info(f"保存个人信息失败", "ERROR")
        
        # 在后台线程中保存个人信息
        self.run_background_task(self._save_json_file, on_personal_info_saved, 
                               self.personal_info_file, personal_info)
        return True
    
    def load_task_records(self):
        """加载任务记录"""
        default_tasks = {
            "tasks": [],
            "completed_tasks": [],
            "archived_tasks": []
        }
        try:
            return self._load_json_file(self.task_records_file, default_tasks)
        except Exception as e:
            self.add_debug_info(f"加载任务记录失败: {str(e)}", "ERROR")
            return default_tasks
    
    def save_task_records(self, task_records):
        """保存任务记录"""
        def on_task_records_saved(success, result):
            if success:
                self.add_debug_info(f"任务记录已保存到: {result}", "INFO")
            else:
                self.add_debug_info(f"保存任务记录失败", "ERROR")
        
        # 在后台线程中保存任务记录
        self.run_background_task(self._save_json_file, on_task_records_saved, 
                               self.task_records_file, task_records)
        return True
    
    def show_personal_info_dialog(self):
        """显示个人信息对话框"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                                    QLineEdit, QTextEdit, QComboBox, QPushButton, QListWidget, 
                                    QListWidgetItem, QInputDialog, QMessageBox, QDialogButtonBox)
        from PyQt6.QtCore import Qt
        
        # 加载现有个人信息
        personal_info = self.load_personal_info()
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("管理个人信息")
        dialog.setGeometry(200, 200, 600, 500)
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        
        # 基本信息
        basic_group = QLabel("基本信息")
        basic_group.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 10px;")
        main_layout.addWidget(basic_group)
        
        form_layout = QFormLayout()
        
        # 姓名
        name_edit = QLineEdit(personal_info.get("name", ""))
        form_layout.addRow("姓名:", name_edit)
        
        # 邮箱
        email_edit = QLineEdit(personal_info.get("email", ""))
        form_layout.addRow("邮箱:", email_edit)
        
        # 电话
        phone_edit = QLineEdit(personal_info.get("phone", ""))
        form_layout.addRow("电话:", phone_edit)
        
        # 生日
        birthday_edit = QLineEdit(personal_info.get("birthday", ""))
        form_layout.addRow("生日:", birthday_edit)
        
        # 性别
        gender_combo = QComboBox()
        gender_combo.addItems(["", "男", "女", "其他"])
        gender_index = gender_combo.findText(personal_info.get("gender", ""))
        if gender_index != -1:
            gender_combo.setCurrentIndex(gender_index)
        form_layout.addRow("性别:", gender_combo)
        
        # 职业
        occupation_edit = QLineEdit(personal_info.get("occupation", ""))
        form_layout.addRow("职业:", occupation_edit)
        
        main_layout.addLayout(form_layout)
        
        # 兴趣爱好
        interests_group = QLabel("兴趣爱好")
        interests_group.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px;")
        main_layout.addWidget(interests_group)
        
        interests_layout = QHBoxLayout()
        
        interests_list = QListWidget()
        for interest in personal_info.get("interests", []):
            interests_list.addItem(interest)
        interests_layout.addWidget(interests_list)
        
        interests_buttons_layout = QVBoxLayout()
        add_interest_btn = QPushButton("添加")
        remove_interest_btn = QPushButton("删除")
        interests_buttons_layout.addWidget(add_interest_btn)
        interests_buttons_layout.addWidget(remove_interest_btn)
        interests_buttons_layout.addStretch()
        interests_layout.addLayout(interests_buttons_layout)
        
        main_layout.addLayout(interests_layout)
        
        # 个性与背景
        personality_group = QLabel("个性与背景")
        personality_group.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px;")
        main_layout.addWidget(personality_group)
        
        # 个性描述
        personality_edit = QTextEdit(personal_info.get("personality", ""))
        personality_edit.setMinimumHeight(60)
        main_layout.addWidget(QLabel("个性描述:"))
        main_layout.addWidget(personality_edit)
        
        # 背景信息
        background_edit = QTextEdit(personal_info.get("background", ""))
        background_edit.setMinimumHeight(60)
        main_layout.addWidget(QLabel("背景信息:"))
        main_layout.addWidget(background_edit)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(button_box)
        
        # 连接信号槽
        def add_interest():
            interest, ok = QInputDialog.getText(dialog, "添加兴趣", "输入兴趣爱好:")
            if ok and interest.strip():
                interests_list.addItem(interest.strip())
        
        def remove_interest():
            selected_items = interests_list.selectedItems()
            for item in selected_items:
                interests_list.takeItem(interests_list.row(item))
        
        add_interest_btn.clicked.connect(add_interest)
        remove_interest_btn.clicked.connect(remove_interest)
        
        def save_personal_info():
            # 收集信息
            updated_info = {
                "name": name_edit.text().strip(),
                "email": email_edit.text().strip(),
                "phone": phone_edit.text().strip(),
                "birthday": birthday_edit.text().strip(),
                "gender": gender_combo.currentText(),
                "occupation": occupation_edit.text().strip(),
                "interests": [interests_list.item(i).text() for i in range(interests_list.count())],
                "personality": personality_edit.toPlainText(),
                "background": background_edit.toPlainText(),
                "custom_fields": personal_info.get("custom_fields", {})
            }
            
            # 保存信息
            if self.save_personal_info(updated_info):
                QMessageBox.information(dialog, "成功", "个人信息已保存")
                dialog.accept()
            else:
                QMessageBox.critical(dialog, "错误", "保存个人信息失败")
        
        button_box.accepted.connect(save_personal_info)
        button_box.rejected.connect(dialog.reject)
        
        # 执行对话框
        dialog.exec()
    
    def show_task_manager(self):
        """显示任务管理器"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                                    QListWidgetItem, QPushButton, QLabel, QTextEdit, 
                                    QLineEdit, QDateTimeEdit, QComboBox, QMessageBox, 
                                    QInputDialog, QFormLayout, QTabWidget, QDialogButtonBox)
        from PyQt6.QtCore import Qt, QDateTime
        
        # 加载现有任务记录
        task_records = self.load_task_records()
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("管理任务记录")
        dialog.setGeometry(200, 200, 700, 500)
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 待办任务标签页
        todo_tab = QWidget()
        todo_layout = QVBoxLayout(todo_tab)
        
        # 任务列表
        todo_list = QListWidget()
        todo_layout.addWidget(QLabel("待办任务:"))
        todo_layout.addWidget(todo_list)
        
        # 完成任务标签页
        completed_tab = QWidget()
        completed_layout = QVBoxLayout(completed_tab)
        
        completed_list = QListWidget()
        completed_layout.addWidget(QLabel("已完成任务:"))
        completed_layout.addWidget(completed_list)
        
        # 归档任务标签页
        archived_tab = QWidget()
        archived_layout = QVBoxLayout(archived_tab)
        
        archived_list = QListWidget()
        archived_layout.addWidget(QLabel("归档任务:"))
        archived_layout.addWidget(archived_list)
        
        # 添加标签页到标签控件
        tab_widget.addTab(todo_tab, "待办任务")
        tab_widget.addTab(completed_tab, "已完成任务")
        tab_widget.addTab(archived_tab, "归档任务")
        
        # 任务操作按钮
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加任务")
        edit_btn = QPushButton("编辑任务")
        complete_btn = QPushButton("标记完成")
        archive_btn = QPushButton("归档任务")
        delete_btn = QPushButton("删除任务")
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(complete_btn)
        button_layout.addWidget(archive_btn)
        button_layout.addWidget(delete_btn)
        
        main_layout.addLayout(button_layout)
        
        # 加载任务到列表
        def load_tasks():
            # 清空列表
            todo_list.clear()
            completed_list.clear()
            archived_list.clear()
            
            # 加载待办任务
            for task in task_records["tasks"]:
                item = QListWidgetItem(f"[{task.get('priority', '中')}] {task['title']}")
                item.setData(Qt.ItemDataRole.UserRole, task)
                todo_list.addItem(item)
            
            # 加载已完成任务
            for task in task_records["completed_tasks"]:
                item = QListWidgetItem(f"[{task.get('priority', '中')}] {task['title']} (完成于: {task.get('completed_at', '')})")
                item.setData(Qt.ItemDataRole.UserRole, task)
                completed_list.addItem(item)
            
            # 加载归档任务
            for task in task_records["archived_tasks"]:
                item = QListWidgetItem(f"[{task.get('priority', '中')}] {task['title']}")
                item.setData(Qt.ItemDataRole.UserRole, task)
                archived_list.addItem(item)
        
        # 初始加载任务
        load_tasks()
        
        # 获取当前选中的任务和列表
        def get_selected_task():
            current_tab = tab_widget.currentIndex()
            if current_tab == 0:  # 待办任务
                list_widget = todo_list
            elif current_tab == 1:  # 已完成任务
                list_widget = completed_list
            else:  # 归档任务
                list_widget = archived_list
            
            selected_items = list_widget.selectedItems()
            if selected_items:
                return selected_items[0], list_widget
            return None, None
        
        # 添加任务
        def add_task():
            # 创建任务编辑对话框
            task_edit_dialog = QDialog(dialog)
            task_edit_dialog.setWindowTitle("添加任务")
            task_edit_dialog.setGeometry(300, 200, 400, 300)
            
            edit_layout = QVBoxLayout(task_edit_dialog)
            
            form_layout = QFormLayout()
            
            # 任务标题
            title_edit = QLineEdit()
            form_layout.addRow("任务标题:", title_edit)
            
            # 任务描述
            desc_edit = QTextEdit()
            form_layout.addRow("任务描述:", desc_edit)
            
            # 优先级
            priority_combo = QComboBox()
            priority_combo.addItems(["高", "中", "低"])
            form_layout.addRow("优先级:", priority_combo)
            
            # 截止日期
            due_date_edit = QDateTimeEdit()
            due_date_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
            due_date_edit.setCalendarPopup(True)
            form_layout.addRow("截止日期:", due_date_edit)
            
            edit_layout.addLayout(form_layout)
            
            # 按钮
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            edit_layout.addWidget(button_box)
            
            def save_new_task():
                title = title_edit.text().strip()
                if not title:
                    QMessageBox.warning(task_edit_dialog, "警告", "任务标题不能为空")
                    return
                
                new_task = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "description": desc_edit.toPlainText(),
                    "priority": priority_combo.currentText(),
                    "due_date": due_date_edit.dateTime().toString(Qt.DateFormat.ISODate),
                    "created_at": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate),
                    "status": "todo"
                }
                
                task_records["tasks"].append(new_task)
                self.save_task_records(task_records)
                load_tasks()
                task_edit_dialog.accept()
            
            button_box.accepted.connect(save_new_task)
            button_box.rejected.connect(task_edit_dialog.reject)
            
            task_edit_dialog.exec()
        
        # 编辑任务
        def edit_task():
            selected_item, list_widget = get_selected_task()
            if not selected_item:
                QMessageBox.warning(dialog, "警告", "请先选择一个任务")
                return
            
            task = selected_item.data(Qt.ItemDataRole.UserRole)
            
            # 创建任务编辑对话框
            task_edit_dialog = QDialog(dialog)
            task_edit_dialog.setWindowTitle("编辑任务")
            task_edit_dialog.setGeometry(300, 200, 400, 300)
            
            edit_layout = QVBoxLayout(task_edit_dialog)
            
            form_layout = QFormLayout()
            
            # 任务标题
            title_edit = QLineEdit(task["title"])
            form_layout.addRow("任务标题:", title_edit)
            
            # 任务描述
            desc_edit = QTextEdit(task.get("description", ""))
            form_layout.addRow("任务描述:", desc_edit)
            
            # 优先级
            priority_combo = QComboBox()
            priority_combo.addItems(["高", "中", "低"])
            priority_index = priority_combo.findText(task.get("priority", "中"))
            if priority_index != -1:
                priority_combo.setCurrentIndex(priority_index)
            form_layout.addRow("优先级:", priority_combo)
            
            # 截止日期
            due_date_edit = QDateTimeEdit()
            due_date = QDateTime.fromString(task.get("due_date", ""), Qt.DateFormat.ISODate)
            if due_date.isValid():
                due_date_edit.setDateTime(due_date)
            else:
                due_date_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
            due_date_edit.setCalendarPopup(True)
            form_layout.addRow("截止日期:", due_date_edit)
            
            edit_layout.addLayout(form_layout)
            
            # 按钮
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            edit_layout.addWidget(button_box)
            
            def save_edited_task():
                title = title_edit.text().strip()
                if not title:
                    QMessageBox.warning(task_edit_dialog, "警告", "任务标题不能为空")
                    return
                
                # 更新任务
                updated_task = {
                    **task,
                    "title": title,
                    "description": desc_edit.toPlainText(),
                    "priority": priority_combo.currentText(),
                    "due_date": due_date_edit.dateTime().toString(Qt.DateFormat.ISODate)
                }
                
                # 替换原任务
                current_tab = tab_widget.currentIndex()
                if current_tab == 0:  # 待办任务
                    task_list = task_records["tasks"]
                elif current_tab == 1:  # 已完成任务
                    task_list = task_records["completed_tasks"]
                else:  # 归档任务
                    task_list = task_records["archived_tasks"]
                
                for i, t in enumerate(task_list):
                    if t["id"] == task["id"]:
                        task_list[i] = updated_task
                        break
                
                self.save_task_records(task_records)
                load_tasks()
                task_edit_dialog.accept()
            
            button_box.accepted.connect(save_edited_task)
            button_box.rejected.connect(task_edit_dialog.reject)
            
            task_edit_dialog.exec()
        
        # 标记任务为完成
        def complete_task():
            selected_item, list_widget = get_selected_task()
            if not selected_item:
                QMessageBox.warning(dialog, "警告", "请先选择一个任务")
                return
            
            current_tab = tab_widget.currentIndex()
            if current_tab != 0:  # 只有待办任务可以标记为完成
                QMessageBox.warning(dialog, "警告", "只能标记待办任务为完成")
                return
            
            task = selected_item.data(Qt.ItemDataRole.UserRole)
            
            # 更新任务状态
            completed_task = {
                **task,
                "status": "completed",
                "completed_at": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
            }
            
            # 从待办列表移除，添加到已完成列表
            task_records["tasks"] = [t for t in task_records["tasks"] if t["id"] != task["id"]]
            task_records["completed_tasks"].append(completed_task)
            
            self.save_task_records(task_records)
            load_tasks()
            QMessageBox.information(dialog, "成功", "任务已标记为完成")
        
        # 归档任务
        def archive_task():
            selected_item, list_widget = get_selected_task()
            if not selected_item:
                QMessageBox.warning(dialog, "警告", "请先选择一个任务")
                return
            
            task = selected_item.data(Qt.ItemDataRole.UserRole)
            
            current_tab = tab_widget.currentIndex()
            if current_tab == 0:  # 待办任务
                task_list = task_records["tasks"]
            elif current_tab == 1:  # 已完成任务
                task_list = task_records["completed_tasks"]
            else:  # 归档任务
                QMessageBox.warning(dialog, "警告", "任务已经是归档状态")
                return
            
            # 更新任务状态
            archived_task = {
                **task,
                "status": "archived",
                "archived_at": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
            }
            
            # 从原列表移除，添加到归档列表
            task_records["archived_tasks"].append(archived_task)
            if current_tab == 0:  # 待办任务
                task_records["tasks"] = [t for t in task_list if t["id"] != task["id"]]
            else:  # 已完成任务
                task_records["completed_tasks"] = [t for t in task_list if t["id"] != task["id"]]
            
            self.save_task_records(task_records)
            load_tasks()
            QMessageBox.information(dialog, "成功", "任务已归档")
        
        # 删除任务
        def delete_task():
            selected_item, list_widget = get_selected_task()
            if not selected_item:
                QMessageBox.warning(dialog, "警告", "请先选择一个任务")
                return
            
            task = selected_item.data(Qt.ItemDataRole.UserRole)
            
            reply = QMessageBox.question(dialog, "确认", f"确定要删除任务 '{task['title']}' 吗？", 
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
            
            current_tab = tab_widget.currentIndex()
            if current_tab == 0:  # 待办任务
                task_records["tasks"] = [t for t in task_records["tasks"] if t["id"] != task["id"]]
            elif current_tab == 1:  # 已完成任务
                task_records["completed_tasks"] = [t for t in task_records["completed_tasks"] if t["id"] != task["id"]]
            else:  # 归档任务
                task_records["archived_tasks"] = [t for t in task_records["archived_tasks"] if t["id"] != task["id"]]
            
            self.save_task_records(task_records)
            load_tasks()
            QMessageBox.information(dialog, "成功", "任务已删除")
        
        # 连接信号槽
        add_btn.clicked.connect(add_task)
        edit_btn.clicked.connect(edit_task)
        complete_btn.clicked.connect(complete_task)
        archive_btn.clicked.connect(archive_task)
        delete_btn.clicked.connect(delete_task)
        
        # 执行对话框
        dialog.exec()
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QTabWidget,
                                    QFormLayout, QWidget, QSpinBox, QDoubleSpinBox,
                                    QCheckBox, QPushButton, QColorDialog, QFontDialog,
                                    QLabel, QLineEdit, QComboBox, QSlider, QGroupBox)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置")
        dialog.setGeometry(200, 200, 800, 600)
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        
        # 创建标签页控件
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # -------------------- 基本设置 --------------------
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # 窗口设置
        window_group = QGroupBox("窗口设置")
        window_layout = QFormLayout(window_group)
        
        # 窗口宽度
        window_width_spin = QSpinBox()
        window_width_spin.setRange(800, 2000)
        window_width_spin.setValue(self.settings['window']['width'])
        window_layout.addRow("窗口宽度:", window_width_spin)
        
        # 窗口高度
        window_height_spin = QSpinBox()
        window_height_spin.setRange(600, 1500)
        window_height_spin.setValue(self.settings['window']['height'])
        window_layout.addRow("窗口高度:", window_height_spin)
        
        # 自动保存窗口大小
        auto_save_window_check = QCheckBox("自动保存窗口大小")
        auto_save_window_check.setChecked(self.settings['window']['auto_save'])
        window_layout.addRow(auto_save_window_check)
        
        basic_layout.addWidget(window_group)
        
        # 外观设置
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout(appearance_group)
        
        # 主题选择
        theme_combo = QComboBox()
        theme_combo.addItems(["默认主题", "深色主题", "浅色主题"])
        theme_index = theme_combo.findText(self.settings['appearance']['theme'])
        if theme_index != -1:
            theme_combo.setCurrentIndex(theme_index)
        appearance_layout.addRow("主题:", theme_combo)
        
        # 字体设置
        font_button = QPushButton("选择字体")
        font_button.clicked.connect(self.select_font)
        appearance_layout.addRow("字体:", font_button)
        
        basic_layout.addWidget(appearance_group)
        
        tab_widget.addTab(basic_tab, "基本设置")
        
        # -------------------- 网络设置 --------------------
        network_tab = QWidget()
        network_layout = QVBoxLayout(network_tab)
        
        # 连接设置
        connection_group = QGroupBox("连接设置")
        connection_layout = QFormLayout(connection_group)
        
        # 超时设置
        timeout_spin = QSpinBox()
        timeout_spin.setRange(10, 300)
        timeout_spin.setValue(self.settings['network']['timeout'])
        timeout_spin.setSuffix(" 秒")
        connection_layout.addRow("请求超时:", timeout_spin)
        
        # 重试次数
        retry_spin = QSpinBox()
        retry_spin.setRange(0, 5)
        retry_spin.setValue(self.settings['network']['retry_count'])
        connection_layout.addRow("重试次数:", retry_spin)
        
        network_layout.addWidget(connection_group)
        
        # 代理设置
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QFormLayout(proxy_group)
        
        # 使用代理
        use_proxy_check = QCheckBox("使用代理服务器")
        use_proxy_check.setChecked(self.settings['network']['use_proxy'])
        proxy_layout.addRow(use_proxy_check)
        
        # 代理类型
        proxy_type_combo = QComboBox()
        proxy_type_combo.addItems(["HTTP", "HTTPS", "SOCKS5"])
        proxy_type_index = proxy_type_combo.findText(self.settings['network']['proxy_type'])
        if proxy_type_index != -1:
            proxy_type_combo.setCurrentIndex(proxy_type_index)
        proxy_layout.addRow("代理类型:", proxy_type_combo)
        
        # 代理地址
        proxy_host_edit = QLineEdit()
        proxy_host_edit.setText(self.settings['network']['proxy_host'])
        proxy_host_edit.setPlaceholderText("代理服务器地址")
        proxy_layout.addRow("代理地址:", proxy_host_edit)
        
        # 代理端口
        proxy_port_spin = QSpinBox()
        proxy_port_spin.setRange(1, 65535)
        proxy_port_spin.setValue(self.settings['network']['proxy_port'])
        proxy_layout.addRow("代理端口:", proxy_port_spin)
        
        network_layout.addWidget(proxy_group)
        
        tab_widget.addTab(network_tab, "网络设置")
        
        # -------------------- 聊天设置 --------------------
        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)
        
        # 消息设置
        message_group = QGroupBox("消息设置")
        message_layout = QFormLayout(message_group)
        
        # 自动滚动
        auto_scroll_check = QCheckBox("自动滚动对话")
        auto_scroll_check.setChecked(self.settings['chat']['auto_scroll'])
        message_layout.addRow(auto_scroll_check)
        
        # 自动保存
        auto_save_check = QCheckBox("自动保存对话")
        auto_save_check.setChecked(self.settings['chat']['auto_save'])
        message_layout.addRow(auto_save_check)
        
        # 显示时间戳
        show_timestamp_check = QCheckBox("显示消息时间戳")
        show_timestamp_check.setChecked(self.settings['chat']['show_timestamp'])
        message_layout.addRow("显示时间戳:", show_timestamp_check)
        
        chat_layout.addWidget(message_group)
        
        # 响应设置
        response_group = QGroupBox("响应设置")
        response_layout = QFormLayout(response_group)
        
        # 流式输出
        streaming_check = QCheckBox("AI流式输出")
        streaming_check.setChecked(self.settings['chat']['streaming'])
        response_layout.addRow(streaming_check)
        
        # 响应速度
        response_speed_slider = QSlider(Qt.Orientation.Horizontal)
        response_speed_slider.setRange(1, 10)
        response_speed_slider.setValue(self.settings['chat']['response_speed'])
        response_layout.addRow("响应速度:", response_speed_slider)
        
        chat_layout.addWidget(response_group)
        
        tab_widget.addTab(chat_tab, "聊天设置")
        
        # -------------------- 调试设置 --------------------
        debug_tab = QWidget()
        debug_layout = QVBoxLayout(debug_tab)
        
        # 调试模式
        debug_group = QGroupBox("调试模式")
        debug_form_layout = QFormLayout(debug_group)
        
        # 启用调试模式
        debug_mode_check = QCheckBox("启用调试模式")
        debug_mode_check.setChecked(self.settings['debug']['enabled'])
        debug_form_layout.addRow(debug_mode_check)
        
        # 显示详细日志
        verbose_log_check = QCheckBox("显示详细日志")
        verbose_log_check.setChecked(self.settings['debug']['verbose'])
        debug_form_layout.addRow(verbose_log_check)
        
        # 日志级别
        log_level_combo = QComboBox()
        log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_index = log_level_combo.findText(self.settings['debug']['log_level'])
        if log_level_index != -1:
            log_level_combo.setCurrentIndex(log_level_index)
        debug_form_layout.addRow("日志级别:", log_level_combo)
        
        debug_layout.addWidget(debug_group)
        
        tab_widget.addTab(debug_tab, "调试设置")
        
        # -------------------- 快捷键设置 --------------------
        shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_tab)
        
        # 快捷键设置
        shortcuts_group = QGroupBox("快捷键设置")
        shortcuts_form_layout = QFormLayout(shortcuts_group)
        
        # 创建快捷键编辑控件字典
        shortcut_edits = {}
        
        # 遍历所有快捷键设置
        for action, shortcut in self.settings['shortcuts'].items():
            shortcut_edit = QLineEdit(shortcut)
            shortcut_edit.setPlaceholderText(f"为{action}设置快捷键")
            shortcuts_form_layout.addRow(f"{action}:", shortcut_edit)
            shortcut_edits[action] = shortcut_edit
        
        shortcuts_layout.addWidget(shortcuts_group)
        
        tab_widget.addTab(shortcuts_tab, "快捷键设置")
        
        # -------------------- 数据库设置 --------------------
        database_tab = QWidget()
        database_layout = QVBoxLayout(database_tab)
        
        # 数据库基本设置
        database_basic_group = QGroupBox("数据库基本设置")
        database_basic_form = QFormLayout(database_basic_group)
        
        # 启用数据库
        database_enabled_check = QCheckBox("启用数据库连接")
        database_enabled_check.setChecked(self.settings['database']['enabled'])
        database_basic_form.addRow(database_enabled_check)
        
        # 数据库类型
        database_type_combo = QComboBox()
        database_type_combo.addItems(["mysql", "postgresql", "sqlite"])
        database_type_index = database_type_combo.findText(self.settings['database']['type'])
        if database_type_index != -1:
            database_type_combo.setCurrentIndex(database_type_index)
        database_basic_form.addRow("数据库类型:", database_type_combo)
        
        database_layout.addWidget(database_basic_group)
        
        # 数据库连接设置
        database_conn_group = QGroupBox("数据库连接设置")
        database_conn_form = QFormLayout(database_conn_group)
        
        # 主机地址
        database_host_edit = QLineEdit(self.settings['database']['host'])
        database_conn_form.addRow("主机地址:", database_host_edit)
        
        # 端口
        database_port_spin = QSpinBox()
        database_port_spin.setRange(1, 65535)
        database_port_spin.setValue(self.settings['database']['port'])
        database_conn_form.addRow("端口:", database_port_spin)
        
        # 数据库名称
        database_name_edit = QLineEdit(self.settings['database']['database'])
        database_conn_form.addRow("数据库名称:", database_name_edit)
        
        # 用户名
        database_user_edit = QLineEdit(self.settings['database']['username'])
        database_conn_form.addRow("用户名:", database_user_edit)
        
        # 密码
        database_pass_edit = QLineEdit(self.settings['database']['password'])
        database_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        database_conn_form.addRow("密码:", database_pass_edit)
        
        database_layout.addWidget(database_conn_group)
        
        # 数据库同步设置
        database_sync_group = QGroupBox("数据库同步设置")
        database_sync_form = QFormLayout(database_sync_group)
        
        # 同步间隔
        database_sync_interval_spin = QSpinBox()
        database_sync_interval_spin.setRange(60, 3600)
        database_sync_interval_spin.setValue(self.settings['database']['sync_interval'])
        database_sync_interval_spin.setSuffix(" 秒")
        database_sync_form.addRow("自动同步间隔:", database_sync_interval_spin)
        
        # 启动时同步
        database_sync_on_startup_check = QCheckBox()
        database_sync_on_startup_check.setChecked(self.settings['database']['sync_on_startup'])
        database_sync_form.addRow("启动时同步数据:", database_sync_on_startup_check)
        
        # 同步配置
        database_sync_config_check = QCheckBox()
        database_sync_config_check.setChecked(self.settings['database']['sync_config'])
        database_sync_form.addRow("同步配置:", database_sync_config_check)
        
        # 同步对话历史
        database_sync_conversations_check = QCheckBox()
        database_sync_conversations_check.setChecked(self.settings['database']['sync_conversations'])
        database_sync_form.addRow("同步对话历史:", database_sync_conversations_check)
        
        # 同步记忆数据
        database_sync_memories_check = QCheckBox()
        database_sync_memories_check.setChecked(self.settings['database']['sync_memories'])
        database_sync_form.addRow("同步记忆数据:", database_sync_memories_check)
        
        database_layout.addWidget(database_sync_group)
        
        # 数据库操作按钮
        database_buttons_layout = QHBoxLayout()
        
        # 测试连接按钮
        test_connection_btn = QPushButton("测试连接")
        
        # 手动上传按钮
        manual_upload_btn = QPushButton("手动上传数据")
        
        database_buttons_layout.addWidget(test_connection_btn)
        database_buttons_layout.addWidget(manual_upload_btn)
        database_layout.addLayout(database_buttons_layout)
        
        # 连接按钮信号
        def test_database_connection():
            """测试数据库连接"""
            # 创建临时数据库管理器进行测试
            test_db_manager = DatabaseManager(self, self.settings)
            
            # 更新测试数据库管理器的配置
            test_db_manager.db_config = {
                'enabled': True,
                'type': database_type_combo.currentText(),
                'host': database_host_edit.text().strip(),
                'port': database_port_spin.value(),
                'database': database_name_edit.text().strip(),
                'username': database_user_edit.text().strip(),
                'password': database_pass_edit.text(),
                'sync_config': database_sync_config_check.isChecked(),
                'sync_conversations': database_sync_conversations_check.isChecked(),
                'sync_memories': database_sync_memories_check.isChecked()
            }
            
            # 测试连接
            if test_db_manager.connect():
                QMessageBox.information(dialog, "成功", "数据库连接测试成功！")
                test_db_manager.disconnect()
            else:
                QMessageBox.critical(dialog, "失败", "数据库连接测试失败，请检查配置！")
        
        def manual_upload_data():
            """手动上传数据到数据库"""
            # 应用当前设置
            apply_settings()
            
            # 检查数据库是否启用
            if not self.settings['database']['enabled']:
                QMessageBox.warning(dialog, "警告", "数据库功能未启用，请先启用数据库功能！")
                return
            
            # 确认上传
            reply = QMessageBox.question(dialog, "确认", "确定要手动上传数据到数据库吗？",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
            
            # 上传数据
            try:
                # 确保数据库管理器已初始化
                if not hasattr(self, 'db_manager') or not self.db_manager:
                    self.db_manager = DatabaseManager(self, self.settings)
                
                # 连接数据库
                if not self.db_manager.is_connected:
                    if not self.db_manager.connect():
                        QMessageBox.critical(dialog, "失败", "数据库连接失败，请检查配置！")
                        return
                
                # 同步所有数据（后台线程执行）
                if self.db_manager.sync_all(upload=True, download=False):
                    QMessageBox.information(dialog, "成功", "数据上传已启动，将在后台执行。")
                else:
                    QMessageBox.warning(dialog, "警告", "数据上传失败，可能已有同步任务在运行。")
            except Exception as e:
                QMessageBox.critical(dialog, "失败", f"上传数据失败: {str(e)}")
        
        test_connection_btn.clicked.connect(test_database_connection)
        manual_upload_btn.clicked.connect(manual_upload_data)
        
        tab_widget.addTab(database_tab, "数据库设置")
        
        # -------------------- 记忆设置 --------------------
        memory_tab = QWidget()
        memory_layout = QVBoxLayout(memory_tab)
        
        # 基本记忆设置
        basic_memory_group = QGroupBox("基本记忆设置")
        basic_memory_layout = QFormLayout(basic_memory_group)
        
        # 启用记忆功能
        memory_enabled_check = QCheckBox("启用记忆功能")
        memory_enabled_check.setChecked(self.settings['memory']['enabled'])
        basic_memory_layout.addRow(memory_enabled_check)
        
        # 记忆类型
        memory_type_combo = QComboBox()
        memory_type_combo.addItems(["short_term", "long_term", "none"])
        memory_type_index = memory_type_combo.findText(self.settings['memory']['memory_type'])
        if memory_type_index != -1:
            memory_type_combo.setCurrentIndex(memory_type_index)
        basic_memory_layout.addRow("记忆类型:", memory_type_combo)
        
        memory_layout.addWidget(basic_memory_group)
        
        # 高级记忆设置
        advanced_memory_group = QGroupBox("高级记忆设置")
        advanced_memory_layout = QFormLayout(advanced_memory_group)
        
        # 最大记忆长度
        max_memory_length_spin = QSpinBox()
        max_memory_length_spin.setRange(1, 100)
        max_memory_length_spin.setValue(self.settings['memory']['max_memory_length'])
        max_memory_length_spin.setSuffix(" 条")
        advanced_memory_layout.addRow("最大记忆长度:", max_memory_length_spin)
        
        # 最大令牌数
        max_tokens_spin = QSpinBox()
        max_tokens_spin.setRange(1024, 32768)
        max_tokens_spin.setValue(self.settings['memory']['max_tokens'])
        max_tokens_spin.setSuffix(" 令牌")
        advanced_memory_layout.addRow("最大令牌数:", max_tokens_spin)
        
        # 记忆持久化
        memory_persistence_check = QCheckBox("记忆持久化")
        memory_persistence_check.setChecked(self.settings['memory']['memory_persistence'])
        advanced_memory_layout.addRow(memory_persistence_check)
        
        # 记忆保留天数
        memory_retention_spin = QSpinBox()
        memory_retention_spin.setRange(1, 365)
        memory_retention_spin.setValue(self.settings['memory']['memory_retention_days'])
        memory_retention_spin.setSuffix(" 天")
        advanced_memory_layout.addRow("记忆保留天数:", memory_retention_spin)
        
        memory_layout.addWidget(advanced_memory_group)
        
        tab_widget.addTab(memory_tab, "记忆设置")
        
        # -------------------- 按钮盒 --------------------
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel | 
                                     QDialogButtonBox.StandardButton.Apply |
                                     QDialogButtonBox.StandardButton.RestoreDefaults)
        main_layout.addWidget(button_box)
        
        # 连接按钮信号
        def apply_settings():
            """应用设置（内部函数，用于捕获控件值）"""
            # 更新窗口设置
            self.settings['window']['width'] = window_width_spin.value()
            self.settings['window']['height'] = window_height_spin.value()
            self.settings['window']['auto_save'] = auto_save_window_check.isChecked()
            
            # 更新外观设置
            self.settings['appearance']['theme'] = theme_combo.currentText()
            
            # 更新网络设置
            self.settings['network']['timeout'] = timeout_spin.value()
            self.settings['network']['retry_count'] = retry_spin.value()
            self.settings['network']['use_proxy'] = use_proxy_check.isChecked()
            self.settings['network']['proxy_type'] = proxy_type_combo.currentText()
            self.settings['network']['proxy_host'] = proxy_host_edit.text().strip()
            self.settings['network']['proxy_port'] = proxy_port_spin.value()
            
            # 更新聊天设置
            self.settings['chat']['auto_scroll'] = auto_scroll_check.isChecked()
            self.settings['chat']['auto_save'] = auto_save_check.isChecked()
            self.settings['chat']['show_timestamp'] = show_timestamp_check.isChecked()
            self.settings['chat']['streaming'] = streaming_check.isChecked()
            self.settings['chat']['response_speed'] = response_speed_slider.value()
            
            # 更新调试设置
            self.settings['debug']['enabled'] = debug_mode_check.isChecked()
            self.settings['debug']['verbose'] = verbose_log_check.isChecked()
            self.settings['debug']['log_level'] = log_level_combo.currentText()
            
            # 更新快捷键设置
            for action, edit in shortcut_edits.items():
                self.settings['shortcuts'][action] = edit.text().strip()
            
            # 更新记忆设置
            self.settings['memory']['enabled'] = memory_enabled_check.isChecked()
            self.settings['memory']['memory_type'] = memory_type_combo.currentText()
            self.settings['memory']['max_memory_length'] = max_memory_length_spin.value()
            self.settings['memory']['max_tokens'] = max_tokens_spin.value()
            self.settings['memory']['memory_persistence'] = memory_persistence_check.isChecked()
            self.settings['memory']['memory_retention_days'] = memory_retention_spin.value()
            
            # 更新数据库设置
            self.settings['database']['enabled'] = database_enabled_check.isChecked()
            self.settings['database']['type'] = database_type_combo.currentText()
            self.settings['database']['host'] = database_host_edit.text().strip()
            self.settings['database']['port'] = database_port_spin.value()
            self.settings['database']['database'] = database_name_edit.text().strip()
            self.settings['database']['username'] = database_user_edit.text().strip()
            self.settings['database']['password'] = database_pass_edit.text()
            self.settings['database']['sync_interval'] = database_sync_interval_spin.value()
            self.settings['database']['sync_on_startup'] = database_sync_on_startup_check.isChecked()
            self.settings['database']['sync_config'] = database_sync_config_check.isChecked()
            self.settings['database']['sync_conversations'] = database_sync_conversations_check.isChecked()
            self.settings['database']['sync_memories'] = database_sync_memories_check.isChecked()
            
            # 重启数据库连接
            if self.db_manager:
                self.db_manager.disconnect()
                if self.settings['database']['enabled']:
                    self.db_manager.connect()
            
            # 重启同步定时器
            if hasattr(self, 'sync_timer'):
                self.sync_timer.stop()
            self.setup_sync_timer()
            
            # 应用到UI
            self.resize(window_width_spin.value(), window_height_spin.value())
            self.debug_mode_check.setChecked(debug_mode_check.isChecked())
            self.auto_scroll_check.setChecked(auto_scroll_check.isChecked())
            self.auto_save_check.setChecked(auto_save_check.isChecked())
            self.streaming_check.setChecked(streaming_check.isChecked())
            
            # 保存配置
            self.settings_manager.save_settings()
            
            self.add_debug_info("设置已应用", "INFO")
            self.status_bar.showMessage("设置已应用", 3000)
        
        def restore_defaults():
            """恢复默认设置"""
            self.settings_manager.reset_settings()
            self.settings = self.settings_manager.settings
            
            # 重新加载设置到控件
            window_width_spin.setValue(self.settings['window']['width'])
            window_height_spin.setValue(self.settings['window']['height'])
            auto_save_window_check.setChecked(self.settings['window']['auto_save'])
            
            theme_index = theme_combo.findText(self.settings['appearance']['theme'])
            if theme_index != -1:
                theme_combo.setCurrentIndex(theme_index)
            
            timeout_spin.setValue(self.settings['network']['timeout'])
            retry_spin.setValue(self.settings['network']['retry_count'])
            use_proxy_check.setChecked(self.settings['network']['use_proxy'])
            proxy_type_index = proxy_type_combo.findText(self.settings['network']['proxy_type'])
            if proxy_type_index != -1:
                proxy_type_combo.setCurrentIndex(proxy_type_index)
            proxy_host_edit.setText(self.settings['network']['proxy_host'])
            proxy_port_spin.setValue(self.settings['network']['proxy_port'])
            
            auto_scroll_check.setChecked(self.settings['chat']['auto_scroll'])
            auto_save_check.setChecked(self.settings['chat']['auto_save'])
            show_timestamp_check.setChecked(self.settings['chat']['show_timestamp'])
            streaming_check.setChecked(self.settings['chat']['streaming'])
            response_speed_slider.setValue(self.settings['chat']['response_speed'])
            
            debug_mode_check.setChecked(self.settings['debug']['enabled'])
            verbose_log_check.setChecked(self.settings['debug']['verbose'])
            log_level_index = log_level_combo.findText(self.settings['debug']['log_level'])
            if log_level_index != -1:
                log_level_combo.setCurrentIndex(log_level_index)
            
            # 更新快捷键设置
            for action, edit in shortcut_edits.items():
                edit.setText(self.settings['shortcuts'][action])
            
            # 更新记忆设置
            memory_enabled_check.setChecked(self.settings['memory']['enabled'])
            memory_type_index = memory_type_combo.findText(self.settings['memory']['memory_type'])
            if memory_type_index != -1:
                memory_type_combo.setCurrentIndex(memory_type_index)
            max_memory_length_spin.setValue(self.settings['memory']['max_memory_length'])
            max_tokens_spin.setValue(self.settings['memory']['max_tokens'])
            memory_persistence_check.setChecked(self.settings['memory']['memory_persistence'])
            memory_retention_spin.setValue(self.settings['memory']['memory_retention_days'])
            
            # 更新数据库设置
            database_enabled_check.setChecked(self.settings['database']['enabled'])
            database_type_index = database_type_combo.findText(self.settings['database']['type'])
            if database_type_index != -1:
                database_type_combo.setCurrentIndex(database_type_index)
            database_host_edit.setText(self.settings['database']['host'])
            database_port_spin.setValue(self.settings['database']['port'])
            database_name_edit.setText(self.settings['database']['database'])
            database_user_edit.setText(self.settings['database']['username'])
            database_pass_edit.setText(self.settings['database']['password'])
            database_sync_interval_spin.setValue(self.settings['database']['sync_interval'])
            database_sync_on_startup_check.setChecked(self.settings['database']['sync_on_startup'])
            database_sync_config_check.setChecked(self.settings['database']['sync_config'])
            database_sync_conversations_check.setChecked(self.settings['database']['sync_conversations'])
            database_sync_memories_check.setChecked(self.settings['database']['sync_memories'])
        
        button_box.accepted.connect(lambda: (apply_settings(), dialog.accept()))
        button_box.rejected.connect(dialog.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(apply_settings)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(restore_defaults)
        
        # 执行对话框
        dialog.exec()
    
    def select_font(self):
        """选择字体"""
        from PyQt6.QtWidgets import QFontDialog
        
        font, ok = QFontDialog.getFont(self)
        if ok:
            # 应用字体到所有控件
            self.setFont(font)
            self.conversation_text.setFont(font)
            self.input_text.setFont(font)
            self.debug_text.setFont(font)
            # 保存字体设置
            self.settings['appearance']['font'] = font.toString()
            self.settings_manager.save_settings()
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", "🤖 多功能AI聊天助手\n\n版本: 1.0.0\n作者: AI助手\n\n一个功能丰富、界面美观的AI聊天助手，支持多种AI平台集成。")
    
    def show_help(self):
        """显示帮助对话框"""
        QMessageBox.information(self, "使用帮助", "使用帮助功能开发中...")
    
    def show_statistics_dialog(self):
        """显示统计报告对话框"""
        from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QPushButton, 
                                    QTabWidget, QWidget, QLabel, QGridLayout, QFileDialog)
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("聊天统计报告")
        dialog.setGeometry(100, 100, 1000, 700)
        
        # 创建主布局
        main_layout = QVBoxLayout(dialog)
        
        # 初始化统计管理器
        stats_manager = StatisticsManager(self.conversation_history)
        
        # 获取统计摘要
        stats_summary = stats_manager.get_statistics_summary()
        
        # 创建统计概览区域
        summary_group = QWidget()
        summary_grid = QGridLayout(summary_group)
        
        # 显示统计概览数据
        stats_labels = [
            ("总对话次数", f"{stats_summary['total_conversations']} 次"),
            ("总消息数量", f"{stats_summary['total_messages']} 条"),
            ("用户消息", f"{stats_summary['user_messages']} 条"),
            ("AI消息", f"{stats_summary['ai_messages']} 条"),
            ("平均响应时间", f"{stats_summary['average_response_time']} 秒"),
            ("最快响应时间", f"{stats_summary['min_response_time']} 秒"),
            ("最慢响应时间", f"{stats_summary['max_response_time']} 秒"),
            ("总对话时长", f"{stats_summary['total_duration']} 分钟")
        ]
        
        # 添加统计标签
        for i, (label, value) in enumerate(stats_labels):
            summary_grid.addWidget(QLabel(label + ":"), i // 2, i % 2 * 2)
            summary_grid.addWidget(QLabel(value), i // 2, i % 2 * 2 + 1)
        
        main_layout.addWidget(summary_group)
        
        # 尝试导入pyqtgraph创建图表
        try:
            import pyqtgraph as pg
            from pyqtgraph import PlotWidget
            
            # 创建标签页
            tab_widget = QTabWidget()
            main_layout.addWidget(tab_widget)
            
            # -------------------- 统计图表标签页 --------------------
            chart_tab = QWidget()
            chart_layout = QVBoxLayout(chart_tab)
            
            # 创建图表容器
            chart_widget = PlotWidget()
            chart_layout.addWidget(chart_widget)
            
            # 设置图表样式
            chart_widget.setBackground('w')
            chart_widget.setTitle('聊天统计概览', size='14pt', color='black')
            
            # 获取每日统计数据
            daily_stats = stats_manager.get_daily_statistics()
            
            if daily_stats:
                # 准备数据
                dates = list(daily_stats.keys())
                dates.sort()  # 按日期排序
                
                # 转换日期为datetime对象
                date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
                date_timestamps = [date.timestamp() for date in date_objects]
                
                # 消息数量数据
                total_messages = [daily_stats[date]['messages'] for date in dates]
                user_messages = [daily_stats[date]['user_messages'] for date in dates]
                ai_messages = [daily_stats[date]['ai_messages'] for date in dates]
                
                # 响应时间数据
                avg_response_times = [daily_stats[date]['average_response_time'] for date in dates]
                
                # 设置X轴为日期轴
                from pyqtgraph import DateAxisItem
                axis = DateAxisItem(orientation='bottom')
                chart_widget.setAxisItems({'bottom': axis})
                
                # 设置Y轴范围
                max_messages = max(total_messages) if total_messages else 10
                chart_widget.setYRange(0, max_messages + 5)
                
                # 创建双Y轴
                plot_item = chart_widget.getPlotItem()
                plot_item.addLegend()
                
                # 绘制消息数量条形图
                bar_graph = pg.BarGraphItem(x=date_timestamps, height=total_messages, width=0.5, brush='blue', name='总消息数')
                plot_item.addItem(bar_graph)
                
                # 绘制用户消息和AI消息折线图
                plot_item.plot(date_timestamps, user_messages, pen='green', name='用户消息')
                plot_item.plot(date_timestamps, ai_messages, pen='red', name='AI消息')
                
                # 绘制响应时间折线图（使用右侧Y轴）
                axis2 = pg.AxisItem('right')
                plot_item.setAxisItems({'right': axis2})
                response_plot = pg.PlotCurveItem(date_timestamps, avg_response_times, pen='purple', name='平均响应时间')
                plot_item.addItem(response_plot)
            
            tab_widget.addTab(chart_tab, "统计图表")
            
            # -------------------- 响应时间分布标签页 --------------------
            response_tab = QWidget()
            response_layout = QVBoxLayout(response_tab)
            
            # 创建响应时间分布图表
            response_chart = PlotWidget()
            response_layout.addWidget(response_chart)
            response_chart.setBackground('w')
            response_chart.setTitle('响应时间分布', size='14pt', color='black')
            
            # 获取响应时间分布
            rt_dist = stats_summary['response_time_distribution']
            rt_categories = ['< 1秒', '1-5秒', '5-10秒', '> 10秒']
            rt_values = [
                rt_dist['fast'],
                rt_dist['normal'],
                rt_dist['slow'],
                rt_dist['very_slow']
            ]
            
            # 绘制饼图
            pie_chart = pg.PlotWidget()
            pie_chart.setBackground('w')
            pie_chart.setTitle('响应时间分布', size='14pt', color='black')
            
            # 使用BarGraphItem绘制响应时间分布条形图
            bar_graph = pg.BarGraphItem(x=range(len(rt_categories)), height=rt_values, width=0.6, brush='blue')
            response_chart.addItem(bar_graph)
            
            # 设置X轴标签
            response_chart.getAxis('bottom').setTicks([[(i, cat) for i, cat in enumerate(rt_categories)]])
            
            response_layout.addWidget(pie_chart)
            tab_widget.addTab(response_tab, "响应时间分布")
        except ImportError:
            # 如果pyqtgraph导入失败，显示提示
            error_label = QLabel("未安装pyqtgraph库，无法显示图表。请运行 'pip install pyqtgraph' 安装。")
            main_layout.addWidget(error_label)
        
        # -------------------- 导出按钮 --------------------
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close | QDialogButtonBox.StandardButton.Save)
        main_layout.addWidget(button_box)
        
        # 导出统计报告函数
        def export_stats():
            """导出统计报告"""
            # 让用户选择导出格式和路径
            file_path, _ = QFileDialog.getSaveFileName(
                dialog, 
                "导出统计报告", 
                os.path.join(os.getcwd(), f"chat_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"), 
                "JSON文件 (*.json);;CSV文件 (*.csv)"
            )
            
            if file_path:
                format = 'json' if file_path.endswith('.json') else 'csv'
                success, result = stats_manager.export_statistics(file_path, format)
                if success:
                    QMessageBox.information(self, "成功", f"统计报告已成功导出到: {result}")
                else:
                    QMessageBox.critical(self, "错误", f"导出统计报告失败: {result}")
        
        # 连接按钮信号
        button_box.rejected.connect(dialog.reject)
        button_box.accepted.connect(export_stats)
        
        dialog.exec()
    
    def export_statistics(self, file_path=None):
        """导出统计报告"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        stats_manager = StatisticsManager(self.conversation_history)
        
        # 如果没有提供文件路径，让用户选择
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "导出统计报告", 
                os.path.join(os.getcwd(), f"chat_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"), 
                "JSON文件 (*.json);;CSV文件 (*.csv)"
            )
            
        if file_path:
            format = 'json' if file_path.endswith('.json') else 'csv'
            success, result = stats_manager.export_statistics(file_path, format)
            if success:
                QMessageBox.information(self, "成功", f"统计报告已成功导出到: {result}")
            else:
                QMessageBox.critical(self, "错误", f"导出统计报告失败: {result}")
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        # 停止网络监控
        self.network_monitor.stop_monitoring()
        
        # 停止配置文件监控
        if hasattr(self, 'config_observer'):
            self.config_observer.stop()
            self.config_observer.join(timeout=1)
        
        # 确保对话历史被保存
        if self.settings.get('chat', {}).get('auto_save', False):
            self.save_conversation()
            # 等待保存完成
            QApplication.processEvents()
        
        # 停止数据库管理器
        if hasattr(self, 'db_manager') and self.db_manager:
            # 停止正在运行的同步线程
            if hasattr(self.db_manager, 'sync_thread') and self.db_manager.sync_thread and self.db_manager.sync_thread.isRunning():
                self.db_manager.sync_thread.stop()
                self.db_manager.sync_thread.wait()  # 等待线程完成
                self.db_manager.sync_thread.deleteLater()
            # 断开数据库连接
            if hasattr(self.db_manager, 'disconnect'):
                self.db_manager.disconnect()
        
        # 停止定期同步定时器
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
            self.sync_timer.deleteLater()
        
        # 停止自动保存定时器
        if hasattr(self, 'auto_save_timer') and self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            self.auto_save_timer.deleteLater()
        
        # 等待所有后台线程完成
        QApplication.processEvents()
        
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，跨平台一致性更好
    
    # 创建启动动画
    splash = SplashScreen()
    splash.show()
    
    # 更新进度
    splash.update_progress(10, "加载配置文件...")
    QApplication.processEvents()
    
    # 直接创建主窗口，不使用手动延时
    window = UniversalChatBotPyQt6()
    
    splash.update_progress(50, "初始化UI组件...")
    QApplication.processEvents()
    
    splash.update_progress(70, "初始化服务...")
    QApplication.processEvents()
    
    splash.update_progress(90, "加载对话历史...")
    QApplication.processEvents()
    
    splash.update_progress(100, "初始化完成！")
    QApplication.processEvents()
    
    # 显示主窗口
    window.show()
    window.raise_()
    window.activateWindow()
    
    # 关闭启动动画
    splash.fade_out(duration=500)
    # 等待渐变效果完成
    app.processEvents()
    
    # 使用定时器确保启动动画完全关闭后再删除
    QTimer.singleShot(600, lambda: (splash.close(), splash.deleteLater()))
    
    sys.exit(app.exec())
