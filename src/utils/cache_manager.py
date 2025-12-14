import os
import time
from typing import Dict, Any, List

class CacheManager:
    """智能缓存管理器，用于优化内存使用和加载速度"""
    
    def __init__(self):
        # 对话历史缓存
        self.conversation_cache = {
            "data": [],
            "last_updated": 0,
            "cache_size": 0
        }
        
        # 主题样式缓存
        self.theme_cache = {
            "styles": {},
            "last_updated": 0
        }
        
        # 缓存配置
        self.cache_config = {
            "max_conversation_size": 1000,  # 最大缓存对话数量
            "cache_ttl": 3600,  # 缓存过期时间（秒）
            "cleanup_interval": 300  # 缓存清理间隔（秒）
        }
        
        # 最后清理时间
        self.last_cleanup = time.time()
    
    def get_conversation_cache(self) -> List[Dict[str, Any]]:
        """获取对话历史缓存"""
        # 检查缓存是否过期
        if time.time() - self.conversation_cache["last_updated"] > self.cache_config["cache_ttl"]:
            return []
        
        return self.conversation_cache["data"]
    
    def update_conversation_cache(self, conversations: List[Dict[str, Any]]) -> None:
        """更新对话历史缓存"""
        # 如果对话数量超过最大缓存限制，只缓存最新的消息
        if len(conversations) > self.cache_config["max_conversation_size"]:
            conversations = conversations[-self.cache_config["max_conversation_size"]:]
        
        self.conversation_cache = {
            "data": conversations,
            "last_updated": time.time(),
            "cache_size": len(conversations)
        }
    
    def get_theme_style(self, theme_name: str, custom_theme: Dict[str, Any]) -> Dict[str, Any]:
        """获取主题样式缓存"""
        # 创建缓存键
        cache_key = f"{theme_name}_{str(sorted(custom_theme.items()))}"
        
        # 检查缓存是否存在且未过期
        if cache_key in self.theme_cache["styles"]:
            cache_entry = self.theme_cache["styles"][cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_config["cache_ttl"]:
                return cache_entry["style"]
        
        return None
    
    def update_theme_style(self, theme_name: str, custom_theme: Dict[str, Any], style: Dict[str, Any]) -> None:
        """更新主题样式缓存"""
        cache_key = f"{theme_name}_{str(sorted(custom_theme.items()))}"
        self.theme_cache["styles"][cache_key] = {
            "style": style,
            "timestamp": time.time()
        }
    
    def cleanup_cache(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        
        # 检查是否需要清理
        if current_time - self.last_cleanup < self.cache_config["cleanup_interval"]:
            return
        
        # 清理主题样式缓存
        expired_keys = []
        for key, entry in self.theme_cache["styles"].items():
            if current_time - entry["timestamp"] > self.cache_config["cache_ttl"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.theme_cache["styles"][key]
        
        # 更新最后清理时间
        self.last_cleanup = current_time
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        self.conversation_cache = {
            "data": [],
            "last_updated": 0,
            "cache_size": 0
        }
        
        self.theme_cache = {
            "styles": {},
            "last_updated": 0
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "conversation_cache_size": len(self.conversation_cache["data"]),
            "theme_cache_size": len(self.theme_cache["styles"]),
            "last_updated": self.conversation_cache["last_updated"],
            "last_cleanup": self.last_cleanup
        }
