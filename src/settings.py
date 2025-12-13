import os
import json
from .utils import load_json_file, save_json_file, merge_dicts


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
        self.load_settings()
    
    def load_settings(self):
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
                    # 处理应用设置，使用递归合并确保所有默认设置都被包含
                    self.settings = merge_dicts(self.default_settings, config_data.get('settings', {}))
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
    
    def save_settings(self):
        """保存设置"""
        try:
            # 构建完整的配置数据
            config_data = {
                'platforms': self.platforms,
                'settings': self.settings
            }
            save_json_file(self.config_file, config_data)
        except Exception as e:
            print(f"保存设置失败: {str(e)}")
            raise e
    
    def update_settings(self, new_settings):
        """更新设置"""
        self.settings = merge_dicts(self.settings, new_settings)
        self.save_settings()
    
    def reset_settings(self):
        """重置为默认设置"""
        self.settings = self.default_settings.copy()
        self.save_settings()
