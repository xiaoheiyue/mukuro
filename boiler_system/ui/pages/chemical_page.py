"""
化学品管理页面 - Chemical Page
管理清洗化学品的库存和使用
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QTextEdit, QFormLayout,
    QDialog, QDialogButtonBox, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import logging
from typing import Dict

from core.database import DatabaseManager


class ChemicalPage(QWidget):
    """化学品管理页面类"""
    
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
        title_label = QLabel("🧪 化学品管理")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 控制栏
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        add_btn = QPushButton("➕ 添加化学品")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_chemical)
        control_layout.addWidget(add_btn)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # 库存概览
        overview_group = QGroupBox("📊 库存概览")
        overview_layout = QVBoxLayout(overview_group)
        
        self.overview_table = QTableWidget()
        self.overview_table.setColumnCount(7)
        self.overview_table.setHorizontalHeaderLabels([
            "ID", "名称", "类型", "当前库存", "单位", "最低库存", "状态"
        ])
        self.overview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        overview_layout.addWidget(self.overview_table)
        
        main_layout.addWidget(overview_group)
        
        # 使用记录
        usage_group = QGroupBox("📝 使用记录")
        usage_layout = QVBoxLayout(usage_group)
        
        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(6)
        self.usage_table.setHorizontalHeaderLabels([
            "ID", "化学品", "用量", "用途", "操作人", "时间"
        ])
        self.usage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        usage_layout.addWidget(self.usage_table)
        
        main_layout.addWidget(usage_group)
        
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
            background-color: #00BCD4;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            self._update_overview_table()
            self._update_usage_table()
        except Exception as e:
            self.logger.error(f"刷新化学品数据失败：{e}")
    
    def _update_overview_table(self):
        """更新库存概览表格"""
        chemicals = self.db_manager.get_all_chemicals()
        
        self.overview_table.setRowCount(len(chemicals))
        
        for row, chem in enumerate(chemicals):
            self.overview_table.setItem(row, 0, QTableWidgetItem(str(chem.get('id', ''))))
            self.overview_table.setItem(row, 1, QTableWidgetItem(chem.get('chemical_name', '')))
            self.overview_table.setItem(row, 2, QTableWidgetItem(chem.get('chemical_type', '')))
            
            qty_item = QTableWidgetItem(f"{chem.get('current_quantity', 0):.2f}")
            if chem.get('current_quantity', 0) <= chem.get('min_quantity', 0):
                qty_item.setForeground(Qt.GlobalColor.red)
            self.overview_table.setItem(row, 3, qty_item)
            
            self.overview_table.setItem(row, 4, QTableWidgetItem(chem.get('unit', '')))
            self.overview_table.setItem(row, 5, QTableWidgetItem(f"{chem.get('min_quantity', 0):.2f}"))
            
            status = "⚠️ 低库存" if chem.get('current_quantity', 0) <= chem.get('min_quantity', 0) else "✅ 正常"
            self.overview_table.setItem(row, 6, QTableWidgetItem(status))
    
    def _update_usage_table(self):
        """更新使用记录表格"""
        usage_records = self.db_manager.get_chemical_usage()[:20]
        
        self.usage_table.setRowCount(len(usage_records))
        
        for row, record in enumerate(usage_records):
            self.usage_table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            
            chem = self.db_manager.get_chemical(record.get('chemical_id'))
            chem_name = chem.get('chemical_name', '') if chem else ''
            self.usage_table.setItem(row, 1, QTableWidgetItem(chem_name))
            
            self.usage_table.setItem(row, 2, QTableWidgetItem(f"{record.get('quantity_used', 0):.2f} {record.get('unit', '')}"))
            self.usage_table.setItem(row, 3, QTableWidgetItem(record.get('usage_purpose', '')))
            self.usage_table.setItem(row, 4, QTableWidgetItem(str(record.get('used_by', ''))))
            self.usage_table.setItem(row, 5, QTableWidgetItem(str(record.get('created_at', ''))[:19]))
    
    def _add_chemical(self):
        """添加化学品"""
        dialog = AddChemicalDialog(self.db_manager, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "化学品已添加！")


class AddChemicalDialog(QDialog):
    """添加化学品对话框"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("添加化学品")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QTextEdit()
        self.name_edit.setMaximumHeight(40)
        form.addRow("名称:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["acid", "alkali", "neutralizer", "dispersant", "other"])
        form.addRow("类型:", self.type_combo)
        
        self.qty_edit = QTextEdit()
        self.qty_edit.setMaximumHeight(40)
        form.addRow("初始数量:", self.qty_edit)
        
        self.unit_edit = QTextEdit()
        self.unit_edit.setMaximumHeight(40)
        self.unit_edit.setText("L")
        form.addRow("单位:", self.unit_edit)
        
        self.min_qty_edit = QTextEdit()
        self.min_qty_edit.setMaximumHeight(40)
        form.addRow("最低库存:", self.min_qty_edit)
        
        self.location_edit = QTextEdit()
        self.location_edit.setMaximumHeight(40)
        form.addRow("存放位置:", self.location_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        name = self.name_edit.toPlainText()
        ctype = self.type_combo.currentText()
        try:
            qty = float(self.qty_edit.toPlainText() or 0)
            min_qty = float(self.min_qty_edit.toPlainText() or 0)
        except ValueError:
            qty = 0
            min_qty = 0
        unit = self.unit_edit.toPlainText()
        location = self.location_edit.toPlainText()
        
        if name:
            self.db_manager.add_chemical(
                chemical_name=name,
                chemical_type=ctype,
                current_quantity=qty,
                unit=unit,
                min_quantity=min_qty,
                storage_location=location
            )
            super().accept()
