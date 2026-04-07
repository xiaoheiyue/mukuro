"""
日志模块 - Logging Module
负责系统日志的记录和管理
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """自定义日志格式器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    max_size_mb: int = 100,
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        console_output: 是否输出到控制台
        max_size_mb: 单个日志文件最大大小 (MB)
        backup_count: 保留的备份文件数量
        
    Returns:
        配置好的 logger 实例
    """
    # 创建 logger
    logger = logging.getLogger("BoilerSystem")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有的 handlers
    logger.handlers.clear()
    
    # 创建格式器
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加控制台 handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # 添加文件 handler
    if log_file:
        # 确保目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用轮转文件 handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # 添加定时轮转 handler (每天)
        timed_handler = TimedRotatingFileHandler(
            log_file + ".daily",
            when='D',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8'
        )
        timed_handler.setLevel(logging.INFO)
        timed_handler.setFormatter(detailed_formatter)
        logger.addHandler(timed_handler)
    
    return logger


class LoggerManager:
    """
    日志管理器类
    管理多个日志记录器和日志相关操作
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._loggers = {}
    
    def get_logger(
        self,
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """
        获取或创建日志记录器
        
        Args:
            name: logger 名称
            level: 日志级别
            log_file: 日志文件路径
            
        Returns:
            logger 实例
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = setup_logger(level, log_file)
        logger.name = name
        self._loggers[name] = logger
        
        return logger
    
    def set_level(self, name: str, level: str):
        """
        设置 logger 级别
        
        Args:
            name: logger 名称
            level: 日志级别
        """
        if name in self._loggers:
            self._loggers[name].setLevel(getattr(logging, level.upper(), logging.INFO))
    
    def close_all(self):
        """关闭所有 logger 的 handlers"""
        for logger in self._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        self._loggers.clear()
    
    @staticmethod
    def get_log_files(log_dir: str) -> list:
        """
        获取日志目录下的所有日志文件
        
        Args:
            log_dir: 日志目录路径
            
        Returns:
            日志文件列表
        """
        if not os.path.exists(log_dir):
            return []
        
        log_files = []
        for file in os.listdir(log_dir):
            if file.endswith('.log') or file.endswith('.log.daily'):
                log_files.append(os.path.join(log_dir, file))
        
        return sorted(log_files, key=os.path.getmtime, reverse=True)
    
    @staticmethod
    def clear_old_logs(log_dir: str, days: int = 30):
        """
        清理指定天数之前的日志文件
        
        Args:
            log_dir: 日志目录路径
            days: 保留的天数
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if not os.path.exists(log_dir):
            return
        
        for file in os.listdir(log_dir):
            if file.endswith('.log') or file.endswith('.log.daily'):
                file_path = os.path.join(log_dir, file)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除日志文件失败：{file_path}, 错误：{e}")
    
    @staticmethod
    def export_logs(
        log_dir: str,
        output_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        levels: Optional[list] = None
    ):
        """
        导出日志到文件
        
        Args:
            log_dir: 日志目录路径
            output_file: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
            levels: 要导出的日志级别列表
        """
        log_files = LoggerManager.get_log_files(log_dir)
        
        all_logs = []
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        all_logs.append(line)
            except Exception:
                continue
        
        # 过滤日志
        filtered_logs = []
        for log_line in all_logs:
            # 检查日期范围
            include = True
            
            if start_date or end_date:
                try:
                    # 尝试从日志行中提取日期
                    date_str = log_line.split(' - ')[0]
                    log_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    
                    if start_date and log_date < start_date:
                        include = False
                    if end_date and log_date > end_date:
                        include = False
                except (ValueError, IndexError):
                    pass
            
            # 检查日志级别
            if levels and include:
                level_match = False
                for level in levels:
                    if level.upper() in log_line:
                        level_match = True
                        break
                if not level_match:
                    include = False
            
            if include:
                filtered_logs.append(log_line)
        
        # 写入输出文件
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(filtered_logs)
        
        return len(filtered_logs)


class AuditLogger:
    """
    审计日志记录器
    专门用于记录用户操作和系统安全相关事件
    """
    
    def __init__(self, logger: logging.Logger):
        """
        初始化审计日志记录器
        
        Args:
            logger: 基础 logger 实例
        """
        self.logger = logger
        self.audit_logger = logging.getLogger("AuditLogger")
        
        # 审计日志总是使用详细格式
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 确保审计日志有独立的 handler
        if not self.audit_logger.handlers:
            audit_handler = logging.FileHandler(
                'logs/audit.log',
                encoding='utf-8'
            )
            audit_handler.setFormatter(formatter)
            self.audit_logger.addHandler(audit_handler)
            self.audit_logger.setLevel(logging.INFO)
    
    def log_login(self, username: str, success: bool, ip_address: str = ""):
        """记录登录事件"""
        status = "成功" if success else "失败"
        message = f"用户登录 | 用户名：{username} | 状态：{status} | IP: {ip_address}"
        self.audit_logger.info(message)
    
    def log_logout(self, username: str):
        """记录登出事件"""
        message = f"用户登出 | 用户名：{username}"
        self.audit_logger.info(message)
    
    def log_permission_change(self, operator: str, target_user: str, new_permission: str):
        """记录权限变更事件"""
        message = f"权限变更 | 操作员：{operator} | 目标用户：{target_user} | 新权限：{new_permission}"
        self.audit_logger.warning(message)
    
    def log_config_change(self, operator: str, config_item: str, old_value: str, new_value: str):
        """记录配置变更事件"""
        message = f"配置变更 | 操作员：{operator} | 配置项：{config_item} | 原值：{old_value} | 新值：{new_value}"
        self.audit_logger.warning(message)
    
    def log_operation(self, operator: str, operation: str, details: str = ""):
        """记录操作事件"""
        message = f"操作记录 | 操作员：{operator} | 操作：{operation} | 详情：{details}"
        self.audit_logger.info(message)
    
    def log_alarm_acknowledge(self, operator: str, alarm_id: int, alarm_type: str):
        """记录报警确认事件"""
        message = f"报警确认 | 操作员：{operator} | 报警 ID: {alarm_id} | 类型：{alarm_type}"
        self.audit_logger.info(message)
    
    def log_emergency_stop(self, operator: str, reason: str):
        """记录紧急停止事件"""
        message = f"紧急停止 | 操作员：{operator} | 原因：{reason}"
        self.audit_logger.critical(message)
    
    def log_data_export(self, operator: str, data_type: str, file_path: str):
        """记录数据导出事件"""
        message = f"数据导出 | 操作员：{operator} | 数据类型：{data_type} | 文件：{file_path}"
        self.audit_logger.info(message)
