#!/usr/bin/env python3
"""
简易命令行版本的对话助手
"""

import os
import json
import requests
import uuid
import time
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CliSettingsManager:
    """命令行版本的设置管理器"""
    
    def __init__(self, config_file):
        self.config_file = config_file
        self.settings = {
            'window': {'width': 1200, 'height': 800, 'auto_save': True},
            'appearance': {'theme': '默认主题', 'font': None, 'font_size': 12},
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
                'memory_type': 'short_term',
                'max_memory_length': 10,
                'max_tokens': 8192,
                'memory_persistence': True,
                'memory_retention_days': 7
            },
            'debug': {
                'enabled': True,
                'verbose': False,
                'log_level': 'INFO'
            },
            'shortcuts': {
                'send_message': 'Ctrl+Enter',
                'clear_chat': 'Ctrl+L',
                'copy_selected': 'Ctrl+C',
                'paste_text': 'Ctrl+V',
                'show_settings': 'Ctrl+S'
            }
        }
        self.platforms = {}
        self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 检查配置格式
                if 'platforms' in config_data:
                    self.platforms = config_data.get('platforms', {})
                    self.settings = self._merge_settings(self.settings, config_data.get('settings', {}))
                else:
                    # 旧格式
                    self.platforms = config_data
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
            print(f"加载配置失败: {str(e)}")
            # 使用默认设置
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
    
    def _merge_settings(self, default, user):
        """递归合并设置"""
        result = default.copy()
        for key, value in user.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result

class CliChatbot:
    """命令行版本的对话助手"""
    
    def __init__(self):
        # 配置文件路径
        self.config_file = os.path.join(os.getcwd(), "chatbot_config.json")
        # 初始化设置管理器
        self.settings_manager = CliSettingsManager(self.config_file)
        self.settings = self.settings_manager.settings
        self.platforms = self.settings_manager.platforms
        
        # 选择默认平台
        self.selected_platform = None
        self.selected_model = None
        self.api_key = None
        self.base_url = None
        
        # 初始化对话历史
        self.conversation_history = []
        
        # 打印欢迎信息
        self.print_welcome()
        # 配置平台
        self.setup_platform()
    
    def print_welcome(self):
        """打印欢迎信息"""
        print("=" * 50)
        print("🤖 简易命令行对话助手")
        print("=" * 50)
        print("可用命令:")
        print("  /help - 显示帮助信息")
        print("  /platform - 查看和切换平台")
        print("  /model - 查看和切换模型")
        print("  /history - 查看对话历史")
        print("  /clear - 清空对话历史")
        print("  /exit - 退出程序")
        print("=" * 50)
    
    def save_settings(self):
        """保存设置到配置文件"""
        try:
            config_data = {
                'platforms': self.platforms,
                'settings': self.settings
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
    
    def setup_platform(self):
        """设置平台和模型"""
        # 显示可用平台
        print("\n可用平台:")
        available_platforms = [p for p, config in self.platforms.items() if config['enabled']]
        
        if not available_platforms:
            print("没有可用平台，请检查配置文件")
            exit(1)
        
        for i, platform in enumerate(available_platforms):
            print(f"  {i+1}. {platform}")
        
        # 选择平台
        choice = input(f"请选择平台 (1-{len(available_platforms)}, 默认1): ")
        if choice.strip():
            try:
                index = int(choice) - 1
                if 0 <= index < len(available_platforms):
                    self.selected_platform = available_platforms[index]
                else:
                    print("无效选择，使用默认平台")
                    self.selected_platform = available_platforms[0]
            except ValueError:
                print("无效输入，使用默认平台")
                self.selected_platform = available_platforms[0]
        else:
            self.selected_platform = available_platforms[0]
        
        platform_config = self.platforms[self.selected_platform]
        print(f"\n已选择平台: {self.selected_platform}")
        print(f"平台名称: {platform_config['name']}")
        print(f"API地址: {platform_config['base_url']}")
        
        # 检查是否已保存API密钥
        saved_api_key = platform_config.get('api_key', '')
        use_saved = False
        
        if saved_api_key:
            # 询问是否使用已保存的API密钥
            use_saved_input = input(f"已检测到保存的API密钥，是否使用？ (y/n, 默认y): ")
            if use_saved_input.strip().lower() in ['', 'y', 'yes']:
                use_saved = True
                self.api_key = saved_api_key
                print("使用已保存的API密钥")
        
        # 输入API密钥（如果未使用保存的）
        if not use_saved:
            api_key_hint = platform_config.get('api_key_hint', '')
            self.api_key = input(f"请输入API密钥 (示例: {api_key_hint}): ")
            if not self.api_key.strip():
                print("API密钥不能为空")
                exit(1)
            
            self.api_key = self.api_key.strip()
            
            # 询问是否保存API密钥
            save_input = input(f"是否保存API密钥到配置文件？ (y/n, 默认n): ")
            if save_input.strip().lower() in ['y', 'yes']:
                # 保存API密钥到平台配置
                platform_config['api_key'] = self.api_key
                self.save_settings()
                print("API密钥已保存")
        
        self.base_url = platform_config['base_url']
        
        # 选择模型
        models = platform_config['models']
        print(f"\n可用模型:")
        for i, model in enumerate(models):
            print(f"  {i+1}. {model}")
        
        # 检查是否已保存模型
        saved_model = platform_config.get('selected_model', '')
        model_choice = input(f"请选择模型 (1-{len(models)}, 默认1, 已保存: {saved_model if saved_model else '无'}): ")
        
        if model_choice.strip():
            try:
                index = int(model_choice) - 1
                if 0 <= index < len(models):
                    self.selected_model = models[index]
                else:
                    print("无效选择，使用默认模型")
                    self.selected_model = models[0]
            except ValueError:
                print("无效输入，使用默认模型")
                self.selected_model = models[0]
        else:
            # 如果有保存的模型，使用保存的，否则使用默认
            if saved_model and saved_model in models:
                self.selected_model = saved_model
                print(f"使用已保存的模型: {self.selected_model}")
            else:
                self.selected_model = models[0]
        
        # 保存当前选择的模型
        platform_config['selected_model'] = self.selected_model
        self.save_settings()
        
        print(f"\n已选择模型: {self.selected_model}")
        print("=" * 50)
    
    def call_ai_api(self, message):
        """调用AI API"""
        try:
            # 构建API URL
            if "/chat/completions" in self.base_url:
                api_url = self.base_url
            else:
                api_url = f"{self.base_url}/chat/completions"
            
            # 创建请求数据
            payload = {
                "model": self.selected_model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "stream": self.settings['chat']['streaming']
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                verify=False,  # 不验证SSL证书
                timeout=self.settings['network']['timeout'],
                stream=self.settings['chat']['streaming']
            )
            
            if response.status_code == 200:
                if self.settings['chat']['streaming']:
                    return self.handle_streaming_response(response)
                else:
                    return self.handle_non_streaming_response(response)
            else:
                return f"API错误: {response.status_code} - {response.text}"
        
        except Exception as e:
            return f"调用API失败: {str(e)}"
    
    def handle_streaming_response(self, response):
        """处理流式响应"""
        print("AI: ", end="", flush=True)
        ai_response = ""
        
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    chunk_str = chunk.decode('utf-8')
                    events = chunk_str.split('data: ')
                    
                    for event in events:
                        event = event.strip()
                        if event and event != '[DONE]':
                            try:
                                data = json.loads(event)
                                if 'choices' in data and data['choices']:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        print(content, end="", flush=True)
                                        ai_response += content
                            except json.JSONDecodeError:
                                continue
            print()
            return ai_response
        except Exception as e:
            return f"处理流式响应失败: {str(e)}"
    
    def handle_non_streaming_response(self, response):
        """处理非流式响应"""
        try:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            print(f"AI: {ai_response}")
            return ai_response
        except Exception as e:
            return f"处理响应失败: {str(e)}"
    
    def run(self):
        """运行对话循环"""
        while True:
            try:
                user_input = input("\n你: ")
                
                if not user_input.strip():
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                    continue
                
                # 调用AI API
                ai_response = self.call_ai_api(user_input)
                
                # 保存对话历史
                self.conversation_history.append({
                    'id': str(uuid.uuid4()),
                    'sender': '用户',
                    'message': user_input,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                self.conversation_history.append({
                    'id': str(uuid.uuid4()),
                    'sender': 'AI',
                    'message': ai_response,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
            except KeyboardInterrupt:
                print("\n\n程序已退出")
                break
    
    def handle_command(self, command):
        """处理命令"""
        cmd = command.strip().lower()
        
        if cmd == '/help':
            self.print_welcome()
        elif cmd == '/platform':
            self.setup_platform()
        elif cmd == '/model':
            # 显示可用模型
            if self.selected_platform:
                models = self.platforms[self.selected_platform]['models']
                print("\n可用模型:")
                for i, model in enumerate(models):
                    print(f"  {i+1}. {model}")
                
                # 选择模型
                choice = input(f"请选择模型 (1-{len(models)}, 默认当前): ")
                if choice.strip():
                    try:
                        index = int(choice) - 1
                        if 0 <= index < len(models):
                            self.selected_model = models[index]
                            print(f"已切换到模型: {self.selected_model}")
                        else:
                            print("无效选择")
                    except ValueError:
                        print("无效输入")
            else:
                print("未选择平台")
        elif cmd == '/history':
            print("\n对话历史:")
            if not self.conversation_history:
                print("  暂无对话历史")
            else:
                for msg in self.conversation_history:
                    print(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}")
        elif cmd == '/clear':
            self.conversation_history = []
            print("对话历史已清空")
        elif cmd == '/exit':
            print("程序已退出")
            exit(0)
        else:
            print(f"未知命令: {command}")
            print("可用命令: /help, /platform, /model, /history, /clear, /exit")

if __name__ == "__main__":
    chatbot = CliChatbot()
    chatbot.run()
