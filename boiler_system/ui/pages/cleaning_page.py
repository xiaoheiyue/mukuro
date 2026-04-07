"""
清洗管理页面 - Cleaning Management Page
管理和执行锅炉清洗流程
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox,
    QProgressBar, QTextEdit, QFormLayout, QDialog,
    QDialogButtonBox, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QFont

import logging
from typing import Dict, Any
from datetime import datetime

from core.database import DatabaseManager


class CleaningManagementPage(QWidget):
    """清洗管理页面类"""
    
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
        title_label = QLabel("🧹 清洗管理")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 控制栏
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # 开始清洗按钮
        start_btn = QPushButton("🚀 开始新清洗")
        start_btn.setObjectName("primaryButton")
        start_btn.clicked.connect(self._start_cleaning)
        control_layout.addWidget(start_btn)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # 运行中的清洗
        running_group = QGroupBox("🔄 运行中的清洗")
        running_layout = QVBoxLayout(running_group)
        
        self.running_table = QTableWidget()
        self.running_table.setColumnCount(7)
        self.running_table.setHorizontalHeaderLabels([
            "ID", "锅炉", "类型", "开始时间", "进度", "状态", "操作"
        ])
        self.running_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        running_layout.addWidget(self.running_table)
        
        main_layout.addWidget(running_group)
        
        # 历史记录
        history_group = QGroupBox("📜 清洗历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "锅炉", "类型", "开始时间", "持续时间", "结果"
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
            background-color: #FF9800;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        QPushButton#primaryButton:hover {
            background-color: #F57C00;
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
            self._update_running_table()
            self._update_history_table()
        except Exception as e:
            self.logger.error(f"刷新清洗数据失败：{e}")
    
    def _update_running_table(self):
        """更新运行中清洗表格"""
        records = self.db_manager.get_cleaning_records(status='running')
        
        self.running_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            self.running_table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            
            # 锅炉名称
            boiler = self.db_manager.get_boiler(record.get('boiler_id'))
            boiler_name = boiler.get('name', '') if boiler else ''
            self.running_table.setItem(row, 1, QTableWidgetItem(boiler_name))
            
            self.running_table.setItem(row, 2, QTableWidgetItem(record.get('cleaning_type', '')))
            self.running_table.setItem(row, 3, QTableWidgetItem(str(record.get('start_time', ''))[:19]))
            
            # 进度条
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(50)  # 示例值
            self.running_table.setCellWidget(row, 4, progress)
            
            self.running_table.setItem(row, 5, QTableWidgetItem(record.get('status', '')))
            
            # 完成按钮
            complete_btn = QPushButton("✅ 完成")
            complete_btn.setObjectName("completeButton")
            complete_btn.clicked.connect(lambda checked, r=record: self._complete_cleaning(r))
            self.running_table.setCellWidget(row, 6, complete_btn)
    
    def _update_history_table(self):
        """更新历史清洗表格"""
        records = self.db_manager.get_cleaning_records(status='completed')[:20]
        
        self.history_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            
            boiler = self.db_manager.get_boiler(record.get('boiler_id'))
            boiler_name = boiler.get('name', '') if boiler else ''
            self.history_table.setItem(row, 1, QTableWidgetItem(boiler_name))
            
            self.history_table.setItem(row, 2, QTableWidgetItem(record.get('cleaning_type', '')))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(record.get('start_time', ''))[:19]))
            
            duration = record.get('duration_minutes')
            duration_str = f"{duration}分钟" if duration else '-'
            self.history_table.setItem(row, 4, QTableWidgetItem(duration_str))
            
            result = record.get('result', '')
            self.history_table.setItem(row, 5, QTableWidgetItem(result))
    
    def _start_cleaning(self):
        """开始新清洗"""
        dialog = CleaningDialog(self.db_manager, self)
        if dialog.exec() == 1:  # Accepted
            self.refresh_data()
            QMessageBox.information(self, "成功", "清洗任务已启动！")
    
    def _complete_cleaning(self, record: Dict):
        """完成清洗"""
        dialog = CompleteCleaningDialog(record, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "清洗已完成记录！")


class CleaningDialog(QDialog):
    """新建清洗对话框"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.setWindowTitle("开始新清洗")
        self.setMinimumWidth(400)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # 锅炉选择
        self.boiler_combo = QComboBox()
        boilers = self.db_manager.get_all_boilers()
        for boiler in boilers:
            self.boiler_combo.addItem(boiler.get('name', ''), boiler.get('id'))
        form.addRow("锅炉:", self.boiler_combo)
        
        # 清洗类型
        self.type_combo = QComboBox()
        types = [
            "acid_cleaning", "alkali_cleaning", "high_pressure_water",
            "steam_blowing", "mechanical_cleaning", "ultrasonic_cleaning"
        ]
        self.type_combo.addItems(types)
        form.addRow("清洗类型:", self.type_combo)
        
        # 化学品类型
        self.chemical_edit = QTextEdit()
        self.chemical_edit.setMaximumHeight(60)
        form.addRow("化学品:", self.chemical_edit)
        
        # 备注
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form.addRow("备注:", self.notes_edit)
        
        layout.addLayout(form)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        boiler_id = self.boiler_combo.currentData()
        cleaning_type = self.type_combo.currentText()
        chemical_type = self.chemical_edit.toPlainText()
        notes = self.notes_edit.toPlainText()
        
        if boiler_id:
            self.db_manager.create_cleaning_record(
                boiler_id=boiler_id,
                cleaning_type=cleaning_type,
                chemical_type=chemical_type,
                notes=notes
            )
            super().accept()


class CompleteCleaningDialog(QDialog):
    """完成清洗对话框"""
    
    def __init__(self, record: Dict, parent=None):
        super().__init__(parent)
        
        self.record = record
        self.setWindowTitle("完成清洗记录")
        self.setMinimumWidth(400)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # 持续时间
        self.duration_edit = QTextEdit()
        self.duration_edit.setMaximumHeight(40)
        self.duration_edit.setPlaceholderText("分钟")
        form.addRow("持续时间:", self.duration_edit)
        
        # 化学品用量
        self.chemical_used_edit = QTextEdit()
        self.chemical_used_edit.setMaximumHeight(40)
        form.addRow("化学品用量:", self.chemical_used_edit)
        
        # 结果
        self.result_combo = QComboBox()
        self.result_combo.addItems(["成功", "部分成功", "失败"])
        form.addRow("结果:", self.result_combo)
        
        # 备注
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form.addRow("备注:", self.notes_edit)
        
        layout.addLayout(form)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        record_id = self.record.get('id')
        
        try:
            duration = int(self.duration_edit.toPlainText() or 0)
            chemical_used = float(self.chemical_used_edit.toPlainText() or 0)
        except ValueError:
            duration = 0
            chemical_used = 0
        
        result = self.result_combo.currentText()
        notes = self.notes_edit.toPlainText()
        
        self.db_manager.complete_cleaning_record(
            record_id=record_id,
            duration_minutes=duration,
            chemical_used=chemical_used,
            result=result,
            notes=notes
        )
        
        super().accept()
