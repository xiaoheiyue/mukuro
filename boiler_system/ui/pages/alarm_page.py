"""
报警管理页面 - Alarm Management Page
查看和处理系统报警
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
    QCheckBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import logging
from typing import Dict, Any
from datetime import datetime

from core.database import DatabaseManager


class AlarmManagementPage(QWidget):
    """报警管理页面类"""
    
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
        title_label = QLabel("🚨 报警管理")
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
        self.level_combo.addItem("严重", "critical")
        self.level_combo.addItem("警告", "warning")
        self.level_combo.addItem("信息", "info")
        filter_layout.addWidget(self.level_combo)
        
        filter_layout.addWidget(QLabel("状态:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("全部", "all")
        self.status_combo.addItem("未确认", "unacknowledged")
        self.status_combo.addItem("已确认", "acknowledged")
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addStretch()
        
        # 确认全部按钮
        ack_all_btn = QPushButton("✅ 确认全部")
        ack_all_btn.setObjectName("actionButton")
        ack_all_btn.clicked.connect(self._acknowledge_all)
        filter_layout.addWidget(ack_all_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        main_layout.addWidget(filter_frame)
        
        # 活动报警
        active_group = QGroupBox("⚠️ 活动报警")
        active_layout = QVBoxLayout(active_group)
        
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(7)
        self.active_table.setHorizontalHeaderLabels([
            "ID", "锅炉", "类型", "级别", "消息", "时间", "操作"
        ])
        self.active_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        active_layout.addWidget(self.active_table)
        
        main_layout.addWidget(active_group)
        
        # 历史报警
        history_group = QGroupBox("📜 报警历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "锅炉", "类型", "级别", "消息", "时间", "状态"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)
        
        main_layout.addWidget(history_group)
        
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
            self._update_active_table()
            self._update_history_table()
        except Exception as e:
            self.logger.error(f"刷新报警数据失败：{e}")
    
    def _update_active_table(self):
        """更新活动报警表格"""
        alarms = self.db_manager.get_active_alarms()
        
        self.active_table.setRowCount(len(alarms))
        
        for row, alarm in enumerate(alarms):
            self.active_table.setItem(row, 0, QTableWidgetItem(str(alarm.get('id', ''))))
            
            boiler = self.db_manager.get_boiler(alarm.get('boiler_id'))
            boiler_name = boiler.get('name', '') if boiler else 'N/A'
            self.active_table.setItem(row, 1, QTableWidgetItem(boiler_name))
            
            self.active_table.setItem(row, 2, QTableWidgetItem(alarm.get('alarm_type', '')))
            
            level = alarm.get('alarm_level', '')
            level_item = QTableWidgetItem(level)
            if level == 'critical':
                level_item.setForeground(Qt.GlobalColor.red)
            elif level == 'warning':
                level_item.setForeground(Qt.GlobalColor.darkYellow)
            self.active_table.setItem(row, 3, level_item)
            
            self.active_table.setItem(row, 4, QTableWidgetItem(alarm.get('message', '')))
            self.active_table.setItem(row, 5, QTableWidgetItem(str(alarm.get('created_at', ''))[:19]))
            
            # 确认按钮
            ack_btn = QPushButton("✅ 确认")
            ack_btn.clicked.connect(lambda checked, a=alarm: self._acknowledge_alarm(a))
            self.active_table.setCellWidget(row, 6, ack_btn)
    
    def _update_history_table(self):
        """更新历史报警表格"""
        alarms = self.db_manager.get_alarm_history(limit=50)
        
        self.history_table.setRowCount(len(alarms))
        
        for row, alarm in enumerate(alarms):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(alarm.get('id', ''))))
            
            boiler = self.db_manager.get_boiler(alarm.get('boiler_id'))
            boiler_name = boiler.get('name', '') if boiler else 'N/A'
            self.history_table.setItem(row, 1, QTableWidgetItem(boiler_name))
            
            self.history_table.setItem(row, 2, QTableWidgetItem(alarm.get('alarm_type', '')))
            
            level = alarm.get('alarm_level', '')
            level_item = QTableWidgetItem(level)
            if level == 'critical':
                level_item.setForeground(Qt.GlobalColor.red)
            self.history_table.setItem(row, 3, level_item)
            
            self.history_table.setItem(row, 4, QTableWidgetItem(alarm.get('message', '')))
            self.history_table.setItem(row, 5, QTableWidgetItem(str(alarm.get('created_at', ''))[:19]))
            
            status = "已确认" if alarm.get('is_acknowledged') else "未确认"
            self.history_table.setItem(row, 6, QTableWidgetItem(status))
    
    def _acknowledge_alarm(self, alarm: Dict):
        """确认单个报警"""
        alarm_id = alarm.get('id')
        if alarm_id:
            self.db_manager.acknowledge_alarm(alarm_id, 1)  # TODO: 使用实际用户 ID
            self.logger.info(f"确认报警：{alarm_id}")
            self.refresh_data()
    
    def _acknowledge_all(self):
        """确认全部报警"""
        reply = QMessageBox.question(
            self, "确认全部",
            "确定要确认所有活动报警吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            alarms = self.db_manager.get_active_alarms()
            for alarm in alarms:
                self.db_manager.acknowledge_alarm(alarm.get('id'), 1)
            self.logger.info("确认全部报警")
            self.refresh_data()
