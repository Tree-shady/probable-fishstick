from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QFont


class SplashScreen(QWidget):
    """启动动画窗口类"""
    def __init__(self):
        super().__init__()
        self.opacity = 1.0  # 初始透明度
        self.init_ui()
    
    def init_ui(self):
        """初始化启动动画UI"""
        # 设置窗口属性
        self.setWindowTitle("多功能AI聊天助手")
        self.setFixedSize(400, 300)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # 无边框
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        self.setWindowModality(Qt.WindowModality.ApplicationModal)  # 模态窗口
        
        # 设置窗口透明度
        self.setWindowOpacity(self.opacity)
        
        # 主布局
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title_label = QLabel("🤖 多功能AI聊天助手")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("版本: 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        layout.addWidget(version_label)
        
        # 描述
        desc_label = QLabel("一个功能丰富、界面美观的AI聊天助手")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # 加载动画（使用QLabel模拟进度）
        self.progress_label = QLabel("正在初始化...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 居中显示
        self.center()
    
    def center(self):
        """将窗口居中显示"""
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def update_progress(self, value, message=None):
        """更新进度条值"""
        self.progress_bar.setValue(value)
        if message:
            self.progress_label.setText(message)
        self.repaint()  # 强制重绘，确保进度条更新
    
    def fade_out(self, duration=500):
        """淡出效果"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()
    
    def fade_in(self, duration=500):
        """淡入效果"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()


class ThemeManager:
    """主题管理器，负责管理应用程序的主题样式"""
    
    def __init__(self):
        self.themes = {
            '浅色主题': """QWidget {
    background-color: #f0f0f0;
    color: #333333;
}

QMainWindow {
    background-color: #f0f0f0;
}

QHeaderView::section {
    background-color: #e0e0e0;
    color: #333333;
    padding: 8px;
    border: 1px solid #d0d0d0;
}

QTableView {
    background-color: white;
    gridline-color: #e0e0e0;
}

QTableWidget {
    background-color: white;
    gridline-color: #e0e0e0;
}

QListWidget {
    background-color: white;
    border: 1px solid #e0e0e0;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f0f0f0;
}

QListWidget::item:selected {
    background-color: #c0e0ff;
    color: #000000;
}

QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #f0f0f0;
    height: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:horizontal {
    background-color: #c0c0c0;
    border-radius: 5px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: none;
}

QPushButton {
    background-color: #e0e0e0;
    color: #333333;
    border: 1px solid #d0d0d0;
    padding: 6px 12px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #d0d0d0;
}

QPushButton:pressed {
    background-color: #c0c0c0;
}

QPushButton:disabled {
    background-color: #f0f0f0;
    color: #a0a0a0;
    border: 1px solid #e0e0e0;
}

QLineEdit, QTextEdit {
    background-color: white;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #4da6ff;
    outline: none;
}

QComboBox {
    background-color: white;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    border: none;
    width: 16px;
    height: 16px;
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23333333'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
}

QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    margin-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    background-color: transparent;
}

QTabWidget::pane {
    background-color: white;
    border: 1px solid #d0d0d0;
    border-top: none;
}

QTabBar::tab {
    background-color: #f0f0f0;
    color: #333333;
    padding: 8px 16px;
    border: 1px solid #d0d0d0;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    color: #333333;
    border-bottom: 1px solid white;
    margin-bottom: -1px;
}

QTabBar::tab:hover {
    background-color: #e0e0e0;
}

QCheckBox {
    color: #333333;
}

QRadioButton {
    color: #333333;
}

QLabel {
    color: #333333;
}

QTextBrowser {
    background-color: white;
    color: #333333;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 8px;
}

QMessageBox {
    background-color: white;
    color: #333333;
}

QMessageBox QPushButton {
    min-width: 80px;
}""",
            '深色主题': """QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
}

QMainWindow {
    background-color: #1a1a1a;
}

QHeaderView::section {
    background-color: #2a2a2a;
    color: #e0e0e0;
    padding: 8px;
    border: 1px solid #3a3a3a;
}

QTableView {
    background-color: #2a2a2a;
    gridline-color: #3a3a3a;
    color: #e0e0e0;
}

QTableWidget {
    background-color: #2a2a2a;
    gridline-color: #3a3a3a;
    color: #e0e0e0;
}

QListWidget {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    color: #e0e0e0;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #3a3a3a;
}

QListWidget::item:selected {
    background-color: #004080;
    color: white;
}

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background-color: #4a4a4a;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #1a1a1a;
    height: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    border-radius: 5px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background: none;
}

QPushButton {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    padding: 6px 12px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #3a3a3a;
}

QPushButton:pressed {
    background-color: #4a4a4a;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #5a5a5a;
    border: 1px solid #3a3a3a;
}

QLineEdit, QTextEdit {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #4da6ff;
    outline: none;
}

QComboBox {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    border: none;
    width: 16px;
    height: 16px;
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23e0e0e0'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
}

QComboBox QAbstractItemView {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
}

QComboBox QAbstractItemView::item {
    padding: 8px;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #004080;
    color: white;
}

QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    background-color: transparent;
    color: #e0e0e0;
}

QTabWidget::pane {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-top: none;
}

QTabBar::tab {
    background-color: #2a2a2a;
    color: #e0e0e0;
    padding: 8px 16px;
    border: 1px solid #3a3a3a;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border-bottom: 1px solid #3a3a3a;
    margin-bottom: -1px;
}

QTabBar::tab:hover {
    background-color: #3a3a3a;
}

QCheckBox {
    color: #e0e0e0;
}

QRadioButton {
    color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
}

QTextBrowser {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 8px;
}

QMessageBox {
    background-color: #2a2a2a;
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-width: 80px;
}"""
        }
    
    def get_theme_stylesheet(self, theme_name):
        """获取指定主题的样式表"""
        return self.themes.get(theme_name, self.themes['浅色主题'])
    
    def get_available_themes(self):
        """获取可用主题列表"""
        return list(self.themes.keys())
