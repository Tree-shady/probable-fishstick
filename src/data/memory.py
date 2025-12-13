import os
from typing import Dict, Any, List
from ..utils.helpers import load_json_file, save_json_file

class MemoryManager:
    """记忆管理类，负责处理个人信息和任务记录"""
    
    def __init__(self, parent, memories_dir: str):
        self.parent = parent
        self.memories_dir = memories_dir
        # 确保记忆存储目录存在
        os.makedirs(self.memories_dir, exist_ok=True)
        
        # 个人信息和任务记录文件路径
        self.personal_info_file = os.path.join(self.memories_dir, "personal_info.json")
        self.task_records_file = os.path.join(self.memories_dir, "task_records.json")
    
    def load_personal_info(self) -> Dict[str, Any]:
        """加载个人信息"""
        return load_json_file(self.personal_info_file, {})
    
    def save_personal_info(self, personal_info: Dict[str, Any]) -> bool:
        """保存个人信息"""
        return save_json_file(self.personal_info_file, personal_info)
    
    def load_task_records(self) -> Dict[str, Any]:
        """加载任务记录"""
        return load_json_file(self.task_records_file, {"tasks": []})
    
    def save_task_records(self, task_records: Dict[str, Any]) -> bool:
        """保存任务记录"""
        return save_json_file(self.task_records_file, task_records)
    
    def add_task(self, task_content: str) -> bool:
        """添加新任务"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        tasks.append({
            "content": task_content,
            "completed": False,
            "timestamp": self.parent.get_current_timestamp()
        })
        task_records["tasks"] = tasks
        return self.save_task_records(task_records)
    
    def complete_task(self, task_index: int) -> bool:
        """标记任务为完成"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        if 0 <= task_index < len(tasks):
            tasks[task_index]["completed"] = True
            task_records["tasks"] = tasks
            return self.save_task_records(task_records)
        return False
    
    def delete_task(self, task_index: int) -> bool:
        """删除任务"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        if 0 <= task_index < len(tasks):
            tasks.pop(task_index)
            task_records["tasks"] = tasks
            return self.save_task_records(task_records)
        return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取未完成的任务"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        return [task for task in tasks if not task.get("completed", False)]
    
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """获取已完成的任务"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        return [task for task in tasks if task.get("completed", False)]
