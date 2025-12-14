import base64
import os
import time
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Optional, Tuple, Dict

class EncryptionManager:
    """加密管理类，负责API密钥的加密和解密，以及端到端加密支持"""
    
    def __init__(self):
        self.key_file = os.path.join(os.path.expanduser("~"), ".universal_chatbot_key")
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        
        # 端到端加密相关
        self.e2e_keys_file = os.path.join(os.path.expanduser("~"), ".universal_chatbot_e2e_keys.json")
        self.e2e_keys = self._load_or_generate_e2e_keys()
        
        # 活动日志记录开关
        self.log_enabled = True
    
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
    
    def _load_or_generate_e2e_keys(self) -> Dict[str, str]:
        """加载或生成端到端加密密钥"""
        try:
            if os.path.exists(self.e2e_keys_file):
                with open(self.e2e_keys_file, 'rb') as f:
                    import json
                    keys = json.load(f)
                    return keys
            else:
                # 生成新的端到端加密密钥
                e2e_key = Fernet.generate_key().decode()
                keys = {
                    "e2e_key": e2e_key,
                    "created_at": str(time.time())
                }
                
                # 保存密钥文件
                with open(self.e2e_keys_file, 'wb') as f:
                    json.dump(keys, f)
                
                # 设置文件权限
                try:
                    os.chmod(self.e2e_keys_file, 0o600)
                except Exception as e:
                    print(f"设置端到端密钥文件权限失败: {str(e)}")
                
                return keys
        except Exception as e:
            print(f"加载或生成端到端密钥失败: {str(e)}")
            # 生成临时密钥
            e2e_key = Fernet.generate_key().decode()
            return {
                "e2e_key": e2e_key,
                "created_at": str(time.time())
            }
    
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
        except Exception:
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
    
    def encrypt_e2e(self, text: str, conversation_id: str = "default") -> str:
        """端到端加密消息"""
        if not text:
            return ""
        try:
            # 使用端到端加密密钥
            e2e_key = self.e2e_keys["e2e_key"].encode()
            e2e_cipher = Fernet(e2e_key)
            
            # 添加会话ID作为额外保护
            protected_text = f"{conversation_id}::{text}"
            encrypted_bytes = e2e_cipher.encrypt(protected_text.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            print(f"端到端加密失败: {str(e)}")
            return text
    
    def decrypt_e2e(self, encrypted_text: str, conversation_id: str = "default") -> str:
        """端到端解密消息"""
        if not encrypted_text:
            return ""
        try:
            # 检查是否是有效的base64字符串
            if len(encrypted_text) % 4 != 0:
                return encrypted_text
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            
            # 使用端到端加密密钥
            e2e_key = self.e2e_keys["e2e_key"].encode()
            e2e_cipher = Fernet(e2e_key)
            
            decrypted_bytes = e2e_cipher.decrypt(encrypted_bytes)
            decrypted_text = decrypted_bytes.decode()
            
            # 验证并提取会话ID
            if "::" in decrypted_text:
                extracted_conversation_id, actual_text = decrypted_text.split("::", 1)
                if extracted_conversation_id == conversation_id:
                    return actual_text
                else:
                    print("会话ID不匹配，解密失败")
                    return encrypted_text
            
            return decrypted_text
        except Exception as e:
            print(f"端到端解密失败: {str(e)}")
            return encrypted_text
    
    def generate_asymmetric_keys(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """生成非对称密钥对"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def encrypt_with_public_key(self, text: str, public_key: rsa.RSAPublicKey) -> str:
        """使用公钥加密文本"""
        if not text:
            return ""
        try:
            encrypted_bytes = public_key.encrypt(
                text.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            print(f"公钥加密失败: {str(e)}")
            return text
    
    def decrypt_with_private_key(self, encrypted_text: str, private_key: rsa.RSAPrivateKey) -> str:
        """使用私钥解密文本"""
        if not encrypted_text:
            return ""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_bytes = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"私钥解密失败: {str(e)}")
            return encrypted_text
    
    def export_e2e_key(self, password: str) -> str:
        """导出端到端密钥，使用密码加密"""
        try:
            # 生成基于密码的密钥
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # 加密端到端密钥
            cipher = Fernet(key)
            encrypted_e2e_key = cipher.encrypt(self.e2e_keys["e2e_key"].encode())
            
            # 组合salt和加密的密钥
            export_data = {
                "salt": base64.urlsafe_b64encode(salt).decode(),
                "encrypted_key": base64.urlsafe_b64encode(encrypted_e2e_key).decode(),
                "version": "1.0"
            }
            
            import json
            return json.dumps(export_data)
        except Exception as e:
            print(f"导出端到端密钥失败: {str(e)}")
            return ""
    
    def import_e2e_key(self, import_data: str, password: str) -> bool:
        """从导出数据导入端到端密钥"""
        try:
            import json
            data = json.loads(import_data)
            
            # 提取salt和加密的密钥
            salt = base64.urlsafe_b64decode(data["salt"].encode())
            encrypted_key = base64.urlsafe_b64decode(data["encrypted_key"].encode())
            
            # 生成基于密码的密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # 解密端到端密钥
            cipher = Fernet(key)
            decrypted_key = cipher.decrypt(encrypted_key).decode()
            
            # 更新端到端密钥
            self.e2e_keys["e2e_key"] = decrypted_key
            self.e2e_keys["updated_at"] = str(time.time())
            
            # 保存到文件
            with open(self.e2e_keys_file, 'wb') as f:
                json.dump(self.e2e_keys, f)
            
            return True
        except Exception as e:
            print(f"导入端到端密钥失败: {str(e)}")
            return False
