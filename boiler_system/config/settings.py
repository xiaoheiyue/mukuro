"""
配置管理模块 - Configuration Management Module
负责系统配置的加载、保存和管理
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "data/boiler_system.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_connections: int = 10


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/boiler_system.log"
    max_size_mb: int = 100
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class SensorConfig:
    """传感器配置"""
    update_interval_ms: int = 1000
    alarm_threshold_pressure: float = 2.5  # MPa
    alarm_threshold_temperature: float = 200.0  # °C
    alarm_threshold_water_level: float = 10.0  # %
    warning_threshold_pressure: float = 2.0  # MPa
    warning_threshold_temperature: float = 180.0  # °C
    sensor_timeout_seconds: int = 30


@dataclass
class CleaningConfig:
    """清洗配置"""
    default_cycle_hours: int = 8
    min_cleaning_duration_minutes: int = 30
    max_cleaning_duration_minutes: int = 120
    chemical_dosing_rate: float = 0.5  # L/min
    rinse_duration_minutes: int = 15
    drying_duration_minutes: int = 10


@dataclass
class AlarmConfig:
    """报警配置"""
    sound_enabled: bool = True
    visual_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    auto_acknowledge_minutes: int = 0
    escalation_minutes: int = 15


@dataclass
class UserInterfaceConfig:
    """用户界面配置"""
    language: str = "zh_CN"
    theme: str = "light"
    refresh_rate_ms: int = 500
    chart_update_interval_ms: int = 2000
    show_tooltips: bool = True
    font_size: int = 10


@dataclass
class SafetyConfig:
    """安全配置"""
    emergency_stop_enabled: bool = True
    auto_shutdown_on_critical: bool = True
    operator_confirmation_required: bool = True
    safety_interlock_enabled: bool = True
    max_operating_pressure: float = 2.5  # MPa
    max_operating_temperature: float = 200.0  # °C
    min_water_level: float = 15.0  # %


@dataclass
class ReportConfig:
    """报告配置"""
    auto_generate: bool = True
    generation_time: str = "00:00"
    format: str = "PDF"
    include_charts: bool = True
    retention_days: int = 90
    export_path: str = "reports"


class Settings:
    """
    系统设置类 - System Settings Class
    管理所有系统配置项
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化设置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = config_file or "config/settings.json"
        
        # 初始化各模块配置
        self.database = DatabaseConfig()
        self.logging = LogConfig()
        self.sensor = SensorConfig()
        self.cleaning = CleaningConfig()
        self.alarm = AlarmConfig()
        self.ui = UserInterfaceConfig()
        self.safety = SafetyConfig()
        self.report = ReportConfig()
        
        # 快捷访问属性
        self.database_path = self.database.path
        self.log_level = self.logging.level
        self.log_file = self.logging.file
        
        # 确保目录存在
        self._ensure_directories()
        
        # 加载配置文件（如果存在）
        if os.path.exists(self.config_file):
            self.load()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            os.path.dirname(self.database.path),
            os.path.dirname(self.log_file),
            "data/backups",
            "logs",
            "reports",
            "exports"
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典
        
        Returns:
            配置字典
        """
        return {
            "database": asdict(self.database),
            "logging": asdict(self.logging),
            "sensor": asdict(self.sensor),
            "cleaning": asdict(self.cleaning),
            "alarm": asdict(self.alarm),
            "ui": asdict(self.ui),
            "safety": asdict(self.safety),
            "report": asdict(self.report)
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """
        从字典加载配置
        
        Args:
            data: 配置字典
        """
        if "database" in data:
            for key, value in data["database"].items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        if "logging" in data:
            for key, value in data["logging"].items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        
        if "sensor" in data:
            for key, value in data["sensor"].items():
                if hasattr(self.sensor, key):
                    setattr(self.sensor, key, value)
        
        if "cleaning" in data:
            for key, value in data["cleaning"].items():
                if hasattr(self.cleaning, key):
                    setattr(self.cleaning, key, value)
        
        if "alarm" in data:
            for key, value in data["alarm"].items():
                if hasattr(self.alarm, key):
                    setattr(self.alarm, key, value)
        
        if "ui" in data:
            for key, value in data["ui"].items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)
        
        if "safety" in data:
            for key, value in data["safety"].items():
                if hasattr(self.safety, key):
                    setattr(self.safety, key, value)
        
        if "report" in data:
            for key, value in data["report"].items():
                if hasattr(self.report, key):
                    setattr(self.report, key, value)
        
        # 更新快捷访问属性
        self.database_path = self.database.path
        self.log_level = self.logging.level
        self.log_file = self.logging.file
    
    def save(self, filepath: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            filepath: 文件路径，如果为None则使用默认路径
        """
        filepath = filepath or self.config_file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
    
    def load(self, filepath: Optional[str] = None):
        """
        从文件加载配置
        
        Args:
            filepath: 文件路径，如果为None则使用默认路径
        """
        filepath = filepath or self.config_file
        
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.from_dict(data)
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.database = DatabaseConfig()
        self.logging = LogConfig()
        self.sensor = SensorConfig()
        self.cleaning = CleaningConfig()
        self.alarm = AlarmConfig()
        self.ui = UserInterfaceConfig()
        self.safety = SafetyConfig()
        self.report = ReportConfig()
        
        self.database_path = self.database.path
        self.log_level = self.logging.level
        self.log_file = self.logging.file
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置的有效性
        
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        # 验证数据库配置
        if not self.database.path:
            errors.append("数据库路径不能为空")
        
        # 验证传感器配置
        if self.sensor.alarm_threshold_pressure <= 0:
            errors.append("压力报警阈值必须大于0")
        
        if self.sensor.alarm_threshold_temperature <= 0:
            errors.append("温度报警阈值必须大于0")
        
        if self.sensor.warning_threshold_pressure >= self.sensor.alarm_threshold_pressure:
            errors.append("压力警告阈值必须小于报警阈值")
        
        if self.sensor.warning_threshold_temperature >= self.sensor.alarm_threshold_temperature:
            errors.append("温度警告阈值必须小于报警阈值")
        
        # 验证清洗配置
        if self.cleaning.min_cleaning_duration_minutes <= 0:
            errors.append("最小清洗时间必须大于0")
        
        if self.cleaning.max_cleaning_duration_minutes <= self.cleaning.min_cleaning_duration_minutes:
            errors.append("最大清洗时间必须大于最小清洗时间")
        
        # 验证安全配置
        if self.safety.max_operating_pressure <= 0:
            errors.append("最大工作压力必须大于0")
        
        if self.safety.max_operating_temperature <= 0:
            errors.append("最大工作温度必须大于0")
        
        if self.safety.min_water_level < 0 or self.safety.min_water_level > 100:
            errors.append("最低水位必须在0-100之间")
        
        return len(errors) == 0, errors
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置的扁平化字典"""
        return self.to_dict()
    
    def update_setting(self, category: str, key: str, value: Any) -> bool:
        """
        更新单个设置项
        
        Args:
            category: 设置类别
            key: 设置键
            value: 设置值
            
        Returns:
            是否成功更新
        """
        category_map = {
            "database": self.database,
            "logging": self.logging,
            "sensor": self.sensor,
            "cleaning": self.cleaning,
            "alarm": self.alarm,
            "ui": self.ui,
            "safety": self.safety,
            "report": self.report
        }
        
        if category not in category_map:
            return False
        
        config_obj = category_map[category]
        
        if not hasattr(config_obj, key):
            return False
        
        # 类型转换
        current_value = getattr(config_obj, key)
        try:
            if isinstance(current_value, bool):
                value = bool(value)
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
            elif isinstance(current_value, str):
                value = str(value)
            
            setattr(config_obj, key, value)
            
            # 更新快捷访问属性
            if category == "database" and key == "path":
                self.database_path = value
            elif category == "logging":
                if key == "level":
                    self.log_level = value
                elif key == "file":
                    self.log_file = value
            
            return True
        except (ValueError, TypeError):
            return False
