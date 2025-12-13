import base64
import os
from cryptography.fernet import Fernet
from typing import Optional

class EncryptionManager:
    """加密管理类，负责API密钥的加密和解密"""
    
    def __init__(self):
        self.key_file = os.path.join(os.path.expanduser("~"), ".universal_chatbot_key")
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self) -> bytes:
        """加载或生成加密密钥"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    return f.read()
            else:
                # 生成新密钥
                key = Fernet.generate_key()
                # 确保密钥目录存在
            # 保存密钥到用户主目录，权限设置为只有当前用户可读写
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                
                # 设置文件权限
                try:
                    os.chmod(self.key_file, 0o600)
                    # 如果是Windows系统，尝试使用win32security进一步限制权限
                    if os.name == 'nt':
                        try:
                            import win32security
                            import win32con
                            import win32api
                            
                            # 获取当前用户的SID
                            user = win32api.GetUserName()
                            sid = win32security.LookupAccountName(None, user)[0]
                            
                            # 设置文件的DACL，只允许当前用户访问
                            dacl = win32security.ACL()
                            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, win32con.FILE_ALL_ACCESS, sid)
                            
                            # 获取文件的安全描述符
                            sd = win32security.GetFileSecurity(self.key_file, win32security.DACL_SECURITY_INFORMATION)
                            sd.SetSecurityDescriptorDacl(1, dacl, 0)
                            win32security.SetFileSecurity(self.key_file, win32security.DACL_SECURITY_INFORMATION, sd)
                        except ImportError:
                            # 如果pywin32库不可用，忽略错误，但记录日志
                            print("pywin32库不可用，无法进一步限制Windows文件权限")
                        except Exception as e:
                            # 其他Windows权限设置错误，忽略错误，但记录日志
                            print(f"在Windows上进一步限制文件权限失败: {str(e)}")
                except Exception as e:
                    # 如果权限设置失败，忽略错误，但记录日志
                    print(f"设置密钥文件权限失败: {str(e)}")
                
                return key
        except Exception as e:
            # 如果所有操作都失败，生成一个临时密钥，但不保存
            print(f"加载或生成密钥失败，使用临时密钥: {str(e)}")
            return Fernet.generate_key()
    
    def encrypt(self, text: str) -> str:
        """加密文本"""
        if not text:
            return ""
        try:
            encrypted_bytes = self.cipher.encrypt(text.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            print(f"加密失败: {str(e)}")
            return text
    
    def decrypt(self, encrypted_text: str) -> str:
        """解密文本"""
        if not encrypted_text:
            return ""
        try:
            # 检查是否是有效的base64字符串
            # 有效的base64字符串长度应该是4的倍数，并且只包含有效的base64字符
            if len(encrypted_text) % 4 != 0:
                return encrypted_text
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            return self.cipher.decrypt(encrypted_bytes).decode()
        except base64.binascii.Error:
            # 处理base64解码错误，不打印错误信息
            return encrypted_text
        except Exception as e:
            # 如果解密失败，返回原始文本，不打印错误信息
            return encrypted_text
    
    def is_encrypted(self, text: str) -> bool:
        """检查文本是否已加密"""
        if not text:
            return False
        try:
            # 尝试解密，如果成功则已加密
            self.decrypt(text)
            return True
        except Exception:
            return False
