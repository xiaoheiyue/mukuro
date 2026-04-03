"""
人力资源共享服务中心工单处理系统 - 数据存储层
提供本地JSON文件存储功能
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Generic
from pathlib import Path

from models import (
    Ticket, TicketStatus, TicketPriority, TicketCategory,
    User, UserRole, TicketComment, TicketAttachment,
    TicketHistory, SLAConfiguration, KnowledgeBaseArticle,
    Notification, ReportConfig
)

T = TypeVar('T')


class DataStorage:
    """数据存储服务类"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义各实体的存储文件路径
        self.files = {
            'tickets': self.data_dir / 'tickets.json',
            'users': self.data_dir / 'users.json',
            'comments': self.data_dir / 'comments.json',
            'attachments': self.data_dir / 'attachments.json',
            'histories': self.data_dir / 'histories.json',
            'sla_configs': self.data_dir / 'sla_configs.json',
            'knowledge_base': self.data_dir / 'knowledge_base.json',
            'notifications': self.data_dir / 'notifications.json',
            'report_configs': self.data_dir / 'report_configs.json'
        }
        
        # 初始化数据文件
        self._initialize_files()
        
        # 内存缓存
        self._cache: Dict[str, List[Dict]] = {}
        self._load_all_data()
    
    def _initialize_files(self):
        """初始化所有数据文件"""
        for file_path in self.files.values():
            if not file_path.exists():
                self._write_file(file_path, [])
    
    def _load_all_data(self):
        """加载所有数据到缓存"""
        for key, file_path in self.files.items():
            self._cache[key] = self._read_file(file_path)
    
    def _read_file(self, file_path: Path) -> List[Dict]:
        """从文件读取数据"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return []
    
    def _write_file(self, file_path: Path, data: List[Dict]):
        """写入数据到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
    
    def _save_file(self, key: str):
        """保存指定类型的数据到文件"""
        if key in self._cache:
            self._write_file(self.files[key], self._cache[key])
    
    def get_all(self, entity_type: str) -> List[Dict]:
        """获取所有指定类型的实体"""
        return self._cache.get(entity_type, []).copy()
    
    def get_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict]:
        """根据ID获取实体"""
        for item in self._cache.get(entity_type, []):
            if item.get('id') == entity_id:
                return item.copy()
        return None
    
    def add(self, entity_type: str, data: Dict) -> Dict:
        """添加新实体"""
        if entity_type not in self._cache:
            self._cache[entity_type] = []
        
        # 确保有id字段
        if 'id' not in data:
            import uuid
            data['id'] = str(uuid.uuid4())
        
        self._cache[entity_type].append(data)
        self._save_file(entity_type)
        return data.copy()
    
    def update(self, entity_type: str, entity_id: str, data: Dict) -> Optional[Dict]:
        """更新实体"""
        items = self._cache.get(entity_type, [])
        for i, item in enumerate(items):
            if item.get('id') == entity_id:
                # 保留原有ID
                data['id'] = entity_id
                # 更新时间戳
                if 'updated_at' in item:
                    data['updated_at'] = datetime.now().isoformat()
                items[i] = data
                self._save_file(entity_type)
                return data.copy()
        return None
    
    def delete(self, entity_type: str, entity_id: str) -> bool:
        """删除实体"""
        items = self._cache.get(entity_type, [])
        original_len = len(items)
        self._cache[entity_type] = [item for item in items if item.get('id') != entity_id]
        
        if len(self._cache[entity_type]) < original_len:
            self._save_file(entity_type)
            return True
        return False
    
    def query(self, entity_type: str, filters: Dict[str, Any] = None) -> List[Dict]:
        """查询实体，支持过滤条件"""
        items = self._cache.get(entity_type, [])
        
        if not filters:
            return [item.copy() for item in items]
        
        result = []
        for item in items:
            match = True
            for key, value in filters.items():
                if key not in item:
                    match = False
                    break
                if isinstance(value, list):
                    if item[key] not in value:
                        match = False
                        break
                elif item[key] != value:
                    match = False
                    break
            if match:
                result.append(item.copy())
        
        return result
    
    def search(self, entity_type: str, search_term: str, fields: List[str] = None) -> List[Dict]:
        """搜索实体，在指定字段中查找包含搜索词的记录"""
        items = self._cache.get(entity_type, [])
        
        if not fields:
            # 默认搜索常用字段
            fields = ['title', 'description', 'ticket_number']
        
        result = []
        search_term_lower = search_term.lower()
        
        for item in items:
            for field in fields:
                if field in item:
                    value = str(item[field]).lower()
                    if search_term_lower in value:
                        result.append(item.copy())
                        break
        
        return result
    
    def count(self, entity_type: str, filters: Dict[str, Any] = None) -> int:
        """统计实体数量"""
        return len(self.query(entity_type, filters))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计数据"""
        tickets = self._cache.get('tickets', [])
        users = self._cache.get('users', [])
        
        status_counts = {}
        category_counts = {}
        priority_counts = {}
        
        for ticket in tickets:
            status = ticket.get('status', 'UNKNOWN')
            category = ticket.get('category', 'UNKNOWN')
            priority = ticket.get('priority', 'MEDIUM')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            'total_tickets': len(tickets),
            'total_users': len(users),
            'tickets_by_status': status_counts,
            'tickets_by_category': category_counts,
            'tickets_by_priority': priority_counts,
            'open_tickets': sum(1 for t in tickets if t.get('status') not in ['CLOSED', 'CANCELLED', 'RESOLVED']),
            'overdue_tickets': sum(1 for t in tickets if t.get('sla_breach', False))
        }


# 全局存储实例
_storage_instance: Optional[DataStorage] = None


def get_storage(data_dir: str = "data") -> DataStorage:
    """获取全局存储实例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = DataStorage(data_dir)
    return _storage_instance
