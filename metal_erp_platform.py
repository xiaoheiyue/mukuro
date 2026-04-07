#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
金属制品生产全流程协同管理平台 (Metal Production Collaborative Management Platform)
基于 PyQt6 实现
功能涵盖：订单、生产、库存、质检、设备、报表、系统管理
"""

import sys
import random
import datetime
import logging
from enum import Enum
from typing import List, Dict, Optional, Any

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QFormLayout, QLineEdit, 
    QComboBox, QDateEdit, QSpinBox, QDialog, QDialogButtonBox, 
    QMessageBox, QMenu, QMenuBar, QAction, QStatusBar, QToolBar,
    QGroupBox, QGridLayout, QProgressBar, QTextEdit, QSplitter,
    QTabWidget, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QDate, QModelIndex
from PyQt6.QtGui import QFont, QColor, QIcon, QAction, QPalette, QBrush

# 尝试导入 pyqtgraph 用于图表，如果未安装则使用占位符
try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False
    print("警告: 未找到 pyqtgraph，图表功能将降级显示。请安装: pip install pyqtgraph")

# ==========================================
# 1. 数据模型与枚举 (Data Models & Enums)
# ==========================================

class OrderStatus(Enum):
    PENDING = "待处理"
    PLANNED = "已排产"
    IN_PROGRESS = "生产中"
    QC_PENDING = "待质检"
    COMPLETED = "已完成"
    CANCELLED = "已取消"

class EquipmentStatus(Enum):
    RUNNING = "运行中"
    IDLE = "空闲"
    MAINTENANCE = "维护中"
    ERROR = "故障"

class MockDatabase:
    """模拟数据库，生成初始数据"""
    
    @staticmethod
    def get_initial_orders() -> List[Dict]:
        statuses = [OrderStatus.PENDING, OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED]
        products = ["不锈钢板材", "铝合金型材", "铜管", "钛合金零件", "镀锌钢板"]
        orders = []
        for i in range(1, 21):
            orders.append({
                "id": f"ORD-{2023000 + i}",
                "customer": f"客户_{chr(65 + i % 5)}{i}",
                "product": random.choice(products),
                "quantity": random.randint(100, 5000),
                "deadline": QDate.currentDate().addDays(random.randint(5, 30)).toString("yyyy-MM-dd"),
                "status": random.choice(statuses).value,
                "priority": random.choice(["高", "中", "低"])
            })
        return orders

    @staticmethod
    def get_initial_inventory() -> List[Dict]:
        items = [
            {"name": "304不锈钢卷", "category": "原材料", "stock": 1200, "unit": "kg", "min_stock": 500},
            {"name": "6061铝棒", "category": "原材料", "stock": 800, "unit": "kg", "min_stock": 300},
            {"name": "紫铜板", "category": "原材料", "stock": 200, "unit": "kg", "min_stock": 100},
            {"name": "成品-法兰盘", "category": "成品", "stock": 5000, "unit": "件", "min_stock": 1000},
            {"name": "成品-散热片", "category": "成品", "stock": 300, "unit": "件", "min_stock": 500},
        ]
        return items

    @staticmethod
    def get_initial_equipment() -> List[Dict]:
        return [
            {"id": "EQ-001", "name": "数控冲床 #1", "type": "冲压", "status": EquipmentStatus.RUNNING.value, "efficiency": 92},
            {"id": "EQ-002", "name": "激光切割机 #2", "type": "切割", "status": EquipmentStatus.IDLE.value, "efficiency": 88},
            {"id": "EQ-003", "name": "折弯机 #3", "type": "成型", "status": EquipmentStatus.MAINTENANCE.value, "efficiency": 0},
            {"id": "EQ-004", "name": "焊接机器人 #4", "type": "焊接", "status": EquipmentStatus.RUNNING.value, "efficiency": 95},
            {"id": "EQ-005", "name": "喷涂线 #5", "type": "表面处理", "status": EquipmentStatus.ERROR.value, "efficiency": 40},
        ]

# ==========================================
# 2. 自定义组件 (Custom Widgets)
# ==========================================

class StatusLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("padding: 4px; border-radius: 4px; font-weight: bold;")
        self.update_style(text)

    def update_style(self, status: str):
        color = "#cccccc"
        if status in ["已完成", "运行中"]:
            color = "#2ecc71" # Green
            self.setStyleSheet(f"background-color: {color}; color: white; padding: 4px; border-radius: 4px;")
        elif status in ["生产中", "待处理", "空闲"]:
            color = "#3498db" # Blue
            self.setStyleSheet(f"background-color: {color}; color: white; padding: 4px; border-radius: 4px;")
        elif status in ["故障", "已取消", "维护中"]:
            color = "#e74c3c" # Red
            self.setStyleSheet(f"background-color: {color}; color: white; padding: 4px; border-radius: 4px;")
        elif status in ["待质检"]:
            color = "#f39c12" # Orange
            self.setStyleSheet(f"background-color: {color}; color: white; padding: 4px; border-radius: 4px;")
        else:
            self.setStyleSheet("padding: 4px;")

class CardWidget(QFrame):
    def __init__(self, title: str, value: str, unit: str = "", icon_char: str = "?", parent=None):
        super().__init__(parent)
        self.setObjectName("CardWidget")
        self.setStyleSheet("""
            #CardWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            #CardWidget:hover {
                border: 1px solid #3498db;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon_char)
        icon_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        icon_label.setStyleSheet("color: #3498db;")
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        title_label.setStyleSheet("color: #7f8c8d;")
        
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(f"{value} {unit}")
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        layout.addStretch()

class SimpleChartWidget(QWidget):
    """简单的图表占位或基础实现"""
    def __init__(self, title: str, data: List[float], labels: List[str], parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white; border: 1px solid #eee; border-radius: 4px;")
        layout = QVBoxLayout(self)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        if HAS_PYQTGRAPH:
            self.plotWidget = pg.PlotWidget()
            self.plotWidget.setBackground('w')
            self.plotWidget.plot(labels, data, pen='b', symbol='o', symbolBrush='b')
            self.plotWidget.showGrid(x=True, y=True, alpha=0.3)
            layout.addWidget(self.plotWidget)
        else:
            # Fallback visualization
            bar_container = QWidget()
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(10, 10, 10, 10)
            max_val = max(data) if data else 1
            for i, val in enumerate(data):
                h = int((val / max_val) * 100) if max_val > 0 else 10
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setValue(h)
                bar.setFormat(f"{labels[i]}\n{val}")
                bar.setTextVisible(True)
                bar.setOrientation(Qt.Orientation.Vertical)
                bar.setMinimumHeight(100)
                bar_layout.addWidget(bar)
            layout.addWidget(bar_container)

# ==========================================
# 3. 功能页面模块 (Feature Modules)
# ==========================================

class DashboardPage(QWidget):
    def __init__(self, db: MockDatabase):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()
        
        # 模拟实时数据更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulate_realtime_update)
        self.timer.start(5000)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        header = QLabel("生产全景仪表盘")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # KPI Cards
        cards_layout = QGridLayout()
        self.card_total_orders = CardWidget("今日订单", "0", "单", "📦")
        self.card_production = CardWidget("在产进度", "0", "%", "🏭")
        self.card_alerts = CardWidget("异常警报", "0", "起", "⚠️")
        self.card_efficiency = CardWidget("设备综合效率", "0", "%", "⚡")
        
        cards_layout.addWidget(self.card_total_orders, 0, 0)
        cards_layout.addWidget(self.card_production, 0, 1)
        cards_layout.addWidget(self.card_alerts, 0, 2)
        cards_layout.addWidget(self.card_efficiency, 0, 3)
        
        main_layout.addLayout(cards_layout)
        
        # Charts Area
        charts_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Chart: Production Trend
        self.chart_production = SimpleChartWidget("近7日产量趋势 (吨)", 
                                                  [12, 15, 14, 18, 20, 17, 22], 
                                                  ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        
        # Right Chart: Order Status Distribution
        self.chart_orders = SimpleChartWidget("订单状态分布", 
                                              [5, 8, 3, 2], 
                                              ["待处理", "生产中", "待质检", "已完成"])
        
        charts_splitter.addWidget(self.chart_production)
        charts_splitter.addWidget(self.chart_orders)
        charts_splitter.setStretchFactor(0, 1)
        charts_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(charts_splitter, stretch=1)
        
        # Recent Alerts Table
        alert_group = QGroupBox("实时告警列表")
        alert_layout = QVBoxLayout(alert_group)
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(4)
        self.alert_table.setHorizontalHeaderLabels(["时间", "类型", "内容", "状态"])
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alert_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        alert_layout.addWidget(self.alert_table)
        main_layout.addWidget(alert_group, stretch=1)

    def refresh_data(self):
        # Simulate data loading
        self.card_total_orders.findChild(QLabel).setText(f"{random.randint(10, 50)} 单")
        self.card_production.findChild(QLabel).setText(f"{random.randint(60, 95)} %")
        self.card_alerts.findChild(QLabel).setText(f"{random.randint(0, 5)} 起")
        self.card_efficiency.findChild(QLabel).setText(f"{random.randint(80, 98)} %")
        
        # Populate alerts
        self.alert_table.setRowCount(0)
        alerts = [
            ("10:23", "设备", "激光切割机 #2 温度过高", "未处理"),
            ("09:45", "库存", "304不锈钢卷 低于安全库存", "已通知"),
            ("08:30", "质量", "批次 B-2023 尺寸超差", "处理中"),
        ]
        for t, type_, msg, status in alerts:
            row = self.alert_table.rowCount()
            self.alert_table.insertRow(row)
            self.alert_table.setItem(row, 0, QTableWidgetItem(t))
            self.alert_table.setItem(row, 1, QTableWidgetItem(type_))
            self.alert_table.setItem(row, 2, QTableWidgetItem(msg))
            item = QTableWidgetItem(status)
            if status == "未处理":
                item.setForeground(QColor("red"))
            self.alert_table.setItem(row, 3, item)

    def simulate_realtime_update(self):
        # Randomly fluctuate numbers to look alive
        current_eff = int(self.card_efficiency.findChild(QLabel).text().split()[0].replace('%', ''))
        new_eff = max(0, min(100, current_eff + random.randint(-2, 2)))
        self.card_efficiency.findChild(QLabel).setText(f"{new_eff} %")

class OrderManagementPage(QWidget):
    def __init__(self, db: MockDatabase):
        super().__init__()
        self.db = db
        self.orders = db.get_initial_orders()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("搜索订单号/客户...")
        search_box.setFixedWidth(250)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部状态"] + [s.value for s in OrderStatus])
        
        btn_add = QPushButton("+ 新建订单")
        btn_add.setStyleSheet("background-color: #3498db; color: white; padding: 8px; border-radius: 4px;")
        btn_add.clicked.connect(self.add_order_dialog)
        
        btn_export = QPushButton("导出报表")
        btn_export.clicked.connect(self.export_data)
        
        toolbar.addWidget(search_box)
        toolbar.addWidget(self.status_filter)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_export)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.orders[0].keys()))
        self.table.setHorizontalHeaderLabels(list(self.orders[0].keys()))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
        
        self.refresh_table()
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def refresh_table(self):
        self.table.setRowCount(0)
        filter_status = self.status_filter.currentText()
        
        for order in self.orders:
            if filter_status != "全部状态" and order["status"] != filter_status:
                continue
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, key in enumerate(order.keys()):
                val = order[key]
                if key == "status":
                    item = StatusLabel(val)
                    # QTableWidget cannot directly take custom widgets in standard setItem without wrapping
                    # For simplicity in this demo, we use standard QTableWidgetItem but color it
                    item = QTableWidgetItem(val)
                    if val == "已完成": item.setForeground(QColor("green"))
                    elif val == "生产中": item.setForeground(QColor("blue"))
                    elif val == "故障" or val == "已取消": item.setForeground(QColor("red"))
                else:
                    item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

    def add_order_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("新建生产订单")
        dialog.setMinimumWidth(400)
        
        form = QFormLayout()
        inputs = {}
        fields = [
            ("客户名称", "text"),
            ("产品类型", "combo", ["不锈钢板材", "铝合金型材", "铜管"]),
            ("数量", "spin", (100, 10000)),
            ("交货日期", "date"),
            ("优先级", "combo", ["高", "中", "低"])
        ]
        
        for label, f_type, extra in fields:
            if f_type == "text":
                widget = QLineEdit()
            elif f_type == "combo":
                widget = QComboBox()
                widget.addItems(extra)
            elif f_type == "spin":
                widget = QSpinBox()
                widget.setRange(*extra)
            elif f_type == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate().addDays(7))
            
            form.addRow(label, widget)
            inputs[label] = widget
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        
        dialog.setLayout(form)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_id = f"ORD-{2023000 + len(self.orders) + 1}"
            new_order = {
                "id": new_id,
                "customer": inputs["客户名称"].text(),
                "product": inputs["产品类型"].currentText(),
                "quantity": inputs["数量"].value(),
                "deadline": inputs["交货日期"].date().toString("yyyy-MM-dd"),
                "status": OrderStatus.PENDING.value,
                "priority": inputs["优先级"].currentText()
            }
            self.orders.insert(0, new_order)
            self.refresh_table()
            QMessageBox.information(self, "成功", "订单创建成功！")

    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0: return
        
        menu = QMenu(self)
        action_edit = QAction("编辑详情", self)
        action_status = QAction("变更状态", self)
        action_delete = QAction("删除订单", self)
        
        menu.addAction(action_edit)
        menu.addAction(action_status)
        menu.addSeparator()
        menu.addAction(action_delete)
        
        action_delete.triggered.connect(lambda: self.delete_order(row))
        action_status.triggered.connect(lambda: self.change_status(row))
        
        menu.exec(self.table.mapToGlobal(pos))

    def delete_order(self, row):
        reply = QMessageBox.question(self, '确认', '确定要删除该订单吗？', 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Find actual index in self.orders based on ID logic would be better, here simplified
            # In a real app, map view row to model index
            self.orders.pop(row) # Warning: This assumes no filtering, for demo only
            self.refresh_table()

    def change_status(self, row):
        current_id = self.table.item(row, 0).text()
        # Find in list
        for order in self.orders:
            if order['id'] == current_id:
                current_status_idx = [s.value for s in OrderStatus].index(order['status'])
                next_status_idx = (current_status_idx + 1) % len(OrderStatus)
                if next_status_idx == 0: next_status_idx = 1 # Skip pending loop
                
                new_status = list(OrderStatus)[next_status_idx].value
                order['status'] = new_status
                self.refresh_table()
                break

    def export_data(self):
        QMessageBox.information(self, "导出", "数据已导出为 CSV (模拟)")

class InventoryPage(QWidget):
    def __init__(self, db: MockDatabase):
        super().__init__()
        self.items = db.get_initial_inventory()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("库存管理中心")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["物料编码", "名称", "分类", "当前库存", "单位", "最低警戒"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        for item in self.items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Generate fake ID
            pid = f"M-{random.randint(1000,9999)}"
            
            self.table.setItem(row, 0, QTableWidgetItem(pid))
            self.table.setItem(row, 1, QTableWidgetItem(item['name']))
            self.table.setItem(row, 2, QTableWidgetItem(item['category']))
            
            stock_item = QTableWidgetItem(str(item['stock']))
            if item['stock'] < item['min_stock']:
                stock_item.setBackground(QColor("#ffcccc")) # Light red
                stock_item.setForeground(QColor("red"))
                stock_item.setFlags(stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.table.setItem(row, 3, stock_item)
            self.table.setItem(row, 4, QTableWidgetItem(item['unit']))
            self.table.setItem(row, 5, QTableWidgetItem(str(item['min_stock'])))

class EquipmentPage(QWidget):
    def __init__(self, db: MockDatabase):
        super().__init__()
        self.equipments = db.get_initial_equipment()
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(2000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("设备状态监控")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        grid = QGridLayout()
        self.cards = []
        
        for i, eq in enumerate(self.equipments):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #eee;
                    border-radius: 10px;
                }
            """)
            card.setFixedSize(250, 200)
            
            v_layout = QVBoxLayout(card)
            v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_lbl = QLabel(eq['name'])
            name_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            status_lbl = StatusLabel(eq['status'])
            status_lbl.setFixedWidth(100)
            
            eff_lbl = QLabel(f"OEE: {eq['efficiency']}%")
            eff_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Progress bar for efficiency
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(eq['efficiency'])
            progress.setTextVisible(True)
            progress.setFormat("%p%")
            
            v_layout.addWidget(name_lbl)
            v_layout.addSpacing(10)
            v_layout.addWidget(status_lbl)
            v_layout.addSpacing(10)
            v_layout.addWidget(eff_lbl)
            v_layout.addWidget(progress)
            
            grid.addWidget(card, i // 3, i % 3)
            self.cards.append({"frame": card, "eff_lbl": eff_lbl, "progress": progress, "data": eq})
            
        layout.addLayout(grid)
        layout.addStretch()

    def update_simulation(self):
        for item in self.cards:
            if item['data']['status'] == EquipmentStatus.RUNNING.value:
                # Fluctuate efficiency
                current = item['progress'].value()
                new_val = max(0, min(100, current + random.randint(-3, 3)))
                item['progress'].setValue(new_val)
                item['eff_lbl'].setText(f"OEE: {new_val}%")

# ==========================================
# 4. 主窗口框架 (Main Window)
# ==========================================

class MetalERPMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("金属制品生产全流程协同管理平台 v1.0")
        self.resize(1280, 800)
        
        self.db = MockDatabase()
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar Navigation
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(10)
        
        # Logo Area
        logo_lbl = QLabel("MetalERP")
        logo_lbl.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("color: white; margin-bottom: 30px;")
        sidebar_layout.addWidget(logo_lbl)
        
        # Nav Buttons
        self.nav_buttons = {}
        pages = [
            ("dashboard", "📊 总览仪表盘"),
            ("orders", "📝 订单管理"),
            ("production", "🏭 生产计划"),
            ("inventory", "📦 库存管理"),
            ("quality", "🔍 质量检测"),
            ("equipment", "⚙️ 设备监控"),
            ("reports", "📈 统计报表"),
            ("settings", "🔧 系统设置")
        ]
        
        self.stack = QStackedWidget()
        
        for key, text in pages:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 15px 20px;
                    background-color: transparent;
                    color: #ecf0f1;
                    font-size: 14px;
                    border: none;
                    border-left: 4px solid transparent;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.1);
                }
                QPushButton:checked {
                    background-color: rgba(255,255,255,0.2);
                    border-left: 4px solid #3498db;
                    font-weight: bold;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.switch_page(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn
            
            # Create Page Content
            page_widget = self.create_page_content(key)
            self.stack.addWidget(page_widget)
        
        sidebar_layout.addStretch()
        
        # User Profile at bottom
        user_lbl = QLabel("👤 管理员: Admin")
        user_lbl.setStyleSheet("color: #bdc3c7; padding: 10px;")
        sidebar_layout.addWidget(user_lbl)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)
        
        # Status Bar
        self.statusBar().showMessage("系统就绪 | 连接服务器: 192.168.1.100 | 版本: 1.0.0")
        
        # Default Page
        self.switch_page("dashboard")

    def create_page_content(self, key: str) -> QWidget:
        if key == "dashboard":
            return DashboardPage(self.db)
        elif key == "orders":
            return OrderManagementPage(self.db)
        elif key == "inventory":
            return InventoryPage(self.db)
        elif key == "equipment":
            return EquipmentPage(self.db)
        elif key == "production":
            # Placeholder for brevity, structure is same
            w = QWidget()
            l = QVBoxLayout(w)
            l.addWidget(QLabel("<h2>生产排程中心 (甘特图模块)</h2>"))
            l.addWidget(QLabel("此处集成复杂的排程算法与交互式甘特图。"))
            l.addStretch()
            return w
        elif key == "quality":
            w = QWidget()
            l = QVBoxLayout(w)
            l.addWidget(QLabel("<h2>质量追溯系统</h2>"))
            l.addWidget(QLabel("录入质检数据，生成质量分析报告。"))
            l.addStretch()
            return w
        elif key == "reports":
            w = QWidget()
            l = QVBoxLayout(w)
            l.addWidget(QLabel("<h2>多维数据报表</h2>"))
            l.addWidget(QLabel("产量、成本、良率分析。"))
            l.addStretch()
            return w
        elif key == "settings":
            w = QWidget()
            l = QVBoxLayout(w)
            l.addWidget(QLabel("<h2>系统配置</h2>"))
            l.addWidget(QLabel("用户权限、参数设置、日志管理。"))
            l.addStretch()
            return w
        else:
            return QWidget()

    def switch_page(self, key: str):
        # Update Buttons
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        
        # Switch Stack
        index = list(self.nav_buttons.keys()).index(key)
        self.stack.setCurrentIndex(index)

    def apply_styles(self):
        # Global Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f6f9;
            }
            #Sidebar {
                background-color: #2c3e50;
            }
            QTableWidget {
                background-color: white;
                gridline-color: #eee;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #2c3e50;
            }
            QScrollBar:vertical {
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

# ==========================================
# 5. 程序入口 (Entry Point)
# ==========================================

def main():
    app = QApplication(sys.argv)
    
    # Set Application Font
    font = QFont("Microsoft YaHei", 10) # Use a common Chinese font
    app.setFont(font)
    
    window = MetalERPMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
