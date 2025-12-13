import datetime
import os
import json


class StatisticsManager:
    """统计管理类，负责计算和管理各种统计指标"""
    
    def __init__(self, conversation_history=None):
        self.conversation_history = conversation_history or []
        self._cached_stats = None  # 统计数据缓存
        self._cached_daily_stats = None  # 每日统计数据缓存
        self._cache_valid = False  # 缓存是否有效
    
    def update_conversation_history(self, history):
        """更新对话历史"""
        self.conversation_history = history
        self._cache_valid = False  # 缓存失效
    
    def get_total_conversations(self):
        """获取对话数量"""
        # 每个完整对话包含用户消息和AI回复，所以对话数量是AI消息数量
        return len([entry for entry in self.conversation_history if entry['sender'] == 'AI'])
    
    def get_total_messages(self):
        """获取总消息数量"""
        return len(self.conversation_history)
    
    def get_user_message_count(self):
        """获取用户消息数量"""
        return len([entry for entry in self.conversation_history if entry['sender'] == '用户'])
    
    def get_ai_message_count(self):
        """获取AI消息数量"""
        return len([entry for entry in self.conversation_history if entry['sender'] == 'AI'])
    
    def get_response_times(self):
        """获取所有有效响应时间"""
        return [entry.get('response_time') for entry in self.conversation_history 
                if entry['sender'] == 'AI' and entry.get('response_time') is not None]
    
    def get_average_response_time(self):
        """获取平均响应时间（秒）"""
        response_times = self.get_response_times()
        if not response_times:
            return 0
        return sum(response_times) / len(response_times)
    
    def get_min_response_time(self):
        """获取最小响应时间（秒）"""
        response_times = self.get_response_times()
        if not response_times:
            return 0
        return min(response_times)
    
    def get_max_response_time(self):
        """获取最大响应时间（秒）"""
        response_times = self.get_response_times()
        if not response_times:
            return 0
        return max(response_times)
    
    def get_response_time_distribution(self):
        """获取响应时间分布"""
        response_times = self.get_response_times()
        if not response_times:
            return {
                'fast': 0,    # < 1秒
                'normal': 0,  # 1-5秒
                'slow': 0,    # 5-10秒
                'very_slow': 0  # > 10秒
            }
        
        distribution = {
            'fast': 0,
            'normal': 0,
            'slow': 0,
            'very_slow': 0
        }
        
        for rt in response_times:
            if rt < 1:
                distribution['fast'] += 1
            elif rt < 5:
                distribution['normal'] += 1
            elif rt < 10:
                distribution['slow'] += 1
            else:
                distribution['very_slow'] += 1
        
        return distribution
    
    def get_total_conversation_duration(self):
        """获取总对话时长（分钟）"""
        if not self.conversation_history:
            return 0
        
        try:
            first_message = datetime.fromisoformat(self.conversation_history[0]['created_at'])
            last_message = datetime.fromisoformat(self.conversation_history[-1]['created_at'])
            duration = (last_message - first_message).total_seconds() / 60
            return duration
        except:
            return 0
    
    def get_statistics_summary(self):
        """获取统计摘要 - 使用缓存优化"""
        # 如果缓存有效，直接返回缓存数据
        if self._cache_valid and self._cached_stats:
            return self._cached_stats
        
        # 计算统计数据
        stats = {
            'total_conversations': self.get_total_conversations(),
            'total_messages': self.get_total_messages(),
            'user_messages': self.get_user_message_count(),
            'ai_messages': self.get_ai_message_count(),
            'average_response_time': round(self.get_average_response_time(), 2),
            'min_response_time': round(self.get_min_response_time(), 2),
            'max_response_time': round(self.get_max_response_time(), 2),
            'response_time_distribution': self.get_response_time_distribution(),
            'total_duration': round(self.get_total_conversation_duration(), 2)
        }
        
        # 更新缓存
        self._cached_stats = stats
        self._cache_valid = True
        
        return stats
    
    def get_daily_statistics(self):
        """获取每日统计数据 - 使用缓存优化"""
        # 如果缓存有效，直接返回缓存数据
        if self._cache_valid and self._cached_daily_stats:
            return self._cached_daily_stats
        
        # 计算每日统计数据
        daily_stats = {}
        
        for entry in self.conversation_history:
            try:
                date = datetime.fromisoformat(entry['created_at']).strftime('%Y-%m-%d')
                if date not in daily_stats:
                    daily_stats[date] = {
                        'messages': 0,
                        'user_messages': 0,
                        'ai_messages': 0,
                        'response_times': []
                    }
                
                daily_stats[date]['messages'] += 1
                if entry['sender'] == '用户':
                    daily_stats[date]['user_messages'] += 1
                elif entry['sender'] == 'AI':
                    daily_stats[date]['ai_messages'] += 1
                    if entry['response_time'] is not None:
                        daily_stats[date]['response_times'].append(entry['response_time'])
            except:
                continue
        
        # 计算每日平均响应时间
        for date, stats in daily_stats.items():
            if stats['response_times']:
                stats['average_response_time'] = round(sum(stats['response_times']) / len(stats['response_times']), 2)
            else:
                stats['average_response_time'] = 0
        
        # 更新缓存
        self._cached_daily_stats = daily_stats
        self._cache_valid = True
        
        return daily_stats
    
    def export_statistics(self, file_path=None, format='json'):
        """导出统计数据"""
        stats = {
            'summary': self.get_statistics_summary(),
            'daily_stats': self.get_daily_statistics(),
            'export_time': datetime.now().isoformat()
        }
        
        if not file_path:
            file_path = os.path.join(os.getcwd(), f"chat_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}")
        
        try:
            if format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                import csv
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['日期', '消息总数', '用户消息', 'AI消息', '平均响应时间'])
                    for date, data in stats['daily_stats'].items():
                        writer.writerow([
                            date,
                            data['messages'],
                            data['user_messages'],
                            data['ai_messages'],
                            data['average_response_time']
                        ])
            return True, file_path
        except Exception as e:
            return False, str(e)
