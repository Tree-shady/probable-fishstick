#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import requests
import sys

class AIChat:
    def __init__(self):
        self.config_file = 'config.json'
        self.config = self.load_config()
        self.conversation_history = []
        
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
        
        # 更新对话历史
        self.conversation_history.append({"role": "user", "content": message})
        
        data = {
            "model": self.config["model"],
            "messages": self.conversation_history,
            "temperature": self.config["temperature"],
            "max_tokens": self.config["max_tokens"]
        }
        
        try:
            response = requests.post(
                self.config["api_url"],
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()  # 检查HTTP错误
            
            # 打印原始响应内容用于调试
            raw_response = response.text
            print(f"API原始响应: {raw_response}")
            
            result = response.json()
            
            # 检查是否为iflow.cn平台响应格式
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
                                                return assistant_message
                            elif "content" in body:
                                # 直接返回content内容
                                assistant_message = body["content"]
                                # 更新对话历史
                                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                                return assistant_message
                    
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
                                return assistant_message
                
                # 处理其他可能的响应格式
                elif "content" in result:
                    # 直接返回content内容
                    assistant_message = result["content"]
                    # 更新对话历史
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                    return assistant_message
            
            # 响应格式不符合预期，提供更详细的错误信息
            return f"API返回格式异常。原始响应: {raw_response[:200]}...请检查配置和网络连接。"
                
        except requests.exceptions.RequestException as e:
            return f"API调用失败: {str(e)}"
        except json.JSONDecodeError:
            return "API返回格式错误，无法解析。"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("\n对话历史已清空！")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n=== 命令帮助 ===")
        print("/config    - 更新API配置")
        print("/clear     - 清空对话历史")
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
                    elif command == "/help":
                        self.show_help()
                    elif command == "/exit":
                        print("\n再见！")
                        break
                    else:
                        print(f"未知命令: {user_input}，输入 /help 查看帮助")
                else:
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
