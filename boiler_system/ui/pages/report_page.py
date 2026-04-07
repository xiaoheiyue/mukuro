"""
报告管理页面 - Report Page
生成和查看各类运行报告
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QTextEdit, QFormLayout,
    QDialog, QDialogButtonBox, QDateEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import logging
from typing import Dict
from datetime import datetime

from core.database import DatabaseManager


class ReportPage(QWidget):
    """报告管理页面类"""
    
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
        title_label = QLabel("📋 报告管理")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 控制栏
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        new_btn = QPushButton("📝 生成报告")
        new_btn.setObjectName("primaryButton")
        new_btn.clicked.connect(self._generate_report)
        control_layout.addWidget(new_btn)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # 报告列表
        list_group = QGroupBox("📄 报告列表")
        list_layout = QVBoxLayout(list_group)
        
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "ID", "类型", "标题", "日期范围", "状态", "操作"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self.report_table)
        
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
        
        QPushButton#primaryButton {
            background-color: #673AB7;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        QPushButton#viewButton {
            background-color: #2196F3;
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
            self._update_report_table()
        except Exception as e:
            self.logger.error(f"刷新报告数据失败：{e}")
    
    def _update_report_table(self):
        """更新报告表格"""
        reports = self.db_manager.get_reports()
        
        self.report_table.setRowCount(len(reports))
        
        for row, report in enumerate(reports):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(report.get('id', ''))))
            self.report_table.setItem(row, 1, QTableWidgetItem(report.get('report_type', '')))
            self.report_table.setItem(row, 2, QTableWidgetItem(report.get('title', '')))
            
            date_range = f"{report.get('start_date', '')} ~ {report.get('end_date', '')}"
            self.report_table.setItem(row, 3, QTableWidgetItem(date_range))
            
            status_item = QTableWidgetItem(report.get('status', ''))
            if report.get('status') == 'completed':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.report_table.setItem(row, 4, status_item)
            
            view_btn = QPushButton("👁️ 查看")
            view_btn.setObjectName("viewButton")
            view_btn.clicked.connect(lambda checked, r=report: self._view_report(r))
            self.report_table.setCellWidget(row, 5, view_btn)
    
    def _generate_report(self):
        """生成报告"""
        dialog = GenerateReportDialog(self.db_manager, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "报告已生成！")
    
    def _view_report(self, report: Dict):
        """查看报告"""
        QMessageBox.information(
            self, "报告详情",
            f"标题：{report.get('title', '')}\n"
            f"类型：{report.get('report_type', '')}\n"
            f"状态：{report.get('status', '')}\n"
            f"创建时间：{report.get('created_at', '')}"
        )


class GenerateReportDialog(QDialog):
    """生成报告对话框"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("生成报告")
        self.setMinimumWidth(450)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "daily_operation", "weekly_summary", "monthly_analysis",
            "cleaning_report", "maintenance_report", "alarm_analysis",
            "energy_consumption", "water_quality", "custom"
        ])
        form.addRow("报告类型:", self.type_combo)
        
        self.title_edit = QTextEdit()
        self.title_edit.setMaximumHeight(40)
        self.title_edit.setPlaceholderText("输入报告标题")
        form.addRow("标题:", self.title_edit)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        form.addRow("开始日期:", self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        form.addRow("结束日期:", self.end_date)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("报告描述（可选）")
        form.addRow("描述:", self.desc_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        rtype = self.type_combo.currentText()
        title = self.title_edit.toPlainText() or f"报告_{datetime.now().strftime('%Y%m%d')}"
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        desc = self.desc_edit.toPlainText()
        
        report_id = self.db_manager.create_report(
            report_type=rtype,
            title=title,
            description=desc,
            start_date=start,
            end_date=end
        )
        
        if report_id:
            self.db_manager.update_report_file(report_id, f"reports/{rtype}_{start}_{end}.pdf", "completed")
        
        super().accept()
