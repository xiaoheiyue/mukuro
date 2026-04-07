"""
工业锅炉除污处理系统 - 主程序入口
Industrial Boiler Cleaning System - Main Entry Point

本系统用于监控和控制工业锅炉的除污处理过程，包括：
- 实时数据监控
- 除污剂投放控制
- 排污阀控制
- 水质分析
- 报警管理
- 历史记录查询
- 报表生成
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTranslator, QLocale
from PyQt6.QtGui import QFont

from models.database import DatabaseManager
from views.main_window import MainWindow
from utils.logger import setup_logger
from utils.config import Config


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("工业锅炉除污处理系统")
    app.setOrganizationName("IndustrialBoilerCorp")
    app.setApplicationVersion("1.0.0")
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 设置样式
    app.setStyle("Fusion")
    
    # 初始化配置
    config = Config()
    
    # 设置日志
    logger = setup_logger(config.log_level)
    logger.info("启动工业锅炉除污处理系统...")
    
    # 初始化数据库
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        logger.error("数据库初始化失败")
        return 1
    logger.info("数据库初始化成功")
    
    # 创建主窗口
    main_window = MainWindow(db_manager, config)
    main_window.show()
    
    logger.info("系统启动完成")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
