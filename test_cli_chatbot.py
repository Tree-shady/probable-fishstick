#!/usr/bin/env python3
"""
测试命令行对话助手的API密钥保存功能
"""

import os
import json
import tempfile
import sys

# 创建临时配置文件用于测试
temp_dir = tempfile.mkdtemp()
temp_config = os.path.join(temp_dir, "test_config.json")

# 创建测试配置
test_config = {
    "platforms": {
        "测试平台": {
            "name": "测试平台",
            "api_key_hint": "sk-test123456",
            "base_url": "https://test.api.com/v1/chat/completions",
            "models": ["test-model-1", "test-model-2"],
            "enabled": True,
            "api_type": "test"
        }
    },
    "settings": {
        "chat": {
            "streaming": True
        }
    }
}

# 保存测试配置
with open(temp_config, 'w', encoding='utf-8') as f:
    json.dump(test_config, f, ensure_ascii=False, indent=2)

print("测试配置文件已创建:", temp_config)
print("\n测试步骤:")
print("1. 原始配置中没有API密钥")
print("2. 运行命令行助手，输入API密钥并选择保存")
print("3. 再次运行命令行助手，验证是否能检测到并使用已保存的API密钥")
print("\n请按照提示操作，测试完成后按Ctrl+C退出")
print("=" * 50)

# 创建修改后的cli_chatbot.py副本，使用临时配置文件
with open("cli_chatbot.py", 'r', encoding='utf-8') as f:
    content = f.read()

# 修改配置文件路径
test_content = content.replace(
    "self.config_file = os.path.join(os.getcwd(), \"chatbot_config.json\")",
    f"self.config_file = \"{temp_config}\""
)

# 保存修改后的文件
test_cli_file = os.path.join(temp_dir, "test_cli_chatbot.py")
with open(test_cli_file, 'w', encoding='utf-8') as f:
    f.write(test_content)

print(f"\n测试版本已创建:", test_cli_file)
print("\n现在运行测试版本:")
print(f"python {test_cli_file}")
print("\n测试完成后，您可以检查配置文件内容:")
print(f"cat {temp_config}")
print("\n清理测试文件:")
print(f"rm -rf {temp_dir}")
