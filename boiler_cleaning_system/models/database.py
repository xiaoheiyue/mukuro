"""
数据库管理模块
Database Management Module

负责系统所有数据的存储、查询和管理
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
import json


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "boiler_cleaning.db"):
        """
        初始化数据库管理器
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize(self) -> bool:
        """
        初始化数据库，创建所有必要的表
        :return: 是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        full_name TEXT,
                        department TEXT,
                        email TEXT,
                        phone TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP
                    )
                ''')
                
                # 创建锅炉设备表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS boilers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        model TEXT,
                        serial_number TEXT,
                        manufacturer TEXT,
                        install_date DATE,
                        capacity_m3 REAL,
                        max_pressure_mpa REAL,
                        max_temperature_c REAL,
                        status TEXT DEFAULT 'offline',
                        location TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建实时数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS real_time_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        boiler_id INTEGER NOT NULL,
                        temperature REAL,
                        pressure REAL,
                        water_level REAL,
                        ph_value REAL,
                        tds_ppm REAL,
                        conductivity_us REAL,
                        dissolved_oxygen_ppb REAL,
                        flow_rate_m3h REAL,
                        fuel_consumption REAL,
                        exhaust_temperature REAL,
                        cleaning_agent_level REAL,
                        blowdown_valve_status INTEGER,
                        dosing_pump_status INTEGER,
                        alarm_status INTEGER,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (boiler_id) REFERENCES boilers(id)
                    )
                ''')
                
                # 创建历史数据表（用于长期存储）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS historical_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        boiler_id INTEGER NOT NULL,
                        temperature REAL,
                        pressure REAL,
                        water_level REAL,
                        ph_value REAL,
                        tds_ppm REAL,
                        conductivity_us REAL,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (boiler_id) REFERENCES boilers(id)
                    )
                ''')
                
                # 创建除污剂投放记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dosing_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        boiler_id INTEGER NOT NULL,
                        agent_type TEXT,
                        dosage_ml REAL,
                        concentration_percent REAL,
                        method TEXT,
                        operator_id INTEGER,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                        FOREIGN KEY (operator_id) REFERENCES users(id)
                    )
                ''')
                
                # 创建排污记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blowdown_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        boiler_id INTEGER NOT NULL,
                        valve_id INTEGER,
                        open_time TIMESTAMP,
                        close_time TIMESTAMP,
                        duration_seconds INTEGER,
                        reason TEXT,
                        tds_before REAL,
                        tds_after REAL,
                        water_loss_m3 REAL,
                        operator_id INTEGER,
                        mode TEXT,
                        status TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                        FOREIGN KEY (operator_id) REFERENCES users(id)
                    )
                ''')
                
                # 创建报警记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alarm_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        boiler_id INTEGER NOT NULL,
                        alarm_type TEXT NOT NULL,
                        alarm_code TEXT,
                        severity TEXT,
                        message TEXT,
                        value_at_alarm REAL,
                        threshold_value REAL,
                        acknowledged INTEGER DEFAULT 0,
                        acknowledged_by INTEGER,
                        acknowledged_at TIMESTAMP,
                        cleared INTEGER DEFAULT 0,
                        cleared_by INTEGER,
                        cleared_at TIMESTAMP,
                        notes TEXT,
                        occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                        FOREIGN KEY (acknowledged_by) REFERENCES users(id),
                        FOREIGN KEY (cleared_by) REFERENCES users(id)
                    )
                ''')
                
                # 创建水质分析记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS water_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        boiler_id INTEGER NOT NULL,
                        sample_location TEXT,
                        ph_value REAL,
                        tds_ppm REAL,
                        conductivity_us REAL,
                        hardness_ppm REAL,
                        alkalinity_ppm REAL,
                        chloride_ppm REAL,
                        sulfate_ppm REAL,
                        silica_ppm REAL,
                        iron_ppm REAL,
                        copper_ppm REAL,
                        dissolved_oxygen_ppb REAL,
                        turbidity_ntu REAL,
                        color_pt_co REAL,
                        sampler_id INTEGER,
                        analyzer_id INTEGER,
                        sample_time TIMESTAMP,
                        analysis_time TIMESTAMP,
                        result TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                        FOREIGN KEY (sampler_id) REFERENCES users(id),
                        FOREIGN KEY (analyzer_id) REFERENCES users(id)
                    )
                ''')
                
                # 创建设备维护记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS maintenance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        equipment_id INTEGER NOT NULL,
                        equipment_type TEXT,
                        maintenance_type TEXT,
                        description TEXT,
                        parts_replaced TEXT,
                        labor_hours REAL,
                        cost REAL,
                        technician_id INTEGER,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT,
                        next_maintenance_date DATE,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (technician_id) REFERENCES users(id)
                    )
                ''')
                
                # 创建操作日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        action TEXT NOT NULL,
                        module TEXT,
                        details TEXT,
                        ip_address TEXT,
                        result TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                
                # 创建报表配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT,
                        parameters TEXT,
                        schedule TEXT,
                        recipients TEXT,
                        format TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users(id)
                    )
                ''')
                
                # 创建系统设置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key_name TEXT UNIQUE NOT NULL,
                        value TEXT,
                        value_type TEXT,
                        description TEXT,
                        updated_by INTEGER,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (updated_by) REFERENCES users(id)
                    )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_realtime_boiler ON real_time_data(boiler_id, recorded_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_boiler ON historical_data(boiler_id, recorded_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alarm_boiler ON alarm_records(boiler_id, occurred_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dosing_boiler ON dosing_records(boiler_id, created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blowdown_boiler ON blowdown_records(boiler_id, created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_water_analysis_boiler ON water_analysis(boiler_id, sample_time)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_logs_user ON operation_logs(user_id, created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_logs_action ON operation_logs(action)')
                
                # 插入默认管理员账户（密码：admin123）
                cursor.execute('''
                    INSERT OR IGNORE INTO users (username, password_hash, role, full_name)
                    VALUES ('admin', 'e10adc3949ba59abbe56e057f20f883e', 'administrator', '系统管理员')
                ''')
                
                # 插入默认锅炉设备
                cursor.execute('''
                    INSERT OR IGNORE INTO boilers (name, model, capacity_m3, max_pressure_mpa, max_temperature_c)
                    VALUES ('1#锅炉', 'SZL10-1.6-AII', 10.0, 1.6, 200.0)
                ''')
                
                # 插入默认系统设置
                default_settings = [
                    ('sampling_interval', '5', 'integer', '数据采集间隔（秒）'),
                    ('auto_dosing_enabled', '1', 'boolean', '自动投药启用'),
                    ('auto_blowdown_enabled', '1', 'boolean', '自动排污启用'),
                    ('tds_threshold', '3500', 'float', 'TDS 排污阈值（ppm）'),
                    ('ph_min', '7.0', 'float', 'pH 下限'),
                    ('ph_max', '9.0', 'float', 'pH 上限'),
                ]
                
                for setting in default_settings:
                    cursor.execute('''
                        INSERT OR IGNORE INTO system_settings (key_name, value, value_type, description)
                        VALUES (?, ?, ?, ?)
                    ''', setting)
            
            return True
        except Exception as e:
            print(f"数据库初始化失败：{e}")
            return False
    
    # ==================== 用户管理 ====================
    
    def add_user(self, username: str, password_hash: str, role: str, 
                 full_name: str = "", department: str = "", 
                 email: str = "", phone: str = "") -> int:
        """添加用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, full_name, department, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, role, full_name, department, email, phone))
            return cursor.lastrowid
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """获取用户信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        if not kwargs:
            return False
        
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE users SET {fields} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户（软删除）"""
        return self.update_user(user_id, is_active=0)
    
    def get_all_users(self, active_only: bool = False) -> List[Dict]:
        """获取所有用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY username')
            else:
                cursor.execute('SELECT * FROM users ORDER BY username')
            return [dict(row) for row in cursor.fetchall()]
    
    def record_login(self, user_id: int, success: bool) -> None:
        """记录登录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if success:
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP, login_attempts = 0
                    WHERE id = ?
                ''', (user_id,))
            else:
                cursor.execute('''
                    UPDATE users SET login_attempts = login_attempts + 1
                    WHERE id = ?
                ''', (user_id,))
    
    # ==================== 锅炉设备管理 ====================
    
    def add_boiler(self, name: str, model: str = "", serial_number: str = "",
                   manufacturer: str = "", capacity_m3: float = 0.0,
                   max_pressure_mpa: float = 0.0, max_temperature_c: float = 0.0,
                   location: str = "", notes: str = "") -> int:
        """添加锅炉设备"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO boilers (name, model, serial_number, manufacturer, 
                                    capacity_m3, max_pressure_mpa, max_temperature_c,
                                    location, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, model, serial_number, manufacturer, capacity_m3,
                  max_pressure_mpa, max_temperature_c, location, notes))
            return cursor.lastrowid
    
    def get_boiler(self, boiler_id: int) -> Optional[Dict]:
        """获取锅炉信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM boilers WHERE id = ?', (boiler_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_boilers(self, active_only: bool = False) -> List[Dict]:
        """获取所有锅炉"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM boilers ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_boiler_status(self, boiler_id: int, status: str) -> bool:
        """更新锅炉状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE boilers SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, boiler_id))
            return cursor.rowcount > 0
    
    def update_boiler(self, boiler_id: int, **kwargs) -> bool:
        """更新锅炉信息"""
        if not kwargs:
            return False
        
        kwargs['updated_at'] = datetime.now()
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [boiler_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE boilers SET {fields} WHERE id = ?', values)
            return cursor.rowcount > 0
    
    # ==================== 实时数据管理 ====================
    
    def insert_real_time_data(self, boiler_id: int, **kwargs) -> int:
        """插入实时数据"""
        kwargs['boiler_id'] = boiler_id
        kwargs['recorded_at'] = datetime.now()
        
        fields = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?' for _ in kwargs])
        values = list(kwargs.values())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                INSERT INTO real_time_data ({fields}) VALUES ({placeholders})
            ''', values)
            return cursor.lastrowid
    
    def get_latest_real_time_data(self, boiler_id: int) -> Optional[Dict]:
        """获取最新实时数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM real_time_data 
                WHERE boiler_id = ? 
                ORDER BY recorded_at DESC LIMIT 1
            ''', (boiler_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_real_time_data_range(self, boiler_id: int, start_time: datetime, 
                                  end_time: datetime) -> List[Dict]:
        """获取指定时间范围的实时数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM real_time_data 
                WHERE boiler_id = ? AND recorded_at BETWEEN ? AND ?
                ORDER BY recorded_at ASC
            ''', (boiler_id, start_time, end_time))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_real_time_data(self, boiler_id: int, minutes: int = 60) -> List[Dict]:
        """获取最近 N 分钟的实时数据"""
        start_time = datetime.now() - timedelta(minutes=minutes)
        return self.get_real_time_data_range(boiler_id, start_time, datetime.now())
    
    # ==================== 历史数据管理 ====================
    
    def archive_real_time_data(self, days_old: int = 7) -> int:
        """归档旧实时数据到历史数据表"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 移动数据
            cursor.execute('''
                INSERT INTO historical_data (boiler_id, temperature, pressure, 
                                            water_level, ph_value, tds_ppm, 
                                            conductivity_us, recorded_at)
                SELECT boiler_id, temperature, pressure, water_level, ph_value,
                       tds_ppm, conductivity_us, recorded_at
                FROM real_time_data
                WHERE recorded_at < ?
            ''', (cutoff_date,))
            
            moved_count = cursor.rowcount
            
            # 删除已移动的旧数据
            cursor.execute('''
                DELETE FROM real_time_data WHERE recorded_at < ?
            ''', (cutoff_date,))
            
            return moved_count
    
    def get_historical_data(self, boiler_id: int, start_time: datetime,
                            end_time: datetime) -> List[Dict]:
        """获取历史数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM historical_data 
                WHERE boiler_id = ? AND recorded_at BETWEEN ? AND ?
                ORDER BY recorded_at ASC
            ''', (boiler_id, start_time, end_time))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 除污剂投放记录 ====================
    
    def add_dosing_record(self, boiler_id: int, agent_type: str, dosage_ml: float,
                          concentration_percent: float = 30.0, method: str = "auto",
                          operator_id: int = None, notes: str = "") -> int:
        """添加除污剂投放记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dosing_records (boiler_id, agent_type, dosage_ml,
                                           concentration_percent, method, operator_id,
                                           start_time, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'completed', ?)
            ''', (boiler_id, agent_type, dosage_ml, concentration_percent,
                  method, operator_id, notes))
            return cursor.lastrowid
    
    def get_dosing_records(self, boiler_id: int = None, start_date: datetime = None,
                           end_date: datetime = None) -> List[Dict]:
        """获取投放记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM dosing_records WHERE 1=1'
            params = []
            
            if boiler_id:
                query += ' AND boiler_id = ?'
                params.append(boiler_id)
            
            if start_date:
                query += ' AND start_time >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND start_time <= ?'
                params.append(end_date)
            
            query += ' ORDER BY start_time DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 排污记录 ====================
    
    def add_blowdown_record(self, boiler_id: int, valve_id: int = 1,
                            duration_seconds: int = 0, reason: str = "",
                            tds_before: float = 0.0, tds_after: float = 0.0,
                            water_loss_m3: float = 0.0, operator_id: int = None,
                            mode: str = "auto", notes: str = "") -> int:
        """添加排污记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO blowdown_records (boiler_id, valve_id, open_time, close_time,
                                             duration_seconds, reason, tds_before, tds_after,
                                             water_loss_m3, operator_id, mode, status, notes)
                VALUES (?, ?, CURRENT_TIMESTAMP, datetime(CURRENT_TIMESTAMP, ?),
                        ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
            ''', (boiler_id, valve_id, f'+{duration_seconds} seconds', duration_seconds,
                  reason, tds_before, tds_after, water_loss_m3, operator_id, mode, notes))
            return cursor.lastrowid
    
    def get_blowdown_records(self, boiler_id: int = None, start_date: datetime = None,
                             end_date: datetime = None) -> List[Dict]:
        """获取排污记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM blowdown_records WHERE 1=1'
            params = []
            
            if boiler_id:
                query += ' AND boiler_id = ?'
                params.append(boiler_id)
            
            if start_date:
                query += ' AND created_at >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND created_at <= ?'
                params.append(end_date)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 报警记录 ====================
    
    def add_alarm(self, boiler_id: int, alarm_type: str, message: str,
                  severity: str = "warning", alarm_code: str = "",
                  value_at_alarm: float = 0.0, threshold_value: float = 0.0,
                  notes: str = "") -> int:
        """添加报警记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alarm_records (boiler_id, alarm_type, alarm_code, severity,
                                          message, value_at_alarm, threshold_value, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (boiler_id, alarm_type, alarm_code, severity, message,
                  value_at_alarm, threshold_value, notes))
            return cursor.lastrowid
    
    def acknowledge_alarm(self, alarm_id: int, user_id: int) -> bool:
        """确认报警"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alarm_records 
                SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id, alarm_id))
            return cursor.rowcount > 0
    
    def clear_alarm(self, alarm_id: int, user_id: int) -> bool:
        """清除报警"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alarm_records 
                SET cleared = 1, cleared_by = ?, cleared_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id, alarm_id))
            return cursor.rowcount > 0
    
    def get_active_alarms(self, boiler_id: int = None) -> List[Dict]:
        """获取活动报警"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM alarm_records 
                WHERE acknowledged = 0 OR cleared = 0
            '''
            params = []
            
            if boiler_id:
                query += ' AND boiler_id = ?'
                params.append(boiler_id)
            
            query += ' ORDER BY occurred_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_alarm_history(self, boiler_id: int = None, start_date: datetime = None,
                          end_date: datetime = None) -> List[Dict]:
        """获取报警历史"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM alarm_records WHERE 1=1'
            params = []
            
            if boiler_id:
                query += ' AND boiler_id = ?'
                params.append(boiler_id)
            
            if start_date:
                query += ' AND occurred_at >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND occurred_at <= ?'
                params.append(end_date)
            
            query += ' ORDER BY occurred_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 水质分析记录 ====================
    
    def add_water_analysis(self, boiler_id: int, ph_value: float = 0.0,
                           tds_ppm: float = 0.0, conductivity_us: float = 0.0,
                           hardness_ppm: float = 0.0, alkalinity_ppm: float = 0.0,
                           chloride_ppm: float = 0.0, sulfate_ppm: float = 0.0,
                           silica_ppm: float = 0.0, iron_ppm: float = 0.0,
                           copper_ppm: float = 0.0, dissolved_oxygen_ppb: float = 0.0,
                           turbidity_ntu: float = 0.0, sampler_id: int = None,
                           analyzer_id: int = None, notes: str = "") -> int:
        """添加水质分析记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO water_analysis (boiler_id, ph_value, tds_ppm, conductivity_us,
                                           hardness_ppm, alkalinity_ppm, chloride_ppm,
                                           sulfate_ppm, silica_ppm, iron_ppm, copper_ppm,
                                           dissolved_oxygen_ppb, turbidity_ntu, sampler_id,
                                           analyzer_id, sample_time, analysis_time, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
            ''', (boiler_id, ph_value, tds_ppm, conductivity_us, hardness_ppm,
                  alkalinity_ppm, chloride_ppm, sulfate_ppm, silica_ppm, iron_ppm,
                  copper_ppm, dissolved_oxygen_ppb, turbidity_ntu, sampler_id,
                  analyzer_id, notes))
            return cursor.lastrowid
    
    def get_water_analysis_records(self, boiler_id: int = None, start_date: datetime = None,
                                   end_date: datetime = None) -> List[Dict]:
        """获取水质分析记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM water_analysis WHERE 1=1'
            params = []
            
            if boiler_id:
                query += ' AND boiler_id = ?'
                params.append(boiler_id)
            
            if start_date:
                query += ' AND sample_time >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND sample_time <= ?'
                params.append(end_date)
            
            query += ' ORDER BY sample_time DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 维护记录 ====================
    
    def add_maintenance_record(self, equipment_id: int, equipment_type: str,
                               maintenance_type: str, description: str,
                               parts_replaced: str = "", labor_hours: float = 0.0,
                               cost: float = 0.0, technician_id: int = None,
                               next_maintenance_date: datetime = None,
                               notes: str = "") -> int:
        """添加维护记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO maintenance_records (equipment_id, equipment_type,
                                                maintenance_type, description,
                                                parts_replaced, labor_hours, cost,
                                                technician_id, start_time, status,
                                                next_maintenance_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'completed', ?, ?)
            ''', (equipment_id, equipment_type, maintenance_type, description,
                  parts_replaced, labor_hours, cost, technician_id,
                  next_maintenance_date, notes))
            return cursor.lastrowid
    
    def get_maintenance_records(self, equipment_id: int = None,
                                equipment_type: str = None) -> List[Dict]:
        """获取维护记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM maintenance_records WHERE 1=1'
            params = []
            
            if equipment_id:
                query += ' AND equipment_id = ?'
                params.append(equipment_id)
            
            if equipment_type:
                query += ' AND equipment_type = ?'
                params.append(equipment_type)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 操作日志 ====================
    
    def log_operation(self, user_id: int, action: str, module: str = "",
                      details: str = "", ip_address: str = "",
                      result: str = "success") -> int:
        """记录操作日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_logs (user_id, action, module, details,
                                           ip_address, result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, action, module, details, ip_address, result))
            return cursor.lastrowid
    
    def get_operation_logs(self, user_id: int = None, action: str = None,
                           start_date: datetime = None,
                           end_date: datetime = None) -> List[Dict]:
        """获取操作日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM operation_logs WHERE 1=1'
            params = []
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if action:
                query += ' AND action = ?'
                params.append(action)
            
            if start_date:
                query += ' AND created_at >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND created_at <= ?'
                params.append(end_date)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 系统设置 ====================
    
    def get_setting(self, key_name: str, default: Any = None) -> Any:
        """获取系统设置"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value, value_type FROM system_settings WHERE key_name = ?',
                          (key_name,))
            row = cursor.fetchone()
            
            if row:
                value, value_type = row
                if value_type == 'integer':
                    return int(value)
                elif value_type == 'float':
                    return float(value)
                elif value_type == 'boolean':
                    return value == '1'
                elif value_type == 'json':
                    return json.loads(value)
                return value
            return default
    
    def set_setting(self, key_name: str, value: Any, value_type: str = "string",
                    description: str = "", updated_by: int = None) -> bool:
        """设置系统参数"""
        if value_type == 'boolean':
            value = '1' if value else '0'
        elif value_type == 'json':
            value = json.dumps(value)
        else:
            value = str(value)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_settings 
                (key_name, value, value_type, description, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key_name, value, value_type, description, updated_by))
            return cursor.rowcount > 0
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有系统设置"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM system_settings')
            settings = {}
            for row in cursor.fetchall():
                key = row['key_name']
                value = row['value']
                value_type = row['value_type']
                
                if value_type == 'integer':
                    settings[key] = int(value)
                elif value_type == 'float':
                    settings[key] = float(value)
                elif value_type == 'boolean':
                    settings[key] = value == '1'
                elif value_type == 'json':
                    settings[key] = json.loads(value)
                else:
                    settings[key] = value
            return settings
    
    # ==================== 统计查询 ====================
    
    def get_daily_statistics(self, date: datetime = None) -> Dict:
        """获取每日统计数据"""
        if date is None:
            date = datetime.now().date()
        
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 投放统计
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(dosage_ml) as total_dosage
                FROM dosing_records
                WHERE start_time BETWEEN ? AND ?
            ''', (start_of_day, end_of_day))
            row = cursor.fetchone()
            stats['dosing_count'] = row['count'] or 0
            stats['total_dosage_ml'] = row['total_dosage'] or 0
            
            # 排污统计
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(duration_seconds) as total_duration,
                       SUM(water_loss_m3) as total_water_loss
                FROM blowdown_records
                WHERE created_at BETWEEN ? AND ?
            ''', (start_of_day, end_of_day))
            row = cursor.fetchone()
            stats['blowdown_count'] = row['count'] or 0
            stats['total_blowdown_duration'] = row['total_duration'] or 0
            stats['total_water_loss_m3'] = row['total_water_loss'] or 0
            
            # 报警统计
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM alarm_records
                WHERE occurred_at BETWEEN ? AND ?
                GROUP BY severity
            ''', (start_of_day, end_of_day))
            stats['alarms_by_severity'] = {row['severity']: row['count'] 
                                           for row in cursor.fetchall()}
            
            return stats
    
    def get_monthly_statistics(self, year: int = None, month: int = None) -> Dict:
        """获取月度统计数据"""
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 投放统计
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(dosage_ml) as total_dosage,
                       agent_type, COUNT(*) as type_count
                FROM dosing_records
                WHERE start_time BETWEEN ? AND ?
                GROUP BY agent_type
            ''', (start_of_month, end_of_month))
            stats['dosing_by_type'] = {row['agent_type']: {
                'count': row['type_count'],
                'total_dosage_ml': row['total_dosage'] or 0
            } for row in cursor.fetchall()}
            
            # 排污统计按原因
            cursor.execute('''
                SELECT reason, COUNT(*) as count, SUM(water_loss_m3) as total_loss
                FROM blowdown_records
                WHERE created_at BETWEEN ? AND ?
                GROUP BY reason
            ''', (start_of_month, end_of_month))
            stats['blowdown_by_reason'] = {row['reason']: {
                'count': row['count'],
                'total_water_loss_m3': row['total_loss'] or 0
            } for row in cursor.fetchall()}
            
            # 报警趋势（按天）
            cursor.execute('''
                SELECT DATE(occurred_at) as date, COUNT(*) as count
                FROM alarm_records
                WHERE occurred_at BETWEEN ? AND ?
                GROUP BY DATE(occurred_at)
            ''', (start_of_month, end_of_month))
            stats['daily_alarm_trend'] = {row['date']: row['count'] 
                                          for row in cursor.fetchall()}
            
            return stats
    
    # ==================== 数据清理 ====================
    
    def cleanup_old_data(self, retention_days: int = 365) -> int:
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 清理历史数据
            cursor.execute('DELETE FROM historical_data WHERE recorded_at < ?',
                          (cutoff_date,))
            deleted_count += cursor.rowcount
            
            # 清理旧的已确认报警
            cursor.execute('''
                DELETE FROM alarm_records 
                WHERE cleared = 1 AND cleared_at < ?
            ''', (cutoff_date,))
            deleted_count += cursor.rowcount
            
            # 清理旧的操作日志
            cursor.execute('DELETE FROM operation_logs WHERE created_at < ?',
                          (cutoff_date,))
            deleted_count += cursor.rowcount
        
        return deleted_count
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"数据库备份失败：{e}")
            return False
