"""
人力资源共享服务中心工单处理系统 - 业务逻辑层
实现六大核心功能模块
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import uuid

from models import (
    Ticket, TicketStatus, TicketPriority, TicketCategory,
    User, UserRole, TicketComment, TicketAttachment,
    TicketHistory, SLAConfiguration, KnowledgeBaseArticle,
    Notification, ReportConfig
)
from utils.storage import get_storage, DataStorage


class TicketService:
    """工单管理服务 - 核心功能1：工单创建与生命周期管理"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or get_storage()
    
    def create_ticket(self, title: str, description: str, category: TicketCategory,
                     priority: TicketPriority, requester: User,
                     custom_fields: Dict[str, Any] = None) -> Ticket:
        """创建新工单"""
        ticket_data = {
            'id': str(uuid.uuid4()),
            'ticket_number': self._generate_ticket_number(),
            'title': title,
            'description': description,
            'category': category.value,
            'priority': priority.value,
            'status': TicketStatus.DRAFT.value,
            'requester_id': requester.id,
            'requester_name': requester.full_name,
            'requester_department': requester.department,
            'assigned_to': None,
            'assigned_to_name': None,
            'approver_id': None,
            'approver_name': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'submitted_at': None,
            'assigned_at': None,
            'resolved_at': None,
            'closed_at': None,
            'due_date': None,
            'sla_breach': False,
            'tags': [],
            'custom_fields': custom_fields or {},
            'parent_ticket_id': None,
            'related_tickets': []
        }
        
        saved_data = self.storage.add('tickets', ticket_data)
        ticket = Ticket.from_dict(saved_data)
        
        # 记录历史
        self._add_history(ticket.id, 'CREATED', None, None, 
                         requester.id, requester.full_name,
                         f"工单 {ticket.ticket_number} 已创建")
        
        return ticket
    
    def submit_ticket(self, ticket_id: str, user: User) -> Optional[Ticket]:
        """提交工单（从草稿状态）"""
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if not ticket_data:
            return None
        
        if ticket_data['status'] != TicketStatus.DRAFT.value:
            raise ValueError("只有草稿状态的工单可以提交")
        
        ticket_data['status'] = TicketStatus.SUBMITTED.value
        ticket_data['submitted_at'] = datetime.now().isoformat()
        ticket_data['updated_at'] = datetime.now().isoformat()
        
        # 根据分类和优先级设置SLA截止时间
        sla_config = self._get_sla_config(
            TicketCategory(ticket_data['category']),
            TicketPriority(ticket_data['priority'])
        )
        if sla_config:
            due_date = datetime.now() + timedelta(hours=sla_config.resolution_time_hours)
            ticket_data['due_date'] = due_date.isoformat()
        
        saved_data = self.storage.update('tickets', ticket_id, ticket_data)
        
        # 记录历史
        self._add_history(ticket_id, 'STATUS_CHANGED', 
                         TicketStatus.DRAFT.value, TicketStatus.SUBMITTED.value,
                         user.id, user.full_name,
                         "工单已提交")
        
        # 创建通知给HR团队
        self._notify_hr_team(ticket_data['ticket_number'], ticket_data['title'])
        
        return Ticket.from_dict(saved_data)
    
    def assign_ticket(self, ticket_id: str, assignee: User, assigned_by: User) -> Optional[Ticket]:
        """分配工单给处理人"""
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if not ticket_data:
            return None
        
        old_assignee = ticket_data.get('assigned_to')
        ticket_data['assigned_to'] = assignee.id
        ticket_data['assigned_to_name'] = assignee.full_name
        ticket_data['status'] = TicketStatus.ASSIGNED.value
        ticket_data['assigned_at'] = datetime.now().isoformat()
        ticket_data['updated_at'] = datetime.now().isoformat()
        
        saved_data = self.storage.update('tickets', ticket_id, ticket_data)
        
        # 记录历史
        old_value = f"未分配" if not old_assignee else old_assignee
        self._add_history(ticket_id, 'ASSIGNED', old_value, assignee.id,
                         assigned_by.id, assigned_by.full_name,
                         f"工单已分配给 {assignee.full_name}")
        
        # 通知被分配的处理人
        self._notify_user(assignee.id, 'TICKET_ASSIGNED',
                         f"新工单分配：{ticket_data['ticket_number']}",
                         f"您已被分配处理工单：{ticket_data['title']}",
                         ticket_id)
        
        return Ticket.from_dict(saved_data)
    
    def update_status(self, ticket_id: str, new_status: TicketStatus, 
                     user: User, comment: str = "") -> Optional[Ticket]:
        """更新工单状态"""
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if not ticket_data:
            return None
        
        old_status = ticket_data['status']
        ticket_data['status'] = new_status.value
        ticket_data['updated_at'] = datetime.now().isoformat()
        
        # 根据状态设置相应的时间戳
        now = datetime.now().isoformat()
        if new_status == TicketStatus.IN_PROGRESS:
            ticket_data['status'] = TicketStatus.IN_PROGRESS.value
        elif new_status == TicketStatus.RESOLVED:
            ticket_data['resolved_at'] = now
        elif new_status == TicketStatus.CLOSED:
            ticket_data['closed_at'] = now
        
        saved_data = self.storage.update('tickets', ticket_id, ticket_data)
        
        # 记录历史
        self._add_history(ticket_id, 'STATUS_CHANGED', old_status, 
                         new_status.value, user.id, user.full_name,
                         comment or f"状态变更为 {new_status.value}")
        
        return Ticket.from_dict(saved_data)
    
    def add_comment(self, ticket_id: str, content: str, user: User,
                   is_internal: bool = False) -> TicketComment:
        """添加评论"""
        comment_data = {
            'id': str(uuid.uuid4()),
            'ticket_id': ticket_id,
            'user_id': user.id,
            'user_name': user.full_name,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_internal': is_internal,
            'attachments': []
        }
        
        saved_data = self.storage.add('comments', comment_data)
        comment = TicketComment.from_dict(saved_data)
        
        # 记录历史
        self._add_history(ticket_id, 'COMMENT_ADDED', None, None,
                         user.id, user.full_name,
                         "添加了评论" + (" (内部)" if is_internal else ""))
        
        # 通知相关人员
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if ticket_data:
            requester_id = ticket_data.get('requester_id')
            assigned_to = ticket_data.get('assigned_to')
            
            # 通知申请人（如果不是内部评论且不是申请人自己加的）
            if not is_internal and requester_id and requester_id != user.id:
                self._notify_user(requester_id, 'COMMENT_ADDED',
                                 f"工单更新：{ticket_data['ticket_number']}",
                                 f"您的工单有新的评论",
                                 ticket_id)
            
            # 通知处理人
            if assigned_to and assigned_to != user.id:
                self._notify_user(assigned_to, 'COMMENT_ADDED',
                                 f"工单更新：{ticket_data['ticket_number']}",
                                 f"您处理的工单有新的评论",
                                 ticket_id)
        
        return comment
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """获取工单详情"""
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if ticket_data:
            return Ticket.from_dict(ticket_data)
        return None
    
    def get_tickets(self, filters: Dict[str, Any] = None) -> List[Ticket]:
        """获取工单列表"""
        tickets_data = self.storage.query('tickets', filters)
        return [Ticket.from_dict(t) for t in tickets_data]
    
    def search_tickets(self, search_term: str) -> List[Ticket]:
        """搜索工单"""
        tickets_data = self.storage.search('tickets', search_term)
        return [Ticket.from_dict(t) for t in tickets_data]
    
    def delete_ticket(self, ticket_id: str, user: User) -> bool:
        """删除工单"""
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if not ticket_data:
            return False
        
        # 只有特定角色可以删除工单
        if user.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            if ticket_data['requester_id'] != user.id:
                raise PermissionError("没有权限删除此工单")
        
        # 删除相关评论和历史记录
        comments = self.storage.query('comments', {'ticket_id': ticket_id})
        for comment in comments:
            self.storage.delete('comments', comment['id'])
        
        histories = self.storage.query('histories', {'ticket_id': ticket_id})
        for history in histories:
            self.storage.delete('histories', history['id'])
        
        return self.storage.delete('tickets', ticket_id)
    
    def _generate_ticket_number(self) -> str:
        """生成工单编号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"TKT-{timestamp}-{random_suffix}"
    
    def _get_sla_config(self, category: TicketCategory, priority: TicketPriority) -> Optional[SLAConfiguration]:
        """获取SLA配置"""
        sla_configs = self.storage.get_all('sla_configs')
        for config_data in sla_configs:
            if (config_data['category'] == category.value and 
                config_data['priority'] == priority.value and
                config_data.get('is_active', True)):
                return SLAConfiguration.from_dict(config_data)
        return None
    
    def _add_history(self, ticket_id: str, action_type: str,
                    old_value: Optional[str], new_value: Optional[str],
                    performed_by: str, performed_by_name: str,
                    description: str = ""):
        """添加历史记录"""
        history_data = {
            'id': str(uuid.uuid4()),
            'ticket_id': ticket_id,
            'action_type': action_type,
            'old_value': old_value,
            'new_value': new_value,
            'performed_by': performed_by,
            'performed_by_name': performed_by_name,
            'performed_at': datetime.now().isoformat(),
            'description': description
        }
        self.storage.add('histories', history_data)
    
    def _notify_user(self, user_id: str, notification_type: str,
                    title: str, message: str, related_ticket_id: str = None):
        """创建用户通知"""
        notification_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'related_ticket_id': related_ticket_id,
            'is_read': False,
            'created_at': datetime.now().isoformat(),
            'read_at': None
        }
        self.storage.add('notifications', notification_data)
    
    def _notify_hr_team(self, ticket_number: str, ticket_title: str):
        """通知HR团队新工单"""
        users_data = self.storage.get_all('users')
        for user_data in users_data:
            if user_data.get('role') in [UserRole.HR_MANAGER.value, UserRole.HR_SPECIALIST.value]:
                self._notify_user(
                    user_data['id'],
                    'TICKET_CREATED',
                    f"新工单：{ticket_number}",
                    f"新工单已提交：{ticket_title}"
                )
    
    def get_ticket_comments(self, ticket_id: str, include_internal: bool = False,
                           current_user: User = None) -> List[TicketComment]:
        """获取工单评论"""
        comments_data = self.storage.query('comments', {'ticket_id': ticket_id})
        
        # 过滤内部评论
        if not include_internal:
            comments_data = [c for c in comments_data if not c.get('is_internal', False)]
        
        return [TicketComment.from_dict(c) for c in comments_data]
    
    def get_ticket_history(self, ticket_id: str) -> List[TicketHistory]:
        """获取工单历史"""
        histories_data = self.storage.query('histories', {'ticket_id': ticket_id})
        return [TicketHistory.from_dict(h) for h in histories_data]
    
    def check_sla_breach(self) -> List[Ticket]:
        """检查SLA违规"""
        breached_tickets = []
        tickets_data = self.storage.get_all('tickets')
        
        for ticket_data in tickets_data:
            if ticket_data['status'] in [TicketStatus.CLOSED.value, TicketStatus.CANCELLED.value]:
                continue
            
            category = TicketCategory(ticket_data['category'])
            priority = TicketPriority(ticket_data['priority'])
            sla_config = self._get_sla_config(category, priority)
            
            if sla_config:
                ticket = Ticket.from_dict(ticket_data)
                if ticket.is_sla_breached(sla_config) and not ticket.sla_breach:
                    ticket_data['sla_breach'] = True
                    self.storage.update('tickets', ticket_data['id'], ticket_data)
                    breached_tickets.append(ticket)
                    
                    # 通知上级
                    self._notify_escalation(ticket)
        
        return breached_tickets
    
    def _notify_escalation(self, ticket: Ticket):
        """SLA违规升级通知"""
        users_data = self.storage.get_all('users')
        for user_data in users_data:
            if user_data.get('role') == UserRole.HR_MANAGER.value:
                self._notify_user(
                    user_data['id'],
                    'SLA_BREACH',
                    f"SLA违规警告：{ticket.ticket_number}",
                    f"工单 {ticket.title} 已超过SLA规定时间，需要立即处理！",
                    ticket.id
                )


class UserService:
    """用户管理服务 - 核心功能2：用户与权限管理"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or get_storage()
    
    def create_user(self, username: str, email: str, full_name: str,
                   department: str, position: str, role: UserRole,
                   phone: str = "") -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing = self.storage.query('users', {'username': username})
        if existing:
            raise ValueError(f"用户名 {username} 已存在")
        
        # 检查邮箱是否已存在
        existing = self.storage.query('users', {'email': email})
        if existing:
            raise ValueError(f"邮箱 {email} 已存在")
        
        user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'full_name': full_name,
            'department': department,
            'position': position,
            'role': role.value,
            'phone': phone,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True,
            'last_login': None
        }
        
        saved_data = self.storage.add('users', user_data)
        return User.from_dict(saved_data)
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        user_data = self.storage.get_by_id('users', user_id)
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        users_data = self.storage.query('users', {'username': username})
        if users_data:
            return User.from_dict(users_data[0])
        return None
    
    def get_all_users(self, filters: Dict[str, Any] = None) -> List[User]:
        """获取所有用户"""
        users_data = self.storage.query('users', filters)
        return [User.from_dict(u) for u in users_data]
    
    def update_user(self, user_id: str, updates: Dict[str, Any], 
                   operator: User) -> Optional[User]:
        """更新用户信息"""
        user_data = self.storage.get_by_id('users', user_id)
        if not user_data:
            return None
        
        # 权限检查
        if operator.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            if operator.id != user_id:
                raise PermissionError("没有权限修改此用户信息")
        
        # 不允许直接修改某些字段
        protected_fields = ['id', 'username', 'created_at', 'role']
        for field in protected_fields:
            if field in updates:
                del updates[field]
        
        updates['updated_at'] = datetime.now().isoformat()
        user_data.update(updates)
        
        saved_data = self.storage.update('users', user_id, user_data)
        return User.from_dict(saved_data)
    
    def deactivate_user(self, user_id: str, operator: User) -> bool:
        """停用用户"""
        user_data = self.storage.get_by_id('users', user_id)
        if not user_data:
            return False
        
        if operator.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            raise PermissionError("没有权限停用用户")
        
        user_data['is_active'] = False
        user_data['updated_at'] = datetime.now().isoformat()
        
        self.storage.update('users', user_id, user_data)
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证（简化版，实际应使用密码哈希）"""
        user_data = self.storage.query('users', {'username': username})
        if user_data and len(user_data) > 0:
            user = User.from_dict(user_data[0])
            if user.is_active:
                # 简化：这里假设密码验证通过
                # 实际应用中应该验证密码哈希
                user.last_login = datetime.now()
                user_data[0]['last_login'] = user.last_login.isoformat()
                self.storage.update('users', user.id, user_data[0])
                return user
        return None
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """根据角色获取用户列表"""
        return self.get_all_users({'role': role.value})
    
    def get_hr_specialists(self) -> List[User]:
        """获取所有HR专员"""
        return self.get_users_by_role(UserRole.HR_SPECIALIST)
    
    def get_approvers(self) -> List[User]:
        """获取所有审批人"""
        users = self.get_all_users()
        return [u for u in users if u.role in [UserRole.HR_MANAGER, UserRole.ADMIN]]


class KnowledgeBaseService:
    """知识库服务 - 核心功能3：知识库管理"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or get_storage()
    
    def create_article(self, title: str, content: str, category: TicketCategory,
                      author: User, tags: List[str] = None) -> KnowledgeBaseArticle:
        """创建知识库文章"""
        article_data = {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': content,
            'category': category.value,
            'tags': tags or [],
            'author_id': author.id,
            'author_name': author.full_name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'published_at': None,
            'view_count': 0,
            'helpful_count': 0,
            'not_helpful_count': 0,
            'is_published': False,
            'related_tickets': []
        }
        
        saved_data = self.storage.add('knowledge_base', article_data)
        return KnowledgeBaseArticle.from_dict(saved_data)
    
    def publish_article(self, article_id: str, publisher: User) -> Optional[KnowledgeBaseArticle]:
        """发布文章"""
        article_data = self.storage.get_by_id('knowledge_base', article_id)
        if not article_data:
            return None
        
        # 权限检查
        if publisher.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            if article_data['author_id'] != publisher.id:
                raise PermissionError("没有权限发布此文章")
        
        article_data['is_published'] = True
        article_data['published_at'] = datetime.now().isoformat()
        article_data['updated_at'] = datetime.now().isoformat()
        
        saved_data = self.storage.update('knowledge_base', article_id, article_data)
        return KnowledgeBaseArticle.from_dict(saved_data)
    
    def get_article(self, article_id: str) -> Optional[KnowledgeBaseArticle]:
        """获取文章详情"""
        article_data = self.storage.get_by_id('knowledge_base', article_id)
        if article_data:
            article = KnowledgeBaseArticle.from_dict(article_data)
            # 增加浏览次数
            article.view_count += 1
            article_data['view_count'] = article.view_count
            self.storage.update('knowledge_base', article_id, article_data)
            return article
        return None
    
    def search_articles(self, search_term: str, category: TicketCategory = None) -> List[KnowledgeBaseArticle]:
        """搜索文章"""
        articles_data = self.storage.search('knowledge_base', search_term, 
                                           ['title', 'content', 'tags'])
        
        if category:
            articles_data = [a for a in articles_data if a['category'] == category.value]
        
        return [KnowledgeBaseArticle.from_dict(a) for a in articles_data]
    
    def get_published_articles(self, category: TicketCategory = None) -> List[KnowledgeBaseArticle]:
        """获取已发布的文章"""
        filters = {'is_published': True}
        if category:
            filters['category'] = category.value
        
        articles_data = self.storage.query('knowledge_base', filters)
        return [KnowledgeBaseArticle.from_dict(a) for a in articles_data]
    
    def rate_article(self, article_id: str, helpful: bool) -> bool:
        """评价文章是否有用"""
        article_data = self.storage.get_by_id('knowledge_base', article_id)
        if not article_data:
            return False
        
        if helpful:
            article_data['helpful_count'] = article_data.get('helpful_count', 0) + 1
        else:
            article_data['not_helpful_count'] = article_data.get('not_helpful_count', 0) + 1
        
        article_data['updated_at'] = datetime.now().isoformat()
        self.storage.update('knowledge_base', article_id, article_data)
        return True
    
    def update_article(self, article_id: str, updates: Dict[str, Any],
                      editor: User) -> Optional[KnowledgeBaseArticle]:
        """更新文章"""
        article_data = self.storage.get_by_id('knowledge_base', article_id)
        if not article_data:
            return None
        
        # 权限检查
        if editor.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            if article_data['author_id'] != editor.id:
                raise PermissionError("没有权限修改此文章")
        
        # 保护某些字段
        protected_fields = ['id', 'author_id', 'author_name', 'created_at', 'view_count']
        for field in protected_fields:
            if field in updates:
                del updates[field]
        
        updates['updated_at'] = datetime.now().isoformat()
        article_data.update(updates)
        
        saved_data = self.storage.update('knowledge_base', article_id, article_data)
        return KnowledgeBaseArticle.from_dict(saved_data)
    
    def delete_article(self, article_id: str, deleter: User) -> bool:
        """删除文章"""
        article_data = self.storage.get_by_id('knowledge_base', article_id)
        if not article_data:
            return False
        
        # 权限检查
        if deleter.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            if article_data['author_id'] != deleter.id:
                raise PermissionError("没有权限删除此文章")
        
        return self.storage.delete('knowledge_base', article_id)
    
    def get_related_articles(self, ticket: Ticket) -> List[KnowledgeBaseArticle]:
        """获取与工单相关的推荐文章"""
        # 基于分类和标题关键词搜索
        articles = self.get_published_articles(ticket.category)
        
        # 简单的关键词匹配
        title_keywords = set(ticket.title.lower().split())
        recommended = []
        
        for article in articles:
            article_title_words = set(article.title.lower().split())
            # 计算关键词重叠度
            overlap = len(title_keywords & article_title_words)
            if overlap > 0:
                recommended.append((overlap, article))
        
        # 按相关性排序
        recommended.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in recommended[:5]]


class ReportService:
    """报表服务 - 核心功能4：统计分析与报表"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or get_storage()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        stats = self.storage.get_statistics()
        
        # 计算更多指标
        tickets_data = self.storage.get_all('tickets')
        
        # 今日新增
        today = datetime.now().date()
        today_tickets = sum(1 for t in tickets_data 
                          if datetime.fromisoformat(t['created_at']).date() == today)
        
        # 本周新增
        week_ago = today - timedelta(days=7)
        week_tickets = sum(1 for t in tickets_data 
                         if datetime.fromisoformat(t['created_at']).date() >= week_ago)
        
        # 平均解决时间（小时）
        resolved_tickets = [t for t in tickets_data if t.get('resolved_at')]
        avg_resolution_time = 0
        if resolved_tickets:
            total_hours = 0
            count = 0
            for ticket in resolved_tickets:
                created = datetime.fromisoformat(ticket['created_at'])
                resolved = datetime.fromisoformat(ticket['resolved_at'])
                hours = (resolved - created).total_seconds() / 3600
                total_hours += hours
                count += 1
            avg_resolution_time = total_hours / count if count > 0 else 0
        
        # SLA达成率
        total_active = sum(1 for t in tickets_data 
                         if t['status'] not in [TicketStatus.CLOSED.value, TicketStatus.CANCELLED.value])
        sla_met = total_active - stats['overdue_tickets']
        sla_rate = (sla_met / total_active * 100) if total_active > 0 else 100
        
        # 满意度（基于知识库评价）
        kb_data = self.storage.get_all('knowledge_base')
        total_ratings = sum(a.get('helpful_count', 0) + a.get('not_helpful_count', 0) 
                          for a in kb_data)
        helpful_ratings = sum(a.get('helpful_count', 0) for a in kb_data)
        satisfaction_rate = (helpful_ratings / total_ratings * 100) if total_ratings > 0 else 0
        
        return {
            **stats,
            'today_tickets': today_tickets,
            'week_tickets': week_tickets,
            'avg_resolution_time': round(avg_resolution_time, 2),
            'sla_compliance_rate': round(sla_rate, 2),
            'satisfaction_rate': round(satisfaction_rate, 2)
        }
    
    def get_ticket_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取工单趋势数据"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend_data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            tickets_data = self.storage.get_all('tickets')
            
            created_count = sum(1 for t in tickets_data 
                              if datetime.fromisoformat(t['created_at']).date() == current_date)
            resolved_count = sum(1 for t in tickets_data 
                               if t.get('resolved_at') and 
                               datetime.fromisoformat(t['resolved_at']).date() == current_date)
            
            trend_data.append({
                'date': date_str,
                'created': created_count,
                'resolved': resolved_count
            })
            
            current_date += timedelta(days=1)
        
        return trend_data
    
    def get_category_distribution(self) -> List[Dict[str, Any]]:
        """获取工单分类分布"""
        tickets_data = self.storage.get_all('tickets')
        category_counts = {}
        
        for ticket in tickets_data:
            category = ticket.get('category', 'UNKNOWN')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        result = []
        for category, count in category_counts.items():
            result.append({
                'category': category,
                'count': count,
                'percentage': round(count / len(tickets_data) * 100, 2) if tickets_data else 0
            })
        
        return sorted(result, key=lambda x: x['count'], reverse=True)
    
    def get_priority_distribution(self) -> List[Dict[str, Any]]:
        """获取优先级分布"""
        tickets_data = self.storage.get_all('tickets')
        priority_counts = {}
        
        for ticket in tickets_data:
            priority = ticket.get('priority', 'MEDIUM')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        result = []
        for priority, count in priority_counts.items():
            result.append({
                'priority': priority,
                'count': count,
                'percentage': round(count / len(tickets_data) * 100, 2) if tickets_data else 0
            })
        
        return sorted(result, key=lambda x: x['count'], reverse=True)
    
    def get_agent_performance(self) -> List[Dict[str, Any]]:
        """获取处理人绩效数据"""
        users_data = self.storage.get_all('users')
        tickets_data = self.storage.get_all('tickets')
        
        agent_stats = {}
        
        for ticket in tickets_data:
            assigned_to = ticket.get('assigned_to')
            if not assigned_to:
                continue
            
            if assigned_to not in agent_stats:
                agent_stats[assigned_to] = {
                    'total': 0,
                    'resolved': 0,
                    'in_progress': 0,
                    'overdue': 0
                }
            
            agent_stats[assigned_to]['total'] += 1
            
            if ticket['status'] == TicketStatus.RESOLVED.value:
                agent_stats[assigned_to]['resolved'] += 1
            elif ticket['status'] == TicketStatus.IN_PROGRESS.value:
                agent_stats[assigned_to]['in_progress'] += 1
            
            if ticket.get('sla_breach', False):
                agent_stats[assigned_to]['overdue'] += 1
        
        result = []
        for user_id, stats in agent_stats.items():
            user = next((u for u in users_data if u['id'] == user_id), None)
            if user:
                resolution_rate = (stats['resolved'] / stats['total'] * 100) if stats['total'] > 0 else 0
                result.append({
                    'user_id': user_id,
                    'user_name': user['full_name'],
                    'department': user['department'],
                    'total_tickets': stats['total'],
                    'resolved_tickets': stats['resolved'],
                    'in_progress_tickets': stats['in_progress'],
                    'overdue_tickets': stats['overdue'],
                    'resolution_rate': round(resolution_rate, 2)
                })
        
        return sorted(result, key=lambda x: x['total_tickets'], reverse=True)
    
    def generate_report(self, report_type: str, 
                       start_date: datetime = None,
                       end_date: datetime = None) -> Dict[str, Any]:
        """生成综合报表"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        tickets_data = self.storage.get_all('tickets')
        
        # 日期过滤
        filtered_tickets = []
        for ticket in tickets_data:
            created_at = datetime.fromisoformat(ticket['created_at'])
            if start_date <= created_at <= end_date:
                filtered_tickets.append(ticket)
        
        report = {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_tickets': len(filtered_tickets),
                'resolved_tickets': sum(1 for t in filtered_tickets 
                                       if t['status'] == TicketStatus.RESOLVED.value),
                'pending_tickets': sum(1 for t in filtered_tickets 
                                      if t['status'] in [TicketStatus.SUBMITTED.value, 
                                                        TicketStatus.ASSIGNED.value,
                                                        TicketStatus.IN_PROGRESS.value]),
                'sla_breach_count': sum(1 for t in filtered_tickets 
                                       if t.get('sla_breach', False))
            }
        }
        
        return report
    
    def export_data(self, entity_type: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """导出数据"""
        return self.storage.query(entity_type, filters)


class NotificationService:
    """通知服务 - 核心功能5：消息通知中心"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or get_storage()
    
    def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """获取用户通知"""
        filters = {'user_id': user_id}
        if unread_only:
            filters['is_read'] = False
        
        notifications_data = self.storage.query('notifications', filters)
        return [Notification.from_dict(n) for n in notifications_data]
    
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """标记通知为已读"""
        notification_data = self.storage.get_by_id('notifications', notification_id)
        if not notification_data:
            return False
        
        if notification_data['user_id'] != user_id:
            raise PermissionError("只能标记自己的通知")
        
        notification_data['is_read'] = True
        notification_data['read_at'] = datetime.now().isoformat()
        
        self.storage.update('notifications', notification_id, notification_data)
        return True
    
    def mark_all_as_read(self, user_id: str) -> int:
        """标记所有通知为已读"""
        notifications_data = self.storage.query('notifications', 
                                               {'user_id': user_id, 'is_read': False})
        
        count = 0
        for notification in notifications_data:
            notification['is_read'] = True
            notification['read_at'] = datetime.now().isoformat()
            self.storage.update('notifications', notification['id'], notification)
            count += 1
        
        return count
    
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """删除通知"""
        notification_data = self.storage.get_by_id('notifications', notification_id)
        if not notification_data:
            return False
        
        if notification_data['user_id'] != user_id:
            raise PermissionError("只能删除自己的通知")
        
        return self.storage.delete('notifications', notification_id)
    
    def get_unread_count(self, user_id: str) -> int:
        """获取未读通知数量"""
        return self.storage.count('notifications', {'user_id': user_id, 'is_read': False})
    
    def send_broadcast(self, title: str, message: str, 
                      sender: User, target_roles: List[UserRole] = None) -> int:
        """发送广播通知"""
        users_data = self.storage.get_all('users')
        count = 0
        
        for user_data in users_data:
            if target_roles and user_data.get('role') not in [r.value for r in target_roles]:
                continue
            
            notification_data = {
                'id': str(uuid.uuid4()),
                'user_id': user_data['id'],
                'title': title,
                'message': message,
                'notification_type': 'BROADCAST',
                'related_ticket_id': None,
                'is_read': False,
                'created_at': datetime.now().isoformat(),
                'read_at': None
            }
            self.storage.add('notifications', notification_data)
            count += 1
        
        return count


class SLAService:
    """SLA管理服务 - 核心功能6：SLA配置与监控"""
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or get_storage()
        self._initialize_default_sla_configs()
    
    def _initialize_default_sla_configs(self):
        """初始化默认SLA配置"""
        existing = self.storage.get_all('sla_configs')
        if existing:
            return
        
        defaults = [
            # 紧急优先级
            {'category': 'URGENT', 'priority': '紧急', 'response': 2, 'resolution': 8, 'escalation': 4},
            {'category': 'HIGH', 'priority': '高', 'response': 4, 'resolution': 24, 'escalation': 12},
            {'category': 'MEDIUM', 'priority': '中', 'response': 8, 'resolution': 48, 'escalation': 24},
            {'category': 'LOW', 'priority': '低', 'response': 24, 'resolution': 72, 'escalation': 48},
        ]
        
        for default in defaults:
            for category in TicketCategory:
                config_data = {
                    'id': str(uuid.uuid4()),
                    'category': category.value,
                    'priority': default['priority'],
                    'response_time_hours': default['response'],
                    'resolution_time_hours': default['resolution'],
                    'escalation_time_hours': default['escalation'],
                    'is_active': True
                }
                self.storage.add('sla_configs', config_data)
    
    def get_sla_config(self, category: TicketCategory, priority: TicketPriority) -> Optional[SLAConfiguration]:
        """获取SLA配置"""
        configs_data = self.storage.query('sla_configs', {
            'category': category.value,
            'priority': priority.value,
            'is_active': True
        })
        
        if configs_data:
            return SLAConfiguration.from_dict(configs_data[0])
        return None
    
    def get_all_sla_configs(self) -> List[SLAConfiguration]:
        """获取所有SLA配置"""
        configs_data = self.storage.get_all('sla_configs')
        return [SLAConfiguration.from_dict(c) for c in configs_data]
    
    def create_sla_config(self, category: TicketCategory, priority: TicketPriority,
                         response_time: int, resolution_time: int,
                         escalation_time: int, creator: User) -> SLAConfiguration:
        """创建SLA配置"""
        # 检查是否已存在
        existing = self.get_sla_config(category, priority)
        if existing:
            raise ValueError(f"{category.value} - {priority.value} 的SLA配置已存在")
        
        config_data = {
            'id': str(uuid.uuid4()),
            'category': category.value,
            'priority': priority.value,
            'response_time_hours': response_time,
            'resolution_time_hours': resolution_time,
            'escalation_time_hours': escalation_time,
            'is_active': True
        }
        
        saved_data = self.storage.add('sla_configs', config_data)
        return SLAConfiguration.from_dict(saved_data)
    
    def update_sla_config(self, config_id: str, updates: Dict[str, Any],
                         updater: User) -> Optional[SLAConfiguration]:
        """更新SLA配置"""
        config_data = self.storage.get_by_id('sla_configs', config_id)
        if not config_data:
            return None
        
        # 权限检查
        if updater.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            raise PermissionError("没有权限修改SLA配置")
        
        # 保护某些字段
        protected_fields = ['id', 'category', 'priority']
        for field in protected_fields:
            if field in updates:
                del updates[field]
        
        config_data.update(updates)
        saved_data = self.storage.update('sla_configs', config_id, config_data)
        return SLAConfiguration.from_dict(saved_data)
    
    def deactivate_sla_config(self, config_id: str, updater: User) -> bool:
        """停用SLA配置"""
        config_data = self.storage.get_by_id('sla_configs', config_id)
        if not config_data:
            return False
        
        if updater.role not in [UserRole.ADMIN, UserRole.HR_MANAGER]:
            raise PermissionError("没有权限修改SLA配置")
        
        config_data['is_active'] = False
        self.storage.update('sla_configs', config_id, config_data)
        return True
    
    def get_sla_status(self, ticket_id: str) -> Dict[str, Any]:
        """获取工单SLA状态"""
        ticket_data = self.storage.get_by_id('tickets', ticket_id)
        if not ticket_data:
            return {}
        
        ticket = Ticket.from_dict(ticket_data)
        category = ticket.category
        priority = ticket.priority
        
        sla_config = self.get_sla_config(category, priority)
        if not sla_config:
            return {'error': 'No SLA configuration found'}
        
        elapsed_hours = ticket.get_elapsed_hours()
        remaining_hours = ticket.get_remaining_sla_hours(sla_config)
        is_breached = ticket.is_sla_breached(sla_config)
        
        # 计算各阶段进度
        response_progress = min(100, (elapsed_hours / sla_config.response_time_hours) * 100)
        resolution_progress = min(100, (elapsed_hours / sla_config.resolution_time_hours) * 100)
        escalation_progress = min(100, (elapsed_hours / sla_config.escalation_time_hours) * 100)
        
        return {
            'ticket_id': ticket_id,
            'ticket_number': ticket.ticket_number,
            'category': category.value,
            'priority': priority.value,
            'elapsed_hours': round(elapsed_hours, 2),
            'remaining_hours': round(remaining_hours, 2),
            'is_breached': is_breached,
            'sla_config': {
                'response_time': sla_config.response_time_hours,
                'resolution_time': sla_config.resolution_time_hours,
                'escalation_time': sla_config.escalation_time_hours
            },
            'progress': {
                'response': round(response_progress, 2),
                'resolution': round(resolution_progress, 2),
                'escalation': round(escalation_progress, 2)
            }
        }
    
    def get_sla_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """获取SLA合规报告"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        tickets_data = self.storage.get_all('tickets')
        
        # 过滤日期范围内的工单
        filtered_tickets = []
        for ticket in tickets_data:
            created_at = datetime.fromisoformat(ticket['created_at'])
            if start_date <= created_at <= end_date:
                filtered_tickets.append(ticket)
        
        total = len(filtered_tickets)
        breached = sum(1 for t in filtered_tickets if t.get('sla_breach', False))
        compliant = total - breached
        
        compliance_rate = (compliant / total * 100) if total > 0 else 100
        
        # 按分类统计
        by_category = {}
        for ticket in filtered_tickets:
            category = ticket.get('category', 'UNKNOWN')
            if category not in by_category:
                by_category[category] = {'total': 0, 'breached': 0}
            by_category[category]['total'] += 1
            if ticket.get('sla_breach', False):
                by_category[category]['breached'] += 1
        
        # 按优先级统计
        by_priority = {}
        for ticket in filtered_tickets:
            priority = ticket.get('priority', 'MEDIUM')
            if priority not in by_priority:
                by_priority[priority] = {'total': 0, 'breached': 0}
            by_priority[priority]['total'] += 1
            if ticket.get('sla_breach', False):
                by_priority[priority]['breached'] += 1
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'overall': {
                'total_tickets': total,
                'compliant': compliant,
                'breached': breached,
                'compliance_rate': round(compliance_rate, 2)
            },
            'by_category': {
                cat: {
                    **data,
                    'compliance_rate': round((data['total'] - data['breached']) / data['total'] * 100, 2) 
                                      if data['total'] > 0 else 100
                }
                for cat, data in by_category.items()
            },
            'by_priority': {
                pri: {
                    **data,
                    'compliance_rate': round((data['total'] - data['breached']) / data['total'] * 100, 2)
                                      if data['total'] > 0 else 100
                }
                for pri, data in by_priority.items()
            }
        }
