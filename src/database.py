from PyQt6.QtCore import QThread
from .api import BackgroundTaskThread
import json
from datetime import datetime


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
            # 确保在后台线程中不要直接调用GUI方法，避免线程安全问题
            # 检查连接状态
            if not self.db_manager.is_connected:
                # 尝试重新连接
                if not self.db_manager.connect():
                    # 使用信号传递结果，而不是直接调用GUI方法
                    self.task_complete.emit(False, "数据库连接失败，已尝试重新连接", None)
                    return
            
            # 执行同步
            success = self.task_func(*self.args, **self.kwargs)
            self.task_complete.emit(success, "同步完成" if success else "同步失败", None)
        except Exception as e:
            error_msg = f"同步异常: {str(e)}"
            self.task_complete.emit(False, error_msg, None)
        finally:
            # 确保线程资源被正确清理
            self.quit()
            # 不在run方法中清除sync_thread引用，避免竞争条件
            # 线程引用清理在on_sync_complete回调中处理


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
        # 启动自动同步定时器
        self.setup_sync_timer()
    
    def connect(self):
        """连接到数据库，添加了详细的错误信息和更好的资源管理"""
        # 移除enabled检查，允许直接调用connect方法进行连接
        # 当用户点击"立即同步"按钮时，应该直接尝试连接，而不是检查enabled状态
        # if not self.db_config.get('enabled', False):
        #     if hasattr(self.chatbot, 'add_debug_info'):
        #         self.chatbot.add_debug_info("数据库功能未启用", "INFO")
        #     return False
        
        try:
            db_type = self.db_config.get('type', 'mysql')
            host = self.db_config.get('host', 'localhost')
            port = self.db_config.get('port', 3306)
            database = self.db_config.get('database', 'chatbot')
            username = self.db_config.get('username', 'root')
            
            # 移除在connect方法中直接调用GUI方法，避免线程安全问题
            # GUI日志将通过DatabaseManager的其他方法或信号处理
            
            # 确保导入失败时不会导致整个程序崩溃
            if db_type == 'mysql':
                # 尝试导入MySQL驱动
                try:
                    import mysql.connector
                except ImportError:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
                
                try:
                    # 设置连接超时，避免无限等待
                    self.connection = mysql.connector.connect(
                        host=host,
                        port=port,
                        database=database,
                        user=username,
                        password=self.db_config.get('password', ''),
                        connect_timeout=5  # 5秒超时
                    )
                except mysql.connector.Error as e:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
                except Exception as e:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
            elif db_type == 'postgresql':
                # 尝试导入PostgreSQL驱动
                try:
                    import psycopg2
                except ImportError:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
                
                try:
                    self.connection = psycopg2.connect(
                        host=host,
                        port=port,
                        dbname=database,
                        user=username,
                        password=self.db_config.get('password', ''),
                        connect_timeout=5  # 5秒超时
                    )
                except psycopg2.Error as e:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
                except Exception as e:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
            elif db_type == 'sqlite':
                # 尝试导入SQLite驱动（Python标准库，通常不需要安装）
                try:
                    import sqlite3
                except ImportError:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
                
                try:
                    db_path = self.db_config.get('database', ':memory:')
                    self.connection = sqlite3.connect(db_path)
                except sqlite3.Error as e:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
                except Exception as e:
                    # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                    return False
            else:
                # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                return False
            
            try:
                # 创建游标
                self.cursor = self.connection.cursor()
                self.is_connected = True
                
                # 初始化数据库表
                self.init_database()
                
                return True
            except Exception as e:
                # 移除在connect方法中直接调用GUI方法，避免线程安全问题
                # 确保资源被清理
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                if self.connection:
                    self.connection.close()
                    self.connection = None
                self.is_connected = False
                return False
        
        except Exception as e:
            # 移除在connect方法中直接调用GUI方法，避免线程安全问题
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
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info("已断开数据库连接", "INFO")
            except Exception as e:
                if hasattr(self.chatbot, 'add_debug_info'):
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
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info("数据库表初始化成功", "INFO")
        
        except Exception as e:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"初始化数据库表失败: {str(e)}", "ERROR")
            self.connection.rollback()
    
    def sync_config(self, upload=True, download=False):
        """同步配置数据"""
        if not self.is_connected:
            if hasattr(self.chatbot, 'add_debug_info'):
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
                if hasattr(self.chatbot, 'add_debug_info'):
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
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info("已从数据库下载配置", "INFO")
                    return True
        
        except Exception as e:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"同步配置失败: {str(e)}", "ERROR")
            self.connection.rollback()
            return False
    
    def sync_conversations(self, upload=True, download=False):
        """同步对话历史"""
        if not self.is_connected:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info("未连接到数据库，无法同步对话历史", "WARNING")
            return False
        
        try:
            if upload:
                # 上传对话历史 - 优化：只上传新增或修改的消息
                local_history = self.chatbot.conversation_history
                if not local_history:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info("本地对话历史为空，无需上传", "INFO")
                    return True
                
                # 获取会话ID
                session_id = getattr(self.chatbot, 'session_id', 'default')
                
                # 优化：只处理最近的100条消息，避免处理过多数据
                recent_history = local_history[-100:]
                local_count = len(recent_history)
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info(f"开始上传对话历史，共{local_count}条消息", "INFO")
                
                # 收集所有需要处理的消息ID，确保每条消息都有唯一id
                message_ids = []
                for msg in recent_history:
                    # 检查id格式，如果不是UUID格式，重新生成
                    import uuid
                    try:
                        # 尝试解析为UUID，如果失败则重新生成
                        uuid_obj = uuid.UUID(msg.get('id', ''))
                        # 检查UUID版本，确保是随机UUID（版本4）
                        if uuid_obj.version != 4:
                            msg['id'] = str(uuid.uuid4())
                    except (ValueError, AttributeError):
                        # 如果id不是有效的UUID，生成新的UUID
                        msg['id'] = str(uuid.uuid4())
                    message_ids.append(msg['id'])
                
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
                    # 兼容处理：如果没有'content'字段，尝试使用'message'字段
                    msg_content = message.get('content', message.get('message', ''))
                    # 兼容处理：如果没有'timestamp'字段，使用当前时间
                    timestamp = message.get('timestamp', datetime.now().isoformat())
                    
                    # 确保created_at是正确的ISO格式，添加兼容处理
                    created_at = message.get('created_at', datetime.now())
                    created_at_str = created_at.isoformat() if isinstance(created_at, datetime) else created_at
                    
                    response_time = message.get('response_time')
                    
                    if msg_id in existing_ids:
                        # 添加到更新列表
                        update_data.append((sender, msg_content, timestamp, created_at_str, response_time, msg_id))
                    else:
                        # 添加到插入列表
                        insert_data.append((msg_id, sender, msg_content, timestamp, created_at_str, response_time, session_id))
                
                # 执行批量插入或更新 - 使用INSERT ... ON DUPLICATE KEY UPDATE避免主键冲突
                if insert_data:
                    total_count = len(insert_data)
                    # 使用INSERT ... ON DUPLICATE KEY UPDATE，避免主键冲突
                    self.cursor.executemany(
                        "INSERT INTO conversation_history (id, sender, message, timestamp, "
                        "created_at, response_time, session_id) VALUES (%s, %s, %s, %s, %s, %s, %s) "
                        "ON DUPLICATE KEY UPDATE sender = VALUES(sender), message = VALUES(message), "
                        "timestamp = VALUES(timestamp), created_at = VALUES(created_at), "
                        "response_time = VALUES(response_time), session_id = VALUES(session_id)",
                        insert_data
                    )
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"已处理{total_count}条消息（插入或更新）", "INFO")
                
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
                            'content': row[2],  # 使用'content'字段，保持本地一致性
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
                    
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info(f"已从数据库下载{len(downloaded_history)}条对话历史", "INFO")
            
            return True
        
        except Exception as e:
            self.connection.rollback()
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"同步对话历史失败: {str(e)}", "ERROR")
            return False
    
    def sync_memories(self, upload=True, download=False):
        """同步记忆数据"""
        if not self.is_connected:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info("未连接到数据库，无法同步记忆数据", "WARNING")
            return False
        
        try:
            if upload:
                # 检查chatbot是否有相关方法
                if hasattr(self.chatbot, 'load_personal_info') and hasattr(self.chatbot, 'load_task_records'):
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
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info("记忆数据已上传到数据库", "INFO")
                else:
                    if hasattr(self.chatbot, 'add_debug_info'):
                        self.chatbot.add_debug_info("chatbot没有记忆数据相关方法，跳过记忆数据同步", "WARNING")
            
            if download:
                # 下载记忆数据
                self.cursor.execute("SELECT id, memory_type, memory_data FROM memories")
                rows = self.cursor.fetchall()
                
                for row in rows:
                    memory_id, memory_type, memory_data = row
                    if memory_id == 'personal_info' and hasattr(self.chatbot, 'save_personal_info'):
                        # 保存个人信息
                        self.chatbot.save_personal_info(json.loads(memory_data))
                    elif memory_id == 'task_records' and hasattr(self.chatbot, 'save_task_records'):
                        # 保存任务记录
                        self.chatbot.save_task_records(json.loads(memory_data))
                
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info(f"已从数据库下载{len(rows)}条记忆数据", "INFO")
            
            return True
        
        except Exception as e:
            self.connection.rollback()
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"同步记忆数据失败: {str(e)}", "ERROR")
            return False
    
    def _sync_all(self, upload=True, download=False):
        """内部同步所有数据方法，在后台线程中执行"""
        sync_results = {
            'config': True,
            'conversations': True,
            'memories': True
        }
        
        # 检查是否需要中断
        if hasattr(self, 'sync_thread') and hasattr(self.sync_thread, 'abort') and self.sync_thread.abort:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info("同步操作已被中断", "INFO")
            return False
        
        try:
            # 同步配置
            if self.db_config.get('sync_config', True):
                sync_results['config'] = self.sync_config(upload=upload, download=download)
            
            # 同步对话历史
            if self.db_config.get('sync_conversations', True):
                sync_results['conversations'] = self.sync_conversations(upload=upload, download=download)
            
            # 同步记忆数据
            if self.db_config.get('sync_memories', True):
                sync_results['memories'] = self.sync_memories(upload=upload, download=download)
            
            # 只要有一个同步成功，就返回True
            return any(sync_results.values())
        
        except Exception as e:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"同步所有数据失败: {str(e)}", "ERROR")
            return False
    
    def sync_all(self, upload=True, download=False):
        """同步所有数据，在后台线程中执行"""
        try:
            # 检查是否已有同步线程在运行
            if self.sync_thread and self.sync_thread.isRunning():
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info("已有同步线程在运行，请勿重复启动", "WARNING")
                return False
            
            # 创建并启动后台同步线程
            self.sync_thread = DatabaseSyncThread(self, upload, download)
            
            # 连接信号槽处理同步完成
            def on_sync_complete(success, message, result):
                if hasattr(self.chatbot, 'add_debug_info'):
                    self.chatbot.add_debug_info(f"后台同步{message}", "INFO" if success else "ERROR")
                # 清除线程引用
                self.sync_thread = None
            
            self.sync_thread.task_complete.connect(on_sync_complete)
            self.sync_thread.start()
            
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"已启动后台同步线程，上传: {upload}, 下载: {download}", "INFO")
            return True
        except Exception as e:
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"启动同步线程失败: {str(e)}", "ERROR")
            # 确保线程引用被清除
            self.sync_thread = None
            return False
    
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
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"数据库连接已断开: {str(e)}", "WARNING")
            self.is_connected = False
            return False
    
    def setup_sync_timer(self):
        """设置自动同步定时器"""
        from PyQt6.QtCore import QTimer
        
        # 停止现有的定时器
        if hasattr(self, 'sync_timer') and self.sync_timer:
            self.sync_timer.stop()
            self.sync_timer.deleteLater()
            self.sync_timer = None
        
        # 如果启用了数据库，设置自动同步定时器
        if self.db_config.get('enabled', False):
            sync_interval = self.db_config.get('sync_interval', 300)  # 默认300秒
            # 创建QTimer时不传递self，因为DatabaseManager不是QObject
            self.sync_timer = QTimer()
            self.sync_timer.timeout.connect(self.sync_all)
            self.sync_timer.start(sync_interval * 1000)  # 转换为毫秒
            if hasattr(self.chatbot, 'add_debug_info'):
                self.chatbot.add_debug_info(f"已启动自动同步定时器，间隔: {sync_interval}秒", "INFO")
