"""
仪表板页面 - Dashboard Page
显示系统整体运行状态和统计数据
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QGroupBox,
    QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush

import logging
from typing import Dict, Any
from datetime import datetime

from core.database import DatabaseManager


class DashboardPage(QWidget):
    """仪表板页面类"""
    
    def __init__(self, db_manager: DatabaseManager, logger: logging.Logger, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.logger = logger
        
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 内容部件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📊 系统概览")
        title_label.setObjectName("dashboardTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        content_layout.addWidget(title_label)
        
        # 统计卡片区域
        stats_group = QGroupBox("📈 实时统计")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(10)
        
        # 创建统计卡片
        self.stat_cards = {}
        stat_items = [
            ("total_boilers", "锅炉总数", "🔥", "#2196F3"),
            ("running_boilers", "运行中", "▶️", "#4CAF50"),
            ("active_alarms", "活动报警", "🚨", "#F44336"),
            ("cleaning_progress", "清洗进度", "🧹", "#FF9800"),
            ("pending_maintenance", "待维护", "🔧", "#9C27B0"),
            ("low_stock_chemicals", "低库存化学品", "🧪", "#795548"),
            ("online_sensors", "在线传感器", "📡", "#00BCD4"),
            ("shift_status", "值班状态", "👷", "#607D8B"),
        ]
        
        for i, (key, title, icon, color) in enumerate(stat_items):
            card = self._create_stat_card(title, icon, color)
            row = i // 4
            col = i % 4
            stats_layout.addWidget(card, row, col)
            self.stat_cards[key] = card
        
        content_layout.addWidget(stats_group)
        
        # 锅炉状态区域
        boiler_group = QGroupBox("🔥 锅炉状态")
        boiler_layout = QVBoxLayout(boiler_group)
        
        self.boiler_status_frame = QFrame()
        self.boiler_status_layout = QHBoxLayout(self.boiler_status_frame)
        self.boiler_status_layout.setSpacing(10)
        boiler_layout.addWidget(self.boiler_status_frame)
        
        content_layout.addWidget(boiler_group)
        
        # 最近报警区域
        alarm_group = QGroupBox("🚨 最近报警")
        alarm_layout = QVBoxLayout(alarm_group)
        
        self.alarm_list_frame = QFrame()
        self.alarm_list_layout = QVBoxLayout(self.alarm_list_frame)
        alarm_layout.addWidget(self.alarm_list_frame)
        
        content_layout.addWidget(alarm_group)
        
        # 快速操作区域
        quick_action_group = QGroupBox("⚡ 快速操作")
        quick_action_layout = QHBoxLayout(quick_action_group)
        
        quick_actions = [
            ("🔍 查看锅炉", "boilers"),
            ("🧹 开始清洗", "cleaning"),
            ("🚨 报警管理", "alarms"),
            ("📋 生成报告", "reports"),
            ("🔧 维护计划", "maintenance"),
        ]
        
        for text, page_key in quick_actions:
            btn = QPushButton(text)
            btn.setObjectName("quickActionButton")
            btn.setFixedHeight(40)
            # btn.clicked.connect(lambda checked, k=page_key: self._navigate_to(k))
            quick_action_layout.addWidget(btn)
        
        content_layout.addWidget(quick_action_group)
        
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self._apply_styles()
    
    def _create_stat_card(self, title: str, icon: str, color: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setObjectName("statCard")
        card.setFixedHeight(100)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 图标和标题
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("statCardTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel("--")
        value_label.setObjectName("statCardValue")
        value_font = QFont("Microsoft YaHei", 24, QFont.Weight.Bold)
        value_label.setFont(value_font)
        layout.addWidget(value_label)
        
        # 存储引用以便更新
        card.value_label = value_label
        card.color = color
        
        return card
    
    def _apply_styles(self):
        """应用样式"""
        stylesheet = """
        QLabel#dashboardTitle {
            color: #1976D2;
            padding: 10px;
            background-color: #E3F2FD;
            border-radius: 5px;
        }
        
        QGroupBox {
            font-weight: bold;
            font-size: 14px;
            border: 1px solid #BDBDBD;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        #statCard {
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
        }
        
        #statCard:hover {
            border: 1px solid #1976D2;
            background-color: #E3F2FD;
        }
        
        #statCardTitle {
            font-size: 14px;
            color: #757575;
        }
        
        #statCardValue {
            color: #212121;
        }
        
        #quickActionButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-weight: bold;
        }
        
        #quickActionButton:hover {
            background-color: #1976D2;
        }
        
        #quickActionButton:pressed {
            background-color: #0D47A1;
        }
        
        .alarm-item {
            background-color: #FFEBEE;
            border-left: 4px solid #F44336;
            padding: 10px;
            margin: 5px;
            border-radius: 3px;
        }
        
        .alarm-item.warning {
            background-color: #FFF3E0;
            border-left: 4px solid #FF9800;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            # 获取统计数据
            stats = self.db_manager.get_statistics()
            
            # 更新统计卡片
            if 'boilers' in stats:
                self._update_stat_card('total_boilers', str(stats['boilers'].get('total', 0)))
                self._update_stat_card('running_boilers', str(stats['boilers'].get('running', 0)))
            
            if 'alarms_24h' in stats:
                self._update_stat_card('active_alarms', str(stats['alarms_24h'].get('unacknowledged', 0)))
            
            if 'cleanings_7d' in stats:
                running = stats['cleanings_7d'].get('running', 0)
                total = stats['cleanings_7d'].get('total', 1)
                progress = int((running / max(total, 1)) * 100)
                self._update_stat_card('cleaning_progress', f"{progress}%")
            
            if 'users' in stats:
                total_users = stats['users'].get('total', 0)
                self._update_stat_card('shift_status', f"{total_users}人")
            
            # 更新锅炉状态
            self._update_boiler_statuses()
            
            # 更新报警列表
            self._update_alarm_list()
            
        except Exception as e:
            self.logger.error(f"刷新仪表板数据失败：{e}")
    
    def _update_stat_card(self, key: str, value: str):
        """更新统计卡片数值"""
        if key in self.stat_cards:
            self.stat_cards[key].value_label.setText(value)
    
    def _update_boiler_statuses(self):
        """更新锅炉状态显示"""
        # 清除现有部件
        while self.boiler_status_layout.count():
            item = self.boiler_status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取所有锅炉
        boilers = self.db_manager.get_all_boilers()
        
        if not boilers:
            label = QLabel("暂无锅炉数据")
            label.setStyleSheet("color: #999; padding: 20px;")
            self.boiler_status_layout.addWidget(label)
            return
        
        for boiler in boilers:
            status_widget = self._create_boiler_status_widget(boiler)
            self.boiler_status_layout.addWidget(status_widget)
    
    def _create_boiler_status_widget(self, boiler: Dict) -> QFrame:
        """创建锅炉状态部件"""
        widget = QFrame()
        widget.setFixedWidth(200)
        widget.setFixedHeight(80)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 锅炉名称
        name_label = QLabel(boiler.get('name', '未知'))
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # 状态
        status = boiler.get('status', 'offline')
        status_colors = {
            'running': '#4CAF50',
            'offline': '#9E9E9E',
            'maintenance': '#FF9800',
            'fault': '#F44336',
        }
        status_texts = {
            'running': '🟢 运行中',
            'offline': '⚫ 离线',
            'maintenance': '🟠 维护中',
            'fault': '🔴 故障',
        }
        
        status_label = QLabel(status_texts.get(status, '⚫ 未知'))
        status_label.setStyleSheet(f"color: {status_colors.get(status, '#999')};")
        layout.addWidget(status_label)
        
        return widget
    
    def _update_alarm_list(self):
        """更新报警列表"""
        # 清除现有部件
        while self.alarm_list_layout.count():
            item = self.alarm_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取最近的报警
        alarms = self.db_manager.get_alarm_history(limit=5)
        
        if not alarms:
            label = QLabel("暂无报警记录")
            label.setStyleSheet("color: #999; padding: 20px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.alarm_list_layout.addWidget(label)
            return
        
        for alarm in alarms:
            alarm_widget = self._create_alarm_widget(alarm)
            self.alarm_list_layout.addWidget(alarm_widget)
    
    def _create_alarm_widget(self, alarm: Dict) -> QFrame:
        """创建报警部件"""
        widget = QFrame()
        widget.setFixedHeight(60)
        
        is_acknowledged = alarm.get('is_acknowledged', False)
        alarm_level = alarm.get('alarm_level', 'warning')
        
        if is_acknowledged:
            widget.setStyleSheet("""
                QFrame {
                    background-color: #EEEEEE;
                    border-left: 4px solid #9E9E9E;
                    padding: 10px;
                    margin: 5px;
                    border-radius: 3px;
                }
            """)
        elif alarm_level == 'critical':
            widget.setStyleSheet("""
                QFrame {
                    background-color: #FFEBEE;
                    border-left: 4px solid #F44336;
                    padding: 10px;
                    margin: 5px;
                    border-radius: 3px;
                }
            """)
        else:
            widget.setStyleSheet("""
                QFrame {
                    background-color: #FFF3E0;
                    border-left: 4px solid #FF9800;
                    padding: 10px;
                    margin: 5px;
                    border-radius: 3px;
                }
            """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # 报警类型和时间
        top_layout = QHBoxLayout()
        type_label = QLabel(f"🚨 {alarm.get('alarm_type', '未知')}")
        type_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        top_layout.addWidget(type_label)
        
        time_label = QLabel(alarm.get('created_at', '')[:16])
        time_label.setStyleSheet("color: #999; font-size: 12px;")
        top_layout.addStretch()
        top_layout.addWidget(time_label)
        
        layout.addLayout(top_layout)
        
        # 报警消息
        msg_label = QLabel(alarm.get('message', ''))
        msg_label.setStyleSheet("color: #666;")
        layout.addWidget(msg_label)
        
        return widget
