import os
import time
from typing import Dict, Any, List
from ..utils.helpers import load_json_file, save_json_file

class MemoryManager:
    """记忆管理类，负责处理个人信息、任务记录、日历事件和笔记"""
    
    def __init__(self, parent, memories_dir: str):
        self.parent = parent
        self.memories_dir = memories_dir
        # 确保记忆存储目录存在
        os.makedirs(self.memories_dir, exist_ok=True)
        
        # 个人信息和任务记录文件路径
        self.personal_info_file = os.path.join(self.memories_dir, "personal_info.json")
        self.task_records_file = os.path.join(self.memories_dir, "task_records.json")
        self.calendar_events_file = os.path.join(self.memories_dir, "calendar_events.json")
        self.notes_file = os.path.join(self.memories_dir, "notes.json")
    
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
            "id": f"task_{time.time()}_{id(task_content)}",
            "content": task_content,
            "completed": False,
            "timestamp": self.parent.get_current_timestamp(),
            "priority": "medium"
        })
        task_records["tasks"] = tasks
        return self.save_task_records(task_records)
    
    def complete_task(self, task_id: str) -> bool:
        """标记任务为完成"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        for task in tasks:
            if task.get("id") == task_id:
                task["completed"] = True
                task["completed_at"] = self.parent.get_current_timestamp()
                task_records["tasks"] = tasks
                return self.save_task_records(task_records)
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        task_records = self.load_task_records()
        tasks = task_records.get("tasks", [])
        tasks = [task for task in tasks if task.get("id") != task_id]
        task_records["tasks"] = tasks
        return self.save_task_records(task_records)
    
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
    
    # 日历事件相关方法
    def load_calendar_events(self) -> Dict[str, Any]:
        """加载日历事件"""
        return load_json_file(self.calendar_events_file, {"events": []})
    
    def save_calendar_events(self, events: Dict[str, Any]) -> bool:
        """保存日历事件"""
        return save_json_file(self.calendar_events_file, events)
    
    def add_calendar_event(self, event_title: str, event_date: str, event_time: str, event_description: str = "") -> bool:
        """添加日历事件"""
        events = self.load_calendar_events()
        event_list = events.get("events", [])
        event_list.append({
            "id": f"event_{time.time()}_{id(event_title)}",
            "title": event_title,
            "date": event_date,
            "time": event_time,
            "description": event_description,
            "timestamp": self.parent.get_current_timestamp(),
            "reminder": False
        })
        events["events"] = event_list
        return self.save_calendar_events(events)
    
    def get_calendar_events(self, date: str = None) -> List[Dict[str, Any]]:
        """获取日历事件，可选按日期筛选"""
        events = self.load_calendar_events()
        event_list = events.get("events", [])
        
        if date:
            return [event for event in event_list if event.get("date") == date]
        
        return event_list
    
    # 笔记应用相关方法
    def load_notes(self) -> Dict[str, Any]:
        """加载笔记"""
        return load_json_file(self.notes_file, {"notes": []})
    
    def save_notes(self, notes: Dict[str, Any]) -> bool:
        """保存笔记"""
        return save_json_file(self.notes_file, notes)
    
    def add_note(self, note_title: str, note_content: str) -> bool:
        """添加笔记"""
        notes = self.load_notes()
        note_list = notes.get("notes", [])
        note_list.append({
            "id": f"note_{time.time()}_{id(note_title)}",
            "title": note_title,
            "content": note_content,
            "timestamp": self.parent.get_current_timestamp(),
            "last_updated": self.parent.get_current_timestamp()
        })
        notes["notes"] = note_list
        return self.save_notes(notes)
    
    def update_note(self, note_id: str, note_title: str, note_content: str) -> bool:
        """更新笔记"""
        notes = self.load_notes()
        note_list = notes.get("notes", [])
        for note in note_list:
            if note.get("id") == note_id:
                note["title"] = note_title
                note["content"] = note_content
                note["last_updated"] = self.parent.get_current_timestamp()
                notes["notes"] = note_list
                return self.save_notes(notes)
        return False
    
    def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        notes = self.load_notes()
        note_list = notes.get("notes", [])
        note_list = [note for note in note_list if note.get("id") != note_id]
        notes["notes"] = note_list
        return self.save_notes(notes)
    
    def get_notes(self) -> List[Dict[str, Any]]:
        """获取所有笔记"""
        notes = self.load_notes()
        return notes.get("notes", [])
