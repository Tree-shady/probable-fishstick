from PyQt6.QtCore import QThread, pyqtSignal
import requests
import json
import time
from typing import Optional


class BackgroundTaskThread(QThread):
    """通用后台任务线程类"""
    task_complete = pyqtSignal(bool, str, object)
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.abort = False
        self.setObjectName(f"BackgroundTask-{id(self)}")  # 设置线程名称，便于调试
    
    def run(self):
        """执行任务"""
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.task_complete.emit(True, "任务完成", result)
        except Exception as e:
            self.task_complete.emit(False, f"任务失败: {str(e)}", None)
        finally:
            # 确保线程资源被正确清理
            self.quit()
    
    def stop(self):
        """停止任务"""
        self.abort = True
        self.quit()


class ApiCallThread(QThread):
    """API调用线程类"""
    # 定义信号
    streaming_content = pyqtSignal(str)
    streaming_finished = pyqtSignal()
    api_error = pyqtSignal(str)
    non_streaming_response = pyqtSignal(str)
    debug_info = pyqtSignal(str, str)
    
    def __init__(self, api_url: str, api_key: str, model: str, message: str, is_streaming: bool, response_speed: int = 5, verify_ssl: bool = False):
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.message = message
        self.is_streaming = is_streaming
        self.response_speed = response_speed  # 响应速度，范围1-10，值越大速度越快
        self.verify_ssl = verify_ssl  # 是否验证SSL证书
        self.setObjectName(f"ApiCallThread-{id(self)}")  # 设置线程名称
    
    def run(self):
        """执行API调用"""
        try:
            # 创建API请求数据
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": self.message}
                ],
                "stream": self.is_streaming
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self.debug_info.emit(f"调用API: {self.api_url}", "INFO")
            self.debug_info.emit(f"使用模型: {self.model}", "INFO")
            self.debug_info.emit(f"流式输出: {self.is_streaming}", "INFO")
            # 显示完整的JSON格式请求信息
            self.debug_info.emit(f"请求头: {json.dumps(headers, indent=2)}", "DEBUG")
            self.debug_info.emit(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}", "DEBUG")
            
            if self.is_streaming:
                # 流式输出
                self._streaming_response(payload, headers)
            else:
                # 非流式输出
                self._non_streaming_response(payload, headers)
        
        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            self.api_error.emit(error_msg)
            self.debug_info.emit(error_msg, "ERROR")
        finally:
            self.quit()
    
    def _non_streaming_response(self, payload, headers):
        """非流式API响应处理"""
        try:
            # 发送API请求
            response = requests.post(self.api_url, json=payload, headers=headers, verify=self.verify_ssl, timeout=30)
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                self.non_streaming_response.emit(ai_response)
            else:
                error_msg = f"API错误: {response.status_code} - {response.text}"
                self.api_error.emit(error_msg)
                self.debug_info.emit(error_msg, "ERROR")
        except Exception as e:
            error_msg = f"非流式响应处理失败: {str(e)}"
            self.api_error.emit(error_msg)
            self.debug_info.emit(error_msg, "ERROR")
    
    def _streaming_response(self, payload, headers):
        """流式API响应处理"""
        try:
            # 发送流式API请求
            with requests.post(self.api_url, json=payload, headers=headers, verify=self.verify_ssl, stream=True, timeout=60) as response:
                if response.status_code == 200:
                    # 处理流式响应
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            # 解码响应块
                            chunk_str = chunk.decode('utf-8')
                            # 分割SSE事件
                            events = chunk_str.split('data: ')
                            
                            for event in events:
                                event = event.strip()
                                if event and event != '[DONE]':
                                    try:
                                        # 解析JSON
                                        data = json.loads(event)
                                        # 提取AI回复
                                        if 'choices' in data and data['choices']:
                                            delta = data['choices'][0].get('delta', {})
                                            if 'content' in delta:
                                                content = delta['content']
                                                # 通过信号更新UI
                                                self.streaming_content.emit(content)
                                                # 根据响应速度添加延迟
                                                if content:
                                                    # 响应速度范围1-10，值越大速度越快
                                                    # 计算延迟时间：0.11 - (0.01 * response_speed)
                                                    delay = 0.11 - (0.01 * self.response_speed)
                                                    if delay > 0:
                                                        time.sleep(delay)
                                    except json.JSONDecodeError:
                                        continue
                    
                    # 流式响应结束
                    self.streaming_finished.emit()
                else:
                    error_msg = f"API错误: {response.status_code} - {response.text}"
                    self.api_error.emit(error_msg)
                    self.debug_info.emit(error_msg, "ERROR")
        except Exception as e:
            error_msg = f"流式响应处理失败: {str(e)}"
            self.api_error.emit(error_msg)
            self.debug_info.emit(error_msg, "ERROR")
