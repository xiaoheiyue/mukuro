"""投药控制模块"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QPushButton, QProgressBar, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class DosingControlWidget(QWidget):
    def __init__(self, db_manager, config, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.config = config
        self.dosing_active = False
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("💊 投药控制")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        status_group = QGroupBox("投药状态")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("状态：停止")
        status_layout.addWidget(self.status_label)
        self.level_progress = QProgressBar()
        self.level_progress.setRange(0, 100)
        self.level_progress.setValue(0)
        status_layout.addWidget(self.level_progress)
        self.level_label = QLabel("液位：0%")
        status_layout.addWidget(self.level_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        control_group = QGroupBox("控制操作")
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("启动投药")
        self.start_btn.clicked.connect(self.start_dosing)
        control_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("停止投药")
        self.stop_btn.clicked.connect(self.stop_dosing)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        layout.addStretch()
    
    def start_dosing(self):
        if QMessageBox.question(self, "确认", "确定启动投药？") == 1:
            self.dosing_active = True
            self.status_label.setText("状态：运行中")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            QMessageBox.information(self, "提示", "投药已启动")
    
    def stop_dosing(self):
        self.dosing_active = False
        self.status_label.setText("状态：停止")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.information(self, "提示", "投药已停止")
    
    def refresh_data(self):
        pass
