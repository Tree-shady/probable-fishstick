from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from .utils import compute_file_hash


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
        self.last_file_hash = compute_file_hash(self.chatbot.config_file)
    
    def on_modified(self, event):
        """当文件被修改时触发"""
        if not event.is_directory and event.src_path == self.chatbot.config_file:
            current_time = time.time()
            # 防抖处理，避免短时间内多次触发
            if current_time - self.last_modified > self.debounce_time:
                # 计算当前文件哈希
                current_hash = compute_file_hash(self.chatbot.config_file)
                
                # 只有当文件内容真正改变时才重新加载
                if current_hash != self.last_file_hash:
                    self.last_modified = current_time
                    self.last_file_hash = current_hash
                    # 触发配置变化信号，在主线程中处理
                    self.config_reloader.config_changed.emit()
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"配置文件已更新，哈希值变化: {current_hash}", "INFO")


class ConfigObserver:
    """配置文件监控器"""
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.observer = Observer()
        self.handler = ConfigFileHandler(chatbot)
        self.running = False
    
    def start(self):
        """开始监控配置文件"""
        if self.running:
            return
        
        # 监控配置文件所在目录
        import os
        config_dir = os.path.dirname(self.chatbot.config_file)
        # 如果目录不存在，先创建
        os.makedirs(config_dir, exist_ok=True)
        # 启动监控
        self.observer.schedule(self.handler, config_dir, recursive=False)
        self.observer.start()
        self.running = True
        if hasattr(self.chatbot, 'add_debug_info'):
            self.chatbot.add_debug_info(f"已启动配置文件监控: {self.chatbot.config_file}", "INFO")
    
    def stop(self):
        """停止监控配置文件"""
        if self.running:
            self.observer.stop()
            self.observer.join(timeout=1)
            self.running = False
