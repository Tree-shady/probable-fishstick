#!/usr/bin/env python3
"""
测试异步文件管理器的功能
"""

import unittest
import os
import tempfile
import asyncio
from src.utils.async_helpers import AsyncFileManager


class TestAsyncFileManager(unittest.IsolatedAsyncioTestCase):
    """测试异步文件管理器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.json")
        
    def tearDown(self):
        """清理测试环境"""
        # 删除临时文件和目录
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    async def test_async_save_load_json(self):
        """测试异步保存和加载JSON文件"""
        # 测试数据
        test_data = {
            "key1": "value1",
            "key2": 123,
            "key3": [1, 2, 3],
            "key4": {"nested": "value"}
        }
        
        # 异步保存JSON文件
        success = await AsyncFileManager.async_save_json_file(self.test_file, test_data)
        self.assertTrue(success, "保存JSON文件应成功")
        
        # 异步加载JSON文件
        loaded_data = await AsyncFileManager.async_load_json_file(self.test_file)
        self.assertEqual(loaded_data, test_data, "加载的JSON数据应与保存的数据相同")
    
    async def test_async_load_nonexistent_file(self):
        """测试异步加载不存在的文件"""
        # 异步加载不存在的文件
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        loaded_data = await AsyncFileManager.async_load_json_file(nonexistent_file)
        self.assertEqual(loaded_data, {}, "加载不存在的文件应返回默认空字典")
        
        # 使用自定义默认值
        loaded_data = await AsyncFileManager.async_load_json_file(nonexistent_file, default=[1, 2, 3])
        self.assertEqual(loaded_data, [1, 2, 3], "加载不存在的文件应返回自定义默认值")
    
    async def test_async_save_to_nonexistent_dir(self):
        """测试异步保存到不存在的目录"""
        # 异步保存到不存在的目录
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        nonexistent_file = os.path.join(nonexistent_dir, "test.json")
        
        test_data = {"key": "value"}
        success = await AsyncFileManager.async_save_json_file(nonexistent_file, test_data)
        self.assertTrue(success, "保存到不存在的目录应成功")
        
        # 验证文件已创建
        self.assertTrue(os.path.exists(nonexistent_file), "文件应已创建")
        
        # 清理
        os.remove(nonexistent_file)
        os.rmdir(nonexistent_dir)
    
    async def test_async_save_invalid_json(self):
        """测试异步保存无效的JSON数据"""
        # 测试保存无效的JSON数据（如包含不可序列化对象）
        import datetime
        invalid_data = {"datetime": datetime.datetime.now()}
        
        success = await AsyncFileManager.async_save_json_file(self.test_file, invalid_data)
        self.assertFalse(success, "保存无效的JSON数据应失败")
    
    async def test_async_load_invalid_json(self):
        """测试异步加载无效的JSON文件"""
        # 创建无效的JSON文件
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("invalid json data")
        
        # 异步加载无效的JSON文件
        loaded_data = await AsyncFileManager.async_load_json_file(self.test_file)
        self.assertEqual(loaded_data, {}, "加载无效的JSON文件应返回默认空字典")
        
        # 使用自定义默认值
        loaded_data = await AsyncFileManager.async_load_json_file(self.test_file, default=["default"])
        self.assertEqual(loaded_data, ["default"], "加载无效的JSON文件应返回自定义默认值")


if __name__ == "__main__":
    unittest.main()
