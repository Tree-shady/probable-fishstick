import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.chatbot import UniversalChatBotPyQt6
from src.ui import SplashScreen


def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，跨平台一致性更好
    
    # 创建启动动画
    splash = SplashScreen()
    splash.show()
    
    # 更新进度
    splash.update_progress(10, "加载配置文件...")
    QApplication.processEvents()
    
    # 直接创建主窗口，不使用手动延时
    window = UniversalChatBotPyQt6()
    
    splash.update_progress(50, "初始化UI组件...")
    QApplication.processEvents()
    
    splash.update_progress(70, "初始化服务...")
    QApplication.processEvents()
    
    splash.update_progress(90, "加载对话历史...")
    QApplication.processEvents()
    
    splash.update_progress(100, "初始化完成！")
    QApplication.processEvents()
    
    # 显示主窗口
    window.show()
    window.raise_()
    window.activateWindow()
    
    # 关闭启动动画
    splash.fade_out(duration=500)
    # 等待渐变效果完成
    app.processEvents()
    
    # 使用定时器确保启动动画完全关闭后再删除
    QTimer.singleShot(600, lambda: (splash.close(), splash.deleteLater()))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
