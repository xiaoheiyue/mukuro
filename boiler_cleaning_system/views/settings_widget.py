"""系统设置模块"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QMessageBox, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SettingsWidget(QWidget):
    def __init__(self, db_manager, config, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.config = config
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("⚙️ 系统设置")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 锅炉参数设置
        boiler_group = QGroupBox("锅炉参数")
        boiler_form = QFormLayout()
        self.max_temp = QDoubleSpinBox()
        self.max_temp.setRange(0, 300)
        self.max_temp.setValue(200)
        boiler_form.addRow("最高温度 (°C):", self.max_temp)
        self.max_pressure = QDoubleSpinBox()
        self.max_pressure.setRange(0, 5)
        self.max_pressure.setValue(1.6)
        boiler_form.addRow("最高压力 (MPa):", self.max_pressure)
        self.min_water_level = QSpinBox()
        self.min_water_level.setRange(0, 100)
        self.min_water_level.setValue(20)
        boiler_form.addRow("最低水位 (%):", self.min_water_level)
        boiler_group.setLayout(boiler_form)
        layout.addWidget(boiler_group)
        
        # 投药设置
        dosing_group = QGroupBox("投药设置")
        dosing_form = QFormLayout()
        self.dosing_rate = QDoubleSpinBox()
        self.dosing_rate.setRange(0, 1000)
        self.dosing_rate.setValue(50)
        dosing_form.addRow("投药率 (ml/m³):", self.dosing_rate)
        self.auto_dosing = QCheckBox("启用自动投药")
        self.auto_dosing.setChecked(True)
        dosing_form.addRow("", self.auto_dosing)
        dosing_group.setLayout(dosing_form)
        layout.addWidget(dosing_group)
        
        # 排污设置
        blowdown_group = QGroupBox("排污设置")
        blowdown_form = QFormLayout()
        self.tds_threshold = QSpinBox()
        self.tds_threshold.setRange(0, 10000)
        self.tds_threshold.setValue(3500)
        blowdown_form.addRow("TDS 阈值 (ppm):", self.tds_threshold)
        self.auto_blowdown = QCheckBox("启用自动排污")
        self.auto_blowdown.setChecked(True)
        blowdown_form.addRow("", self.auto_blowdown)
        blowdown_group.setLayout(blowdown_form)
        layout.addWidget(blowdown_group)
        
        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        layout.addStretch()
    
    def save_settings(self):
        QMessageBox.information(self, "提示", "设置已保存")
    
    def refresh_data(self):
        pass
