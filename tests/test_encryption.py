#!/usr/bin/env python3
"""
测试加密模块的功能
"""

import unittest
import os
import tempfile
from src.utils.encryption import EncryptionManager


class TestEncryptionManager(unittest.TestCase):
    """测试加密管理器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.mkdtemp()
        self.temp_key_file = os.path.join(self.temp_dir, ".test_key")
        
    def tearDown(self):
        """清理测试环境"""
        # 删除临时文件和目录
        if os.path.exists(self.temp_key_file):
            os.remove(self.temp_key_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_encrypt_decrypt(self):
        """测试加密和解密功能"""
        # 创建加密管理器
        encryption_manager = EncryptionManager()
        
        # 测试文本
        test_text = "test_api_key_123456"
        
        # 加密文本
        encrypted = encryption_manager.encrypt(test_text)
        self.assertNotEqual(encrypted, test_text, "加密后的文本应与原文本不同")
        
        # 解密文本
        decrypted = encryption_manager.decrypt(encrypted)
        self.assertEqual(decrypted, test_text, "解密后的文本应与原文本相同")
    
    def test_decrypt_invalid_text(self):
        """测试解密无效文本"""
        # 创建加密管理器
        encryption_manager = EncryptionManager()
        
        # 测试解密无效文本
        invalid_text = "invalid_encrypted_text"
        decrypted = encryption_manager.decrypt(invalid_text)
        self.assertEqual(decrypted, invalid_text, "解密无效文本应返回原文本")
    
    def test_encrypt_empty_text(self):
        """测试加密空文本"""
        # 创建加密管理器
        encryption_manager = EncryptionManager()
        
        # 测试加密空文本
        empty_text = ""
        encrypted = encryption_manager.encrypt(empty_text)
        self.assertEqual(encrypted, empty_text, "加密空文本应返回空文本")
    
    def test_decrypt_empty_text(self):
        """测试解密空文本"""
        # 创建加密管理器
        encryption_manager = EncryptionManager()
        
        # 测试解密空文本
        empty_text = ""
        decrypted = encryption_manager.decrypt(empty_text)
        self.assertEqual(decrypted, empty_text, "解密空文本应返回空文本")
    
    def test_is_encrypted(self):
        """测试检查文本是否已加密"""
        # 创建加密管理器
        encryption_manager = EncryptionManager()
        
        # 测试文本
        test_text = "test_text"
        encrypted_text = encryption_manager.encrypt(test_text)
        
        # 检查未加密文本
        self.assertFalse(encryption_manager.is_encrypted(test_text), "未加密文本应返回False")
        
        # 检查已加密文本
        self.assertTrue(encryption_manager.is_encrypted(encrypted_text), "已加密文本应返回True")


if __name__ == "__main__":
    unittest.main()
