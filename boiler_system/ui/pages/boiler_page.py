"""
锅炉监控页面 - Boiler Monitor Page
实时监控锅炉运行参数
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import logging
from typing import Dict, Any

from core.database import DatabaseManager


class BoilerMonitorPage(QWidget):
    """锅炉监控页面类"""
    
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
        title_label = QLabel("🔥 锅炉监控")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 控制栏
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 锅炉选择
        control_layout.addWidget(QLabel("选择锅炉："))
        self.boiler_combo = QComboBox()
        self.boiler_combo.currentIndexChanged.connect(self._on_boiler_selected)
        control_layout.addWidget(self.boiler_combo)
        
        control_layout.addStretch()
        
        # 操作按钮
        start_btn = QPushButton("▶️ 启动")
        start_btn.setObjectName("actionButton")
        start_btn.clicked.connect(self._start_boiler)
        control_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("⏹️ 停止")
        stop_btn.setObjectName("actionButtonWarning")
        stop_btn.clicked.connect(self._stop_boiler)
        control_layout.addWidget(stop_btn)
        
        maintenance_btn = QPushButton("🔧 维护模式")
        maintenance_btn.setObjectName("actionButtonInfo")
        maintenance_btn.clicked.connect(self._set_maintenance)
        control_layout.addWidget(maintenance_btn)
        
        main_layout.addWidget(control_frame)
        
        # 参数显示区
        params_group = QGroupBox("📊 运行参数")
        params_layout = QGridLayout(params_group)
        
        self.param_labels = {}
        params = [
            ("pressure", "压力", "MPa", "#2196F3"),
            ("temperature", "温度", "°C", "#F44336"),
            ("water_level", "水位", "%", "#4CAF50"),
            ("flow_rate", "流量", "m³/h", "#FF9800"),
            ("ph_value", "pH 值", "", "#9C27B0"),
            ("conductivity", "电导率", "μS/cm", "#00BCD4"),
        ]
        
        for i, (key, name, unit, color) in enumerate(params):
            # 名称
            name_label = QLabel(f"{name}:")
            name_label.setFont(QFont("Microsoft YaHei", 12))
            params_layout.addWidget(name_label, i, 0)
            
            # 数值
            value_label = QLabel("--")
            value_label.setObjectName(f"paramValue_{key}")
            value_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
            value_label.setStyleSheet(f"color: {color};")
            params_layout.addWidget(value_label, i, 1)
            
            # 单位
            if unit:
                unit_label = QLabel(unit)
                unit_label.setStyleSheet("color: #999;")
                params_layout.addWidget(unit_label, i, 2)
            
            self.param_labels[key] = value_label
        
        main_layout.addWidget(params_group)
        
        # 锅炉列表
        list_group = QGroupBox("📋 锅炉列表")
        list_layout = QVBoxLayout(list_group)
        
        self.boiler_table = QTableWidget()
        self.boiler_table.setColumnCount(6)
        self.boiler_table.setHorizontalHeaderLabels([
            "ID", "名称", "型号", "状态", "位置", "操作"
        ])
        self.boiler_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.boiler_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        list_layout.addWidget(self.boiler_table)
        
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
        
        QPushButton#actionButtonWarning {
            background-color: #F44336;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        
        QPushButton#actionButtonInfo {
            background-color: #2196F3;
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
            # 更新锅炉列表
            self._update_boiler_table()
            
            # 更新锅炉选择框
            self._update_boiler_combo()
            
            # 如果已选择锅炉，更新参数
            current_index = self.boiler_combo.currentIndex()
            if current_index >= 0:
                boiler_id = self.boiler_combo.currentData()
                self._update_sensor_data(boiler_id)
                
        except Exception as e:
            self.logger.error(f"刷新锅炉数据失败：{e}")
    
    def _update_boiler_table(self):
        """更新锅炉表格"""
        boilers = self.db_manager.get_all_boilers()
        
        self.boiler_table.setRowCount(len(boilers))
        
        for row, boiler in enumerate(boilers):
            self.boiler_table.setItem(row, 0, QTableWidgetItem(str(boiler.get('id', ''))))
            self.boiler_table.setItem(row, 1, QTableWidgetItem(boiler.get('name', '')))
            self.boiler_table.setItem(row, 2, QTableWidgetItem(boiler.get('model', '')))
            
            status = boiler.get('status', 'offline')
            status_item = QTableWidgetItem(status)
            if status == 'running':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == 'maintenance':
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.boiler_table.setItem(row, 3, status_item)
            
            self.boiler_table.setItem(row, 4, QTableWidgetItem(boiler.get('location', '')))
            
            # 操作按钮
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.setContentsMargins(5, 2, 5, 2)
            
            view_btn = QPushButton("👁️")
            view_btn.setFixedWidth(40)
            view_btn.clicked.connect(lambda checked, b=boiler: self._view_boiler(b))
            btn_layout.addWidget(view_btn)
            
            self.boiler_table.setCellWidget(row, 5, btn_frame)
    
    def _update_boiler_combo(self):
        """更新锅炉选择框"""
        current_data = self.boiler_combo.currentData()
        
        self.boiler_combo.clear()
        boilers = self.db_manager.get_all_boilers()
        
        for boiler in boilers:
            self.boiler_combo.addItem(boiler.get('name', ''), boiler.get('id'))
        
        if current_data:
            index = self.boiler_combo.findData(current_data)
            if index >= 0:
                self.boiler_combo.setCurrentIndex(index)
    
    def _update_sensor_data(self, boiler_id: int):
        """更新传感器数据"""
        sensor_data = self.db_manager.get_latest_sensor_data(boiler_id)
        
        if sensor_data:
            for key in self.param_labels:
                value = sensor_data.get(key)
                if value is not None:
                    self.param_labels[key].setText(f"{value:.2f}")
                else:
                    self.param_labels[key].setText("--")
        else:
            for label in self.param_labels.values():
                label.setText("--")
    
    def _on_boiler_selected(self, index: int):
        """锅炉选择变化处理"""
        if index >= 0:
            boiler_id = self.boiler_combo.currentData()
            self._update_sensor_data(boiler_id)
    
    def _start_boiler(self):
        """启动锅炉"""
        boiler_id = self.boiler_combo.currentData()
        if boiler_id:
            reply = QMessageBox.question(
                self, "确认启动",
                f"确定要启动锅炉吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.update_boiler_status(boiler_id, 'running')
                self.logger.info(f"启动锅炉：{boiler_id}")
                self.refresh_data()
    
    def _stop_boiler(self):
        """停止锅炉"""
        boiler_id = self.boiler_combo.currentData()
        if boiler_id:
            reply = QMessageBox.warning(
                self, "确认停止",
                f"确定要停止锅炉吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.update_boiler_status(boiler_id, 'offline')
                self.logger.info(f"停止锅炉：{boiler_id}")
                self.refresh_data()
    
    def _set_maintenance(self):
        """设置维护模式"""
        boiler_id = self.boiler_combo.currentData()
        if boiler_id:
            reply = QMessageBox.question(
                self, "确认维护模式",
                f"确定要将锅炉设置为维护模式吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.update_boiler_status(boiler_id, 'maintenance')
                self.logger.info(f"锅炉进入维护模式：{boiler_id}")
                self.refresh_data()
    
    def _view_boiler(self, boiler: Dict):
        """查看锅炉详情"""
        QMessageBox.information(
            self, "锅炉详情",
            f"名称：{boiler.get('name', '')}\n"
            f"型号：{boiler.get('model', '')}\n"
            f"状态：{boiler.get('status', '')}\n"
            f"位置：{boiler.get('location', '')}"
        )
