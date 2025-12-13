from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QLabel
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer
from typing import Optional

class SplashScreen(QSplashScreen):
    """启动动画类"""
    
    def __init__(self, pixmap: Optional[QPixmap] = None):
        if not pixmap:
            # 创建默认的启动图片
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.white)
        super().__init__(pixmap)
        
        # 创建进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 250, 300, 20)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # 创建进度文本
        self.progress_text = QLabel(self)
        self.progress_text.setGeometry(50, 270, 300, 20)
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.progress_text.setFont(font)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 300)
        self.center()
    
    def center(self):
        """将窗口居中显示"""
        screen = self.screen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)
    
    def update_progress(self, progress: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.progress_text.setText(message)
    
    def fade_out(self, duration: int = 1000):
        """淡出效果"""
        self.opacity = 1.0
        self.fade_duration = duration
        self.fade_step = 0.05
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self._fade_out_step)
        self.fade_timer.start(int(duration * self.fade_step))
    
    def _fade_out_step(self):
        """淡出效果的每一步"""
        self.opacity -= self.fade_step
        if self.opacity <= 0:
            self.fade_timer.stop()
        else:
            self.setWindowOpacity(self.opacity)
