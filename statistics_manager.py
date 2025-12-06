#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统计管理模块
用于管理对话统计数据，生成统计报告和图表
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import statistics


class StatisticsManager:
    """统计管理器，用于生成和管理统计数据"""
    
    def __init__(self, conversation_manager):
        """初始化统计管理器"""
        self.conversation_manager = conversation_manager
    
    def get_conversation_statistics(self):
        """获取对话统计数据"""
        conversations = self.conversation_manager.get_conversations()
        total_conversations = len(conversations)
        
        # 按文件夹统计
        folder_stats = defaultdict(int)
        for conv in conversations:
            folder = conv.get("folder", "default")
            folder_stats[folder] += 1
        
        # 按标签统计
        tag_stats = defaultdict(int)
        for conv in conversations:
            tags = conv.get("tags", [])
            for tag in tags:
                tag_stats[tag] += 1
        
        return {
            "total_conversations": total_conversations,
            "folder_stats": dict(folder_stats),
            "tag_stats": dict(tag_stats)
        }
    
    def get_message_statistics(self):
        """获取消息统计数据"""
        conversations = self.conversation_manager.get_conversations()
        total_messages = 0
        user_messages = 0
        assistant_messages = 0
        
        for conv in conversations:
            messages = self.conversation_manager.load_conversation(conv["id"])
            total_messages += len(messages)
            for msg in messages:
                if msg.get("role") == "user":
                    user_messages += 1
                elif msg.get("role") == "assistant":
                    assistant_messages += 1
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "message_ratio": user_messages / assistant_messages if assistant_messages > 0 else 0
        }
    
    def get_response_time_statistics(self):
        """获取响应时间统计数据"""
        conversations = self.conversation_manager.get_conversations()
        response_times = []
        
        for conv in conversations:
            messages = self.conversation_manager.load_conversation(conv["id"])
            
            # 按时间顺序排序消息
            messages.sort(key=lambda x: x.get("timestamp", ""))
            
            # 计算每条用户消息后的AI响应时间
            for i in range(len(messages) - 1):
                if messages[i].get("role") == "user" and messages[i+1].get("role") == "assistant":
                    try:
                        user_time = datetime.fromisoformat(messages[i]["timestamp"])
                        assistant_time = datetime.fromisoformat(messages[i+1]["timestamp"])
                        response_time = (assistant_time - user_time).total_seconds()
                        if response_time > 0:  # 只统计有效的响应时间
                            response_times.append(response_time)
                    except (ValueError, KeyError):
                        # 跳过缺少时间戳的消息
                        continue
        
        if not response_times:
            return {
                "total_responses": 0,
                "average_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "median_response_time": 0,
                "response_times": []
            }
        
        return {
            "total_responses": len(response_times),
            "average_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "median_response_time": statistics.median(response_times),
            "response_times": response_times
        }
    
    def get_conversation_duration_statistics(self):
        """获取对话时长统计数据"""
        conversations = self.conversation_manager.get_conversations()
        durations = []
        
        for conv in conversations:
            messages = self.conversation_manager.load_conversation(conv["id"])
            if len(messages) < 2:
                continue
            
            try:
                # 获取第一条和最后一条消息的时间戳
                first_time = datetime.fromisoformat(messages[0]["timestamp"])
                last_time = datetime.fromisoformat(messages[-1]["timestamp"])
                duration = (last_time - first_time).total_seconds()
                if duration > 0:  # 只统计有效的对话时长
                    durations.append(duration)
            except (ValueError, KeyError):
                # 跳过缺少时间戳的对话
                continue
        
        if not durations:
            return {
                "total_durations": 0,
                "average_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "median_duration": 0,
                "durations": []
            }
        
        return {
            "total_durations": len(durations),
            "average_duration": statistics.mean(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "median_duration": statistics.median(durations),
            "durations": durations
        }
    
    def get_activity_statistics(self):
        """获取活跃度统计数据"""
        conversations = self.conversation_manager.get_conversations()
        activity_by_date = defaultdict(int)
        
        for conv in conversations:
            try:
                # 使用创建日期作为统计依据
                created_at = conv["created_at"]
                date = created_at.split("T")[0]  # 只取日期部分
                activity_by_date[date] += 1
            except (ValueError, KeyError):
                continue
        
        # 按日期排序
        sorted_activity = sorted(activity_by_date.items(), key=lambda x: x[0])
        dates = [item[0] for item in sorted_activity]
        counts = [item[1] for item in sorted_activity]
        
        return {
            "activity_by_date": dict(activity_by_date),
            "dates": dates,
            "counts": counts
        }
    
    def get_all_statistics(self):
        """获取所有统计数据"""
        return {
            "conversation_stats": self.get_conversation_statistics(),
            "message_stats": self.get_message_statistics(),
            "response_time_stats": self.get_response_time_statistics(),
            "conversation_duration_stats": self.get_conversation_duration_statistics(),
            "activity_stats": self.get_activity_statistics(),
            "generated_at": datetime.datetime.now().isoformat()
        }
    
    def export_statistics(self, file_path):
        """导出统计数据到JSON文件"""
        stats = self.get_all_statistics()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def generate_statistics_report(self):
        """生成统计报告文本"""
        stats = self.get_all_statistics()
        
        report = """# AI对话软件统计报告

## 生成时间
{generated_at}

## 对话统计
- 总对话数: {total_conversations}

### 按文件夹统计
{folder_stats}

### 按标签统计
{tag_stats}

## 消息统计
- 总消息数: {total_messages}
- 用户消息数: {user_messages}
- AI消息数: {assistant_messages}
- 消息比例(用户:AI): {message_ratio:.2f}:1

## 响应时间统计
- 总响应次数: {total_responses}
- 平均响应时间: {average_response_time:.2f}秒
- 最短响应时间: {min_response_time:.2f}秒
- 最长响应时间: {max_response_time:.2f}秒
- 中位数响应时间: {median_response_time:.2f}秒

## 对话时长统计
- 有效对话数: {total_durations}
- 平均对话时长: {average_duration:.2f}秒
- 最短对话时长: {min_duration:.2f}秒
- 最长对话时长: {max_duration:.2f}秒
- 中位数对话时长: {median_duration:.2f}秒

## 活跃度统计
- 活跃日期数: {active_days}
- 最活跃日期: {most_active_date}
- 当日对话数: {most_active_count}

## 按日期活跃度
{activity_by_date}

"""
        
        # 格式化文件夹统计
        folder_stats_text = ""
        for folder, count in stats["conversation_stats"]["folder_stats"].items():
            folder_stats_text += f"  - {folder}: {count}\n"
        
        # 格式化标签统计
        tag_stats_text = ""
        for tag, count in stats["conversation_stats"]["tag_stats"].items():
            tag_stats_text += f"  - {tag}: {count}\n"
        
        # 格式化活跃度统计
        activity_by_date_text = ""
        for date, count in zip(stats["activity_stats"]["dates"], stats["activity_stats"]["counts"]):
            activity_by_date_text += f"  - {date}: {count}\n"
        
        # 计算最活跃日期
        if stats["activity_stats"]["dates"]:
            most_active_index = stats["activity_stats"]["counts"].index(max(stats["activity_stats"]["counts"]))
            most_active_date = stats["activity_stats"]["dates"][most_active_index]
            most_active_count = stats["activity_stats"]["counts"][most_active_index]
        else:
            most_active_date = "无数据"
            most_active_count = 0
        
        return report.format(
            generated_at=stats["generated_at"],
            total_conversations=stats["conversation_stats"]["total_conversations"],
            folder_stats=folder_stats_text.strip(),
            tag_stats=tag_stats_text.strip(),
            total_messages=stats["message_stats"]["total_messages"],
            user_messages=stats["message_stats"]["user_messages"],
            assistant_messages=stats["message_stats"]["assistant_messages"],
            message_ratio=stats["message_stats"]["message_ratio"],
            total_responses=stats["response_time_stats"]["total_responses"],
            average_response_time=stats["response_time_stats"]["average_response_time"],
            min_response_time=stats["response_time_stats"]["min_response_time"],
            max_response_time=stats["response_time_stats"]["max_response_time"],
            median_response_time=stats["response_time_stats"]["median_response_time"],
            total_durations=stats["conversation_duration_stats"]["total_durations"],
            average_duration=stats["conversation_duration_stats"]["average_duration"],
            min_duration=stats["conversation_duration_stats"]["min_duration"],
            max_duration=stats["conversation_duration_stats"]["max_duration"],
            median_duration=stats["conversation_duration_stats"]["median_duration"],
            active_days=len(stats["activity_stats"]["dates"]),
            most_active_date=most_active_date,
            most_active_count=most_active_count,
            activity_by_date=activity_by_date_text.strip()
        )
