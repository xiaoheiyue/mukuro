"""
仪表盘模块
Dashboard Widget Module
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QGroupBox, QProgressBar, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class DashboardWidget(QWidget):
    """仪表盘组件"""
    
    def __init__(self, db_manager, config, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.config = config
        
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📊 系统仪表盘")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # 状态概览卡片
        status_group = QGroupBox("🖥️ 系统状态概览")
        status_layout = QGridLayout()
        status_layout.setSpacing(15)
        
        # 运行锅炉数量
        self.boiler_count_card = self._create_stat_card("运行锅炉", "0", "台", "#2196F3")
        status_layout.addWidget(self.boiler_count_card, 0, 0)
        
        # 活动报警数
        self.alarm_count_card = self._create_stat_card("活动报警", "0", "个", "#f44336")
        status_layout.addWidget(self.alarm_count_card, 0, 1)
        
        # 今日投药量
        self.dosing_today_card = self._create_stat_card("今日投药", "0", "ml", "#4CAF50")
        status_layout.addWidget(self.dosing_today_card, 0, 2)
        
        # 今日排污次数
        self.blowdown_today_card = self._create_stat_card("今日排污", "0", "次", "#ff9800")
        status_layout.addWidget(self.blowdown_today_card, 0, 3)
        
        status_group.setLayout(status_layout)
        content_layout.addWidget(status_group)
        
        # 实时数据卡片
        realtime_group = QGroupBox("📈 实时数据监控")
        realtime_layout = QGridLayout()
        realtime_layout.setSpacing(15)
        
        # 温度
        self.temp_card = self._create_gauge_card("锅炉温度", "0.0", "°C", 0, 200)
        realtime_layout.addWidget(self.temp_card, 0, 0)
        
        # 压力
        self.pressure_card = self._create_gauge_card("锅炉压力", "0.00", "MPa", 0, 2)
        realtime_layout.addWidget(self.pressure_card, 0, 1)
        
        # 水位
        self.water_level_card = self._create_gauge_card("锅炉水位", "0", "%", 0, 100)
        realtime_layout.addWidget(self.water_level_card, 0, 2)
        
        # pH 值
        self.ph_card = self._create_gauge_card("pH 值", "0.0", "", 0, 14)
        realtime_layout.addWidget(self.ph_card, 1, 0)
        
        # TDS
        self.tds_card = self._create_gauge_card("TDS", "0", "ppm", 0, 5000)
        realtime_layout.addWidget(self.tds_card, 1, 1)
        
        # 除污剂液位
        self.agent_level_card = self._create_gauge_card("除污剂液位", "0", "%", 0, 100)
        realtime_layout.addWidget(self.agent_level_card, 1, 2)
        
        realtime_group.setLayout(realtime_layout)
        content_layout.addWidget(realtime_group)
        
        # 快速操作
        quick_action_group = QGroupBox("⚡ 快速操作")
        quick_action_layout = QHBoxLayout()
        quick_action_layout.setSpacing(10)
        
        self.dosing_btn = QPushButton("💊 启动投药")
        self.dosing_btn.setObjectName("infoButton")
        quick_action_layout.addWidget(self.dosing_btn)
        
        self.blowdown_btn = QPushButton("🚰 手动排污")
        self.blowdown_btn.setObjectName("warningButton")
        quick_action_layout.addWidget(self.blowdown_btn)
        
        self.alarm_btn = QPushButton("🚨 查看报警")
        self.alarm_btn.setObjectName("dangerButton")
        quick_action_layout.addWidget(self.alarm_btn)
        
        self.report_btn = QPushButton("📊 生成报表")
        self.report_btn.setObjectName("infoButton")
        quick_action_layout.addWidget(self.report_btn)
        
        quick_action_group.setLayout(quick_action_layout)
        content_layout.addWidget(quick_action_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
    
    def _create_stat_card(self, title, value, unit, color):
        """创建统计卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666666; font-size: 14px;")
        layout.addWidget(title_label)
        
        value_layout = QHBoxLayout()
        value_label = QLabel(value)
        value_label.setObjectName("valueLabel")
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        value_layout.addWidget(value_label)
        
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #999999; font-size: 14px;")
        value_layout.addWidget(unit_label)
        
        layout.addLayout(value_layout)
        
        # 存储引用以便更新
        card.value_label = value_label
        card.title = title
        
        return card
    
    def _create_gauge_card(self, title, value, unit, min_val, max_val):
        """创建仪表卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666666; font-size: 14px;")
        layout.addWidget(title_label)
        
        # 数值
        value_label = QLabel(f"{value} {unit}")
        value_label.setObjectName("valueLabel")
        value_label.setStyleSheet("color: #2196F3; font-size: 24px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # 进度条
        progress = QProgressBar()
        progress.setMinimum(min_val)
        progress.setMaximum(max_val)
        progress.setValue(0)
        progress.setTextVisible(False)
        progress.setFixedHeight(20)
        layout.addWidget(progress)
        
        # 范围标签
        range_label = QLabel(f"{min_val} - {max_val}")
        range_label.setStyleSheet("color: #999999; font-size: 12px;")
        range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(range_label)
        
        # 存储引用
        card.value_label = value_label
        card.progress = progress
        card.unit = unit
        
        return card
    
    def refresh_data(self):
        """刷新数据"""
        # 获取锅炉数量
        boilers = self.db_manager.get_all_boilers()
        running_count = sum(1 for b in boilers if b.get('status') == 'online')
        self.boiler_count_card.value_label.setText(str(running_count))
        
        # 获取活动报警数
        active_alarms = self.db_manager.get_active_alarms()
        self.alarm_count_card.value_label.setText(str(len(active_alarms)))
        
        # 获取今日统计数据
        from datetime import datetime
        today = datetime.now().date()
        stats = self.db_manager.get_daily_statistics(today)
        
        self.dosing_today_card.value_label.setText(f"{stats.get('total_dosage_ml', 0):.0f}")
        self.blowdown_today_card.value_label.setText(str(stats.get('blowdown_count', 0)))
        
        # 获取最新实时数据
        if boilers:
            latest_data = self.db_manager.get_latest_real_time_data(boilers[0]['id'])
            if latest_data:
                # 更新温度
                temp = latest_data.get('temperature', 0) or 0
                self.temp_card.value_label.setText(f"{temp:.1f} °C")
                self.temp_card.progress.setValue(int(temp))
                
                # 更新压力
                pressure = latest_data.get('pressure', 0) or 0
                self.pressure_card.value_label.setText(f"{pressure:.2f} MPa")
                self.pressure_card.progress.setValue(int(pressure * 50))
                
                # 更新水位
                water_level = latest_data.get('water_level', 0) or 0
                self.water_level_card.value_label.setText(f"{water_level:.0f} %")
                self.water_level_card.progress.setValue(int(water_level))
                
                # 更新 pH 值
                ph = latest_data.get('ph_value', 0) or 0
                self.ph_card.value_label.setText(f"{ph:.1f}")
                self.ph_card.progress.setValue(int(ph * 7))
                
                # 更新 TDS
                tds = latest_data.get('tds_ppm', 0) or 0
                self.tds_card.value_label.setText(f"{tds:.0f} ppm")
                self.tds_card.progress.setValue(min(int(tds), 5000))
                
                # 更新除污剂液位
                agent_level = latest_data.get('cleaning_agent_level', 0) or 0
                self.agent_level_card.value_label.setText(f"{agent_level:.0f} %")
                self.agent_level_card.progress.setValue(int(agent_level))
