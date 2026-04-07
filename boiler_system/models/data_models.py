"""
数据模型模块 - Data Models Module
定义系统使用的各种数据模型和枚举类型
"""

from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 枚举类型 ====================

class BoilerStatus(Enum):
    """锅炉状态枚举"""
    OFFLINE = "offline"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    MAINTENANCE = "maintenance"
    FAULT = "fault"
    EMERGENCY_STOP = "emergency_stop"


class CleaningStatus(Enum):
    """清洗状态枚举"""
    PENDING = "pending"
    PREPARING = "preparing"
    DRAINING = "draining"
    FILLING = "filling"
    CHEMICAL_CLEANING = "chemical_cleaning"
    RINSING = "rinsing"
    DRYING = "drying"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CleaningType(Enum):
    """清洗类型枚举"""
    ACID_CLEANING = "acid_cleaning"  # 酸洗
    ALKALI_CLEANING = "alkali_cleaning"  # 碱洗
    HIGH_PRESSURE_WATER = "high_pressure_water"  # 高压水冲洗
    STEAM_BLOWING = "steam_blowing"  # 蒸汽吹扫
    MECHANICAL_CLEANING = "mechanical_cleaning"  # 机械清洗
    ULTRASONIC_CLEANING = "ultrasonic_cleaning"  # 超声波清洗


class AlarmLevel(IntEnum):
    """报警级别枚举"""
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


class AlarmType(Enum):
    """报警类型枚举"""
    PRESSURE_HIGH = "pressure_high"
    PRESSURE_LOW = "pressure_low"
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    WATER_LEVEL_HIGH = "water_level_high"
    WATER_LEVEL_LOW = "water_level_low"
    FLOW_RATE_ABNORMAL = "flow_rate_abnormal"
    PH_VALUE_ABNORMAL = "ph_value_abnormal"
    CONDUCTIVITY_HIGH = "conductivity_high"
    TURBIDITY_HIGH = "turbidity_high"
    DISSOLVED_OXYGEN_LOW = "dissolved_oxygen_low"
    SENSOR_FAILURE = "sensor_failure"
    COMMUNICATION_FAILURE = "communication_failure"
    POWER_FAILURE = "power_failure"
    VALVE_FAILURE = "valve_failure"
    PUMP_FAILURE = "pump_failure"
    CHEMICAL_LOW = "chemical_low"
    CLEANING_TIMEOUT = "cleaning_timeout"
    MAINTENANCE_REQUIRED = "maintenance_required"
    SAFETY_INTERLOCK = "safety_interlock"
    EMERGENCY_STOP_ACTIVATED = "emergency_stop_activated"


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    MAINTENANCE = "maintenance"


class MaintenanceStatus(Enum):
    """维护状态枚举"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class MaintenanceType(Enum):
    """维护类型枚举"""
    ROUTINE = "routine"  # 例行维护
    PREVENTIVE = "preventive"  # 预防性维护
    CORRECTIVE = "corrective"  # 纠正性维护
    EMERGENCY = "emergency"  # 紧急维护
    INSPECTION = "inspection"  # 检查
    CALIBRATION = "calibration"  # 校准


class ReportType(Enum):
    """报告类型枚举"""
    DAILY_OPERATION = "daily_operation"  # 日常运行报告
    WEEKLY_SUMMARY = "weekly_summary"  # 周总结报告
    MONTHLY_ANALYSIS = "monthly_analysis"  # 月度分析报告
    CLEANING_REPORT = "cleaning_report"  # 清洗报告
    MAINTENANCE_REPORT = "maintenance_report"  # 维护报告
    ALARM_ANALYSIS = "alarm_analysis"  # 报警分析报告
    ENERGY_CONSUMPTION = "energy_consumption"  # 能耗报告
    WATER_QUALITY = "water_quality"  # 水质报告
    CUSTOM = "custom"  # 自定义报告


class ShiftStatus(Enum):
    """值班状态枚举"""
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"


class LogSeverity(Enum):
    """日志严重程度枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ==================== 数据类 ====================

@dataclass
class SensorReading:
    """传感器读数数据类"""
    boiler_id: int
    pressure: Optional[float] = None  # MPa
    temperature: Optional[float] = None  # °C
    water_level: Optional[float] = None  # %
    flow_rate: Optional[float] = None  # m³/h
    ph_value: Optional[float] = None  # pH
    conductivity: Optional[float] = None  # μS/cm
    turbidity: Optional[float] = None  # NTU
    dissolved_oxygen: Optional[float] = None  # mg/L
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_normal(self, config: 'SensorConfig' = None) -> bool:
        """检查读数是否正常"""
        if config is None:
            return True
        
        if self.pressure and self.pressure > config.alarm_threshold_pressure:
            return False
        if self.temperature and self.temperature > config.alarm_threshold_temperature:
            return False
        if self.water_level and self.water_level < config.alarm_threshold_water_level:
            return False
        
        return True
    
    def get_warnings(self, config: 'SensorConfig' = None) -> List[str]:
        """获取警告列表"""
        warnings = []
        
        if config is None:
            return warnings
        
        if self.pressure:
            if self.pressure > config.alarm_threshold_pressure:
                warnings.append(f"压力过高：{self.pressure} MPa")
            elif self.pressure > config.warning_threshold_pressure:
                warnings.append(f"压力警告：{self.pressure} MPa")
        
        if self.temperature:
            if self.temperature > config.alarm_threshold_temperature:
                warnings.append(f"温度过高：{self.temperature} °C")
            elif self.temperature > config.warning_threshold_temperature:
                warnings.append(f"温度警告：{self.temperature} °C")
        
        if self.water_level:
            if self.water_level < config.alarm_threshold_water_level:
                warnings.append(f"水位过低：{self.water_level} %")
        
        return warnings


@dataclass
class AlarmInfo:
    """报警信息数据类"""
    id: int
    boiler_id: Optional[int]
    alarm_type: AlarmType
    alarm_level: AlarmLevel
    message: str
    value: Optional[float]
    threshold: Optional[float]
    is_acknowledged: bool
    acknowledged_by: Optional[int]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlarmInfo':
        """从字典创建实例"""
        return cls(
            id=data.get('id', 0),
            boiler_id=data.get('boiler_id'),
            alarm_type=AlarmType(data.get('alarm_type', 'sensor_failure')),
            alarm_level=AlarmLevel[data.get('alarm_level', 'WARNING').upper()],
            message=data.get('message', ''),
            value=data.get('value'),
            threshold=data.get('threshold'),
            is_acknowledged=bool(data.get('is_acknowledged', False)),
            acknowledged_by=data.get('acknowledged_by'),
            acknowledged_at=datetime.fromisoformat(data['acknowledged_at']) if data.get('acknowledged_at') else None,
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )
    
    def acknowledge(self, user_id: int):
        """确认报警"""
        self.is_acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now()
    
    def resolve(self):
        """解决报警"""
        self.resolved_at = datetime.now()


@dataclass
class CleaningProcess:
    """清洗过程数据类"""
    id: int
    boiler_id: int
    cleaning_type: CleaningType
    status: CleaningStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    chemical_used: Optional[float]
    chemical_type: str
    rinse_cycles: int
    operator_id: Optional[int]
    notes: str
    result: str
    
    @property
    def elapsed_minutes(self) -> int:
        """获取已用时间（分钟）"""
        if self.start_time:
            end = self.end_time or datetime.now()
            return int((end - self.start_time).total_seconds() / 60)
        return 0
    
    @property
    def progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.status == CleaningStatus.COMPLETED:
            return 100.0
        if self.status == CleaningStatus.CANCELLED or self.status == CleaningStatus.FAILED:
            return 0.0
        
        # 根据状态估算进度
        progress_map = {
            CleaningStatus.PENDING: 0,
            CleaningStatus.PREPARING: 5,
            CleaningStatus.DRAINING: 15,
            CleaningStatus.FILLING: 25,
            CleaningStatus.CHEMICAL_CLEANING: 50,
            CleaningStatus.RINSING: 75,
            CleaningStatus.DRYING: 90,
        }
        
        return progress_map.get(self.status, 0)


@dataclass
class BoilerInfo:
    """锅炉信息数据类"""
    id: int
    name: str
    model: str
    serial_number: str
    manufacturer: str
    install_date: Optional[str]
    capacity: float  # t/h
    max_pressure: float  # MPa
    max_temperature: float  # °C
    status: BoilerStatus
    location: str
    notes: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoilerInfo':
        """从字典创建实例"""
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            model=data.get('model', ''),
            serial_number=data.get('serial_number', ''),
            manufacturer=data.get('manufacturer', ''),
            install_date=data.get('install_date'),
            capacity=data.get('capacity', 0),
            max_pressure=data.get('max_pressure', 0),
            max_temperature=data.get('max_temperature', 0),
            status=BoilerStatus(data.get('status', 'offline')),
            location=data.get('location', ''),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )
    
    def is_available(self) -> bool:
        """检查锅炉是否可用"""
        return self.status in [BoilerStatus.OFFLINE, BoilerStatus.RUNNING]
    
    def is_running(self) -> bool:
        """检查锅炉是否正在运行"""
        return self.status == BoilerStatus.RUNNING


@dataclass
class UserInfo:
    """用户信息数据类"""
    id: int
    username: str
    real_name: str
    role: UserRole
    department: str
    phone: str
    email: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInfo':
        """从字典创建实例"""
        return cls(
            id=data.get('id', 0),
            username=data.get('username', ''),
            real_name=data.get('real_name', ''),
            role=UserRole(data.get('role', 'operator')),
            department=data.get('department', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            is_active=bool(data.get('is_active', True)),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return self.real_name or self.username


@dataclass
class ChemicalItem:
    """化学品库存项数据类"""
    id: int
    chemical_name: str
    chemical_type: str
    current_quantity: float
    unit: str
    min_quantity: float
    max_quantity: float
    supplier: str
    last_purchase_date: Optional[str]
    expiry_date: Optional[str]
    storage_location: str
    notes: str
    
    @property
    def is_low_stock(self) -> bool:
        """检查是否为低库存"""
        return self.current_quantity <= self.min_quantity
    
    @property
    def stock_percentage(self) -> float:
        """获取库存百分比"""
        if self.max_quantity <= 0:
            return 0
        return (self.current_quantity / self.max_quantity) * 100


@dataclass
class MaintenanceRecord:
    """维护记录数据类"""
    id: int
    boiler_id: int
    maintenance_type: MaintenanceType
    description: str
    scheduled_date: Optional[str]
    completed_date: Optional[str]
    technician_id: Optional[int]
    parts_replaced: str
    cost: float
    status: MaintenanceStatus
    notes: str
    
    @property
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if self.scheduled_date and self.status not in [MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED]:
            scheduled = datetime.strptime(self.scheduled_date, '%Y-%m-%d')
            return datetime.now() > scheduled
        return False


@dataclass
class SystemStatistics:
    """系统统计数据类"""
    total_boilers: int = 0
    running_boilers: int = 0
    offline_boilers: int = 0
    maintenance_boilers: int = 0
    
    total_alarms_24h: int = 0
    unacknowledged_alarms: int = 0
    critical_alarms: int = 0
    warning_alarms: int = 0
    
    total_cleanings_7d: int = 0
    completed_cleanings: int = 0
    running_cleanings: int = 0
    
    total_users: int = 0
    admin_users: int = 0
    operator_users: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemStatistics':
        """从字典创建实例"""
        stats = cls()
        
        if 'boilers' in data:
            stats.total_boilers = data['boilers'].get('total', 0)
            stats.running_boilers = data['boilers'].get('running', 0)
            stats.offline_boilers = data['boilers'].get('offline', 0)
            stats.maintenance_boilers = data['boilers'].get('maintenance', 0)
        
        if 'alarms_24h' in data:
            stats.total_alarms_24h = data['alarms_24h'].get('total', 0)
            stats.unacknowledged_alarms = data['alarms_24h'].get('unacknowledged', 0)
            stats.critical_alarms = data['alarms_24h'].get('critical', 0)
            stats.warning_alarms = data['alarms_24h'].get('warning', 0)
        
        if 'cleanings_7d' in data:
            stats.total_cleanings_7d = data['cleanings_7d'].get('total', 0)
            stats.completed_cleanings = data['cleanings_7d'].get('completed', 0)
            stats.running_cleanings = data['cleanings_7d'].get('running', 0)
        
        if 'users' in data:
            stats.total_users = data['users'].get('total', 0)
            stats.admin_users = data['users'].get('admins', 0)
            stats.operator_users = data['users'].get('operators', 0)
        
        return stats


@dataclass
class DashboardData:
    """仪表板数据数据类"""
    statistics: SystemStatistics = field(default_factory=SystemStatistics)
    active_alarms: List[AlarmInfo] = field(default_factory=list)
    running_cleanings: List[CleaningProcess] = field(default_factory=list)
    recent_sensor_readings: Dict[int, SensorReading] = field(default_factory=dict)
    boiler_statuses: Dict[int, BoilerStatus] = field(default_factory=dict)
    low_stock_chemicals: List[ChemicalItem] = field(default_factory=list)
    pending_maintenance: List[MaintenanceRecord] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ChartDataPoint:
    """图表数据点"""
    timestamp: datetime
    value: float
    label: str = ""


@dataclass
class ChartSeries:
    """图表系列"""
    name: str
    color: str
    data: List[ChartDataPoint] = field(default_factory=list)
    unit: str = ""


@dataclass
class ReportDefinition:
    """报告定义数据类"""
    id: int
    report_type: ReportType
    title: str
    description: str
    start_date: Optional[str]
    end_date: Optional[str]
    file_path: str
    generated_by: Optional[int]
    status: str
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportDefinition':
        """从字典创建实例"""
        return cls(
            id=data.get('id', 0),
            report_type=ReportType(data.get('report_type', 'custom')),
            title=data.get('title', ''),
            description=data.get('description', ''),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            file_path=data.get('file_path', ''),
            generated_by=data.get('generated_by'),
            status=data.get('status', 'pending'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class ShiftRecord:
    """值班记录数据类"""
    id: int
    user_id: int
    user_name: str
    shift_start: datetime
    shift_end: Optional[datetime]
    handover_notes: str
    incidents: str
    status: ShiftStatus
    
    @property
    def duration_hours(self) -> float:
        """获取值班时长（小时）"""
        if self.shift_start:
            end = self.shift_end or datetime.now()
            return (end - self.shift_start).total_seconds() / 3600
        return 0


@dataclass
class PermissionInfo:
    """权限信息数据类"""
    id: int
    name: str
    description: str
    category: str


@dataclass
class SystemLog:
    """系统日志数据类"""
    id: int
    log_level: LogSeverity
    module: str
    message: str
    details: str
    user_id: Optional[int]
    ip_address: str
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemLog':
        """从字典创建实例"""
        return cls(
            id=data.get('id', 0),
            log_level=LogSeverity(data.get('log_level', 'INFO')),
            module=data.get('module', ''),
            message=data.get('message', ''),
            details=data.get('details', ''),
            user_id=data.get('user_id'),
            ip_address=data.get('ip_address', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class CleaningStep:
    """清洗步骤数据类"""
    """用于指导清洗流程的步骤"""
    order: int
    name: str
    description: str
    expected_duration_minutes: int
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_completed: bool = False
    actual_duration_minutes: Optional[int] = None
    notes: str = ""


@dataclass
class SafetyInterlock:
    """安全联锁数据类"""
    name: str
    description: str
    is_active: bool
    condition: str
    action: str
    priority: int
    last_triggered: Optional[datetime] = None


@dataclass
class ValveState:
    """阀门状态数据类"""
    valve_id: str
    name: str
    is_open: bool
    position_percentage: float  # 0-100，用于调节阀
    is_manual: bool
    last_updated: datetime


@dataclass
class PumpState:
    """泵状态数据类"""
    pump_id: str
    name: str
    is_running: bool
    speed_rpm: Optional[int]
    frequency_hz: Optional[float]
    inlet_pressure: Optional[float]
    outlet_pressure: Optional[float]
    temperature: Optional[float]
    vibration: Optional[float]
    last_updated: datetime


@dataclass
class EquipmentStatus:
    """设备状态数据类"""
    boiler_id: int
    valves: List[ValveState] = field(default_factory=list)
    pumps: List[PumpState] = field(default_factory=list)
    sensors_ok: bool = True
    communication_ok: bool = True
    power_ok: bool = True
    safety_system_ok: bool = True
    last_updated: datetime = field(default_factory=datetime.now)
