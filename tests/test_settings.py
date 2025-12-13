#!/usr/bin/env python3
"""
测试设置管理器的功能
"""

import unittest
import os
import tempfile
import json
from src.data.settings import SettingsManager


class TestSettingsManager(unittest.TestCase):
    """测试设置管理器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_file = os.path.join(self.temp_dir, "test_config.json")
        
    def tearDown(self):
        """清理测试环境"""
        # 删除临时文件和目录
        if os.path.exists(self.temp_config_file):
            os.remove(self.temp_config_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_settings_manager_init(self):
        """测试设置管理器初始化"""
        # 创建设置管理器
        settings_manager = SettingsManager(self.temp_config_file)
        
        # 检查默认设置是否正确
        self.assertIsInstance(settings_manager.settings, dict, "设置应为字典类型")
        self.assertIsInstance(settings_manager.platforms, dict, "平台配置应为字典类型")
        self.assertIn("chat", settings_manager.settings, "设置中应包含chat配置")
        self.assertIn("network", settings_manager.settings, "设置中应包含network配置")
    
    def test_save_load_settings(self):
        """测试保存和加载设置"""
        # 创建设置管理器
        settings_manager = SettingsManager(self.temp_config_file)
        
        # 修改设置
        new_settings = {
            "chat": {
                "auto_scroll": False,
                "streaming": False,
                "response_speed": 3
            },
            "network": {
                "timeout": 60,
                "verify_ssl": True
            }
        }
        settings_manager.update_settings(new_settings)
        
        # 创建新的设置管理器，加载相同的配置文件
        new_settings_manager = SettingsManager(self.temp_config_file)
        
        # 检查加载的设置是否与保存的设置相同
        self.assertEqual(new_settings_manager.settings["chat"]["auto_scroll"], False, "加载的auto_scroll设置应与保存的相同")
        self.assertEqual(new_settings_manager.settings["chat"]["streaming"], False, "加载的streaming设置应与保存的相同")
        self.assertEqual(new_settings_manager.settings["chat"]["response_speed"], 3, "加载的response_speed设置应与保存的相同")
        self.assertEqual(new_settings_manager.settings["network"]["timeout"], 60, "加载的timeout设置应与保存的相同")
        self.assertEqual(new_settings_manager.settings["network"]["verify_ssl"], True, "加载的verify_ssl设置应与保存的相同")
    
    def test_reset_settings(self):
        """测试重置设置"""
        # 创建设置管理器
        settings_manager = SettingsManager(self.temp_config_file)
        
        # 修改设置
        settings_manager.update_settings({
            "chat": {
                "auto_scroll": False,
                "streaming": False
            }
        })
        
        # 重置设置
        settings_manager.reset_settings()
        
        # 检查设置是否已重置为默认值
        self.assertTrue(settings_manager.settings["chat"]["auto_scroll"], "auto_scroll设置应已重置为默认值True")
        self.assertTrue(settings_manager.settings["chat"]["streaming"], "streaming设置应已重置为默认值True")
    
    def test_platform_config_encryption(self):
        """测试平台配置的加密和解密"""
        # 创建设置管理器
        settings_manager = SettingsManager(self.temp_config_file)
        
        # 添加带有API密钥的平台配置
        test_platform = "测试平台"
        settings_manager.platforms[test_platform] = {
            "name": "测试平台",
            "api_key_hint": "sk-test123",
            "base_url": "https://test.api.com",
            "models": ["test-model"],
            "enabled": True,
            "api_type": "test",
            "api_key": "sk-test1234567890"
        }
        
        # 保存设置
        settings_manager.save_settings()
        
        # 重新加载设置
        new_settings_manager = SettingsManager(self.temp_config_file)
        
        # 检查API密钥是否已正确解密
        self.assertEqual(new_settings_manager.platforms[test_platform]["api_key"], "sk-test1234567890", "API密钥应已正确解密")
    
    def test_merge_dicts(self):
        """测试字典合并功能"""
        # 创建设置管理器
        settings_manager = SettingsManager(self.temp_config_file)
        
        # 测试更新设置的合并功能
        original_settings = settings_manager.settings.copy()
        
        # 更新部分设置
        settings_manager.update_settings({
            "chat": {
                "auto_scroll": False
            }
        })
        
        # 检查设置是否已正确合并
        self.assertEqual(settings_manager.settings["chat"]["auto_scroll"], False, "auto_scroll设置应已更新")
        # 检查其他设置是否保持不变
        self.assertEqual(settings_manager.settings["chat"]["streaming"], original_settings["chat"]["streaming"], "其他设置应保持不变")
        self.assertEqual(settings_manager.settings["chat"]["response_speed"], original_settings["chat"]["response_speed"], "其他设置应保持不变")


if __name__ == "__main__":
    unittest.main()
