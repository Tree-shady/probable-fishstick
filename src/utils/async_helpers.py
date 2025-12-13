import asyncio
import aiofiles
import json
from typing import Any, Optional

class AsyncFileManager:
    """异步文件管理类，负责异步文件IO操作"""
    
    @staticmethod
    async def async_load_json_file(file_path: str, default: Optional[Any] = None) -> Any:
        """异步加载JSON文件"""
        if default is None:
            default = {}
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            return default
        except Exception as e:
            print(f"加载JSON文件失败: {file_path}, 错误: {str(e)}")
            return default
    
    @staticmethod
    async def async_save_json_file(file_path: str, data: Any) -> bool:
        """异步保存JSON文件"""
        try:
            import os
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {file_path}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def run_in_executor(func, *args, **kwargs) -> Any:
        """在执行器中运行同步函数，避免阻塞事件循环"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func, *args, **kwargs)
