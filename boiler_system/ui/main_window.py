"""
主窗口模块 - Main Window Module
系统的主界面窗口
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QToolBar, QStatusBar, QLabel,
    QPushButton, QFrame, QSplitter, QMessageBox,
    QSystemTrayIcon, QMenu, QAction, QProgressBar,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPalette

from typing import Optional, Dict, Any
import logging

from config.settings import Settings
from core.database import DatabaseManager
from models.data_models import (
    BoilerStatus, AlarmLevel, UserRole, DashboardData,
    SystemStatistics, AlarmInfo
)


class MainWindow(QMainWindow):
    """
    主窗口类
    工业锅炉除污处理系统的主界面
    """
    
    # 自定义信号
    emergency_stop_triggered = pyqtSignal()
    user_logged_out = pyqtSignal()
    settings_changed = pyqtSignal()
    
    def __init__(self, settings: Settings, db_manager: DatabaseManager, 
                 logger: logging.Logger, parent=None):
        super().__init__(parent)
        
        self.settings = settings
        self.db_manager = db_manager
        self.logger = logger
        self.current_user = None
        
        # 初始化UI
        self._init_ui()
        self._init_toolbar()
        self._init_statusbar()
        self._init_system_tray()
        
        # 启动数据更新定时器
        self.data_update_timer = QTimer()
        self.data_update_timer.timeout.connect(self._update_data)
        self.data_update_timer.start(self.settings.ui.refresh_rate_ms)
        
        # 启动报警检查定时器
        self.alarm_check_timer = QTimer()
        self.alarm_check_timer.timeout.connect(self._check_alarms)
        self.alarm_check_timer.start(5000)  # 每5秒检查一次
        
        self.logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("工业锅炉除污处理系统 v1.0.0")
        self.setMinimumSize(1280, 720)
        self.resize(1400, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建顶部信息栏
        self._create_top_bar(main_layout)
        
        # 创建主体内容区
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧导航栏
        self._create_navigation_panel(content_splitter)
        
        # 右侧内容区
        self._create_content_area(content_splitter)
        
        main_layout.addWidget(content_splitter)
        
        # 应用样式
        self._apply_styles()
    
    def _create_top_bar(self, layout):
        """创建顶部信息栏"""
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)
        
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)
        
        # 系统标题
        title_label = QLabel("🏭 工业锅炉除污处理系统")
        title_label.setObjectName("systemTitle")
        title_font = QFont("Microsoft YaHei", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        # 当前时间
        self.time_label = QLabel("")
        self.time_label.setObjectName("timeLabel")
        self._update_time()
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)
        top_layout.addWidget(self.time_label)
        
        # 报警指示器
        self.alarm_indicator = QLabel("🔔 0")
        self.alarm_indicator.setObjectName("alarmIndicator")
        self.alarm_indicator.setToolTip("未确认报警数量")
        top_layout.addWidget(self.alarm_indicator)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        top_layout.addWidget(separator)
        
        # 当前用户
        self.user_label = QLabel("👤 未登录")
        self.user_label.setObjectName("userLabel")
        top_layout.addWidget(self.user_label)
        
        # 登出按钮
        logout_btn = QPushButton("登出")
        logout_btn.setObjectName("logoutButton")
        logout_btn.clicked.connect(self._logout)
        top_layout.addWidget(logout_btn)
        
        layout.addWidget(top_bar)
    
    def _create_navigation_panel(self, splitter):
        """创建导航面板"""
        nav_panel = QFrame()
        nav_panel.setObjectName("navigationPanel")
        nav_panel.setFixedWidth(200)
        
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(5, 10, 5, 10)
        nav_layout.setSpacing(5)
        
        # 导航按钮列表
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 仪表板"),
            ("boilers", "🔥 锅炉监控"),
            ("cleaning", "🧹 清洗管理"),
            ("alarms", "🚨 报警管理"),
            ("maintenance", "🔧 维护管理"),
            ("chemicals", "🧪 化学品管理"),
            ("reports", "📋 报告管理"),
            ("users", "👥 用户管理"),
            ("logs", "📝 系统日志"),
            ("settings", "⚙️ 系统设置"),
        ]
        
        for key, text in nav_items:
            btn = QPushButton(text)
            btn.setObjectName(f"navButton_{key}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_clicked(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        nav_layout.addStretch()
        
        # 紧急停止按钮
        self.emergency_stop_btn = QPushButton("🛑 紧急停止")
        self.emergency_stop_btn.setObjectName("emergencyStopButton")
        self.emergency_stop_btn.setFixedHeight(50)
        self.emergency_stop_btn.clicked.connect(self._emergency_stop)
        nav_layout.addWidget(self.emergency_stop_btn)
        
        splitter.addWidget(nav_panel)
    
    def _create_content_area(self, splitter):
        """创建内容区域"""
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 页面堆栈
        self.page_stack = QStackedWidget()
        
        # 导入并创建各个页面
        from ui.pages.dashboard_page import DashboardPage
        from ui.pages.boiler_page import BoilerMonitorPage
        from ui.pages.cleaning_page import CleaningManagementPage
        from ui.pages.alarm_page import AlarmManagementPage
        from ui.pages.maintenance_page import MaintenancePage
        from ui.pages.chemical_page import ChemicalPage
        from ui.pages.report_page import ReportPage
        from ui.pages.user_page import UserPage
        from ui.pages.log_page import LogPage
        from ui.pages.settings_page import SettingsPage
        
        self.pages = {
            'dashboard': DashboardPage(self.db_manager, self.logger),
            'boilers': BoilerMonitorPage(self.db_manager, self.logger),
            'cleaning': CleaningManagementPage(self.db_manager, self.logger),
            'alarms': AlarmManagementPage(self.db_manager, self.logger),
            'maintenance': MaintenancePage(self.db_manager, self.logger),
            'chemicals': ChemicalPage(self.db_manager, self.logger),
            'reports': ReportPage(self.db_manager, self.logger),
            'users': UserPage(self.db_manager, self.logger),
            'logs': LogPage(self.db_manager, self.logger),
            'settings': SettingsPage(self.settings, self.db_manager, self.logger),
        }
        
        for page_key, page_widget in self.pages.items():
            self.page_stack.addWidget(page_widget)
        
        content_layout.addWidget(self.page_stack)
        splitter.addWidget(content_frame)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
    
    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # 添加工具栏动作
        actions = [
            ("dashboard", "📊", "仪表板", lambda: self._switch_page('dashboard')),
            ("boilers", "🔥", "锅炉监控", lambda: self._switch_page('boilers')),
            ("cleaning", "🧹", "清洗管理", lambda: self._switch_page('cleaning')),
            ("alarms", "🚨", "报警管理", lambda: self._switch_page('alarms')),
            ("reports", "📋", "报告管理", lambda: self._switch_page('reports')),
        ]
        
        for action_id, icon, tooltip, callback in actions:
            action = QAction(icon, tooltip, self)
            action.triggered.connect(callback)
            toolbar.addAction(action)
        
        toolbar.addSeparator()
        
        # 帮助动作
        help_action = QAction("❓ 帮助", self)
        help_action.triggered.connect(self._show_help)
        toolbar.addAction(help_action)
        
        # 关于动作
        about_action = QAction("ℹ️ 关于", self)
        about_action.triggered.connect(self._show_about)
        toolbar.addAction(about_action)
    
    def _init_statusbar(self):
        """初始化状态栏"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # 系统状态
        self.status_label = QLabel("✅ 系统正常")
        self.status_label.setObjectName("statusLabel")
        statusbar.addWidget(self.status_label)
        
        statusbar.addPermanentWidget(QLabel("|"))
        
        # 数据库状态
        self.db_status_label = QLabel("🟢 数据库连接正常")
        statusbar.addWidget(self.db_status_label)
        
        statusbar.addPermanentWidget(QLabel("|"))
        
        # 版本信息
        version_label = QLabel("v1.0.0")
        statusbar.addPermanentWidget(version_label)
    
    def _init_system_tray(self):
        """初始化系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("工业锅炉除污处理系统")
        
        # 创建托盘图标（简单颜色图标）
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#4CAF50"))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出系统", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()
    
    def _apply_styles(self):
        """应用样式表"""
        stylesheet = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        #topBar {
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
        }
        
        #systemTitle {
            color: #1976D2;
            padding: 5px;
        }
        
        #timeLabel {
            color: #666666;
            font-size: 14px;
            padding: 5px;
        }
        
        #alarmIndicator {
            color: #F44336;
            font-weight: bold;
            font-size: 14px;
            padding: 5px 10px;
            background-color: #FFEBEE;
            border-radius: 15px;
        }
        
        #userLabel {
            color: #333333;
            font-size: 14px;
            padding: 5px 10px;
        }
        
        #logoutButton {
            background-color: #FF5722;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 4px;
        }
        
        #logoutButton:hover {
            background-color: #E64A19;
        }
        
        #navigationPanel {
            background-color: #263238;
            border-right: 1px solid #37474F;
        }
        
        QPushButton#navButton_dashboard,
        QPushButton#navButton_boilers,
        QPushButton#navButton_cleaning,
        QPushButton#navButton_alarms,
        QPushButton#navButton_maintenance,
        QPushButton#navButton_chemicals,
        QPushButton#navButton_reports,
        QPushButton#navButton_users,
        QPushButton#navButton_logs,
        QPushButton#navButton_settings {
            background-color: transparent;
            color: #B0BEC5;
            text-align: left;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
        }
        
        QPushButton#navButton_dashboard:hover,
        QPushButton#navButton_boilers:hover,
        QPushButton#navButton_cleaning:hover,
        QPushButton#navButton_alarms:hover,
        QPushButton#navButton_maintenance:hover,
        QPushButton#navButton_chemicals:hover,
        QPushButton#navButton_reports:hover,
        QPushButton#navButton_users:hover,
        QPushButton#navButton_logs:hover,
        QPushButton#navButton_settings:hover {
            background-color: #37474F;
            color: #FFFFFF;
        }
        
        QPushButton#navButton_dashboard:checked,
        QPushButton#navButton_boilers:checked,
        QPushButton#navButton_cleaning:checked,
        QPushButton#navButton_alarms:checked,
        QPushButton#navButton_maintenance:checked,
        QPushButton#navButton_chemicals:checked,
        QPushButton#navButton_reports:checked,
        QPushButton#navButton_users:checked,
        QPushButton#navButton_logs:checked,
        QPushButton#navButton_settings:checked {
            background-color: #1976D2;
            color: #FFFFFF;
        }
        
        QPushButton#emergencyStopButton {
            background-color: #D32F2F;
            color: white;
            border: 2px solid #B71C1C;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
        }
        
        QPushButton#emergencyStopButton:hover {
            background-color: #B71C1C;
        }
        
        QPushButton#emergencyStopButton:pressed {
            background-color: #8E0000;
        }
        
        #contentFrame {
            background-color: #ffffff;
        }
        
        #statusLabel {
            color: #2E7D32;
            font-weight: bold;
        }
        """
        
        self.setStyleSheet(stylesheet)
    
    def _on_nav_clicked(self, page_key: str):
        """导航按钮点击处理"""
        # 取消其他按钮的选中状态
        for key, btn in self.nav_buttons.items():
            if key != page_key:
                btn.setChecked(False)
        
        # 切换页面
        self._switch_page(page_key)
    
    def _switch_page(self, page_key: str):
        """切换到指定页面"""
        if page_key in self.pages:
            index = list(self.pages.keys()).index(page_key)
            self.page_stack.setCurrentIndex(index)
            
            # 更新导航按钮状态
            for key, btn in self.nav_buttons.items():
                btn.setChecked(key == page_key)
            
            self.logger.debug(f"切换到页面：{page_key}")
    
    def _update_time(self):
        """更新时间显示"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    def _update_data(self):
        """更新数据"""
        # 更新报警计数
        alarm_count = self.db_manager.get_unacknowledged_alarm_count()
        self.alarm_indicator.setText(f"🔔 {alarm_count}")
        
        if alarm_count > 0:
            self.alarm_indicator.setStyleSheet("""
                QLabel#alarmIndicator {
                    color: #F44336;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 5px 10px;
                    background-color: #FFEBEE;
                    border-radius: 15px;
                }
            """)
        else:
            self.alarm_indicator.setStyleSheet("""
                QLabel#alarmIndicator {
                    color: #4CAF50;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 5px 10px;
                    background-color: #E8F5E9;
                    border-radius: 15px;
                }
            """)
        
        # 更新当前页面的数据
        current_index = self.page_stack.currentIndex()
        current_page = self.page_stack.widget(current_index)
        if hasattr(current_page, 'refresh_data'):
            current_page.refresh_data()
    
    def _check_alarms(self):
        """检查报警"""
        active_alarms = self.db_manager.get_active_alarms()
        
        for alarm in active_alarms:
            if alarm['alarm_level'] in ['critical', 'error']:
                # 显示报警通知
                if self.tray_icon and self.tray_icon.isVisible():
                    self.tray_icon.showMessage(
                        "报警通知",
                        f"{alarm['alarm_type']}: {alarm['message']}",
                        QSystemTrayIcon.MessageIcon.Critical,
                        5000
                    )
                break
    
    def _emergency_stop(self):
        """紧急停止"""
        reply = QMessageBox.critical(
            self,
            "紧急停止确认",
            "确定要执行紧急停止吗？\n\n这将立即停止所有运行中的锅炉和清洗过程！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.warning("用户触发紧急停止")
            self.emergency_stop_triggered.emit()
            
            # 这里应该调用实际的紧急停止逻辑
            QMessageBox.warning(
                self,
                "紧急停止已触发",
                "紧急停止命令已发送，请立即检查现场设备状态！"
            )
    
    def _logout(self):
        """登出"""
        reply = QMessageBox.question(
            self,
            "确认登出",
            "确定要登出系统吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("用户登出")
            self.current_user = None
            self.user_label.setText("👤 未登录")
            self.user_logged_out.emit()
            
            # 切换到仪表板页面
            self._switch_page('dashboard')
    
    def _tray_activated(self, reason):
        """系统托盘激活处理"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
        <h2>工业锅炉除污处理系统 - 使用帮助</h2>
        
        <h3>主要功能：</h3>
        <ul>
            <li><b>仪表板</b> - 查看系统整体运行状态和统计数据</li>
            <li><b>锅炉监控</b> - 实时监控锅炉运行参数</li>
            <li><b>清洗管理</b> - 管理和执行锅炉清洗流程</li>
            <li><b>报警管理</b> - 查看和处理系统报警</li>
            <li><b>维护管理</b> - 制定和执行设备维护计划</li>
            <li><b>化学品管理</b> - 管理清洗化学品的库存和使用</li>
            <li><b>报告管理</b> - 生成和查看各类运行报告</li>
            <li><b>用户管理</b> - 管理系统用户和权限</li>
            <li><b>系统日志</b> - 查看系统操作日志</li>
            <li><b>系统设置</b> - 配置系统参数</li>
        </ul>
        
        <h3>快捷键：</h3>
        <ul>
            <li>F1 - 打开帮助</li>
            <li>Ctrl+Q - 退出系统</li>
            <li>Ctrl+S - 打开系统设置</li>
        </ul>
        
        <h3>技术支持：</h3>
        <p>如有问题，请联系系统管理员。</p>
        """
        
        QMessageBox.information(self, "帮助", help_text)
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>工业锅炉除污处理系统</h2>
        <p>版本：1.0.0</p>
        <p>版权所有 © 2024 IndustrialBoilerCorp</p>
        
        <h3>系统信息：</h3>
        <ul>
            <li>基于 PyQt6 开发</li>
            <li>使用 SQLite 数据库</li>
            <li>支持多锅炉同时监控</li>
            <li>完整的清洗流程管理</li>
            <li>实时报警和通知</li>
        </ul>
        
        <p>本系统用于工业锅炉的除污处理监控和管理，
        提供全面的锅炉运行监控、清洗流程控制、
        报警管理、维护计划等功能。</p>
        """
        
        QMessageBox.about(self, "关于", about_text)
    
    def set_current_user(self, user_info: dict):
        """设置当前用户"""
        self.current_user = user_info
        if user_info:
            display_name = user_info.get('real_name') or user_info.get('username', '未知用户')
            self.user_label.setText(f"👤 {display_name}")
            self.logger.info(f"用户登录：{display_name}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出系统吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止定时器
            self.data_update_timer.stop()
            self.alarm_check_timer.stop()
            self.time_timer.stop()
            
            self.logger.info("系统关闭")
            event.accept()
        else:
            event.ignore()
