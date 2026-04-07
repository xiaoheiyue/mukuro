"""
日志管理模块
Logging Management Module
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional


class LoggerManager:
    """日志管理器"""
    
    _instance: Optional['LoggerManager'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if self._logger is not None:
            return
        
        self.log_dir = Path(__file__).parent.parent / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志目录（按日期分类）
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.daily_log_dir = self.log_dir / self.today
        self.daily_log_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_logger(
        self,
        name: str = "BoilerCleaningSystem",
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_size_mb: int = 10,
        backup_count: int = 5,
        console_output: bool = True
    ) -> logging.Logger:
        """
        设置日志记录器
        :param name: 日志记录器名称
        :param level: 日志级别
        :param log_file: 日志文件名
        :param max_size_mb: 单个日志文件最大大小（MB）
        :param backup_count: 保留的备份文件数量
        :param console_output: 是否输出到控制台
        :return: 日志记录器
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper()))
        
        # 清除现有的处理器
        self._logger.handlers.clear()
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.log_dir / "daily").mkdir(parents=True, exist_ok=True)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器 - 按大小轮转
        if log_file is None:
            log_file = f"system_{datetime.now().strftime('%Y%m%d')}.log"
        
        log_path = self.daily_log_dir / log_file
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper()))
        self._logger.addHandler(file_handler)
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, level.upper()))
            self._logger.addHandler(console_handler)
        
        # 错误日志专用处理器
        error_log_path = self.daily_log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        self._logger.addHandler(error_handler)
        
        # 警告日志专用处理器
        warning_log_path = self.daily_log_dir / f"warning_{datetime.now().strftime('%Y%m%d')}.log"
        warning_handler = RotatingFileHandler(
            warning_log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        warning_handler.setFormatter(formatter)
        warning_handler.setLevel(logging.WARNING)
        self._logger.addHandler(warning_handler)
        
        self._logger.info(f"日志系统初始化完成，日志文件：{log_path}")
        
        return self._logger
    
    def get_logger(self) -> logging.Logger:
        """获取日志记录器"""
        if self._logger is None:
            return self.setup_logger()
        return self._logger
    
    def set_level(self, level: str):
        """设置日志级别"""
        if self._logger:
            self._logger.setLevel(getattr(logging, level.upper()))
    
    def add_file_handler(
        self,
        filename: str,
        level: str = "INFO",
        max_size_mb: int = 10,
        backup_count: int = 5
    ):
        """添加文件处理器"""
        if self._logger is None:
            return
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        log_path = self.daily_log_dir / filename
        handler = RotatingFileHandler(
            log_path,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, level.upper()))
        self._logger.addHandler(handler)


# 全局日志函数
def setup_logger(level: str = "INFO") -> logging.Logger:
    """设置并返回日志记录器"""
    manager = LoggerManager()
    return manager.setup_logger(level=level)


def get_logger() -> logging.Logger:
    """获取全局日志记录器"""
    manager = LoggerManager()
    return manager.get_logger()


# 装饰器：记录函数执行日志
def log_execution(logger: Optional[logging.Logger] = None):
    """
    记录函数执行的装饰器
    :param logger: 日志记录器，如果为 None 则使用全局日志
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            log.debug(f"开始执行函数：{func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                log.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                log.error(f"函数 {func.__name__} 执行失败：{str(e)}", exc_info=True)
                raise
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
