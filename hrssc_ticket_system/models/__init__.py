"""
人力资源共享服务中心工单处理系统 - 数据模型层
包含所有核心数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class TicketStatus(Enum):
    """工单状态枚举"""
    DRAFT = "草稿"
    SUBMITTED = "已提交"
    ASSIGNED = "已分配"
    IN_PROGRESS = "处理中"
    PENDING_APPROVAL = "待审批"
    APPROVED = "已批准"
    REJECTED = "已拒绝"
    RESOLVED = "已解决"
    CLOSED = "已关闭"
    CANCELLED = "已取消"


class TicketPriority(Enum):
    """工单优先级枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    URGENT = "紧急"


class TicketCategory(Enum):
    """工单分类枚举"""
    RECRUITMENT = "招聘管理"
    ONBOARDING = "入职管理"
    OFFBOARDING = "离职管理"
    PAYROLL = "薪酬福利"
    TRAINING = "培训发展"
    PERFORMANCE = "绩效管理"
    EMPLOYEE_RELATIONS = "员工关系"
    HR_POLICY = "HR政策咨询"
    SYSTEM_SUPPORT = "系统支持"
    OTHER = "其他"


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "系统管理员"
    HR_MANAGER = "HR经理"
    HR_SPECIALIST = "HR专员"
    REQUESTER = "申请人"
    APPROVER = "审批人"
    VIEWER = "查看者"


@dataclass
class User:
    """用户模型"""
    id: str
    username: str
    email: str
    full_name: str
    department: str
    position: str
    role: UserRole
    phone: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'department': self.department,
            'position': self.position,
            'role': self.role.value,
            'phone': self.phone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(
            id=data.get('id', ''),
            username=data.get('username', ''),
            email=data.get('email', ''),
            full_name=data.get('full_name', ''),
            department=data.get('department', ''),
            position=data.get('position', ''),
            role=UserRole(data.get('role', 'REQUESTER')),
            phone=data.get('phone', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            is_active=data.get('is_active', True),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        )


@dataclass
class TicketComment:
    """工单评论模型"""
    id: str
    ticket_id: str
    user_id: str
    user_name: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_internal: bool = False  # 内部评论（申请人不可见）
    attachments: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_internal': self.is_internal,
            'attachments': self.attachments
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TicketComment':
        return cls(
            id=data.get('id', ''),
            ticket_id=data.get('ticket_id', ''),
            user_id=data.get('user_id', ''),
            user_name=data.get('user_name', ''),
            content=data.get('content', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            is_internal=data.get('is_internal', False),
            attachments=data.get('attachments', [])
        )


@dataclass
class TicketAttachment:
    """工单附件模型"""
    id: str
    ticket_id: str
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    uploaded_by: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat(),
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TicketAttachment':
        return cls(
            id=data.get('id', ''),
            ticket_id=data.get('ticket_id', ''),
            file_name=data.get('file_name', ''),
            file_path=data.get('file_path', ''),
            file_size=data.get('file_size', 0),
            file_type=data.get('file_type', ''),
            uploaded_by=data.get('uploaded_by', ''),
            uploaded_at=datetime.fromisoformat(data['uploaded_at']) if data.get('uploaded_at') else datetime.now(),
            description=data.get('description', '')
        )


@dataclass
class TicketHistory:
    """工单历史记录模型"""
    id: str
    ticket_id: str
    action_type: str  # CREATED, STATUS_CHANGED, ASSIGNED, COMMENT_ADDED, etc.
    old_value: Optional[str]
    new_value: Optional[str]
    performed_by: str
    performed_by_name: str
    performed_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'action_type': self.action_type,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'performed_by': self.performed_by,
            'performed_by_name': self.performed_by_name,
            'performed_at': self.performed_at.isoformat(),
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TicketHistory':
        return cls(
            id=data.get('id', ''),
            ticket_id=data.get('ticket_id', ''),
            action_type=data.get('action_type', ''),
            old_value=data.get('old_value'),
            new_value=data.get('new_value'),
            performed_by=data.get('performed_by', ''),
            performed_by_name=data.get('performed_by_name', ''),
            performed_at=datetime.fromisoformat(data['performed_at']) if data.get('performed_at') else datetime.now(),
            description=data.get('description', '')
        )


@dataclass
class SLAConfiguration:
    """SLA配置模型"""
    id: str
    category: TicketCategory
    priority: TicketPriority
    response_time_hours: int  # 响应时间（小时）
    resolution_time_hours: int  # 解决时间（小时）
    escalation_time_hours: int  # 升级时间（小时）
    is_active: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'category': self.category.value,
            'priority': self.priority.value,
            'response_time_hours': self.response_time_hours,
            'resolution_time_hours': self.resolution_time_hours,
            'escalation_time_hours': self.escalation_time_hours,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SLAConfiguration':
        return cls(
            id=data.get('id', ''),
            category=TicketCategory(data.get('category', 'OTHER')),
            priority=TicketPriority(data.get('priority', 'MEDIUM')),
            response_time_hours=data.get('response_time_hours', 24),
            resolution_time_hours=data.get('resolution_time_hours', 72),
            escalation_time_hours=data.get('escalation_time_hours', 48),
            is_active=data.get('is_active', True)
        )


@dataclass
class Ticket:
    """工单核心模型"""
    id: str
    ticket_number: str  # 工单编号，如 TKT-2024-0001
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    requester_id: str
    requester_name: str
    requester_department: str
    assigned_to: Optional[str] = None  # 处理人ID
    assigned_to_name: Optional[str] = None  # 处理人姓名
    approver_id: Optional[str] = None  # 审批人ID
    approver_name: Optional[str] = None  # 审批人姓名
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    sla_breach: bool = False
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    parent_ticket_id: Optional[str] = None  # 父工单ID（用于子工单）
    related_tickets: List[str] = field(default_factory=list)  # 关联工单
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.ticket_number:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = str(uuid.uuid4())[:8].upper()
            self.ticket_number = f"TKT-{timestamp}-{random_suffix}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'requester_id': self.requester_id,
            'requester_name': self.requester_name,
            'requester_department': self.requester_department,
            'assigned_to': self.assigned_to,
            'assigned_to_name': self.assigned_to_name,
            'approver_id': self.approver_id,
            'approver_name': self.approver_name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'sla_breach': self.sla_breach,
            'tags': self.tags,
            'custom_fields': self.custom_fields,
            'parent_ticket_id': self.parent_ticket_id,
            'related_tickets': self.related_tickets
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticket':
        return cls(
            id=data.get('id', ''),
            ticket_number=data.get('ticket_number', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=TicketCategory(data.get('category', 'OTHER')),
            priority=TicketPriority(data.get('priority', 'MEDIUM')),
            status=TicketStatus(data.get('status', 'DRAFT')),
            requester_id=data.get('requester_id', ''),
            requester_name=data.get('requester_name', ''),
            requester_department=data.get('requester_department', ''),
            assigned_to=data.get('assigned_to'),
            assigned_to_name=data.get('assigned_to_name'),
            approver_id=data.get('approver_id'),
            approver_name=data.get('approver_name'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            submitted_at=datetime.fromisoformat(data['submitted_at']) if data.get('submitted_at') else None,
            assigned_at=datetime.fromisoformat(data['assigned_at']) if data.get('assigned_at') else None,
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            closed_at=datetime.fromisoformat(data['closed_at']) if data.get('closed_at') else None,
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            sla_breach=data.get('sla_breach', False),
            tags=data.get('tags', []),
            custom_fields=data.get('custom_fields', {}),
            parent_ticket_id=data.get('parent_ticket_id'),
            related_tickets=data.get('related_tickets', [])
        )
    
    def get_elapsed_hours(self) -> float:
        """获取工单创建至今经过的小时数"""
        now = datetime.now()
        elapsed = now - self.created_at
        return elapsed.total_seconds() / 3600
    
    def get_remaining_sla_hours(self, sla_config: SLAConfiguration) -> float:
        """获取剩余SLA时间（小时）"""
        elapsed = self.get_elapsed_hours()
        remaining = sla_config.resolution_time_hours - elapsed
        return max(0, remaining)
    
    def is_sla_breached(self, sla_config: SLAConfiguration) -> bool:
        """检查是否违反SLA"""
        return self.get_elapsed_hours() > sla_config.resolution_time_hours


@dataclass
class KnowledgeBaseArticle:
    """知识库文章模型"""
    id: str
    title: str
    content: str
    category: TicketCategory
    tags: List[str] = field(default_factory=list)
    author_id: str = ""
    author_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    view_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    is_published: bool = False
    related_tickets: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category.value,
            'tags': self.tags,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'view_count': self.view_count,
            'helpful_count': self.helpful_count,
            'not_helpful_count': self.not_helpful_count,
            'is_published': self.is_published,
            'related_tickets': self.related_tickets
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeBaseArticle':
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            content=data.get('content', ''),
            category=TicketCategory(data.get('category', 'OTHER')),
            tags=data.get('tags', []),
            author_id=data.get('author_id', ''),
            author_name=data.get('author_name', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None,
            view_count=data.get('view_count', 0),
            helpful_count=data.get('helpful_count', 0),
            not_helpful_count=data.get('not_helpful_count', 0),
            is_published=data.get('is_published', False),
            related_tickets=data.get('related_tickets', [])
        )


@dataclass
class Notification:
    """通知模型"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str  # TICKET_CREATED, TICKET_ASSIGNED, COMMENT_ADDED, etc.
    related_ticket_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'related_ticket_id': self.related_ticket_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            title=data.get('title', ''),
            message=data.get('message', ''),
            notification_type=data.get('notification_type', ''),
            related_ticket_id=data.get('related_ticket_id'),
            is_read=data.get('is_read', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            read_at=datetime.fromisoformat(data['read_at']) if data.get('read_at') else None
        )


@dataclass
class ReportConfig:
    """报表配置模型"""
    id: str
    name: str
    report_type: str  # DAILY, WEEKLY, MONTHLY, CUSTOM
    filters: Dict[str, Any] = field(default_factory=dict)
    columns: List[str] = field(default_factory=list)
    chart_type: str = "bar"  # bar, line, pie
    schedule: str = ""  # Cron expression for scheduled reports
    recipients: List[str] = field(default_factory=list)
    is_active: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'report_type': self.report_type,
            'filters': self.filters,
            'columns': self.columns,
            'chart_type': self.chart_type,
            'schedule': self.schedule,
            'recipients': self.recipients,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportConfig':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            report_type=data.get('report_type', 'CUSTOM'),
            filters=data.get('filters', {}),
            columns=data.get('columns', []),
            chart_type=data.get('chart_type', 'bar'),
            schedule=data.get('schedule', ''),
            recipients=data.get('recipients', []),
            is_active=data.get('is_active', True),
            created_by=data.get('created_by', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )
