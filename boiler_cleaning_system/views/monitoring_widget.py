"""实时监控模块"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class MonitoringWidget(QWidget):
    def __init__(self, db_manager, config, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.config = config
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("📈 实时监控")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        group = QGroupBox("实时数据")
        grid = QGridLayout()
        
        self.temp_label = QLabel("温度：0.0 °C")
        grid.addWidget(self.temp_label, 0, 0)
        self.pressure_label = QLabel("压力：0.00 MPa")
        grid.addWidget(self.pressure_label, 0, 1)
        self.water_label = QLabel("水位：0 %")
        grid.addWidget(self.water_label, 1, 0)
        self.ph_label = QLabel("pH: 0.0")
        grid.addWidget(self.ph_label, 1, 1)
        self.tds_label = QLabel("TDS: 0 ppm")
        grid.addWidget(self.tds_label, 2, 0)
        
        group.setLayout(grid)
        layout.addWidget(group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "温度", "压力", "水位", "pH"])
        layout.addWidget(self.table)
    
    def refresh_data(self):
        boilers = self.db_manager.get_all_boilers()
        if boilers:
            data = self.db_manager.get_latest_real_time_data(boilers[0]['id'])
            if data:
                self.temp_label.setText(f"温度：{data.get('temperature', 0):.1f} °C")
                self.pressure_label.setText(f"压力：{data.get('pressure', 0):.2f} MPa")
                self.water_label.setText(f"水位：{data.get('water_level', 0):.0f} %")
                self.ph_label.setText(f"pH: {data.get('ph_value', 0):.1f}")
                self.tds_label.setText(f"TDS: {data.get('tds_ppm', 0):.0f} ppm")
