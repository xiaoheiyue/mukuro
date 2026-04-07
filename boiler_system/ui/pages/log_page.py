"""
系统日志页面 - Log Page
查看系统操作日志
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QTextEdit, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import logging
from typing import Dict

from core.database import DatabaseManager


class LogPage(QWidget):
    """系统日志页面类"""
    
    def __init__(self, db_manager: DatabaseManager, logger: logging.Logger, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.logger = logger
        
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📝 系统日志")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 过滤栏
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItem("全部", "")
        self.level_combo.addItem("DEBUG", "DEBUG")
        self.level_combo.addItem("INFO", "INFO")
        self.level_combo.addItem("WARNING", "WARNING")
        self.level_combo.addItem("ERROR", "ERROR")
        self.level_combo.addItem("CRITICAL", "CRITICAL")
        filter_layout.addWidget(self.level_combo)
        
        filter_layout.addWidget(QLabel("模块:"))
        self.module_edit = QTextEdit()
        self.module_edit.setMaximumHeight(30)
        self.module_edit.setMaximumWidth(150)
        self.module_edit.setPlaceholderText("输入模块名")
        filter_layout.addWidget(self.module_edit)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 导出")
        export_btn.setObjectName("actionButton")
        export_btn.clicked.connect(self._export_logs)
        filter_layout.addWidget(export_btn)
        
        main_layout.addWidget(filter_frame)
        
        # 日志列表
        list_group = QGroupBox("📋 日志列表")
        list_layout = QVBoxLayout(list_group)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels([
            "ID", "级别", "模块", "消息", "用户", "时间"
        ])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self.log_table)
        
        main_layout.addWidget(list_group)
        
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        stylesheet = """
        QLabel#pageTitle {
            color: #1976D2;
            padding: 10px;
            background-color: #E3F2FD;
            border-radius: 5px;
        }
        
        QGroupBox {
            font-weight: bold;
            font-size: 14px;
            border: 1px solid #BDBDBD;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QPushButton#actionButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            self._update_log_table()
        except Exception as e:
            self.logger.error(f"刷新日志数据失败：{e}")
    
    def _update_log_table(self):
        """更新日志表格"""
        level = self.level_combo.currentData()
        module = self.module_edit.toPlainText().strip() or None
        
        logs = self.db_manager.get_system_logs(
            log_level=level if level else None,
            module=module,
            limit=100
        )
        
        self.log_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            self.log_table.setItem(row, 0, QTableWidgetItem(str(log.get('id', ''))))
            
            level_item = QTableWidgetItem(log.get('log_level', ''))
            level_color = {
                'DEBUG': '#9E9E9E',
                'INFO': '#2196F3',
                'WARNING': '#FF9800',
                'ERROR': '#F44336',
                'CRITICAL': '#9C27B0'
            }.get(log.get('log_level', ''), '#000000')
            level_item.setForeground(Qt.GlobalColor.black)
            level_item.setBackground(Qt.GlobalColor.white)
            self.log_table.setItem(row, 1, level_item)
            
            self.log_table.setItem(row, 2, QTableWidgetItem(log.get('module', '')))
            self.log_table.setItem(row, 3, QTableWidgetItem(log.get('message', '')))
            self.log_table.setItem(row, 4, QTableWidgetItem(str(log.get('user_id', ''))))
            self.log_table.setItem(row, 5, QTableWidgetItem(str(log.get('created_at', ''))[:19]))
    
    def _export_logs(self):
        """导出日志"""
        QMessageBox.information(self, "导出", "日志导出功能开发中...")
