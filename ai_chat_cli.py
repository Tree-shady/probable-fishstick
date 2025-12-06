#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
import sys

class AIChat:
    def __init__(self):
        self.config_file = 'config.json'
        self.history_file = 'conversation_history.json'
        self.config = self.load_config()
        self.conversation_history = self.load_history()
        
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "api_url": "https://api.openai.com/v1/chat/completions",
            "api_key": "",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 合并默认配置和用户配置
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
        else:
            # 保存默认配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def fix_history_roles(self, history):
        """修正对话历史中的role值，确保符合API规范"""
        fixed_history = []
        for message in history:
            if isinstance(message, dict):
                # 确保消息有role和content字段
                if "role" in message and "content" in message:
                    # 根据OpenAI API规范，role应该是'user', 'assistant', 'system'之一
                    role = message["role"]
                    if role == "ai":
                        role = "assistant"
                    fixed_history.append({
                        "role": role,
                        "content": message["content"]
                    })
        return fixed_history
    
    def load_history(self):
        """加载对话历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # 修正对话历史中的role值，确保符合API规范
                fixed_history = self.fix_history_roles(history)
                
                print(f"\n已加载 {len(fixed_history)} 条对话历史")
                print(f"加载的对话历史: {json.dumps(fixed_history, ensure_ascii=False, indent=2)}")
                return fixed_history
            except json.JSONDecodeError:
                print(f"\n警告: 对话历史文件 {self.history_file} 格式错误，已重置")
                return []
            except Exception as e:
                print(f"\n警告: 加载对话历史失败: {str(e)}")
                return []
        return []
    
    def save_history_auto(self):
        """自动保存对话历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"\n警告: 自动保存对话历史失败: {str(e)}")
    
    def update_config(self):
        """更新配置"""
        print("\n=== 更新配置 ===")
        print("当前配置:")
        for key, value in self.config.items():
            print(f"{key}: {value}")
        
        print("\n输入新的配置值，直接回车保持当前值:")
        
        for key, current_value in self.config.items():
            if key == "api_key" and current_value:  # 隐藏现有API密钥
                prompt = f"{key} (当前: {'*'*len(current_value)}): "
            else:
                prompt = f"{key} (当前: {current_value}): "
            
            new_value = input(prompt).strip()
            if new_value:  # 只有输入了新值才更新
                if key in ["temperature", "max_tokens"]:
                    try:
                        if key == "temperature":
                            self.config[key] = float(new_value)
                        else:
                            self.config[key] = int(new_value)
                    except ValueError:
                        print(f"警告: {key} 必须是数字，保持当前值")
                else:
                    self.config[key] = new_value
        
        self.save_config()
        print("\n配置已保存！")
    
    def call_api(self, message):
        """调用AI API"""
        # 准备请求数据
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        # 注意：用户消息已经在run方法中添加到了conversation_history
        # 这里不需要再次添加，否则会导致消息重复
        
        data = {
            "model": self.config["model"],
            "messages": self.conversation_history,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }
        
        try:
            # 设置重试次数和超时时间
            max_retries = 3
            retry_delay = 2  # 重试间隔（秒）
            timeout = 60  # 超时时间（秒）
            
            # 重试机制
            for attempt in range(max_retries):
                try:
                    print(f"正在请求... (第{attempt+1}/{max_retries}次)", end="\r", flush=True)
                    response = requests.post(
                        self.config["api_url"],
                        headers=headers,
                        json=data,
                        timeout=timeout
                    )
                    response.raise_for_status()  # 检查HTTP错误
                    # 如果成功，跳出循环
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        # 还有重试机会
                        print(f"第{attempt+1}次请求失败，{retry_delay}秒后重试: {str(e)}")
                        import time
                        time.sleep(retry_delay)
                    else:
                        # 最后一次尝试失败，抛出异常
                        raise
            
            # 打印原始响应内容用于调试
            raw_response = response.text
            print(f"API原始响应: {raw_response}")
            
            result = response.json()
            
            # 检查是否为iflow.cn平台响应格式
            assistant_message = None
            if isinstance(result, dict):
                # 处理iflow.cn平台响应格式
                if "status" in result and "msg" in result:
                    status = result["status"]
                    msg = result["msg"]
                    
                    if status == "0" or status == 0:
                        # 成功响应，检查body字段
                        if "body" in result and isinstance(result["body"], dict):
                            body = result["body"]
                            # 检查是否包含choices或content字段
                            if "choices" in body:
                                choices = body["choices"]
                                if isinstance(choices, list) and len(choices) > 0:
                                    choice = choices[0]
                                    if isinstance(choice, dict):
                                        if "message" in choice and isinstance(choice["message"], dict):
                                            if "content" in choice["message"]:
                                                assistant_message = choice["message"]["content"]
                                                # 更新对话历史
                                                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                            elif "content" in body:
                                # 直接返回content内容
                                assistant_message = body["content"]
                                # 更新对话历史
                                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                    
                    # 处理错误响应
                    return f"API请求失败: {msg}"
                
                # 处理OpenAI API响应格式
                elif "choices" in result:
                    if isinstance(result["choices"], list) and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        if isinstance(choice, dict) and "message" in choice:
                            message = choice["message"]
                            if isinstance(message, dict) and "content" in message:
                                assistant_message = message["content"]
                                # 更新对话历史
                                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                # 处理其他可能的响应格式
                elif "content" in result:
                    # 直接返回content内容
                    assistant_message = result["content"]
                    # 更新对话历史
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            if assistant_message:
                # 检查并修正role值，确保符合API规范
                # 注意：用户消息的role已经在run方法中正确设置为'user'
                # 这里只需要确保assistant消息的role正确
                
                # 打印对话历史用于调试
                print(f"当前对话历史: {json.dumps(self.conversation_history, ensure_ascii=False, indent=2)}")
                print(f"当前对话历史长度: {len(self.conversation_history)}条消息")
                
                # 自动保存对话历史
                self.save_history_auto()
                return assistant_message
            
            # 响应格式不符合预期，提供更详细的错误信息
            return f"API返回格式异常。原始响应: {raw_response[:200]}...请检查配置和网络连接。"
                
        except requests.exceptions.RequestException as e:
            return f"API调用失败: {str(e)}"
        except json.JSONDecodeError:
            return "API返回格式错误，无法解析。"
    
    def clear_history(self):
        """清空对话历史"""
        # 保存当前历史
        self.save_history_auto()
        self.conversation_history = []
        print("\n对话历史已清空！")
    
    def new_conversation(self):
        """开始新对话"""
        confirm = input("\n确定要开始新对话吗？当前对话历史将被保存并重置 (y/n): ").strip().lower()
        if confirm == "y" or confirm == "yes":
            # 保存当前历史
            self.save_history_auto()
            # 清空对话历史
            self.conversation_history = []
            # 清空历史文件
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            print("\n已开始新对话！")
        else:
            print("\n取消开始新对话。")
    
    def save_history(self):
        """保存对话历史到文件"""
        if not self.conversation_history:
            print("\n对话历史为空，无需保存！")
            return
        
        filename = input("\n请输入保存文件名（默认：chat_history.json）: ").strip()
        if not filename:
            filename = "chat_history.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            print(f"\n对话历史已保存到 {filename}！")
        except Exception as e:
            print(f"\n保存对话历史失败: {str(e)}")
    
    def export_config(self):
        """导出配置到文件"""
        filename = input("\n请输入导出文件名（默认：config_export.json）: ").strip()
        if not filename:
            filename = "config_export.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"\n配置已导出到 {filename}！")
        except Exception as e:
            print(f"\n导出配置失败: {str(e)}")
    
    def import_config(self):
        """从文件导入配置"""
        filename = input("\n请输入导入文件名: ").strip()
        if not filename:
            print("\n请输入有效的文件名！")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 合并导入的配置
            self.config.update(imported_config)
            self.save_config()
            print(f"\n配置已从 {filename} 导入并保存！")
        except FileNotFoundError:
            print(f"\n文件 {filename} 不存在！")
        except json.JSONDecodeError:
            print(f"\n文件 {filename} 格式错误！")
        except Exception as e:
            print(f"\n导入配置失败: {str(e)}")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n=== 命令帮助 ===")
        print("/config    - 更新API配置")
        print("/clear     - 清空对话历史")
        print("/new       - 开始新对话")
        print("/save      - 保存对话历史到文件")
        print("/export    - 导出配置到文件")
        print("/import    - 从文件导入配置")
        print("/help      - 显示帮助信息")
        print("/exit      - 退出程序")
    
    def run(self):
        """运行对话程序"""
        print("\n=== AI对话软件 ===")
        print("支持自定义API大模型，输入 /help 查看命令")
        
        # 检查配置是否完整
        if not self.config["api_key"]:
            print("\n警告: API密钥未配置，请先使用 /config 命令配置")
        
        while True:
            try:
                user_input = input("\n你: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith("/"):
                    command = user_input.lower()
                    if command == "/config":
                        self.update_config()
                    elif command == "/clear":
                        self.clear_history()
                    elif command == "/new":
                        self.new_conversation()
                    elif command == "/save":
                        self.save_history()
                    elif command == "/export":
                        self.export_config()
                    elif command == "/import":
                        self.import_config()
                    elif command == "/help":
                        self.show_help()
                    elif command == "/exit":
                        # 保存当前历史
                        self.save_history_auto()
                        print("\n再见！")
                        break
                    else:
                        print(f"未知命令: {user_input}，输入 /help 查看帮助")
                else:
                    # 更新对话历史
                    self.conversation_history.append({"role": "user", "content": user_input})
                    # 自动保存对话历史
                    self.save_history_auto()
                    # 调用API获取回复
                    print("AI: ", end="", flush=True)
                    response = self.call_api(user_input)
                    print(response)
                    
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n程序错误: {str(e)}")
                print("输入 /help 查看帮助，或 /exit 退出程序")

if __name__ == "__main__":
    chat = AIChat()
    chat.run()
