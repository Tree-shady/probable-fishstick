#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI对话软件web版本后端服务
用于处理API请求，解决跨域问题
"""

from flask import Flask, request, jsonify
import requests
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={"/*": {"origins": "*"}})

# 配置文件路径（与UI版本共享）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
MODEL_CONFIGS_FILE = os.path.join(BASE_DIR, 'model_configs.json')

# 读取配置文件
def read_config():
    """读取配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存配置文件
def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 读取模型配置
def read_model_configs():
    """读取模型配置文件"""
    if os.path.exists(MODEL_CONFIGS_FILE):
        with open(MODEL_CONFIGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存模型配置
def save_model_configs(model_configs):
    """保存模型配置文件"""
    with open(MODEL_CONFIGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(model_configs, f, ensure_ascii=False, indent=2)

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        # 获取请求数据
        data = request.get_json()
        api_url = data.get('api_url')
        api_key = data.get('api_key')
        model = data.get('model')
        messages = data.get('messages')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        if not api_url or not api_key:
            return jsonify({"error": "缺少API URL或API密钥"}), 400
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 准备请求数据
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 发送请求到目标API
        response = requests.post(
            api_url,
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        # 返回原始响应
        return response.json(), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    try:
        config = read_config()
        model_configs = read_model_configs()
        return jsonify({
            "config": config,
            "model_configs": model_configs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.get_json()
        new_config = data.get('config', {})
        
        # 保存更新后的配置
        save_config(new_config)
        return jsonify({"message": "配置更新成功", "config": new_config}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取所有可用模型"""
    try:
        model_configs = read_model_configs()
        return jsonify({"models": model_configs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/<model_name>', methods=['POST'])
def switch_model(model_name):
    """切换模型"""
    try:
        model_configs = read_model_configs()
        
        if model_name not in model_configs:
            return jsonify({"error": "模型不存在"}), 404
        
        # 获取当前模型配置
        model_config = model_configs[model_name]
        
        # 保存到主配置文件
        save_config(model_config)
        
        return jsonify({
            "message": f"已切换到模型: {model_name}",
            "config": model_config
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_server():
    """启动服务器，支持开发和生产模式"""
    import argparse
    import os
    import sys
    import warnings
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='AI对话软件后端服务')
    parser.add_argument('--host', default='0.0.0.0', help='服务器绑定的主机地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器绑定的端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--production', action='store_true', help='生产模式（禁用调试）')
    
    args = parser.parse_args()
    
    # 配置调试模式
    debug = args.debug and not args.production
    
    print("=" * 60)
    print("AI对话软件后端服务")
    print(f"运行模式: {'生产模式' if args.production else '开发模式'}")
    print(f"服务器地址: http://{args.host}:{args.port}")
    print(f"调试模式: {debug}")
    print("=" * 60)
    
    if args.production:
        print("注意：生产环境建议使用Gunicorn或uWSGI等WSGI服务器运行")
        print("例如: gunicorn -w 4 -b 0.0.0.0:5000 backend:app")
        print("或者使用uWSGI: uwsgi --http :5000 --wsgi-file backend.py --callable app --processes 4 --threads 2")
        print("=" * 60)
    
    # 检查是否在WSGI服务器（如Gunicorn）下运行
    is_wsgi = 'gunicorn' in sys.argv[0] or 'uwsgi' in sys.argv[0] or os.environ.get('WSGI_ENV')
    
    if not is_wsgi:
        # 在开发服务器中，抑制生产模式下的警告
        if args.production:
            warnings.filterwarnings("ignore", category=Warning)
            print("开发服务器已启动（生产模式配置）。")
            print("在实际生产环境中，强烈建议使用Gunicorn或uWSGI等WSGI服务器。")
            print("=" * 60)
        # 启动开发服务器
        app.run(host=args.host, port=args.port, debug=debug)

if __name__ == "__main__":
    run_server()