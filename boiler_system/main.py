"""
工业锅炉除污处理系统 - 主程序入口
Industrial Boiler Decontamination System - Main Entry Point

Author: AI Assistant
Version: 1.0.0
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTranslator, QLocale
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow
from config.settings import Settings
from core.database import DatabaseManager
from core.logger import setup_logger


def main():
    """主函数 - Main function"""
    
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setApplicationName("工业锅炉除污处理系统")
    app.setOrganizationName("IndustrialBoilerCorp")
    app.setApplicationVersion("1.0.0")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    font.setStyleHint(QFont.StyleHint.System)
    app.setFont(font)
    
    # 初始化配置
    settings = Settings()
    
    # 初始化日志系统
    logger = setup_logger(settings.log_level, settings.log_file)
    logger.info("应用程序启动 - Application started")
    
    # 初始化数据库
    db_manager = DatabaseManager(settings.database_path)
    db_manager.initialize()
    logger.info("数据库初始化完成 - Database initialized")
    
    # 创建主窗口
    main_window = MainWindow(settings, db_manager, logger)
    
    # 显示主窗口
    main_window.show()
    
    # 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
