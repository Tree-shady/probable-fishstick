#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
对话管理模块
用于管理多个对话，支持对话命名、分类、搜索等功能
"""

import json
import os
import re
from datetime import datetime


class ConversationManager:
    """对话管理器，用于管理多个对话"""
    
    def __init__(self, data_dir="conversations"):
        """初始化对话管理器"""
        self.data_dir = data_dir
        self.conversations_file = os.path.join(data_dir, "conversations.json")
        
        # 确保数据目录存在
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 加载对话列表
        self.conversations = self._load_conversations()
        
    def _load_conversations(self):
        """加载对话列表"""
        if os.path.exists(self.conversations_file):
            try:
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_conversations(self):
        """保存对话列表"""
        with open(self.conversations_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, indent=2, ensure_ascii=False)
    
    def generate_title(self, messages):
        """基于对话内容生成标题"""
        if not messages:
            return "空对话"
        
        # 找到第一条用户消息
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "").strip()
                if content:
                    # 提取前20个字符作为标题
                    if len(content) <= 20:
                        return content
                    return content[:20] + "..."
        
        return "未命名对话"
    
    def create_conversation(self, messages=None, title=None):
        """创建新对话"""
        if messages is None:
            messages = []
        
        # 生成对话ID
        conversation_id = f"conv_{len(self.conversations) + 1}"
        
        # 生成标题
        if not title:
            title = self.generate_title(messages)
        
        # 创建对话元数据
        conversation = {
            "id": conversation_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages_count": len(messages),
            "tags": [],
            "folder": "default",
            "file": f"{conversation_id}.json"
        }
        
        # 保存对话消息
        self.save_conversation(conversation_id, messages)
        
        # 添加到对话列表
        self.conversations[conversation_id] = conversation
        self._save_conversations()
        
        return conversation_id
    
    def save_conversation(self, conversation_id, messages):
        """保存对话消息"""
        file_path = os.path.join(self.data_dir, f"{conversation_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
    
    def load_conversation(self, conversation_id):
        """加载对话消息"""
        file_path = os.path.join(self.data_dir, f"{conversation_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def update_conversation(self, conversation_id, messages):
        """更新对话"""
        if conversation_id in self.conversations:
            # 保存对话消息
            self.save_conversation(conversation_id, messages)
            
            # 更新对话元数据
            self.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
            self.conversations[conversation_id]["messages_count"] = len(messages)
            
            # 如果标题是自动生成的，可以考虑更新标题
            if "自动生成" in self.conversations[conversation_id].get("title", ""):
                new_title = self.generate_title(messages)
                self.conversations[conversation_id]["title"] = new_title
            
            self._save_conversations()
    
    def delete_conversation(self, conversation_id):
        """删除对话"""
        if conversation_id in self.conversations:
            # 删除对话文件
            file_path = os.path.join(self.data_dir, f"{conversation_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从对话列表中移除
            del self.conversations[conversation_id]
            self._save_conversations()
    
    def rename_conversation(self, conversation_id, new_title):
        """重命名对话"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["title"] = new_title
            self._save_conversations()
    
    def add_tag(self, conversation_id, tag):
        """为对话添加标签"""
        if conversation_id in self.conversations:
            tags = self.conversations[conversation_id].get("tags", [])
            if tag not in tags:
                tags.append(tag)
                self.conversations[conversation_id]["tags"] = tags
                self._save_conversations()
    
    def remove_tag(self, conversation_id, tag):
        """移除对话标签"""
        if conversation_id in self.conversations:
            tags = self.conversations[conversation_id].get("tags", [])
            if tag in tags:
                tags.remove(tag)
                self.conversations[conversation_id]["tags"] = tags
                self._save_conversations()
    
    def move_to_folder(self, conversation_id, folder):
        """移动对话到指定文件夹"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["folder"] = folder
            self._save_conversations()
    
    def search_conversations(self, keyword):
        """搜索对话"""
        results = []
        keyword_lower = keyword.lower()
        
        for conversation_id, conversation in self.conversations.items():
            # 搜索标题
            if keyword_lower in conversation.get("title", "").lower():
                results.append(conversation)
                continue
            
            # 搜索消息内容
            messages = self.load_conversation(conversation_id)
            for message in messages:
                content = message.get("content", "").lower()
                if keyword_lower in content:
                    results.append(conversation)
                    break
        
        return results
    
    def get_conversations(self, folder=None, tags=None):
        """获取对话列表，支持按文件夹和标签过滤"""
        results = []
        
        for conversation in self.conversations.values():
            match = True
            
            # 按文件夹过滤
            if folder and conversation.get("folder") != folder:
                match = False
            
            # 按标签过滤
            if tags:
                conversation_tags = set(conversation.get("tags", []))
                if not set(tags).intersection(conversation_tags):
                    match = False
            
            if match:
                results.append(conversation)
        
        # 按更新时间排序
        results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return results
    
    def get_folders(self):
        """获取所有文件夹"""
        folders = set()
        for conversation in self.conversations.values():
            folders.add(conversation.get("folder", "default"))
        return sorted(list(folders))
    
    def get_tags(self):
        """获取所有标签"""
        tags = set()
        for conversation in self.conversations.values():
            for tag in conversation.get("tags", []):
                tags.add(tag)
        return sorted(list(tags))


if __name__ == "__main__":
    # 测试对话管理器
    manager = ConversationManager()
    
    # 创建测试对话
    test_messages = [
        {"role": "user", "content": "你好，什么是人工智能？", "id": "msg_1"},
        {"role": "assistant", "content": "人工智能是计算机科学的一个分支...", "id": "msg_2"}
    ]
    
    # 创建对话
    conversation_id = manager.create_conversation(test_messages)
    print(f"创建对话: {conversation_id}")
    
    # 获取对话列表
    conversations = manager.get_conversations()
    print(f"对话列表: {conversations}")
    
    # 搜索对话
    results = manager.search_conversations("人工智能")
    print(f"搜索结果: {results}")
    
    # 添加标签
    manager.add_tag(conversation_id, "科技")
    manager.add_tag(conversation_id, "AI")
    print(f"添加标签后: {manager.conversations[conversation_id]}")
    
    # 获取标签
    tags = manager.get_tags()
    print(f"所有标签: {tags}")
    
    # 搜索标签
    tag_results = manager.get_conversations(tags=["科技"])
    print(f"按标签搜索: {tag_results}")
