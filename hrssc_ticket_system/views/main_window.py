"""
人力资源共享服务中心工单处理系统 - PyQt6 视图层
主窗口和核心界面组件
"""

import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar, QLabel,
    QPushButton, QFrame, QSplitter, QTabWidget, QMessageBox,
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit, QCheckBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QTreeView, QGroupBox, QScrollArea, QSizePolicy,
    QProgressBar, QSystemTrayIcon, QMenu as QContextMenu, QActionGroup
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QDate, QTime, QModelIndex, QSortFilterProxyModel
)
from PyQt6.QtGui import (
    QIcon, QFont, QColor, QPalette, QBrush, QPixmap, QPainter,
    QLinearGradient, QPen, QAction as QtGuiAction
)

from models import (
    Ticket, TicketStatus, TicketPriority, TicketCategory,
    User, UserRole, TicketComment, KnowledgeBaseArticle, Notification
)
from controllers.services import (
    TicketService, UserService, KnowledgeBaseService,
    ReportService, NotificationService, SLAService
)
from utils.storage import get_storage


class CustomTitleBar(QWidget):
    """自定义标题栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 应用图标和标题
        self.icon_label = QLabel("🎫")
        self.icon_label.setFont(QFont("Arial", 16))
        
        self.title_label = QLabel("人力资源共享服务中心工单处理系统")
        self.title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        
        # 最小化、最大化、关闭按钮
        self.min_button = QPushButton("─")
        self.min_button.setFixedSize(30, 30)
        self.min_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
        """)
        
        self.max_button = QPushButton("□")
        self.max_button.setFixedSize(30, 30)
        self.max_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
        """)
        
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e81123;
                border-radius: 15px;
            }
        """)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.close_button)
        
        self.setStyleSheet("""
            CustomTitleBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3a8a, stop:1 #3b82f6);
            }
        """)


class NavigationPanel(QFrame):
    """左侧导航面板"""
    
    navigation_changed = pyqtSignal(str)  # 发送页面切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = "dashboard"
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 用户信息区域
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-bottom: 1px solid #334155;
            }
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(15, 20, 15, 20)
        
        self.user_avatar = QLabel("👤")
        self.user_avatar.setFont(QFont("Arial", 32))
        self.user_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_avatar.setStyleSheet("color: #94a3b8;")
        
        self.user_name_label = QLabel("用户")
        self.user_name_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.user_name_label.setStyleSheet("color: #ffffff;")
        self.user_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.user_role_label = QLabel("角色")
        self.user_role_label.setFont(QFont("Microsoft YaHei", 9))
        self.user_role_label.setStyleSheet("color: #64748b;")
        self.user_role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        user_layout.addWidget(self.user_avatar)
        user_layout.addWidget(self.user_name_label)
        user_layout.addWidget(self.user_role_label)
        
        layout.addWidget(user_frame)
        
        # 导航菜单
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 6px;
                background-color: #1e293b;
            }
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 3px;
            }
        """)
        
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 10, 0, 10)
        nav_layout.setSpacing(5)
        
        # 导航按钮配置
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊", "仪表盘"),
            ("tickets", "🎫", "工单管理"),
            ("create_ticket", "➕", "创建工单"),
            ("knowledge", "📚", "知识库"),
            ("reports", "📈", "统计报表"),
            ("notifications", "🔔", "消息中心"),
            ("admin", "⚙️", "系统管理"),
        ]
        
        for page_id, icon, text in nav_items:
            btn = self.create_nav_button(icon, text, page_id)
            self.nav_buttons[page_id] = btn
            nav_layout.addWidget(btn)
        
        scroll.setWidget(nav_widget)
        layout.addWidget(scroll)
        
        # 底部信息
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-top: 1px solid #334155;
            }
        """)
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(15, 10, 15, 10)
        
        self.version_label = QLabel("版本 1.0.0")
        self.version_label.setFont(QFont("Microsoft YaHei", 8))
        self.version_label.setStyleSheet("color: #64748b;")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        bottom_layout.addWidget(self.version_label)
        layout.addWidget(bottom_frame)
        
        # 默认选中仪表盘
        self.select_page("dashboard")
    
    def create_nav_button(self, icon: str, text: str, page_id: str) -> QPushButton:
        """创建导航按钮"""
        btn = QPushButton(f"{icon}  {text}")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #94a3b8;
                border: none;
                text-align: left;
                padding-left: 25px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
            }}
            QPushButton:hover {{
                background-color: #334155;
                color: #ffffff;
            }}
            QPushButton:selected {{
                background-color: #3b82f6;
                color: #ffffff;
            }}
        """)
        
        btn.clicked.connect(lambda: self.select_page(page_id))
        return btn
    
    def select_page(self, page_id: str):
        """选择页面"""
        if self.current_page == page_id:
            return
        
        self.current_page = page_id
        
        # 更新所有按钮样式
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: #ffffff;
                        border: none;
                        text-align: left;
                        padding-left: 25px;
                        font-size: 13px;
                        font-family: "Microsoft YaHei";
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: none;
                        text-align: left;
                        padding-left: 25px;
                        font-size: 13px;
                        font-family: "Microsoft YaHei";
                    }
                    QPushButton:hover {
                        background-color: #334155;
                        color: #ffffff;
                    }
                """)
        
        self.navigation_changed.emit(page_id)
    
    def set_user_info(self, user: User):
        """设置用户信息"""
        self.user_name_label.setText(user.full_name)
        self.user_role_label.setText(user.role.value)


class DashboardWidget(QWidget):
    """仪表盘组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ticket_service = TicketService()
        self.report_service = ReportService()
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("工作台概览")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1e293b;")
        layout.addWidget(title_label)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.stat_cards = {}
        stat_configs = [
            ("total_tickets", "总工单数", "🎫", "#3b82f6"),
            ("open_tickets", "待处理", "⏳", "#f59e0b"),
            ("in_progress", "处理中", "🔄", "#8b5cf6"),
            ("overdue", "已超时", "⚠️", "#ef4444"),
        ]
        
        for key, label, icon, color in stat_configs:
            card = self.create_stat_card(label, icon, color)
            self.stat_cards[key] = {"card": card, "value_label": card.findChild(QLabel, "value")}
            stats_layout.addWidget(card)
        
        layout.addLayout(stats_layout)
        
        # 图表和列表区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：工单趋势图（简化为统计信息）
        trend_group = QGroupBox("工单趋势")
        trend_layout = QVBoxLayout(trend_group)
        
        self.trend_chart = QLabel("工单趋势图表区域\n（实际项目中可集成 matplotlib 或 pyqtgraph）")
        self.trend_chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trend_chart.setStyleSheet("""
            QLabel {
                background-color: #f1f5f9;
                border-radius: 8px;
                padding: 20px;
                color: #64748b;
            }
        """)
        trend_layout.addWidget(self.trend_chart)
        
        content_splitter.addWidget(trend_group)
        
        # 右侧：最近工单
        recent_group = QGroupBox("最近工单")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_tickets_table = QTableWidget()
        self.recent_tickets_table.setColumnCount(4)
        self.recent_tickets_table.setHorizontalHeaderLabels(["工单号", "标题", "状态", "优先级"])
        self.recent_tickets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recent_tickets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.recent_tickets_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_tickets_table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #475569;
            }
        """)
        recent_layout.addWidget(self.recent_tickets_table)
        
        content_splitter.addWidget(recent_group)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(content_splitter)
        
        # SLA合规率进度条
        sla_group = QGroupBox("SLA合规情况")
        sla_layout = QVBoxLayout(sla_group)
        
        self.sla_progress = QProgressBar()
        self.sla_progress.setRange(0, 100)
        self.sla_progress.setValue(85)
        self.sla_progress.setFormat("%p%")
        self.sla_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #e2e8f0;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 10px;
            }
        """)
        
        self.sla_label = QLabel("SLA合规率：85%")
        self.sla_label.setStyleSheet("color: #64748b; font-size: 12px;")
        
        sla_layout.addWidget(self.sla_label)
        sla_layout.addWidget(self.sla_progress)
        
        layout.addWidget(sla_group)
        
        layout.addStretch()
    
    def create_stat_card(self, title: str, icon: str, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self.lighten_color(color)});
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 28))
        icon_label.setStyleSheet("color: white;")
        
        value_label = QLabel("--")
        value_label.setObjectName("value")
        value_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 11))
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        layout.addWidget(icon_label)
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        layout.addStretch()
        
        return card
    
    def lighten_color(self, color: str) -> str:
        """生成浅色变体（简化版）"""
        return color
    
    def load_data(self):
        """加载数据"""
        try:
            stats = self.report_service.get_dashboard_stats()
            
            # 更新统计卡片
            if "value" in self.stat_cards["total_tickets"]:
                self.stat_cards["total_tickets"]["value"].setText(str(stats.get('total_tickets', 0)))
            self.stat_cards["open_tickets"]["value"].setText(str(stats.get('open_tickets', 0)))
            self.stat_cards["in_progress"]["value"].setText(
                str(stats.get('tickets_by_status', {}).get('处理中', 0)))
            self.stat_cards["overdue"]["value"].setText(str(stats.get('overdue_tickets', 0)))
            
            # 更新SLA进度
            sla_rate = stats.get('sla_compliance_rate', 0)
            self.sla_progress.setValue(int(sla_rate))
            self.sla_label.setText(f"SLA合规率：{sla_rate}%")
            
            # 加载最近工单
            tickets = self.ticket_service.get_tickets()[:5]
            self.recent_tickets_table.setRowCount(len(tickets))
            
            for row, ticket in enumerate(tickets):
                self.recent_tickets_table.setItem(row, 0, QTableWidgetItem(ticket.ticket_number))
                self.recent_tickets_table.setItem(row, 1, QTableWidgetItem(ticket.title[:30] + "..." if len(ticket.title) > 30 else ticket.title))
                
                status_item = QTableWidgetItem(ticket.status.value)
                self.recent_tickets_table.setItem(row, 2, status_item)
                
                priority_item = QTableWidgetItem(ticket.priority.value)
                self.recent_tickets_table.setItem(row, 3, priority_item)
                
                # 根据状态设置颜色
                if ticket.status == TicketStatus.CLOSED:
                    status_item.setForeground(QBrush(QColor("#10b981")))
                elif ticket.status == TicketStatus.IN_PROGRESS:
                    status_item.setForeground(QBrush(QColor("#3b82f6")))
                elif ticket.sla_breach:
                    status_item.setForeground(QBrush(QColor("#ef4444")))
        
        except Exception as e:
            print(f"加载仪表盘数据失败：{e}")


class TicketListWidget(QWidget):
    """工单列表组件"""
    
    ticket_selected = pyqtSignal(str)  # 发送选中的工单ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ticket_service = TicketService()
        self.current_filter = {}
        self.setup_ui()
        self.load_tickets()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工单编号、标题...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        
        # 筛选下拉框
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", None)
        for status in TicketStatus:
            self.status_filter.addItem(status.value, status.value)
        self.status_filter.setFixedWidth(120)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("全部分类", None)
        for category in TicketCategory:
            self.category_filter.addItem(category.value, category.value)
        self.category_filter.setFixedWidth(120)
        self.category_filter.currentIndexChanged.connect(self.apply_filters)
        
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("全部优先级", None)
        for priority in TicketPriority:
            self.priority_filter.addItem(priority.value, priority.value)
        self.priority_filter.setFixedWidth(100)
        self.priority_filter.currentIndexChanged.connect(self.apply_filters)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        refresh_btn.clicked.connect(self.load_tickets)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(QLabel("状态:"))
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(QLabel("分类:"))
        toolbar.addWidget(self.category_filter)
        toolbar.addWidget(QLabel("优先级:"))
        toolbar.addWidget(self.priority_filter)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # 工单表格
        self.tickets_table = QTableWidget()
        self.tickets_table.setColumnCount(7)
        self.tickets_table.setHorizontalHeaderLabels([
            "工单号", "标题", "分类", "优先级", "状态", "申请人", "创建时间"
        ])
        self.tickets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tickets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tickets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tickets_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tickets_table.setAlternatingRowColors(True)
        self.tickets_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #1e293b;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
                color: #475569;
                font-size: 13px;
            }
        """)
        self.tickets_table.doubleClicked.connect(self.on_ticket_double_clicked)
        
        layout.addWidget(self.tickets_table)
        
        # 底部状态栏
        status_bar = QHBoxLayout()
        self.total_label = QLabel("共 0 条记录")
        self.total_label.setStyleSheet("color: #64748b;")
        status_bar.addWidget(self.total_label)
        status_bar.addStretch()
        
        layout.addLayout(status_bar)
    
    def load_tickets(self):
        """加载工单列表"""
        tickets = self.ticket_service.get_tickets(self.current_filter)
        
        self.tickets_table.setRowCount(len(tickets))
        
        for row, ticket in enumerate(tickets):
            self.tickets_table.setItem(row, 0, QTableWidgetItem(ticket.ticket_number))
            self.tickets_table.setItem(row, 1, QTableWidgetItem(ticket.title[:40] + "..." if len(ticket.title) > 40 else ticket.title))
            self.tickets_table.setItem(row, 2, QTableWidgetItem(ticket.category.value))
            
            priority_item = QTableWidgetItem(ticket.priority.value)
            self.tickets_table.setItem(row, 3, priority_item)
            
            status_item = QTableWidgetItem(ticket.status.value)
            self.tickets_table.setItem(row, 4, status_item)
            
            self.tickets_table.setItem(row, 5, QTableWidgetItem(ticket.requester_name))
            
            created_str = ticket.created_at.strftime("%Y-%m-%d %H:%M")
            self.tickets_table.setItem(row, 6, QTableWidgetItem(created_str))
            
            # 设置优先级颜色
            if ticket.priority == TicketPriority.URGENT:
                priority_item.setForeground(QBrush(QColor("#ef4444")))
                priority_item.setBackground(QBrush(QColor("#fee2e2")))
            elif ticket.priority == TicketPriority.HIGH:
                priority_item.setForeground(QBrush(QColor("#f97316")))
            elif ticket.priority == TicketPriority.MEDIUM:
                priority_item.setForeground(QBrush(QColor("#3b82f6")))
            else:
                priority_item.setForeground(QBrush(QColor("#10b981")))
            
            # 设置状态颜色
            if ticket.status == TicketStatus.CLOSED or ticket.status == TicketStatus.RESOLVED:
                status_item.setForeground(QBrush(QColor("#10b981")))
            elif ticket.status == TicketStatus.IN_PROGRESS:
                status_item.setForeground(QBrush(QColor("#3b82f6")))
            elif ticket.sla_breach:
                status_item.setForeground(QBrush(QColor("#ef4444")))
        
        self.total_label.setText(f"共 {len(tickets)} 条记录")
    
    def apply_filters(self):
        """应用筛选条件"""
        self.current_filter = {}
        
        status = self.status_filter.currentData()
        if status:
            self.current_filter['status'] = status
        
        category = self.category_filter.currentData()
        if category:
            self.current_filter['category'] = category
        
        priority = self.priority_filter.currentData()
        if priority:
            self.current_filter['priority'] = priority
        
        self.load_tickets()
    
    def on_search_changed(self, text: str):
        """搜索变更"""
        if len(text) >= 2:
            tickets = self.ticket_service.search_tickets(text)
            self.display_search_results(tickets)
        elif len(text) == 0:
            self.load_tickets()
    
    def display_search_results(self, tickets: List[Ticket]):
        """显示搜索结果"""
        self.tickets_table.setRowCount(len(tickets))
        
        for row, ticket in enumerate(tickets):
            self.tickets_table.setItem(row, 0, QTableWidgetItem(ticket.ticket_number))
            self.tickets_table.setItem(row, 1, QTableWidgetItem(ticket.title[:40] + "..." if len(ticket.title) > 40 else ticket.title))
            self.tickets_table.setItem(row, 2, QTableWidgetItem(ticket.category.value))
            self.tickets_table.setItem(row, 3, QTableWidgetItem(ticket.priority.value))
            self.tickets_table.setItem(row, 4, QTableWidgetItem(ticket.status.value))
            self.tickets_table.setItem(row, 5, QTableWidgetItem(ticket.requester_name))
            self.tickets_table.setItem(row, 6, QTableWidgetItem(ticket.created_at.strftime("%Y-%m-%d %H:%M")))
        
        self.total_label.setText(f"找到 {len(tickets)} 条记录")
    
    def on_ticket_double_clicked(self, index: QModelIndex):
        """双击工单"""
        row = index.row()
        ticket_id_item = self.tickets_table.item(row, 0)
        if ticket_id_item:
            # 通过工单号查找工单
            ticket_number = ticket_id_item.text()
            tickets = self.ticket_service.get_tickets()
            for ticket in tickets:
                if ticket.ticket_number == ticket_number:
                    self.ticket_selected.emit(ticket.id)
                    break


class CreateTicketDialog(QDialog):
    """创建工单对话框"""
    
    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.ticket_service = TicketService()
        self.setWindowTitle("创建新工单")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📝 创建新工单")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1e293b;")
        layout.addWidget(title_label)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # 标题
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("请输入工单标题")
        self.title_input.setStyleSheet(self.get_input_style())
        form_layout.addRow("标题:", self.title_input)
        
        # 分类
        self.category_combo = QComboBox()
        for category in TicketCategory:
            self.category_combo.addItem(category.value, category)
        self.category_combo.setStyleSheet(self.get_input_style())
        form_layout.addRow("分类:", self.category_combo)
        
        # 优先级
        self.priority_combo = QComboBox()
        for priority in TicketPriority:
            self.priority_combo.addItem(priority.value, priority)
        self.priority_combo.setStyleSheet(self.get_input_style())
        form_layout.addRow("优先级:", self.priority_combo)
        
        # 描述
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请详细描述您的问题或需求...")
        self.description_edit.setMinimumHeight(150)
        self.description_edit.setStyleSheet(self.get_input_style())
        form_layout.addRow("描述:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("提交")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("取消")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                color: #475569;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #cbd5e1;
            }
        """)
        
        layout.addWidget(button_box)
    
    def get_input_style(self) -> str:
        return """
            QLineEdit, QComboBox, QTextEdit {
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
                font-family: "Microsoft YaHei";
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border-color: #3b82f6;
            }
        """
    
    def on_accept(self):
        """接受按钮点击"""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "警告", "请输入工单标题")
            return
        
        description = self.description_edit.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "警告", "请输入工单描述")
            return
        
        category = self.category_combo.currentData()
        priority = self.priority_combo.currentData()
        
        try:
            ticket = self.ticket_service.create_ticket(
                title=title,
                description=description,
                category=category,
                priority=priority,
                requester=self.current_user
            )
            
            # 自动提交
            self.ticket_service.submit_ticket(ticket.id, self.current_user)
            
            QMessageBox.information(self, "成功", f"工单创建成功！\n工单号：{ticket.ticket_number}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建工单失败：{str(e)}")


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.current_user: Optional[User] = None
        self.ticket_service = TicketService()
        self.user_service = UserService()
        self.setup_ui()
        self.initialize_sample_data()
    
    def setup_ui(self):
        self.setWindowTitle("人力资源共享服务中心工单处理系统")
        self.setMinimumSize(1280, 800)
        
        # 移除默认标题栏（可选，需要配合 FramelessWindowHint）
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航
        self.navigation = NavigationPanel()
        self.navigation.navigation_changed.connect(self.on_navigation_changed)
        main_layout.addWidget(self.navigation)
        
        # 右侧内容区
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 顶部栏
        top_bar = self.create_top_bar()
        content_layout.addWidget(top_bar)
        
        # 页面堆栈
        self.page_stack = QStackedWidget()
        self.page_stack.setStyleSheet("background-color: #f8fafc;")
        
        # 添加各页面
        self.dashboard_page = DashboardWidget()
        self.tickets_page = TicketListWidget()
        self.tickets_page.ticket_selected.connect(self.show_ticket_detail)
        self.knowledge_page = QWidget()  # 知识库页面
        self.reports_page = QWidget()  # 报表页面
        self.notifications_page = QWidget()  # 通知页面
        self.admin_page = QWidget()  # 管理页面
        
        self.page_stack.addWidget(self.dashboard_page)
        self.page_stack.addWidget(self.tickets_page)
        self.page_stack.addWidget(self.create_ticket_placeholder())
        self.page_stack.addWidget(self.knowledge_page)
        self.page_stack.addWidget(self.reports_page)
        self.page_stack.addWidget(self.notifications_page)
        self.page_stack.addWidget(self.admin_page)
        
        content_layout.addWidget(self.page_stack)
        
        main_layout.addWidget(content_widget)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f8fafc;
                color: #64748b;
                border-top: 1px solid #e2e8f0;
            }
        """)
    
    def create_top_bar(self) -> QWidget:
        """创建顶部栏"""
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 当前页面标题
        self.page_title_label = QLabel("仪表盘")
        self.page_title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        self.page_title_label.setStyleSheet("color: #1e293b;")
        layout.addWidget(self.page_title_label)
        
        layout.addStretch()
        
        # 新建工单按钮
        new_ticket_btn = QPushButton("➕ 新建工单")
        new_ticket_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        new_ticket_btn.clicked.connect(self.open_create_ticket_dialog)
        layout.addWidget(new_ticket_btn)
        
        # 通知铃铛
        self.notification_btn = QPushButton("🔔")
        self.notification_btn.setFixedSize(40, 40)
        self.notification_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: none;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.notification_btn.clicked.connect(lambda: self.navigation.select_page("notifications"))
        layout.addWidget(self.notification_btn)
        
        # 用户头像
        self.user_avatar_label = QLabel("👤")
        self.user_avatar_label.setFont(QFont("Arial", 20))
        self.user_avatar_label.setFixedSize(40, 40)
        self.user_avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_avatar_label.setStyleSheet("""
            QLabel {
                background-color: #3b82f6;
                border-radius: 20px;
                color: white;
            }
        """)
        layout.addWidget(self.user_avatar_label)
        
        return top_bar
    
    def create_ticket_placeholder(self) -> QWidget:
        """创建工单占位页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("点击「新建工单」按钮创建新工单")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 16px;
                padding: 50px;
            }
        """)
        layout.addWidget(label)
        
        return widget
    
    def on_navigation_changed(self, page_id: str):
        """导航切换"""
        page_map = {
            "dashboard": 0,
            "tickets": 1,
            "create_ticket": 2,
            "knowledge": 3,
            "reports": 4,
            "notifications": 5,
            "admin": 6
        }
        
        page_titles = {
            "dashboard": "仪表盘",
            "tickets": "工单管理",
            "create_ticket": "创建工单",
            "knowledge": "知识库",
            "reports": "统计报表",
            "notifications": "消息中心",
            "admin": "系统管理"
        }
        
        if page_id in page_map:
            self.page_stack.setCurrentIndex(page_map[page_id])
            self.page_title_label.setText(page_titles.get(page_id, ""))
    
    def open_create_ticket_dialog(self):
        """打开创建工单对话框"""
        if not self.current_user:
            QMessageBox.warning(self, "警告", "请先登录")
            return
        
        dialog = CreateTicketDialog(self.current_user, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 刷新列表
            self.tickets_page.load_tickets()
            # 切换到仪表盘
            self.navigation.select_page("dashboard")
    
    def show_ticket_detail(self, ticket_id: str):
        """显示工单详情"""
        QMessageBox.information(self, "工单详情", f"查看工单详情：{ticket_id}\n（完整功能开发中）")
    
    def initialize_sample_data(self):
        """初始化示例数据"""
        try:
            # 创建示例用户
            users_count = self.user_service.storage.count('users')
            if users_count == 0:
                admin = self.user_service.create_user(
                    username="admin",
                    email="admin@company.com",
                    full_name="系统管理员",
                    department="信息技术部",
                    position="系统管理员",
                    role=UserRole.ADMIN,
                    phone="13800138000"
                )
                
                hr_manager = self.user_service.create_user(
                    username="hr_manager",
                    email="hr.manager@company.com",
                    full_name="张经理",
                    department="人力资源部",
                    position="HR经理",
                    role=UserRole.HR_MANAGER,
                    phone="13800138001"
                )
                
                hr_specialist = self.user_service.create_user(
                    username="hr_specialist",
                    email="hr.specialist@company.com",
                    full_name="李专员",
                    department="人力资源部",
                    position="HR专员",
                    role=UserRole.HR_SPECIALIST,
                    phone="13800138002"
                )
                
                employee = self.user_service.create_user(
                    username="employee",
                    email="employee@company.com",
                    full_name="王员工",
                    department="市场部",
                    position="市场专员",
                    role=UserRole.REQUESTER,
                    phone="13800138003"
                )
                
                # 设置当前用户为管理员
                self.current_user = admin
                self.navigation.set_user_info(admin)
                
                # 创建示例工单
                ticket_service = TicketService()
                
                for i in range(5):
                    categories = list(TicketCategory)
                    priorities = list(TicketPriority)
                    
                    ticket = ticket_service.create_ticket(
                        title=f"示例工单 {i+1} - {categories[i % len(categories)].value}",
                        description=f"这是一个示例工单，用于演示系统功能。\n\n问题描述：\n{i+1}. 需要处理的事项...\n2. 相关背景信息...\n3. 期望的解决方案...",
                        category=categories[i % len(categories)],
                        priority=priorities[i % len(priorities)],
                        requester=employee
                    )
                    
                    # 提交工单
                    ticket_service.submit_ticket(ticket.id, employee)
                    
                    # 分配给HR专员
                    if i < 3:
                        ticket_service.assign_ticket(ticket.id, hr_specialist, hr_manager)
                    
                    # 更新状态
                    if i == 0:
                        ticket_service.update_status(ticket.id, TicketStatus.IN_PROGRESS, hr_specialist)
                    elif i == 1:
                        ticket_service.update_status(ticket.id, TicketStatus.RESOLVED, hr_specialist)
                
                print("示例数据初始化完成")
            else:
                # 加载第一个管理员用户
                admins = self.user_service.get_users_by_role(UserRole.ADMIN)
                if admins:
                    self.current_user = admins[0]
                    self.navigation.set_user_info(self.current_user)
        except Exception as e:
            print(f"初始化示例数据失败：{e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置全局样式
    app.setStyle("Fusion")
    
    # 全局样式表
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8fafc;
        }
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            color: #1e293b;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 6px;
            min-width: 80px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #2563eb;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
