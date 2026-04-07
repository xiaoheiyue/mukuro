"""
维护管理页面 - Maintenance Page
设备维护计划和管理
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QTextEdit, QFormLayout,
    QDialog, QDialogButtonBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import logging
from typing import Dict
from datetime import datetime

from core.database import DatabaseManager


class MaintenancePage(QWidget):
    """维护管理页面类"""
    
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
        title_label = QLabel("🔧 维护管理")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 控制栏
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        new_btn = QPushButton("➕ 新建维护")
        new_btn.setObjectName("primaryButton")
        new_btn.clicked.connect(self._new_maintenance)
        control_layout.addWidget(new_btn)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # 待处理维护
        pending_group = QGroupBox("⏳ 待处理维护")
        pending_layout = QVBoxLayout(pending_group)
        
        self.pending_table = QTableWidget()
        self.pending_table.setColumnCount(6)
        self.pending_table.setHorizontalHeaderLabels([
            "ID", "锅炉", "类型", "计划日期", "描述", "操作"
        ])
        self.pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pending_layout.addWidget(self.pending_table)
        
        main_layout.addWidget(pending_group)
        
        # 历史记录
        history_group = QGroupBox("📜 维护历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "锅炉", "类型", "计划日期", "完成日期", "成本", "状态"
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
        
        QPushButton#primaryButton {
            background-color: #9C27B0;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        QPushButton#completeButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            self._update_pending_table()
            self._update_history_table()
        except Exception as e:
            self.logger.error(f"刷新维护数据失败：{e}")
    
    def _update_pending_table(self):
        """更新待处理维护表格"""
        records = self.db_manager.get_maintenance_records(status='scheduled')
        
        self.pending_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            self.pending_table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            
            boiler = self.db_manager.get_boiler(record.get('boiler_id'))
            boiler_name = boiler.get('name', '') if boiler else ''
            self.pending_table.setItem(row, 1, QTableWidgetItem(boiler_name))
            
            self.pending_table.setItem(row, 2, QTableWidgetItem(record.get('maintenance_type', '')))
            self.pending_table.setItem(row, 3, QTableWidgetItem(str(record.get('scheduled_date', ''))))
            self.pending_table.setItem(row, 4, QTableWidgetItem(record.get('description', '')))
            
            complete_btn = QPushButton("✅ 完成")
            complete_btn.setObjectName("completeButton")
            complete_btn.clicked.connect(lambda checked, r=record: self._complete_maintenance(r))
            self.pending_table.setCellWidget(row, 5, complete_btn)
    
    def _update_history_table(self):
        """更新维护历史表格"""
        records = self.db_manager.get_maintenance_records(status='completed')[:20]
        
        self.history_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            
            boiler = self.db_manager.get_boiler(record.get('boiler_id'))
            boiler_name = boiler.get('name', '') if boiler else ''
            self.history_table.setItem(row, 1, QTableWidgetItem(boiler_name))
            
            self.history_table.setItem(row, 2, QTableWidgetItem(record.get('maintenance_type', '')))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(record.get('scheduled_date', ''))))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(record.get('completed_date', ''))))
            self.history_table.setItem(row, 5, QTableWidgetItem(f"¥{record.get('cost', 0):.2f}"))
            self.history_table.setItem(row, 6, QTableWidgetItem(record.get('status', '')))
    
    def _new_maintenance(self):
        """新建维护记录"""
        dialog = MaintenanceDialog(self.db_manager, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "维护计划已创建！")
    
    def _complete_maintenance(self, record: Dict):
        """完成维护"""
        dialog = CompleteMaintenanceDialog(record, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "维护已完成！")


class MaintenanceDialog(QDialog):
    """新建维护对话框"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("新建维护计划")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.boiler_combo = QComboBox()
        boilers = self.db_manager.get_all_boilers()
        for boiler in boilers:
            self.boiler_combo.addItem(boiler.get('name', ''), boiler.get('id'))
        form.addRow("锅炉:", self.boiler_combo)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["routine", "preventive", "corrective", "emergency", "inspection", "calibration"])
        form.addRow("类型:", self.type_combo)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate().addDays(7))
        self.date_edit.setCalendarPopup(True)
        form.addRow("计划日期:", self.date_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        form.addRow("描述:", self.desc_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        boiler_id = self.boiler_combo.currentData()
        mtype = self.type_combo.currentText()
        sdate = self.date_edit.date().toString("yyyy-MM-dd")
        desc = self.desc_edit.toPlainText()
        
        if boiler_id:
            self.db_manager.create_maintenance_record(
                boiler_id=boiler_id,
                maintenance_type=mtype,
                description=desc,
                scheduled_date=sdate
            )
            super().accept()


class CompleteMaintenanceDialog(QDialog):
    """完成维护对话框"""
    
    def __init__(self, record: Dict, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("完成维护")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.parts_edit = QTextEdit()
        self.parts_edit.setMaximumHeight(40)
        form.addRow("更换部件:", self.parts_edit)
        
        self.cost_edit = QTextEdit()
        self.cost_edit.setMaximumHeight(40)
        form.addRow("成本:", self.cost_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form.addRow("备注:", self.notes_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        record_id = self.record.get('id')
        parts = self.parts_edit.toPlainText()
        try:
            cost = float(self.cost_edit.toPlainText() or 0)
        except ValueError:
            cost = 0
        notes = self.notes_edit.toPlainText()
        
        self.db_manager.complete_maintenance(
            record_id=record_id,
            parts_replaced=parts,
            cost=cost,
            notes=notes
        )
        super().accept()
