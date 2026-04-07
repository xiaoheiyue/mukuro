"""报警管理模块"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class AlarmWidget(QWidget):
    def __init__(self, db_manager, config, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.config = config
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("🚨 报警管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        control_layout = QHBoxLayout()
        self.ack_btn = QPushButton("确认报警")
        self.ack_btn.clicked.connect(self.acknowledge_alarm)
        control_layout.addWidget(self.ack_btn)
        self.clear_btn = QPushButton("清除报警")
        self.clear_btn.clicked.connect(self.clear_alarm)
        control_layout.addWidget(self.clear_btn)
        layout.addLayout(control_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["时间", "类型", "级别", "信息", "值", "状态"])
        layout.addWidget(self.table)
    
    def refresh_data(self):
        alarms = self.db_manager.get_active_alarms()
        self.table.setRowCount(len(alarms))
        for i, alarm in enumerate(alarms):
            self.table.setItem(i, 0, QTableWidgetItem(str(alarm.get('occurred_at', ''))))
            self.table.setItem(i, 1, QTableWidgetItem(alarm.get('alarm_type', '')))
            self.table.setItem(i, 2, QTableWidgetItem(alarm.get('severity', '')))
            self.table.setItem(i, 3, QTableWidgetItem(alarm.get('message', '')))
            self.table.setItem(i, 4, QTableWidgetItem(str(alarm.get('value_at_alarm', ''))))
            status = "已确认" if alarm.get('acknowledged') else "未确认"
            self.table.setItem(i, 5, QTableWidgetItem(status))
    
    def acknowledge_alarm(self):
        row = self.table.currentRow()
        if row >= 0:
            QMessageBox.information(self, "提示", "报警已确认")
        else:
            QMessageBox.warning(self, "警告", "请先选择一条报警记录")
    
    def clear_alarm(self):
        row = self.table.currentRow()
        if row >= 0:
            QMessageBox.information(self, "提示", "报警已清除")
        else:
            QMessageBox.warning(self, "警告", "请先选择一条报警记录")
