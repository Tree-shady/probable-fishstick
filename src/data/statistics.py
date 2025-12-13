from typing import Dict, Any, List
from datetime import datetime, timedelta

class StatisticsManager:
    """统计管理类，负责处理对话统计信息"""
    
    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
    
    def update_conversation_history(self, history: List[Dict[str, Any]]) -> None:
        """更新对话历史"""
        self.conversation_history = history
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计概览"""
        total_messages = len(self.conversation_history)
        user_messages = sum(1 for msg in self.conversation_history if msg['sender'] == '用户')
        ai_messages = sum(1 for msg in self.conversation_history if msg['sender'] == 'AI')
        
        # 计算响应时间统计
        response_times = [msg.get('response_time', 0) for msg in self.conversation_history if msg['sender'] == 'AI' and msg.get('response_time') is not None]
        if response_times:
            avg_response_time = round(sum(response_times) / len(response_times), 2)
            min_response_time = round(min(response_times), 2)
            max_response_time = round(max(response_times), 2)
        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
        
        # 计算响应时间分布
        response_time_distribution = {
            'fast': sum(1 for rt in response_times if rt < 1),
            'normal': sum(1 for rt in response_times if 1 <= rt < 5),
            'slow': sum(1 for rt in response_times if 5 <= rt < 10),
            'very_slow': sum(1 for rt in response_times if rt >= 10)
        }
        
        # 计算总对话时长
        if total_messages >= 2:
            first_message_time = self._parse_timestamp(self.conversation_history[0].get('timestamp', ''))
            last_message_time = self._parse_timestamp(self.conversation_history[-1].get('timestamp', ''))
            if first_message_time and last_message_time:
                total_duration = round((last_message_time - first_message_time).total_seconds() / 60, 2)
            else:
                total_duration = 0
        else:
            total_duration = 0
        
        return {
            'total_conversations': max(1, len(self.conversation_history) // 2),  # 近似计算，每两条消息为一个对话
            'total_messages': total_messages,
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'average_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'response_time_distribution': response_time_distribution,
            'total_duration': total_duration
        }
    
    def get_daily_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取每日统计数据"""
        daily_stats: Dict[str, Dict[str, Any]] = {}
        
        for msg in self.conversation_history:
            timestamp = msg.get('timestamp', '')
            date = timestamp.split(' ')[0] if timestamp else ''
            
            if date:
                if date not in daily_stats:
                    daily_stats[date] = {
                        'messages': 0,
                        'user_messages': 0,
                        'ai_messages': 0,
                        'response_times': []
                    }
                
                daily_stats[date]['messages'] += 1
                if msg['sender'] == '用户':
                    daily_stats[date]['user_messages'] += 1
                elif msg['sender'] == 'AI':
                    daily_stats[date]['ai_messages'] += 1
                    if msg.get('response_time') is not None:
                        daily_stats[date]['response_times'].append(msg['response_time'])
        
        # 计算每日平均响应时间
        for date, stats in daily_stats.items():
            response_times = stats['response_times']
            if response_times:
                stats['average_response_time'] = round(sum(response_times) / len(response_times), 2)
            else:
                stats['average_response_time'] = 0
            del stats['response_times']
        
        return daily_stats
    
    def export_statistics(self, file_path: str) -> tuple[bool, str]:
        """导出统计报告"""
        try:
            from ..utils.helpers import save_json_file
            
            stats_data = {
                'summary': self.get_statistics_summary(),
                'daily_stats': self.get_daily_statistics(),
                'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if file_path.endswith('.json'):
                if save_json_file(file_path, stats_data):
                    return True, file_path
                else:
                    return False, "导出失败"
            else:
                # 导出为文本文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("===== 聊天助手统计报告 =====\n\n")
                    f.write(f"导出时间: {stats_data['export_time']}\n\n")
                    
                    f.write("=== 统计概览 ===\n")
                    summary = stats_data['summary']
                    f.write(f"总对话数: {summary['total_conversations']}\n")
                    f.write(f"总消息数: {summary['total_messages']}\n")
                    f.write(f"用户消息数: {summary['user_messages']}\n")
                    f.write(f"AI消息数: {summary['ai_messages']}\n")
                    f.write(f"平均响应时间: {summary['average_response_time']}秒\n")
                    f.write(f"最小响应时间: {summary['min_response_time']}秒\n")
                    f.write(f"最大响应时间: {summary['max_response_time']}秒\n")
                    f.write(f"总对话时长: {summary['total_duration']}分钟\n\n")
                    
                    f.write("=== 响应时间分布 ===\n")
                    distribution = summary['response_time_distribution']
                    f.write(f"快速 (< 1秒): {distribution['fast']}次\n")
                    f.write(f"正常 (1-5秒): {distribution['normal']}次\n")
                    f.write(f"较慢 (5-10秒): {distribution['slow']}次\n")
                    f.write(f"很慢 (> 10秒): {distribution['very_slow']}次\n\n")
                    
                    f.write("=== 每日统计 ===\n")
                    for date, stats in sorted(stats_data['daily_stats'].items()):
                        f.write(f"日期: {date}\n")
                        f.write(f"  - 消息总数: {stats['messages']}\n")
                        f.write(f"  - 用户消息: {stats['user_messages']}\n")
                        f.write(f"  - AI消息: {stats['ai_messages']}\n")
                        f.write(f"  - 平均响应时间: {stats['average_response_time']}秒\n\n")
                return True, file_path
        except Exception as e:
            return False, f"导出失败: {str(e)}"
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """解析时间戳字符串为datetime对象"""
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
