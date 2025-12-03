#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI对话软件主入口
提供启动界面，让用户选择使用哪个版本
"""

import os
import sys
import subprocess


def main():
    """主函数"""
    print("=" * 40)
    print("        AI对话软件")
    print("=" * 40)
    print("请选择要使用的版本：")
    print("1. 命令行版本 (CLI)")
    print("2. PyQt图形界面版本")
    print("0. 退出")
    print("=" * 40)
    
    while True:
        choice = input("请输入选项 (0-2): ").strip()
        
        if choice == "0":
            print("再见！")
            sys.exit(0)
        elif choice == "1":
            print("启动命令行版本...")
            run_cli_version()
            break
        elif choice == "2":
            print("启动PyQt图形界面版本...")
            run_pyqt_version()
            break
        else:
            print("无效选项，请重新输入！")


def run_cli_version():
    """运行命令行版本"""
    cli_file = "ai_chat_cli.py"
    if os.path.exists(cli_file):
        # 使用 subprocess 运行命令行版本
        subprocess.run([sys.executable, cli_file])
    else:
        print(f"错误：找不到命令行版本文件 {cli_file}")
        input("按回车键继续...")
        main()


def run_pyqt_version():
    """运行PyQt图形界面版本"""
    pyqt_file = "ai_chat_pyqt.py"
    if os.path.exists(pyqt_file):
        # 使用 subprocess 运行PyQt版本
        subprocess.run([sys.executable, pyqt_file])
    else:
        print(f"错误：找不到PyQt图形界面版本文件 {pyqt_file}")
        input("按回车键继续...")
        main()


if __name__ == "__main__":
    main()
