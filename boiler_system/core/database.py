"""
数据库管理模块 - Database Management Module
负责数据库连接、表创建和数据操作
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager
import json


class DatabaseManager:
    """
    数据库管理器类
    管理 SQLite 数据库的连接和操作
    """
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
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
    
    def initialize(self):
        """初始化数据库，创建所有必要的表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    real_name TEXT,
                    role TEXT NOT NULL DEFAULT 'operator',
                    department TEXT,
                    phone TEXT,
                    email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建锅炉表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS boilers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    model TEXT,
                    serial_number TEXT,
                    manufacturer TEXT,
                    install_date DATE,
                    capacity REAL,
                    max_pressure REAL,
                    max_temperature REAL,
                    status TEXT DEFAULT 'offline',
                    location TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建传感器数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boiler_id INTEGER NOT NULL,
                    pressure REAL,
                    temperature REAL,
                    water_level REAL,
                    flow_rate REAL,
                    ph_value REAL,
                    conductivity REAL,
                    turbidity REAL,
                    dissolved_oxygen REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (boiler_id) REFERENCES boilers(id)
                )
            ''')
            
            # 创建传感器数据索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_data_boiler 
                ON sensor_data(boiler_id, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp 
                ON sensor_data(timestamp)
            ''')
            
            # 创建清洗记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cleaning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boiler_id INTEGER NOT NULL,
                    cleaning_type TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_minutes INTEGER,
                    chemical_used REAL,
                    chemical_type TEXT,
                    rinse_cycles INTEGER,
                    operator_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                    FOREIGN KEY (operator_id) REFERENCES users(id)
                )
            ''')
            
            # 创建报警记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarm_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boiler_id INTEGER,
                    alarm_type TEXT NOT NULL,
                    alarm_level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    is_acknowledged BOOLEAN DEFAULT 0,
                    acknowledged_by INTEGER,
                    acknowledged_at TIMESTAMP,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                    FOREIGN KEY (acknowledged_by) REFERENCES users(id)
                )
            ''')
            
            # 创建报警记录索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alarm_records_created 
                ON alarm_records(created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alarm_records_acknowledged 
                ON alarm_records(is_acknowledged)
            ''')
            
            # 创建设备维护记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boiler_id INTEGER NOT NULL,
                    maintenance_type TEXT NOT NULL,
                    description TEXT,
                    scheduled_date DATE,
                    completed_date DATE,
                    technician_id INTEGER,
                    parts_replaced TEXT,
                    cost REAL,
                    status TEXT DEFAULT 'scheduled',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                    FOREIGN KEY (technician_id) REFERENCES users(id)
                )
            ''')
            
            # 创建系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_level TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL,
                    details TEXT,
                    user_id INTEGER,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 创建系统日志索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_system_logs_created 
                ON system_logs(created_at)
            ''')
            
            # 创建配置历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    changed_by INTEGER,
                    change_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (changed_by) REFERENCES users(id)
                )
            ''')
            
            # 创建报告表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date DATE,
                    end_date DATE,
                    file_path TEXT,
                    generated_by INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (generated_by) REFERENCES users(id)
                )
            ''')
            
            # 创建化学品库存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chemical_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chemical_name TEXT NOT NULL,
                    chemical_type TEXT,
                    current_quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    min_quantity REAL,
                    max_quantity REAL,
                    supplier TEXT,
                    last_purchase_date DATE,
                    expiry_date DATE,
                    storage_location TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建化学品使用记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chemical_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chemical_id INTEGER NOT NULL,
                    boiler_id INTEGER,
                    cleaning_record_id INTEGER,
                    quantity_used REAL NOT NULL,
                    unit TEXT NOT NULL,
                    used_by INTEGER,
                    usage_purpose TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chemical_id) REFERENCES chemical_inventory(id),
                    FOREIGN KEY (boiler_id) REFERENCES boilers(id),
                    FOREIGN KEY (cleaning_record_id) REFERENCES cleaning_records(id),
                    FOREIGN KEY (used_by) REFERENCES users(id)
                )
            ''')
            
            # 创建权限表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建角色权限关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role TEXT NOT NULL,
                    permission_id INTEGER NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    granted_by INTEGER,
                    PRIMARY KEY (role, permission_id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id),
                    FOREIGN KEY (granted_by) REFERENCES users(id)
                )
            ''')
            
            # 创建值班记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shift_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    shift_start TIMESTAMP NOT NULL,
                    shift_end TIMESTAMP,
                    handover_notes TEXT,
                    incidents TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # 插入默认数据
            self._insert_default_data(cursor)
    
    def _insert_default_data(self, cursor):
        """插入默认数据"""
        # 插入默认管理员用户（密码为 admin123 的哈希）
        import hashlib
        default_password = hashlib.sha256("admin123".encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, real_name, role)
            VALUES ('admin', ?, '系统管理员', 'admin')
        ''', (default_password,))
        
        # 插入默认权限
        default_permissions = [
            ('view_dashboard', '查看仪表板', 'view'),
            ('operate_boiler', '操作锅炉', 'operate'),
            ('start_cleaning', '启动清洗', 'operate'),
            ('stop_cleaning', '停止清洗', 'operate'),
            ('acknowledge_alarm', '确认报警', 'operate'),
            ('view_reports', '查看报告', 'report'),
            ('generate_reports', '生成报告', 'report'),
            ('manage_users', '管理用户', 'admin'),
            ('manage_config', '管理配置', 'admin'),
            ('view_logs', '查看日志', 'admin'),
            ('export_data', '导出数据', 'admin'),
            ('emergency_stop', '紧急停止', 'safety'),
            ('maintenance_access', '维护访问', 'maintenance'),
        ]
        
        for perm in default_permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (name, description, category)
                VALUES (?, ?, ?)
            ''', perm)
        
        # 插入默认角色权限
        role_permissions = [
            ('admin', 'view_dashboard'),
            ('admin', 'operate_boiler'),
            ('admin', 'start_cleaning'),
            ('admin', 'stop_cleaning'),
            ('admin', 'acknowledge_alarm'),
            ('admin', 'view_reports'),
            ('admin', 'generate_reports'),
            ('admin', 'manage_users'),
            ('admin', 'manage_config'),
            ('admin', 'view_logs'),
            ('admin', 'export_data'),
            ('admin', 'emergency_stop'),
            ('admin', 'maintenance_access'),
            ('operator', 'view_dashboard'),
            ('operator', 'operate_boiler'),
            ('operator', 'start_cleaning'),
            ('operator', 'stop_cleaning'),
            ('operator', 'acknowledge_alarm'),
            ('operator', 'view_reports'),
            ('operator', 'emergency_stop'),
            ('viewer', 'view_dashboard'),
            ('viewer', 'view_reports'),
        ]
        
        for role, perm in role_permissions:
            cursor.execute('''
                SELECT id FROM permissions WHERE name = ?
            ''', (perm,))
            result = cursor.fetchone()
            if result:
                cursor.execute('''
                    INSERT OR IGNORE INTO role_permissions (role, permission_id)
                    VALUES (?, ?)
                ''', (role, result[0]))
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回受影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    
    # ==================== 用户管理方法 ====================
    
    def create_user(self, username: str, password_hash: str, real_name: str,
                   role: str = 'operator', department: str = '',
                   phone: str = '', email: str = '') -> int:
        """创建新用户"""
        query = '''
            INSERT INTO users (username, password_hash, real_name, role, department, phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (username, password_hash, real_name, 
                                           role, department, phone, email))
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """获取用户信息"""
        results = self.execute_query(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        )
        return results[0] if results else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户信息"""
        results = self.execute_query(
            'SELECT * FROM users WHERE username = ?', (username,)
        )
        return results[0] if results else None
    
    def authenticate_user(self, username: str, password_hash: str) -> Optional[Dict]:
        """验证用户登录"""
        results = self.execute_query(
            'SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1',
            (username, password_hash)
        )
        
        if results:
            # 更新最后登录时间
            self.execute_update(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (results[0]['id'],)
            )
            return results[0]
        
        return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        if not kwargs:
            return False
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        query = f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        return self.execute_update(query, tuple(values)) > 0
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户（软删除）"""
        return self.execute_update(
            'UPDATE users SET is_active = 0 WHERE id = ?', (user_id,)
        ) > 0
    
    def get_all_users(self, include_inactive: bool = False) -> List[Dict]:
        """获取所有用户"""
        if include_inactive:
            return self.execute_query('SELECT * FROM users ORDER BY username')
        else:
            return self.execute_query('SELECT * FROM users WHERE is_active = 1 ORDER BY username')
    
    def get_users_by_role(self, role: str) -> List[Dict]:
        """根据角色获取用户"""
        return self.execute_query(
            'SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY username',
            (role,)
        )
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有指定权限"""
        results = self.execute_query('''
            SELECT u.role FROM users u
            JOIN role_permissions rp ON u.role = rp.role
            JOIN permissions p ON rp.permission_id = p.id
            WHERE u.id = ? AND p.name = ?
        ''', (user_id, permission))
        
        return len(results) > 0
    
    # ==================== 锅炉管理方法 ====================
    
    def create_boiler(self, name: str, model: str = '', serial_number: str = '',
                     manufacturer: str = '', install_date: str = '',
                     capacity: float = 0, max_pressure: float = 0,
                     max_temperature: float = 0, location: str = '',
                     notes: str = '') -> int:
        """创建新锅炉记录"""
        query = '''
            INSERT INTO boilers (name, model, serial_number, manufacturer, install_date,
                                capacity, max_pressure, max_temperature, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (name, model, serial_number, manufacturer,
                                           install_date, capacity, max_pressure,
                                           max_temperature, location, notes))
    
    def get_boiler(self, boiler_id: int) -> Optional[Dict]:
        """获取锅炉信息"""
        results = self.execute_query('SELECT * FROM boilers WHERE id = ?', (boiler_id,))
        return results[0] if results else None
    
    def get_all_boilers(self, status: Optional[str] = None) -> List[Dict]:
        """获取所有锅炉"""
        if status:
            return self.execute_query('SELECT * FROM boilers WHERE status = ? ORDER BY name', (status,))
        else:
            return self.execute_query('SELECT * FROM boilers ORDER BY name')
    
    def update_boiler_status(self, boiler_id: int, status: str) -> bool:
        """更新锅炉状态"""
        return self.execute_update(
            'UPDATE boilers SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (status, boiler_id)
        ) > 0
    
    def update_boiler(self, boiler_id: int, **kwargs) -> bool:
        """更新锅炉信息"""
        if not kwargs:
            return False
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [boiler_id]
        
        query = f'UPDATE boilers SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        return self.execute_update(query, tuple(values)) > 0
    
    def delete_boiler(self, boiler_id: int) -> bool:
        """删除锅炉"""
        return self.execute_update('DELETE FROM boilers WHERE id = ?', (boiler_id,)) > 0
    
    # ==================== 传感器数据方法 ====================
    
    def add_sensor_data(self, boiler_id: int, pressure: float = None,
                       temperature: float = None, water_level: float = None,
                       flow_rate: float = None, ph_value: float = None,
                       conductivity: float = None, turbidity: float = None,
                       dissolved_oxygen: float = None) -> int:
        """添加传感器数据"""
        query = '''
            INSERT INTO sensor_data (boiler_id, pressure, temperature, water_level,
                                    flow_rate, ph_value, conductivity, turbidity, dissolved_oxygen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (boiler_id, pressure, temperature, water_level,
                                  flow_rate, ph_value, conductivity, turbidity, dissolved_oxygen))
            return cursor.lastrowid
    
    def get_latest_sensor_data(self, boiler_id: int) -> Optional[Dict]:
        """获取最新的传感器数据"""
        results = self.execute_query('''
            SELECT * FROM sensor_data 
            WHERE boiler_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (boiler_id,))
        return results[0] if results else None
    
    def get_sensor_data_range(self, boiler_id: int, start_time: datetime, 
                             end_time: datetime) -> List[Dict]:
        """获取指定时间范围的传感器数据"""
        return self.execute_query('''
            SELECT * FROM sensor_data 
            WHERE boiler_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        ''', (boiler_id, start_time.isoformat(), end_time.isoformat()))
    
    def get_sensor_data_last_hours(self, boiler_id: int, hours: int = 24) -> List[Dict]:
        """获取最近几小时的传感器数据"""
        return self.execute_query('''
            SELECT * FROM sensor_data 
            WHERE boiler_id = ? AND timestamp >= datetime('now', ?)
            ORDER BY timestamp ASC
        ''', (boiler_id, f'-{hours} hours'))
    
    def cleanup_old_sensor_data(self, days: int = 90) -> int:
        """清理旧的传感器数据"""
        return self.execute_update('''
            DELETE FROM sensor_data 
            WHERE timestamp < datetime('now', ?)
        ''', (f'-{days} days',))
    
    # ==================== 清洗记录方法 ====================
    
    def create_cleaning_record(self, boiler_id: int, cleaning_type: str,
                              operator_id: int = None, chemical_type: str = '',
                              notes: str = '') -> int:
        """创建清洗记录"""
        query = '''
            INSERT INTO cleaning_records (boiler_id, cleaning_type, start_time, 
                                         operator_id, chemical_type, notes, status)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, 'running')
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (boiler_id, cleaning_type, operator_id, chemical_type, notes))
            return cursor.lastrowid
    
    def complete_cleaning_record(self, record_id: int, duration_minutes: int = None,
                                chemical_used: float = None, rinse_cycles: int = None,
                                result: str = '', notes: str = '') -> bool:
        """完成清洗记录"""
        updates = []
        values = []
        
        if duration_minutes:
            updates.append('duration_minutes = ?')
            values.append(duration_minutes)
        
        if chemical_used:
            updates.append('chemical_used = ?')
            values.append(chemical_used)
        
        if rinse_cycles:
            updates.append('rinse_cycles = ?')
            values.append(rinse_cycles)
        
        updates.extend(['end_time = CURRENT_TIMESTAMP', "status = 'completed'"])
        
        if result:
            updates.append('result = ?')
            values.append(result)
        
        if notes:
            updates.append('notes = ?')
            values.append(notes)
        
        values.append(record_id)
        
        query = f'''
            UPDATE cleaning_records 
            SET {', '.join(updates)}
            WHERE id = ?
        '''
        
        return self.execute_update(query, tuple(values)) > 0
    
    def get_cleaning_record(self, record_id: int) -> Optional[Dict]:
        """获取清洗记录"""
        results = self.execute_query(
            'SELECT * FROM cleaning_records WHERE id = ?', (record_id,)
        )
        return results[0] if results else None
    
    def get_cleaning_records(self, boiler_id: int = None, 
                            status: str = None,
                            start_date: str = None,
                            end_date: str = None) -> List[Dict]:
        """获取清洗记录列表"""
        conditions = []
        values = []
        
        if boiler_id:
            conditions.append('boiler_id = ?')
            values.append(boiler_id)
        
        if status:
            conditions.append('status = ?')
            values.append(status)
        
        if start_date:
            conditions.append('start_time >= ?')
            values.append(start_date)
        
        if end_date:
            conditions.append('start_time <= ?')
            values.append(end_date)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM cleaning_records 
            {where_clause}
            ORDER BY start_time DESC
        '''
        
        return self.execute_query(query, tuple(values))
    
    # ==================== 报警记录方法 ====================
    
    def create_alarm(self, boiler_id: int, alarm_type: str, alarm_level: str,
                    message: str, value: float = None, threshold: float = None) -> int:
        """创建报警记录"""
        query = '''
            INSERT INTO alarm_records (boiler_id, alarm_type, alarm_level, message, value, threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (boiler_id, alarm_type, alarm_level, message, value, threshold))
            return cursor.lastrowid
    
    def acknowledge_alarm(self, alarm_id: int, user_id: int) -> bool:
        """确认报警"""
        return self.execute_update('''
            UPDATE alarm_records 
            SET is_acknowledged = 1, acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_acknowledged = 0
        ''', (user_id, alarm_id)) > 0
    
    def resolve_alarm(self, alarm_id: int) -> bool:
        """解决报警"""
        return self.execute_update('''
            UPDATE alarm_records 
            SET resolved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND resolved_at IS NULL
        ''', (alarm_id,)) > 0
    
    def get_active_alarms(self, boiler_id: int = None) -> List[Dict]:
        """获取活动报警"""
        conditions = ['is_acknowledged = 0']
        values = []
        
        if boiler_id:
            conditions.append('boiler_id = ?')
            values.append(boiler_id)
        
        query = f'''
            SELECT * FROM alarm_records 
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
        '''
        
        return self.execute_query(query, tuple(values))
    
    def get_alarm_history(self, boiler_id: int = None, 
                         start_date: str = None,
                         end_date: str = None,
                         alarm_type: str = None,
                         limit: int = 100) -> List[Dict]:
        """获取报警历史"""
        conditions = []
        values = []
        
        if boiler_id:
            conditions.append('boiler_id = ?')
            values.append(boiler_id)
        
        if start_date:
            conditions.append('created_at >= ?')
            values.append(start_date)
        
        if end_date:
            conditions.append('created_at <= ?')
            values.append(end_date)
        
        if alarm_type:
            conditions.append('alarm_type = ?')
            values.append(alarm_type)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM alarm_records 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        '''
        
        values.append(limit)
        return self.execute_query(query, tuple(values))
    
    def get_unacknowledged_alarm_count(self) -> int:
        """获取未确认报警数量"""
        results = self.execute_query('''
            SELECT COUNT(*) as count FROM alarm_records WHERE is_acknowledged = 0
        ''')
        return results[0]['count'] if results else 0
    
    # ==================== 维护记录方法 ====================
    
    def create_maintenance_record(self, boiler_id: int, maintenance_type: str,
                                 description: str = '', scheduled_date: str = None,
                                 technician_id: int = None) -> int:
        """创建维护记录"""
        query = '''
            INSERT INTO maintenance_records (boiler_id, maintenance_type, description, 
                                            scheduled_date, technician_id)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (boiler_id, maintenance_type, description,
                                           scheduled_date, technician_id))
    
    def complete_maintenance(self, record_id: int, completed_date: str = None,
                            parts_replaced: str = '', cost: float = 0,
                            notes: str = '') -> bool:
        """完成维护记录"""
        updates = ["status = 'completed'"]
        values = []
        
        if completed_date:
            updates.append('completed_date = ?')
            values.append(completed_date)
        else:
            updates.append('completed_date = CURRENT_DATE')
        
        if parts_replaced:
            updates.append('parts_replaced = ?')
            values.append(parts_replaced)
        
        if cost:
            updates.append('cost = ?')
            values.append(cost)
        
        if notes:
            updates.append('notes = ?')
            values.append(notes)
        
        values.append(record_id)
        
        query = f'''
            UPDATE maintenance_records 
            SET {', '.join(updates)}
            WHERE id = ?
        '''
        
        return self.execute_update(query, tuple(values)) > 0
    
    def get_maintenance_records(self, boiler_id: int = None,
                               status: str = None) -> List[Dict]:
        """获取维护记录"""
        conditions = []
        values = []
        
        if boiler_id:
            conditions.append('boiler_id = ?')
            values.append(boiler_id)
        
        if status:
            conditions.append('status = ?')
            values.append(status)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM maintenance_records 
            {where_clause}
            ORDER BY scheduled_date DESC
        '''
        
        return self.execute_query(query, tuple(values))
    
    # ==================== 系统日志方法 ====================
    
    def add_system_log(self, log_level: str, message: str, module: str = '',
                      details: str = '', user_id: int = None,
                      ip_address: str = '') -> int:
        """添加系统日志"""
        query = '''
            INSERT INTO system_logs (log_level, module, message, details, user_id, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (log_level, module, message, details, user_id, ip_address))
            return cursor.lastrowid
    
    def get_system_logs(self, log_level: str = None, 
                       start_date: str = None,
                       end_date: str = None,
                       module: str = None,
                       limit: int = 100) -> List[Dict]:
        """获取系统日志"""
        conditions = []
        values = []
        
        if log_level:
            conditions.append('log_level = ?')
            values.append(log_level)
        
        if start_date:
            conditions.append('created_at >= ?')
            values.append(start_date)
        
        if end_date:
            conditions.append('created_at <= ?')
            values.append(end_date)
        
        if module:
            conditions.append('module = ?')
            values.append(module)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM system_logs 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        '''
        
        values.append(limit)
        return self.execute_query(query, tuple(values))
    
    # ==================== 化学品库存方法 ====================
    
    def add_chemical(self, chemical_name: str, chemical_type: str = '',
                    current_quantity: float = 0, unit: str = '',
                    min_quantity: float = 0, max_quantity: float = 0,
                    supplier: str = '', storage_location: str = '',
                    notes: str = '') -> int:
        """添加化学品库存"""
        query = '''
            INSERT INTO chemical_inventory (chemical_name, chemical_type, current_quantity,
                                           unit, min_quantity, max_quantity, supplier,
                                           storage_location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (chemical_name, chemical_type, current_quantity,
                                           unit, min_quantity, max_quantity, supplier,
                                           storage_location, notes))
    
    def update_chemical_quantity(self, chemical_id: int, quantity: float,
                                is_addition: bool = True) -> bool:
        """更新化学品数量"""
        if is_addition:
            query = '''
                UPDATE chemical_inventory 
                SET current_quantity = current_quantity + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
        else:
            query = '''
                UPDATE chemical_inventory 
                SET current_quantity = current_quantity - ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND current_quantity >= ?
            '''
            return self.execute_update(query, (quantity, chemical_id, quantity)) > 0
        
        return self.execute_update(query, (quantity, chemical_id)) > 0
    
    def get_low_stock_chemicals(self) -> List[Dict]:
        """获取低库存化学品"""
        return self.execute_query('''
            SELECT * FROM chemical_inventory 
            WHERE current_quantity <= min_quantity AND is_active = 1
            ORDER BY current_quantity ASC
        ''')
    
    def get_all_chemicals(self) -> List[Dict]:
        """获取所有化学品"""
        return self.execute_query('SELECT * FROM chemical_inventory ORDER BY chemical_name')
    
    def get_chemical(self, chemical_id: int) -> Optional[Dict]:
        """获取化学品信息"""
        results = self.execute_query(
            'SELECT * FROM chemical_inventory WHERE id = ?', (chemical_id,)
        )
        return results[0] if results else None
    
    # ==================== 化学品使用记录方法 ====================
    
    def record_chemical_usage(self, chemical_id: int, quantity_used: float,
                             unit: str, used_by: int = None,
                             boiler_id: int = None, cleaning_record_id: int = None,
                             usage_purpose: str = '', notes: str = '') -> int:
        """记录化学品使用"""
        query = '''
            INSERT INTO chemical_usage (chemical_id, quantity_used, unit, used_by,
                                       boiler_id, cleaning_record_id, usage_purpose, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # 同时更新库存
        self.update_chemical_quantity(chemical_id, quantity_used, is_addition=False)
        
        return self.execute_update(query, (chemical_id, quantity_used, unit, used_by,
                                           boiler_id, cleaning_record_id, usage_purpose, notes))
    
    def get_chemical_usage(self, chemical_id: int = None,
                          start_date: str = None,
                          end_date: str = None) -> List[Dict]:
        """获取化学品使用记录"""
        conditions = []
        values = []
        
        if chemical_id:
            conditions.append('chemical_id = ?')
            values.append(chemical_id)
        
        if start_date:
            conditions.append('created_at >= ?')
            values.append(start_date)
        
        if end_date:
            conditions.append('created_at <= ?')
            values.append(end_date)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM chemical_usage 
            {where_clause}
            ORDER BY created_at DESC
        '''
        
        return self.execute_query(query, tuple(values))
    
    # ==================== 报告方法 ====================
    
    def create_report(self, report_type: str, title: str, description: str = '',
                     start_date: str = None, end_date: str = None,
                     generated_by: int = None) -> int:
        """创建报告记录"""
        query = '''
            INSERT INTO reports (report_type, title, description, start_date, end_date, generated_by)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        return self.execute_update(query, (report_type, title, description,
                                           start_date, end_date, generated_by))
    
    def update_report_file(self, report_id: int, file_path: str,
                          status: str = 'completed') -> bool:
        """更新报告文件路径"""
        return self.execute_update('''
            UPDATE reports 
            SET file_path = ?, status = ?
            WHERE id = ?
        ''', (file_path, status, report_id)) > 0
    
    def get_reports(self, report_type: str = None,
                   start_date: str = None,
                   end_date: str = None) -> List[Dict]:
        """获取报告列表"""
        conditions = []
        values = []
        
        if report_type:
            conditions.append('report_type = ?')
            values.append(report_type)
        
        if start_date:
            conditions.append('start_date >= ?')
            values.append(start_date)
        
        if end_date:
            conditions.append('end_date <= ?')
            values.append(end_date)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM reports 
            {where_clause}
            ORDER BY created_at DESC
        '''
        
        return self.execute_query(query, tuple(values))
    
    # ==================== 值班记录方法 ====================
    
    def start_shift(self, user_id: int) -> int:
        """开始值班"""
        query = '''
            INSERT INTO shift_records (user_id, shift_start, status)
            VALUES (?, CURRENT_TIMESTAMP, 'active')
        '''
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            return cursor.lastrowid
    
    def end_shift(self, shift_id: int, handover_notes: str = '',
                 incidents: str = '') -> bool:
        """结束值班"""
        updates = ["status = 'completed'", "shift_end = CURRENT_TIMESTAMP"]
        values = []
        
        if handover_notes:
            updates.append('handover_notes = ?')
            values.append(handover_notes)
        
        if incidents:
            updates.append('incidents = ?')
            values.append(incidents)
        
        values.append(shift_id)
        
        query = f'''
            UPDATE shift_records 
            SET {', '.join(updates)}
            WHERE id = ?
        '''
        
        return self.execute_update(query, tuple(values)) > 0
    
    def get_active_shift(self, user_id: int) -> Optional[Dict]:
        """获取当前活动值班"""
        results = self.execute_query('''
            SELECT * FROM shift_records 
            WHERE user_id = ? AND status = 'active'
            ORDER BY shift_start DESC LIMIT 1
        ''', (user_id,))
        return results[0] if results else None
    
    def get_shift_records(self, user_id: int = None,
                         start_date: str = None,
                         end_date: str = None) -> List[Dict]:
        """获取值班记录"""
        conditions = []
        values = []
        
        if user_id:
            conditions.append('user_id = ?')
            values.append(user_id)
        
        if start_date:
            conditions.append('shift_start >= ?')
            values.append(start_date)
        
        if end_date:
            conditions.append('shift_start <= ?')
            values.append(end_date)
        
        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f'''
            SELECT * FROM shift_records 
            {where_clause}
            ORDER BY shift_start DESC
        '''
        
        return self.execute_query(query, tuple(values))
    
    # ==================== 统计方法 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {}
        
        # 锅炉统计
        boiler_stats = self.execute_query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline,
                SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance
            FROM boilers
        ''')
        stats['boilers'] = boiler_stats[0] if boiler_stats else {}
        
        # 报警统计
        alarm_stats = self.execute_query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_acknowledged = 0 THEN 1 ELSE 0 END) as unacknowledged,
                SUM(CASE WHEN alarm_level = 'critical' THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN alarm_level = 'warning' THEN 1 ELSE 0 END) as warning
            FROM alarm_records
            WHERE created_at >= datetime('now', '-24 hours')
        ''')
        stats['alarms_24h'] = alarm_stats[0] if alarm_stats else {}
        
        # 清洗统计
        cleaning_stats = self.execute_query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running
            FROM cleaning_records
            WHERE start_time >= datetime('now', '-7 days')
        ''')
        stats['cleanings_7d'] = cleaning_stats[0] if cleaning_stats else {}
        
        # 用户统计
        user_stats = self.execute_query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admins,
                SUM(CASE WHEN role = 'operator' THEN 1 ELSE 0 END) as operators
            FROM users
            WHERE is_active = 1
        ''')
        stats['users'] = user_stats[0] if user_stats else {}
        
        return stats
    
    # ==================== 备份和恢复方法 ====================
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        import shutil
        
        try:
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"数据库备份失败：{e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        import shutil
        
        if not os.path.exists(backup_path):
            return False
        
        try:
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            print(f"数据库恢复失败：{e}")
            return False
    
    def get_backup_files(self, backup_dir: str) -> List[Dict]:
        """获取备份文件列表"""
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.db') or file.endswith('.sqlite'):
                file_path = os.path.join(backup_dir, file)
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
