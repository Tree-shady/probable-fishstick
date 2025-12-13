import json
import os
import subprocess
import sys
from datetime import datetime
import uuid


def lazy_import_bs4():
    """懒加载BeautifulSoup"""
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
            from bs4 import BeautifulSoup
            return BeautifulSoup
        except:
            return None


def load_json_file(file_path, default=None):
    """加载JSON文件"""
    if default is None:
        default = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON文件失败: {file_path}, 错误: {str(e)}")
            return default
    return default


def save_json_file(file_path, data):
    """保存JSON文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {file_path}, 错误: {str(e)}")
        return False


def get_unique_id():
    """生成唯一ID"""
    return str(uuid.uuid4())


def get_current_timestamp():
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_iso_timestamp():
    """获取当前ISO格式时间戳"""
    return datetime.now().isoformat()


def compute_file_hash(file_path):
    """计算文件的MD5哈希值"""
    try:
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def ensure_directory_exists(directory):
    """确保目录存在"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {directory}, 错误: {str(e)}")
        return False


def merge_dicts(default, custom):
    """递归合并字典"""
    result = default.copy()
    for key, value in custom.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
