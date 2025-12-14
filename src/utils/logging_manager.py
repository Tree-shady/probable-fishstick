import os
import time
import json
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime

class LoggingManager:
    """日志和审计管理类，负责记录用户活动、操作审计和日志导出"""
    
    def __init__(self):
        # 日志文件路径
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # 不同类型的日志文件
        self.activity_log_file = os.path.join(self.logs_dir, "activity.log")
        self.audit_log_file = os.path.join(self.logs_dir, "audit.log")
        self.error_log_file = os.path.join(self.logs_dir, "error.log")
        
        # 日志配置
        self.log_config = {
            "log_level": "INFO",  # 日志级别: DEBUG, INFO, WARNING, ERROR
            "max_log_size": 10 * 1024 * 1024,  # 最大日志文件大小 (10MB)
            "log_rotation": True,  # 启用日志轮转
            "log_formatter": "json"  # 日志格式: json, text
        }
        
        # 内存中的日志缓冲区
        self.activity_logs: List[Dict[str, str]] = []
        self.audit_logs: List[Dict[str, str]] = []
        self.error_logs: List[Dict[str, str]] = []
        
        # 日志级别映射
        self.log_levels = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3
        }
        
        # 线程锁，确保日志写入的线程安全
        self.lock = threading.Lock()
        
        # 日志计数器
        self.log_counter = {
            "activity": 0,
            "audit": 0,
            "error": 0
        }
    
    def _should_log(self, message_level: str) -> bool:
        """检查是否应该记录该级别的日志"""
        current_level = self.log_levels.get(self.log_config["log_level"], 1)
        message_level_value = self.log_levels.get(message_level, 1)
        return message_level_value >= current_level
    
    def _format_log_entry(self, log_type: str, level: str, message: str, **kwargs) -> Dict[str, str]:
        """格式化日志条目"""
        timestamp = time.time()
        timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        log_entry = {
            "timestamp": timestamp_str,
            "timestamp_unix": str(timestamp),
            "log_type": log_type,
            "level": level,
            "message": message
        }
        
        # 添加额外的关键字参数
        log_entry.update(kwargs)
        
        return log_entry
    
    def _write_log_to_file(self, log_file: str, log_entry: Dict[str, str]) -> None:
        """将日志写入文件"""
        try:
            with self.lock:
                # 检查日志文件大小，如果超过限制则轮转
                if os.path.exists(log_file) and os.path.getsize(log_file) > self.log_config["max_log_size"]:
                    self._rotate_log(log_file)
                
                with open(log_file, "a", encoding="utf-8") as f:
                    if self.log_config["log_formatter"] == "json":
                        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                    else:
                        # 文本格式
                        timestamp = log_entry["timestamp"]
                        level = log_entry["level"]
                        message = log_entry["message"]
                        extra_info = " ".join([f"{k}={v}" for k, v in log_entry.items() if k not in ["timestamp", "level", "message", "log_type"]])
                        if extra_info:
                            f.write(f"[{timestamp}] [{level}] {message} {extra_info}\n")
                        else:
                            f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")
    
    def _rotate_log(self, log_file: str) -> None:
        """轮转日志文件"""
        try:
            # 为当前日志文件添加时间戳后缀
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{log_file}.{timestamp}.bak"
            
            # 重命名当前日志文件
            if os.path.exists(log_file):
                os.rename(log_file, backup_file)
        except Exception as e:
            print(f"轮转日志文件失败: {str(e)}")
    
    def log_activity(self, message: str, level: str = "INFO", **kwargs) -> None:
        """记录用户活动日志"""
        if not self._should_log(level):
            return
        
        log_entry = self._format_log_entry("activity", level, message, **kwargs)
        
        # 添加到内存缓冲区
        self.activity_logs.append(log_entry)
        # 限制内存中日志数量
        if len(self.activity_logs) > 1000:
            self.activity_logs = self.activity_logs[-1000:]
        
        # 写入文件
        self._write_log_to_file(self.activity_log_file, log_entry)
        
        # 更新计数器
        self.log_counter["activity"] += 1
    
    def log_audit(self, operation: str, user: str, success: bool, **kwargs) -> None:
        """记录操作审计日志"""
        message = f"{operation} {'成功' if success else '失败'}"
        level = "INFO" if success else "ERROR"
        
        log_entry = self._format_log_entry("audit", level, message, operation=operation, user=user, success=str(success), **kwargs)
        
        # 添加到内存缓冲区
        self.audit_logs.append(log_entry)
        # 限制内存中日志数量
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
        
        # 写入文件
        self._write_log_to_file(self.audit_log_file, log_entry)
        
        # 更新计数器
        self.log_counter["audit"] += 1
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """记录错误日志"""
        if exception:
            message = f"{message}: {str(exception)}"
            kwargs["exception_type"] = type(exception).__name__
        
        log_entry = self._format_log_entry("error", "ERROR", message, **kwargs)
        
        # 添加到内存缓冲区
        self.error_logs.append(log_entry)
        # 限制内存中日志数量
        if len(self.error_logs) > 1000:
            self.error_logs = self.error_logs[-1000:]
        
        # 写入文件
        self._write_log_to_file(self.error_log_file, log_entry)
        
        # 更新计数器
        self.log_counter["error"] += 1
    
    def get_activity_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, str]]:
        """获取活动日志"""
        with self.lock:
            logs = self.activity_logs.copy()
            if level:
                logs = [log for log in logs if log["level"] == level]
            return logs[-limit:]
    
    def get_audit_logs(self, limit: int = 100, success: Optional[bool] = None) -> List[Dict[str, str]]:
        """获取审计日志"""
        with self.lock:
            logs = self.audit_logs.copy()
            if success is not None:
                logs = [log for log in logs if log.get("success") == str(success)]
            return logs[-limit:]
    
    def get_error_logs(self, limit: int = 100) -> List[Dict[str, str]]:
        """获取错误日志"""
        with self.lock:
            return self.error_logs[-limit:].copy()
    
    def export_logs(self, log_type: str = "all", format: str = "json", start_time: Optional[float] = None, end_time: Optional[float] = None) -> str:
        """导出日志"""
        try:
            # 确定要导出的日志文件
            log_files = []
            if log_type == "all" or log_type == "activity":
                log_files.append(self.activity_log_file)
            if log_type == "all" or log_type == "audit":
                log_files.append(self.audit_log_file)
            if log_type == "all" or log_type == "error":
                log_files.append(self.error_log_file)
            
            # 读取所有日志内容
            all_logs = []
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    log_entry = json.loads(line)
                                    # 过滤时间范围
                                    timestamp_unix = float(log_entry.get("timestamp_unix", 0))
                                    if (start_time is None or timestamp_unix >= start_time) and \
                                       (end_time is None or timestamp_unix <= end_time):
                                        all_logs.append(log_entry)
                                except json.JSONDecodeError:
                                    # 跳过无效的JSON行
                                    continue
            
            # 生成导出文件路径
            export_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = os.path.join(self.logs_dir, f"logs_export_{export_timestamp}.{format}")
            
            # 写入导出文件
            with open(export_file, "w", encoding="utf-8") as f:
                if format == "json":
                    json.dump(all_logs, f, ensure_ascii=False, indent=2)
                else:
                    # 文本格式导出
                    for log in all_logs:
                        timestamp = log.get("timestamp", "")
                        level = log.get("level", "")
                        message = log.get("message", "")
                        log_type = log.get("log_type", "")
                        f.write(f"[{timestamp}] [{log_type}] [{level}] {message}\n")
            
            return export_file
        except Exception as e:
            print(f"导出日志失败: {str(e)}")
            return ""
    
    def analyze_logs(self, log_type: str = "all", time_range: Optional[float] = 3600) -> Dict[str, Any]:
        """分析日志，生成统计报告"""
        try:
            # 确定分析的时间范围
            end_time = time.time()
            start_time = end_time - time_range if time_range else None
            
            # 读取并过滤日志
            all_logs = []
            if log_type == "all" or log_type == "activity":
                all_logs.extend(self._read_logs_from_file(self.activity_log_file, start_time, end_time))
            if log_type == "all" or log_type == "audit":
                all_logs.extend(self._read_logs_from_file(self.audit_log_file, start_time, end_time))
            if log_type == "all" or log_type == "error":
                all_logs.extend(self._read_logs_from_file(self.error_log_file, start_time, end_time))
            
            # 生成统计报告
            report = {
                "total_logs": len(all_logs),
                "time_range": time_range,
                "start_time": start_time,
                "end_time": end_time,
                "logs_by_level": {},
                "logs_by_type": {},
                "logs_by_hour": {},
                "top_operations": {},
                "error_count": 0
            }
            
            # 统计日志级别分布
            for log in all_logs:
                level = log.get("level", "")
                report["logs_by_level"][level] = report["logs_by_level"].get(level, 0) + 1
                
                log_type = log.get("log_type", "")
                report["logs_by_type"][log_type] = report["logs_by_type"].get(log_type, 0) + 1
                
                if level == "ERROR":
                    report["error_count"] += 1
                
                # 按小时统计
                timestamp_str = log.get("timestamp", "")
                if timestamp_str:
                    hour = timestamp_str[:13]  # YYYY-MM-DD HH
                    report["logs_by_hour"][hour] = report["logs_by_hour"].get(hour, 0) + 1
                
                # 统计操作类型（仅审计日志）
                operation = log.get("operation", "")
                if operation:
                    report["top_operations"][operation] = report["top_operations"].get(operation, 0) + 1
            
            # 排序统计结果
            report["top_operations"] = dict(sorted(report["top_operations"].items(), key=lambda x: x[1], reverse=True))
            report["logs_by_hour"] = dict(sorted(report["logs_by_hour"].items()))
            
            return report
        except Exception as e:
            print(f"分析日志失败: {str(e)}")
            return {}
    
    def _read_logs_from_file(self, log_file: str, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict[str, str]]:
        """从文件读取日志"""
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            timestamp_unix = float(log_entry.get("timestamp_unix", 0))
                            if (start_time is None or timestamp_unix >= start_time) and \
                               (end_time is None or timestamp_unix <= end_time):
                                logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        return logs
    
    def clear_logs(self, log_type: str = "all") -> bool:
        """清空日志"""
        try:
            with self.lock:
                if log_type == "all" or log_type == "activity":
                    self.activity_logs.clear()
                    open(self.activity_log_file, "w").close()  # 清空文件
                    self.log_counter["activity"] = 0
                
                if log_type == "all" or log_type == "audit":
                    self.audit_logs.clear()
                    open(self.audit_log_file, "w").close()  # 清空文件
                    self.log_counter["audit"] = 0
                
                if log_type == "all" or log_type == "error":
                    self.error_logs.clear()
                    open(self.error_log_file, "w").close()  # 清空文件
                    self.log_counter["error"] = 0
            
            return True
        except Exception as e:
            print(f"清空日志失败: {str(e)}")
            return False
    
    def get_log_stats(self) -> Dict[str, int]:
        """获取日志统计信息"""
        return self.log_counter.copy()
    
    def update_log_config(self, **kwargs) -> None:
        """更新日志配置"""
        with self.lock:
            self.log_config.update(kwargs)
    
    def log_user_activity(self, username: str, activity: str, **kwargs) -> None:
        """记录用户活动的便捷方法"""
        self.log_activity(f"用户活动: {activity}", "INFO", username=username, **kwargs)
    
    def log_operation(self, username: str, operation: str, success: bool, **kwargs) -> None:
        """记录操作审计的便捷方法"""
        self.log_audit(operation, username, success, **kwargs)
    
    def log_system_error(self, error: Exception, component: str, **kwargs) -> None:
        """记录系统错误的便捷方法"""
        self.log_error(f"系统错误 - {component}", error, component=component, **kwargs)
