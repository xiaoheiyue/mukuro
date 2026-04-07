"""
系统设置页面 - Settings Page
配置系统参数
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGroupBox, QFormLayout, QComboBox,
    QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QMessageBox, QTabWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import logging

from config.settings import Settings
from core.database import DatabaseManager


class SettingsPage(QWidget):
    """系统设置页面类"""
    
    def __init__(self, settings: Settings, db_manager: DatabaseManager, 
                 logger: logging.Logger, parent=None):
        super().__init__(parent)
        
        self.settings = settings
        self.db_manager = db_manager
        self.logger = logger
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("⚙️ 系统设置")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 选项卡
        self.tabs = QTabWidget()
        
        # 常规设置
        general_tab = self._create_general_tab()
        self.tabs.addTab(general_tab, "📌 常规设置")
        
        # 传感器设置
        sensor_tab = self._create_sensor_tab()
        self.tabs.addTab(sensor_tab, "📡 传感器设置")
        
        # 清洗设置
        cleaning_tab = self._create_cleaning_tab()
        self.tabs.addTab(cleaning_tab, "🧹 清洗设置")
        
        # 报警设置
        alarm_tab = self._create_alarm_tab()
        self.tabs.addTab(alarm_tab, "🚨 报警设置")
        
        # 安全设置
        safety_tab = self._create_safety_tab()
        self.tabs.addTab(safety_tab, "🛡️ 安全设置")
        
        main_layout.addWidget(self.tabs)
        
        # 底部按钮
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 保存设置")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        reset_btn = QPushButton("🔄 重置默认")
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)
        
        main_layout.addWidget(button_frame)
        
        self._apply_styles()
        self._load_settings()
    
    def _create_general_tab(self) -> QWidget:
        """创建常规设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        
        # 数据库路径
        self.db_path_edit = QLineEdit()
        form.addRow("数据库路径:", self.db_path_edit)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        form.addRow("日志级别:", self.log_level_combo)
        
        # 日志文件
        self.log_file_edit = QLineEdit()
        form.addRow("日志文件:", self.log_file_edit)
        
        # 界面语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        form.addRow("界面语言:", self.language_combo)
        
        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        form.addRow("界面主题:", self.theme_combo)
        
        # 刷新率
        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(100, 10000)
        self.refresh_rate_spin.setSuffix(" ms")
        form.addRow("数据刷新率:", self.refresh_rate_spin)
        
        content.setLayout(form)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_sensor_tab(self) -> QWidget:
        """创建传感器设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        
        # 更新间隔
        self.sensor_update_spin = QSpinBox()
        self.sensor_update_spin.setRange(100, 10000)
        self.sensor_update_spin.setSuffix(" ms")
        form.addRow("更新间隔:", self.sensor_update_spin)
        
        # 压力报警阈值
        self.pressure_alarm_spin = QDoubleSpinBox()
        self.pressure_alarm_spin.setRange(0, 10)
        self.pressure_alarm_spin.setSuffix(" MPa")
        form.addRow("压力报警阈值:", self.pressure_alarm_spin)
        
        # 温度报警阈值
        self.temp_alarm_spin = QDoubleSpinBox()
        self.temp_alarm_spin.setRange(0, 500)
        self.temp_alarm_spin.setSuffix(" °C")
        form.addRow("温度报警阈值:", self.temp_alarm_spin)
        
        # 水位报警阈值
        self.water_level_alarm_spin = QDoubleSpinBox()
        self.water_level_alarm_spin.setRange(0, 100)
        self.water_level_alarm_spin.setSuffix(" %")
        form.addRow("水位报警阈值:", self.water_level_alarm_spin)
        
        # 压力警告阈值
        self.pressure_warn_spin = QDoubleSpinBox()
        self.pressure_warn_spin.setRange(0, 10)
        self.pressure_warn_spin.setSuffix(" MPa")
        form.addRow("压力警告阈值:", self.pressure_warn_spin)
        
        # 温度警告阈值
        self.temp_warn_spin = QDoubleSpinBox()
        self.temp_warn_spin.setRange(0, 500)
        self.temp_warn_spin.setSuffix(" °C")
        form.addRow("温度警告阈值:", self.temp_warn_spin)
        
        content.setLayout(form)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_cleaning_tab(self) -> QWidget:
        """创建清洗设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        
        # 默认周期
        self.cleaning_cycle_spin = QSpinBox()
        self.cleaning_cycle_spin.setRange(1, 168)
        self.cleaning_cycle_spin.setSuffix(" 小时")
        form.addRow("默认清洗周期:", self.cleaning_cycle_spin)
        
        # 最小清洗时间
        self.min_cleaning_spin = QSpinBox()
        self.min_cleaning_spin.setRange(1, 300)
        self.min_cleaning_spin.setSuffix(" 分钟")
        form.addRow("最小清洗时间:", self.min_cleaning_spin)
        
        # 最大清洗时间
        self.max_cleaning_spin = QSpinBox()
        self.max_cleaning_spin.setRange(1, 500)
        self.max_cleaning_spin.setSuffix(" 分钟")
        form.addRow("最大清洗时间:", self.max_cleaning_spin)
        
        # 化学品投加速率
        self.chemical_rate_spin = QDoubleSpinBox()
        self.chemical_rate_spin.setRange(0, 10)
        self.chemical_rate_spin.setSuffix(" L/min")
        form.addRow("化学品投加速率:", self.chemical_rate_spin)
        
        # 冲洗时间
        self.rinse_time_spin = QSpinBox()
        self.rinse_time_spin.setRange(1, 120)
        self.rinse_time_spin.setSuffix(" 分钟")
        form.addRow("冲洗时间:", self.rinse_time_spin)
        
        # 干燥时间
        self.dry_time_spin = QSpinBox()
        self.dry_time_spin.setRange(1, 120)
        self.dry_time_spin.setSuffix(" 分钟")
        form.addRow("干燥时间:", self.dry_time_spin)
        
        content.setLayout(form)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_alarm_tab(self) -> QWidget:
        """创建报警设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form = QFormLayout()
        
        # 声音报警
        self.sound_alarm_check = QCheckBox("启用声音报警")
        form.addRow("", self.sound_alarm_check)
        
        # 视觉报警
        self.visual_alarm_check = QCheckBox("启用视觉报警")
        form.addRow("", self.visual_alarm_check)
        
        # 邮件通知
        self.email_alarm_check = QCheckBox("启用邮件通知")
        form.addRow("", self.email_alarm_check)
        
        # 短信通知
        self.sms_alarm_check = QCheckBox("启用短信通知")
        form.addRow("", self.sms_alarm_check)
        
        # 自动确认时间
        self.auto_ack_spin = QSpinBox()
        self.auto_ack_spin.setRange(0, 120)
        self.auto_ack_spin.setSuffix(" 分钟")
        form.addRow("自动确认时间:", self.auto_ack_spin)
        
        # 升级时间
        self.escalation_spin = QSpinBox()
        self.escalation_spin.setRange(1, 120)
        self.escalation_spin.setSuffix(" 分钟")
        form.addRow("报警升级时间:", self.escalation_spin)
        
        layout.addLayout(form)
        layout.addStretch()
        
        return widget
    
    def _create_safety_tab(self) -> QWidget:
        """创建安全设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form = QFormLayout()
        
        # 紧急停止
        self.emergency_stop_check = QCheckBox("启用紧急停止功能")
        form.addRow("", self.emergency_stop_check)
        
        # 自动停机
        self.auto_shutdown_check = QCheckBox("严重报警时自动停机")
        form.addRow("", self.auto_shutdown_check)
        
        # 操作员确认
        self.operator_confirm_check = QCheckBox("需要操作员确认")
        form.addRow("", self.operator_confirm_check)
        
        # 安全联锁
        self.safety_interlock_check = QCheckBox("启用安全联锁")
        form.addRow("", self.safety_interlock_check)
        
        # 最大工作压力
        self.max_pressure_spin = QDoubleSpinBox()
        self.max_pressure_spin.setRange(0, 10)
        self.max_pressure_spin.setSuffix(" MPa")
        form.addRow("最大工作压力:", self.max_pressure_spin)
        
        # 最大工作温度
        self.max_temp_spin = QDoubleSpinBox()
        self.max_temp_spin.setRange(0, 500)
        self.max_temp_spin.setSuffix(" °C")
        form.addRow("最大工作温度:", self.max_temp_spin)
        
        # 最低水位
        self.min_water_spin = QDoubleSpinBox()
        self.min_water_spin.setRange(0, 100)
        self.min_water_spin.setSuffix(" %")
        form.addRow("最低水位:", self.min_water_spin)
        
        layout.addLayout(form)
        layout.addStretch()
        
        return widget
    
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
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def _load_settings(self):
        """加载设置"""
        try:
            # 常规设置
            self.db_path_edit.setText(self.settings.database.path)
            self.log_level_combo.setCurrentText(self.settings.logging.level)
            self.log_file_edit.setText(self.settings.logging.file)
            self.language_combo.setCurrentText(self.settings.ui.language)
            self.theme_combo.setCurrentText(self.settings.ui.theme)
            self.refresh_rate_spin.setValue(self.settings.ui.refresh_rate_ms)
            
            # 传感器设置
            self.sensor_update_spin.setValue(self.settings.sensor.update_interval_ms)
            self.pressure_alarm_spin.setValue(self.settings.sensor.alarm_threshold_pressure)
            self.temp_alarm_spin.setValue(self.settings.sensor.alarm_threshold_temperature)
            self.water_level_alarm_spin.setValue(self.settings.sensor.alarm_threshold_water_level)
            self.pressure_warn_spin.setValue(self.settings.sensor.warning_threshold_pressure)
            self.temp_warn_spin.setValue(self.settings.sensor.warning_threshold_temperature)
            
            # 清洗设置
            self.cleaning_cycle_spin.setValue(self.settings.cleaning.default_cycle_hours)
            self.min_cleaning_spin.setValue(self.settings.cleaning.min_cleaning_duration_minutes)
            self.max_cleaning_spin.setValue(self.settings.cleaning.max_cleaning_duration_minutes)
            self.chemical_rate_spin.setValue(self.settings.cleaning.chemical_dosing_rate)
            self.rinse_time_spin.setValue(self.settings.cleaning.rinse_duration_minutes)
            self.dry_time_spin.setValue(self.settings.cleaning.drying_duration_minutes)
            
            # 报警设置
            self.sound_alarm_check.setChecked(self.settings.alarm.sound_enabled)
            self.visual_alarm_check.setChecked(self.settings.alarm.visual_enabled)
            self.email_alarm_check.setChecked(self.settings.alarm.email_enabled)
            self.sms_alarm_check.setChecked(self.settings.alarm.sms_enabled)
            self.auto_ack_spin.setValue(self.settings.alarm.auto_acknowledge_minutes)
            self.escalation_spin.setValue(self.settings.alarm.escalation_minutes)
            
            # 安全设置
            self.emergency_stop_check.setChecked(self.settings.safety.emergency_stop_enabled)
            self.auto_shutdown_check.setChecked(self.settings.safety.auto_shutdown_on_critical)
            self.operator_confirm_check.setChecked(self.settings.safety.operator_confirmation_required)
            self.safety_interlock_check.setChecked(self.settings.safety.safety_interlock_enabled)
            self.max_pressure_spin.setValue(self.settings.safety.max_operating_pressure)
            self.max_temp_spin.setValue(self.settings.safety.max_operating_temperature)
            self.min_water_spin.setValue(self.settings.safety.min_water_level)
            
        except Exception as e:
            self.logger.error(f"加载设置失败：{e}")
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 常规设置
            self.settings.database.path = self.db_path_edit.text()
            self.settings.logging.level = self.log_level_combo.currentText()
            self.settings.logging.file = self.log_file_edit.text()
            self.settings.ui.language = self.language_combo.currentText()
            self.settings.ui.theme = self.theme_combo.currentText()
            self.settings.ui.refresh_rate_ms = self.refresh_rate_spin.value()
            
            # 传感器设置
            self.settings.sensor.update_interval_ms = self.sensor_update_spin.value()
            self.settings.sensor.alarm_threshold_pressure = self.pressure_alarm_spin.value()
            self.settings.sensor.alarm_threshold_temperature = self.temp_alarm_spin.value()
            self.settings.sensor.alarm_threshold_water_level = self.water_level_alarm_spin.value()
            self.settings.sensor.warning_threshold_pressure = self.pressure_warn_spin.value()
            self.settings.sensor.warning_threshold_temperature = self.temp_warn_spin.value()
            
            # 清洗设置
            self.settings.cleaning.default_cycle_hours = self.cleaning_cycle_spin.value()
            self.settings.cleaning.min_cleaning_duration_minutes = self.min_cleaning_spin.value()
            self.settings.cleaning.max_cleaning_duration_minutes = self.max_cleaning_spin.value()
            self.settings.cleaning.chemical_dosing_rate = self.chemical_rate_spin.value()
            self.settings.cleaning.rinse_duration_minutes = self.rinse_time_spin.value()
            self.settings.cleaning.drying_duration_minutes = self.dry_time_spin.value()
            
            # 报警设置
            self.settings.alarm.sound_enabled = self.sound_alarm_check.isChecked()
            self.settings.alarm.visual_enabled = self.visual_alarm_check.isChecked()
            self.settings.alarm.email_enabled = self.email_alarm_check.isChecked()
            self.settings.alarm.sms_enabled = self.sms_alarm_check.isChecked()
            self.settings.alarm.auto_acknowledge_minutes = self.auto_ack_spin.value()
            self.settings.alarm.escalation_minutes = self.escalation_spin.value()
            
            # 安全设置
            self.settings.safety.emergency_stop_enabled = self.emergency_stop_check.isChecked()
            self.settings.safety.auto_shutdown_on_critical = self.auto_shutdown_check.isChecked()
            self.settings.safety.operator_confirmation_required = self.operator_confirm_check.isChecked()
            self.settings.safety.safety_interlock_enabled = self.safety_interlock_check.isChecked()
            self.settings.safety.max_operating_pressure = self.max_pressure_spin.value()
            self.settings.safety.max_operating_temperature = self.max_temp_spin.value()
            self.settings.safety.min_water_level = self.min_water_spin.value()
            
            # 验证设置
            is_valid, errors = self.settings.validate()
            if not is_valid:
                error_msg = "\n".join(errors)
                QMessageBox.warning(self, "验证失败", f"设置验证失败:\n{error_msg}")
                return
            
            # 保存设置到文件
            self.settings.save()
            
            self.logger.info("设置已保存")
            QMessageBox.information(self, "成功", "设置已保存！\n部分设置可能需要重启后生效。")
            
        except Exception as e:
            self.logger.error(f"保存设置失败：{e}")
            QMessageBox.critical(self, "错误", f"保存设置失败：{str(e)}")
    
    def _reset_settings(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要将所有设置重置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.reset_to_defaults()
            self._load_settings()
            self.logger.info("设置已重置为默认值")
            QMessageBox.information(self, "成功", "设置已重置为默认值！")
