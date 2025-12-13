import os
import json
from typing import Dict, Any
from ..utils.helpers import load_json_file, save_json_file, merge_dicts
from ..utils.encryption import EncryptionManager


class SettingsManager:
    """设置管理类，负责处理应用程序的所有设置"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.encryption_manager = EncryptionManager()
        self.default_settings: Dict[str, Any] = {
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
                'sync_memories': True,  # 同步记忆数据
                'sync_after_ai_response': False  # AI回答后自动同步数据库
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
        self.settings: Dict[str, Any] = self.default_settings.copy()
        self.platforms: Dict[str, Any] = {}
        self.load_settings()
    
    def load_settings(self) -> None:
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                config_data = load_json_file(self.config_file)
                
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
                    
                    # 解密所有平台的API密钥
                    for platform_name, platform_config in self.platforms.items():
                        if 'api_key' in platform_config:
                            platform_config['api_key'] = self.encryption_manager.decrypt(platform_config['api_key'])
                    
                    # 处理应用设置，使用递归合并确保所有默认设置都被包含
                    self.settings = merge_dicts(self.default_settings, config_data.get('settings', {}))
                    
                    # 解密数据库的用户名和密码
                    if 'database' in self.settings:
                        if 'username' in self.settings['database'] and self.settings['database']['username']:
                            self.settings['database']['username'] = self.encryption_manager.decrypt(self.settings['database']['username'])
                        if 'password' in self.settings['database'] and self.settings['database']['password']:
                            self.settings['database']['password'] = self.encryption_manager.decrypt(self.settings['database']['password'])
                else:
                    # 旧格式：直接包含平台配置
                    self.platforms = config_data
                    # 解密所有平台的API密钥
                    for platform_name, platform_config in self.platforms.items():
                        if 'api_key' in platform_config:
                            platform_config['api_key'] = self.encryption_manager.decrypt(platform_config['api_key'])
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
            print(f"加载配置失败: {str(e)}")
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
    
    def save_settings(self) -> None:
        """保存设置"""
        try:
            # 使用深拷贝创建平台配置副本，避免修改原始数据
            import copy
            temp_platforms = copy.deepcopy(self.platforms)
            temp_settings = copy.deepcopy(self.settings)
            
            # 对临时副本中的所有平台API密钥进行加密
            for platform_name, platform_config in temp_platforms.items():
                if 'api_key' in platform_config:
                    # 加密API密钥
                    platform_config['api_key'] = self.encryption_manager.encrypt(platform_config['api_key'])
            
            # 加密数据库的用户名和密码
            if 'database' in temp_settings:
                if 'username' in temp_settings['database'] and temp_settings['database']['username']:
                    temp_settings['database']['username'] = self.encryption_manager.encrypt(temp_settings['database']['username'])
                if 'password' in temp_settings['database'] and temp_settings['database']['password']:
                    temp_settings['database']['password'] = self.encryption_manager.encrypt(temp_settings['database']['password'])
            
            # 构建完整的配置数据
            config_data = {
                'platforms': temp_platforms,
                'settings': temp_settings
            }
            save_json_file(self.config_file, config_data)
        except Exception as e:
            print(f"保存设置失败: {str(e)}")
            raise e
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """更新设置"""
        self.settings = merge_dicts(self.settings, new_settings)
        self.save_settings()
    
    def reset_settings(self) -> None:
        """重置为默认设置"""
        self.settings = self.default_settings.copy()
        self.save_settings()
