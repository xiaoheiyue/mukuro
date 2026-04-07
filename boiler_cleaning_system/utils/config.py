"""
配置管理模块
Configuration Management Module
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """系统配置类"""
    
    def __init__(self, config_file: str = "config.json"):
        """初始化配置"""
        self.config_file = config_file
        self.config_dir = Path(__file__).parent.parent / "data"
        self.config_path = self.config_dir / self.config_file
        
        # 默认配置
        self.defaults = {
            # 数据库配置
            "database": {
                "path": "boiler_cleaning.db",
                "backup_enabled": True,
                "backup_interval_hours": 24
            },
            
            # 串口通信配置
            "serial": {
                "port": "COM1",
                "baudrate": 9600,
                "timeout": 1.0,
                "enabled": False
            },
            
            # PLC 通信配置
            "plc": {
                "ip_address": "192.168.1.100",
                "port": 502,
                "station_id": 1,
                "enabled": True
            },
            
            # 锅炉参数配置
            "boiler": {
                "max_temperature": 200.0,
                "min_temperature": 20.0,
                "max_pressure": 1.6,
                "min_pressure": 0.1,
                "max_water_level": 100.0,
                "min_water_level": 20.0,
                "optimal_ph_min": 7.0,
                "optimal_ph_max": 9.0,
                "optimal_tds_max": 3000.0,
                "volume_m3": 10.0
            },
            
            # 除污剂配置
            "cleaning_agent": {
                "tank_capacity_liters": 500.0,
                "dosing_rate_ml_per_m3": 50.0,
                "concentration_percent": 30.0,
                "auto_dosing_enabled": True,
                "min_level_alert": 50.0
            },
            
            # 排污阀配置
            "blowdown_valve": {
                "open_duration_seconds": 30,
                "close_duration_seconds": 300,
                "auto_mode_enabled": True,
                "tds_threshold": 3500.0
            },
            
            # 报警配置
            "alarm": {
                "sound_enabled": True,
                "popup_enabled": True,
                "email_enabled": False,
                "email_recipients": [],
                "sms_enabled": False
            },
            
            # 数据采集配置
            "data_acquisition": {
                "sampling_interval_seconds": 5,
                "logging_interval_seconds": 60,
                "retention_days": 365
            },
            
            # 界面配置
            "ui": {
                "theme": "light",
                "language": "zh_CN",
                "refresh_interval_ms": 1000,
                "chart_update_interval_ms": 5000
            },
            
            # 日志配置
            "logging": {
                "level": "INFO",
                "file": "system.log",
                "max_size_mb": 10,
                "backup_count": 5
            },
            
            # 用户配置
            "user": {
                "session_timeout_minutes": 30,
                "password_min_length": 6,
                "max_login_attempts": 5
            }
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果配置文件不存在，创建默认配置
        if not self.config_path.exists():
            self.save_config(self.defaults)
            return self.defaults.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # 合并配置，确保所有默认值都存在
            config = self._merge_configs(self.defaults, loaded_config)
            return config
        except Exception as e:
            print(f"加载配置文件失败：{e}，使用默认配置")
            return self.defaults.copy()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """递归合并配置字典"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_configs(result[key], value)
                else:
                    result[key] = value
        return result
    
    def save_config(self, config: Optional[Dict] = None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败：{e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        :param key_path: 点分隔的键路径，如 "database.path"
        :param default: 默认值
        :return: 配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值
        :param key_path: 点分隔的键路径
        :param value: 要设置的值
        """
        keys = key_path.split('.')
        config = self.config
        
        try:
            for key in keys[:-1]:
                config = config[key]
            config[keys[-1]] = value
        except KeyError:
            print(f"配置键路径无效：{key_path}")
    
    def save(self):
        """保存当前配置"""
        self.save_config(self.config)
    
    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self.get("logging.level", "INFO")
    
    @property
    def db_path(self) -> str:
        """获取数据库路径"""
        db_path = self.get("database.path", "boiler_cleaning.db")
        return str(self.config_dir / db_path)
    
    @property
    def sampling_interval(self) -> int:
        """获取采样间隔（秒）"""
        return self.get("data_acquisition.sampling_interval_seconds", 5)
    
    @property
    def refresh_interval(self) -> int:
        """获取界面刷新间隔（毫秒）"""
        return self.get("ui.refresh_interval_ms", 1000)
