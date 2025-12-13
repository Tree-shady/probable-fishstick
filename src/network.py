import time
import socket
import platform
import psutil
import threading
import re


class NetworkSecurity:
    """网络安全管理类，负责域名/IP黑白名单检查和SSL验证"""
    def __init__(self):
        # 初始化默认配置
        self.domain_whitelist = []
        self.domain_blacklist = []
        self.ip_whitelist = []
        self.ip_blacklist = []
        self.verify_ssl = False
    
    def check_domain(self, domain):
        """检查域名是否在白名单或黑名单中"""
        # 如果白名单不为空且域名不在白名单中，拒绝访问
        if self.domain_whitelist and domain not in self.domain_whitelist:
            return False, f"域名 {domain} 不在白名单中"
        
        # 如果域名在黑名单中，拒绝访问
        if domain in self.domain_blacklist:
            return False, f"域名 {domain} 在黑名单中"
        
        # 允许访问
        return True, f"域名 {domain} 允许访问"
    
    def check_ip(self, ip):
        """检查IP地址是否在白名单或黑名单中"""
        # 如果白名单不为空且IP不在白名单中，拒绝访问
        if self.ip_whitelist and ip not in self.ip_whitelist:
            return False, f"IP地址 {ip} 不在白名单中"
        
        # 如果IP在黑名单中，拒绝访问
        if ip in self.ip_blacklist:
            return False, f"IP地址 {ip} 在黑名单中"
        
        # 允许访问
        return True, f"IP地址 {ip} 允许访问"
    
    def extract_domain(self, url):
        """从URL中提取域名"""
        try:
            # 使用正则表达式提取域名
            pattern = r'https?://([^/]+)'
            match = re.match(pattern, url)
            if match:
                return match.group(1)
            return None
        except:
            return None
    
    def extract_ip(self, url):
        """从URL中提取IP地址（如果URL直接使用IP）"""
        domain = self.extract_domain(url)
        if domain:
            try:
                # 检查是否是IP地址格式
                socket.inet_aton(domain)
                return domain
            except:
                # 不是IP地址，返回None
                return None
        return None


class NetworkMonitor:
    """本地网络监控类"""
    def __init__(self, parent=None):
        self.parent = parent
        self.running = False
        self.monitor_thread = None
        self.last_update_time = 0  # 记录上次更新时间
        self.update_interval = 180   # 更新间隔（秒）
        
        # 网络状态变量
        self.network_status = "未知"
        self.ip_address = "未知"
        self.ping_latency = "--ms"
        self.upload_speed = "--KB/s"
        self.download_speed = "--KB/s"
        
        # 图表数据
        self.download_history = [0] * 60
        self.upload_history = [0] * 60
        
        # 缓存结果，减少重复计算
        self._cached_ip = None
        self._cached_is_connected = None
        self._last_check_time = 0
        
        # 网络安全管理
        self.security = NetworkSecurity()
    
    def get_ip_address(self):
        """获取本地IP地址（公共方法）"""
        # 优化：缓存IP地址，避免频繁获取
        current_time = time.time()
        if self._cached_ip and current_time - self._last_check_time < 30:  # 30秒缓存
            return self._cached_ip
        
        self._cached_ip = self._get_ip_address()
        self._last_check_time = current_time
        return self._cached_ip
    
    def get_network_speed(self):
        """获取网络上传下载速度（公共方法）"""
        upload_speed, download_speed = self._get_network_speed()
        # 格式化速度显示
        upload_speed_str = f"{upload_speed:.2f}KB/s" if upload_speed > 0 else "--KB/s"
        download_speed_str = f"{download_speed:.2f}KB/s" if download_speed > 0 else "--KB/s"
        return download_speed_str, upload_speed_str
    
    def start_monitoring(self):
        """开始监控网络状态"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_network, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控网络状态"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
    
    def _monitor_network(self):
        """网络监控实现"""
        while self.running:
            try:
                current_time = time.time()
                
                # 网络连接状态检查
                if current_time - self.last_update_time >= self.update_interval:
                    is_connected = self._check_internet_connection()
                    
                    if is_connected != self._cached_is_connected:
                        self._cached_is_connected = is_connected
                        
                        if is_connected:
                            self.network_status = "已连接"
                            ip = self._get_ip_address()
                            self.ip_address = ip
                            latency = self._get_ping_latency()
                            if latency is not None:
                                self.ping_latency = f"{latency}ms"
                        else:
                            self.network_status = "未连接"
                            self.ip_address = "未知"
                            self.ping_latency = "--ms"
                            self.upload_speed = "--KB/s"
                            self.download_speed = "--KB/s"
                    
                    # 更新速度
                    if is_connected:
                        upload_speed, download_speed = self._get_network_speed()
                        self.upload_speed = f"{upload_speed:.2f}KB/s"
                        self.download_speed = f"{download_speed:.2f}KB/s"
                    
                    self.last_update_time = current_time
                
            except Exception as e:
                if self.parent and hasattr(self.parent, 'add_debug_info'):
                    self.parent.add_debug_info(f"网络监控异常: {str(e)}", "ERROR")
            
            time.sleep(0.5)
    
    def _check_internet_connection(self):
        """检查网络连接状态"""
        try:
            with socket.create_connection(('8.8.8.8', 53), timeout=2):
                return True
        except (socket.timeout, socket.error):
            return False
    
    def _get_ip_address(self):
        """获取本地IP地址"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 53))
                ip = s.getsockname()[0]
                return ip
        except:
            return "127.0.0.1"
    
    def _get_ping_latency(self):
        """获取ping延迟"""
        try:
            if platform.system() == "Windows":
                command = ["ping", "-n", "1", "www.baidu.com"]
            else:
                command = ["ping", "-c", "1", "www.baidu.com"]
                
            result = psutil.subprocess.run(command, stdout=psutil.subprocess.PIPE, stderr=psutil.subprocess.PIPE, text=True, timeout=2)
            
            if result.returncode == 0:
                output = result.stdout
                if platform.system() == "Windows":
                    for line in output.split('\n'):
                        if "时间=" in line:
                            try:
                                latency = int(line.split("时间=")[-1].split("ms")[0])
                                return latency
                            except ValueError:
                                continue
                else:
                    for line in output.split('\n'):
                        if "time=" in line:
                            try:
                                latency = float(line.split("time=")[-1].split(" ")[0])
                                return int(latency)
                            except ValueError:
                                continue
            return None
        except Exception:
            return None
    
    def _get_network_speed(self):
        """获取网络上传下载速度"""
        try:
            current_time = time.time()
            if hasattr(self, '_last_speed_sample_time') and current_time - self._last_speed_sample_time < 1:
                return getattr(self, '_last_upload_speed', 0), getattr(self, '_last_download_speed', 0)
                
            net_io = psutil.net_io_counters()
            bytes_sent_before = net_io.bytes_sent
            bytes_recv_before = net_io.bytes_recv
            
            sample_time = 0.5
            time.sleep(sample_time)
            
            net_io = psutil.net_io_counters()
            bytes_sent_after = net_io.bytes_sent
            bytes_recv_after = net_io.bytes_recv
            
            upload_speed = (bytes_sent_after - bytes_sent_before) / 1024 / sample_time
            download_speed = (bytes_recv_after - bytes_recv_before) / 1024 / sample_time
            
            self._last_speed_sample_time = current_time
            self._last_upload_speed = upload_speed
            self._last_download_speed = download_speed
            
            return upload_speed, download_speed
        except Exception as e:
            if self.parent and hasattr(self.parent, 'add_debug_info'):
                self.parent.add_debug_info(f"获取网络速度失败: {str(e)}", "ERROR")
            return 0, 0
