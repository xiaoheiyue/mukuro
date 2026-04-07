"""
主窗口模块
Main Window Module

提供系统的主界面，包含菜单栏、工具栏、状态栏和主要内容区域
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar, QLabel,
    QTabWidget, QFrame, QGroupBox, QPushButton, QMessageBox,
    QSystemTrayIcon, QMenu as QContextMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPalette

from views.dashboard_widget import DashboardWidget
from views.monitoring_widget import MonitoringWidget
from views.dosing_control_widget import DosingControlWidget
from views.blowdown_control_widget import BlowdownControlWidget
from views.water_analysis_widget import WaterAnalysisWidget
from views.alarm_widget import AlarmWidget
from views.history_widget import HistoryWidget
from views.report_widget import ReportWidget
from views.settings_widget import SettingsWidget
from views.login_dialog import LoginDialog

from models.database import DatabaseManager
from utils.config import Config
from utils.logger import get_logger


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号
    user_logged_in = dict
    user_logged_out = pyqtSignal()
    data_refresh_requested = pyqtSignal()
    
    def __init__(self, db_manager: DatabaseManager, config: Config, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.config = config
        self.logger = get_logger()
        self.current_user = None
        
        # 定时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.on_refresh_timeout)
        
        # 初始化 UI
        self._init_ui()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_system_tray()
        
        # 显示登录对话框
        self._show_login_dialog()
        
        self.logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("工业锅炉除污处理系统 V1.0")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # 设置样式表
        self._apply_stylesheet()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        
        # 添加各个功能页面
        self._add_tabs()
        
        main_layout.addWidget(self.tab_widget)
        
        # 启动刷新定时器
        self.refresh_timer.start(self.config.refresh_interval)
    
    def _apply_stylesheet(self):
        """应用样式表"""
        stylesheet = """
        QMainWindow {
            background-color: #f0f0f0;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: white;
            border-radius: 3px;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            border: 1px solid #cccccc;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 8px 16px;
            margin-right: 2px;
            min-width: 100px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 1px solid white;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #f0f0f0;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
        }
        
        QPushButton#dangerButton {
            background-color: #f44336;
        }
        
        QPushButton#dangerButton:hover {
            background-color: #da190b;
        }
        
        QPushButton#warningButton {
            background-color: #ff9800;
        }
        
        QPushButton#warningButton:hover {
            background-color: #e68a00;
        }
        
        QPushButton#infoButton {
            background-color: #2196F3;
        }
        
        QPushButton#infoButton:hover {
            background-color: #1976D2;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QComboBox {
            padding: 5px;
            border: 1px solid #cccccc;
            border-radius: 3px;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border: 1px solid #999999;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
            padding: 5px;
            border: 1px solid #cccccc;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #2196F3;
        }
        
        QTableWidget {
            border: 1px solid #cccccc;
            border-radius: 3px;
            gridline-color: #e0e0e0;
        }
        
        QTableWidget::item {
            padding: 5px;
        }
        
        QTableWidget::item:selected {
            background-color: #2196F3;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 5px;
            border: 1px solid #cccccc;
            font-weight: bold;
        }
        
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 3px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
        
        QLabel#titleLabel {
            font-size: 18px;
            font-weight: bold;
            color: #333333;
        }
        
        QLabel#valueLabel {
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
        }
        
        QLabel#alarmLabel {
            font-size: 16px;
            font-weight: bold;
            color: #f44336;
        }
        
        QStatusBar {
            background-color: #e0e0e0;
            border-top: 1px solid #cccccc;
        }
        
        QStatusBar::item {
            border: none;
        }
        """
        
        self.setStyleSheet(stylesheet)
    
    def _add_tabs(self):
        """添加标签页"""
        # 仪表盘
        self.dashboard_widget = DashboardWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.dashboard_widget, "📊 仪表盘")
        
        # 实时监控
        self.monitoring_widget = MonitoringWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.monitoring_widget, "📈 实时监控")
        
        # 投药控制
        self.dosing_widget = DosingControlWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.dosing_widget, "💊 投药控制")
        
        # 排污控制
        self.blowdown_widget = BlowdownControlWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.blowdown_widget, "🚰 排污控制")
        
        # 水质分析
        self.water_analysis_widget = WaterAnalysisWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.water_analysis_widget, "🧪 水质分析")
        
        # 报警管理
        self.alarm_widget = AlarmWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.alarm_widget, "🚨 报警管理")
        
        # 历史记录
        self.history_widget = HistoryWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.history_widget, "📋 历史记录")
        
        # 报表统计
        self.report_widget = ReportWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.report_widget, "📉 报表统计")
        
        # 系统设置
        self.settings_widget = SettingsWidget(self.db_manager, self.config)
        self.tab_widget.addTab(self.settings_widget, "⚙️ 系统设置")
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件 (&F)")
        
        new_action = QAction("新建 (&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.on_new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开 (&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.on_open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出报表 (&E)", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.on_export_report)
        file_menu.addAction(export_action)
        
        print_action = QAction("打印 (&P)", self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.on_print)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出 (&X)", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑 (&E)")
        
        undo_action = QAction("撤销 (&U)", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.on_undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("重做 (&R)", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.on_redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction("复制 (&C)", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.on_copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("粘贴 (&V)", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.on_paste)
        edit_menu.addAction(paste_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图 (&V)")
        
        refresh_action = QAction("刷新 (&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.on_refresh)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction("全屏 (&F)", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)
        fullscreen_action.toggled.connect(self.on_toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # 控制菜单
        control_menu = menubar.addMenu("控制 (&C)")
        
        start_dosing_action = QAction("启动投药 (&S)", self)
        start_dosing_action.triggered.connect(self.on_start_dosing)
        control_menu.addAction(start_dosing_action)
        
        stop_dosing_action = QAction("停止投药 (&T)", self)
        stop_dosing_action.triggered.connect(self.on_stop_dosing)
        control_menu.addAction(stop_dosing_action)
        
        control_menu.addSeparator()
        
        open_valve_action = QAction("打开排污阀 (&O)", self)
        open_valve_action.triggered.connect(self.on_open_valve)
        control_menu.addAction(open_valve_action)
        
        close_valve_action = QAction("关闭排污阀 (&C)", self)
        close_valve_action.triggered.connect(self.on_close_valve)
        control_menu.addAction(close_valve_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具 (&T)")
        
        calibration_action = QAction("校准传感器 (&C)", self)
        calibration_action.triggered.connect(self.on_calibration)
        tools_menu.addAction(calibration_action)
        
        diagnostic_action = QAction("系统诊断 (&D)", self)
        diagnostic_action.triggered.connect(self.on_diagnostic)
        tools_menu.addAction(diagnostic_action)
        
        tools_menu.addSeparator()
        
        backup_action = QAction("数据备份 (&B)", self)
        backup_action.triggered.connect(self.on_backup_data)
        tools_menu.addAction(backup_action)
        
        restore_action = QAction("数据恢复 (&R)", self)
        restore_action.triggered.connect(self.on_restore_data)
        tools_menu.addAction(restore_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助 (&H)")
        
        help_action = QAction("帮助文档 (&H)", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.on_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("关于 (&A)", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
        # 用户菜单（登录后显示）
        self.user_menu = menubar.addMenu("用户 (&U)")
        self._update_user_menu()
    
    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # 添加常用操作按钮
        refresh_btn = QAction("🔄 刷新", self)
        refresh_btn.triggered.connect(self.on_refresh)
        toolbar.addAction(refresh_btn)
        
        toolbar.addSeparator()
        
        dosing_btn = QAction("💊 投药", self)
        dosing_btn.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addAction(dosing_btn)
        
        blowdown_btn = QAction("🚰 排污", self)
        blowdown_btn.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        toolbar.addAction(blowdown_btn)
        
        alarm_btn = QAction("🚨 报警", self)
        alarm_btn.triggered.connect(lambda: self.tab_widget.setCurrentIndex(5))
        toolbar.addAction(alarm_btn)
        
        toolbar.addSeparator()
        
        report_btn = QAction("📊 报表", self)
        report_btn.triggered.connect(lambda: self.tab_widget.setCurrentIndex(7))
        toolbar.addAction(report_btn)
        
        settings_btn = QAction("⚙️ 设置", self)
        settings_btn.triggered.connect(lambda: self.tab_widget.setCurrentIndex(8))
        toolbar.addAction(settings_btn)
    
    def _create_status_bar(self):
        """创建状态栏"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # 系统状态
        self.status_label = QLabel("系统就绪")
        statusbar.addWidget(self.status_label)
        
        statusbar.addPermanentWidget(QLabel("|"))
        
        # 当前用户
        self.user_label = QLabel("未登录")
        statusbar.addPermanentWidget(self.user_label)
        
        statusbar.addPermanentWidget(QLabel("|"))
        
        # 连接状态
        self.connection_label = QLabel("🟢 在线")
        statusbar.addPermanentWidget(self.connection_label)
        
        statusbar.addPermanentWidget(QLabel("|"))
        
        # 时间显示
        self.time_label = QLabel()
        self.update_time_display()
        statusbar.addPermanentWidget(self.time_label)
        
        # 启动时间更新定时器
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)
    
    def _create_system_tray(self):
        """创建系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("工业锅炉除污处理系统")
        
        # 创建托盘图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#4CAF50"))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # 创建托盘菜单
        tray_menu = QContextMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def _show_login_dialog(self):
        """显示登录对话框"""
        dialog = LoginDialog(self.db_manager, self)
        if dialog.exec() == 1:  # Accepted
            self.current_user = dialog.get_user()
            self._on_login_success()
        else:
            # 用户取消登录，退出程序
            self.close()
    
    def _on_login_success(self):
        """登录成功后的处理"""
        self.logger.info(f"用户 {self.current_user['username']} 登录成功")
        
        # 更新状态栏
        self.user_label.setText(f"👤 {self.current_user['full_name']}")
        self.status_label.setText("系统运行正常")
        
        # 更新用户菜单
        self._update_user_menu()
        
        # 记录登录日志
        self.db_manager.record_login(self.current_user['id'], True)
        self.db_manager.log_operation(
            self.current_user['id'],
            "login",
            "system",
            f"用户登录：{self.current_user['username']}"
        )
    
    def _update_user_menu(self):
        """更新用户菜单"""
        self.user_menu.clear()
        
        if self.current_user:
            profile_action = QAction(f"👤 {self.current_user['full_name']}", self)
            profile_action.setEnabled(False)
            self.user_menu.addAction(profile_action)
            
            self.user_menu.addSeparator()
            
            logout_action = QAction("注销 (&L)", self)
            logout_action.triggered.connect(self.on_logout)
            self.user_menu.addAction(logout_action)
            
            change_password_action = QAction("修改密码 (&P)", self)
            change_password_action.triggered.connect(self.on_change_password)
            self.user_menu.addAction(change_password_action)
        else:
            login_action = QAction("登录 (&L)", self)
            login_action.triggered.connect(self._show_login_dialog)
            self.user_menu.addAction(login_action)
    
    def update_time_display(self):
        """更新时间显示"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"🕐 {current_time}")
    
    def on_refresh_timeout(self):
        """刷新定时器超时处理"""
        # 刷新当前活动页面的数据
        current_index = self.tab_widget.currentIndex()
        widget = self.tab_widget.widget(current_index)
        
        if hasattr(widget, 'refresh_data'):
            widget.refresh_data()
    
    def on_refresh(self):
        """手动刷新"""
        self.logger.debug("手动刷新数据")
        current_index = self.tab_widget.currentIndex()
        widget = self.tab_widget.widget(current_index)
        
        if hasattr(widget, 'refresh_data'):
            widget.refresh_data()
        
        self.status_label.setText("数据已刷新")
    
    def on_new_file(self):
        """新建文件"""
        QMessageBox.information(self, "提示", "新建文件功能开发中...")
    
    def on_open_file(self):
        """打开文件"""
        QMessageBox.information(self, "提示", "打开文件功能开发中...")
    
    def on_export_report(self):
        """导出报表"""
        self.tab_widget.setCurrentIndex(7)  # 切换到报表页面
        if hasattr(self.report_widget, 'export_report'):
            self.report_widget.export_report()
    
    def on_print(self):
        """打印"""
        QMessageBox.information(self, "提示", "打印功能开发中...")
    
    def on_undo(self):
        """撤销"""
        pass
    
    def on_redo(self):
        """重做"""
        pass
    
    def on_copy(self):
        """复制"""
        pass
    
    def on_paste(self):
        """粘贴"""
        pass
    
    def on_toggle_fullscreen(self, checked):
        """切换全屏"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def on_start_dosing(self):
        """启动投药"""
        self.tab_widget.setCurrentIndex(2)
        if hasattr(self.dosing_widget, 'start_dosing'):
            self.dosing_widget.start_dosing()
    
    def on_stop_dosing(self):
        """停止投药"""
        self.tab_widget.setCurrentIndex(2)
        if hasattr(self.dosing_widget, 'stop_dosing'):
            self.dosing_widget.stop_dosing()
    
    def on_open_valve(self):
        """打开排污阀"""
        self.tab_widget.setCurrentIndex(3)
        if hasattr(self.blowdown_widget, 'open_valve'):
            self.blowdown_widget.open_valve()
    
    def on_close_valve(self):
        """关闭排污阀"""
        self.tab_widget.setCurrentIndex(3)
        if hasattr(self.blowdown_widget, 'close_valve'):
            self.blowdown_widget.close_valve()
    
    def on_calibration(self):
        """校准传感器"""
        QMessageBox.information(self, "提示", "传感器校准功能开发中...")
    
    def on_diagnostic(self):
        """系统诊断"""
        QMessageBox.information(self, "提示", "系统诊断功能开发中...")
    
    def on_backup_data(self):
        """数据备份"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要备份当前数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from datetime import datetime
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.db_manager.backup_database(backup_path):
                QMessageBox.information(self, "成功", f"数据备份成功：{backup_path}")
            else:
                QMessageBox.critical(self, "失败", "数据备份失败")
    
    def on_restore_data(self):
        """数据恢复"""
        QMessageBox.warning(
            self, "警告",
            "数据恢复功能开发中...\n此操作将覆盖当前所有数据，请谨慎使用！"
        )
    
    def on_help(self):
        """帮助"""
        help_text = """
        <h2>工业锅炉除污处理系统 - 帮助文档</h2>
        
        <h3>主要功能：</h3>
        <ul>
            <li><b>仪表盘</b> - 查看系统总体运行状态</li>
            <li><b>实时监控</b> - 实时监测锅炉各项参数</li>
            <li><b>投药控制</b> - 控制除污剂的投放</li>
            <li><b>排污控制</b> - 控制锅炉排污操作</li>
            <li><b>水质分析</b> - 记录和分析水质数据</li>
            <li><b>报警管理</b> - 查看和处理系统报警</li>
            <li><b>历史记录</b> - 查询历史运行数据</li>
            <li><b>报表统计</b> - 生成各类统计报表</li>
            <li><b>系统设置</b> - 配置系统参数</li>
        </ul>
        
        <h3>快捷键：</h3>
        <ul>
            <li>F5 - 刷新数据</li>
            <li>F11 - 全屏切换</li>
            <li>Ctrl+E - 导出报表</li>
        </ul>
        """
        QMessageBox.information(self, "帮助", help_text)
    
    def on_about(self):
        """关于"""
        about_text = """
        <h2>工业锅炉除污处理系统</h2>
        <p>版本：1.0.0</p>
        <p>版权所有 © 2024 IndustrialBoilerCorp</p>
        
        <p>本系统用于监控和控制工业锅炉的除污处理过程，包括：</p>
        <ul>
            <li>实时数据监控</li>
            <li>除污剂投放控制</li>
            <li>排污阀控制</li>
            <li>水质分析</li>
            <li>报警管理</li>
            <li>历史记录查询</li>
            <li>报表生成</li>
        </ul>
        
        <p>技术支持：support@industrialboiler.com</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def on_logout(self):
        """注销登录"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要注销当前用户吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info(f"用户 {self.current_user['username']} 注销登录")
            
            # 记录注销日志
            self.db_manager.log_operation(
                self.current_user['id'],
                "logout",
                "system",
                f"用户注销：{self.current_user['username']}"
            )
            
            self.current_user = None
            self.user_label.setText("未登录")
            self.status_label.setText("已注销")
            self._update_user_menu()
            
            # 显示登录对话框
            self._show_login_dialog()
    
    def on_change_password(self):
        """修改密码"""
        QMessageBox.information(self, "提示", "修改密码功能开发中...")
    
    def on_tray_activated(self, reason):
        """系统托盘激活处理"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()
    
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出系统吗？\n系统将在后台继续运行监控任务。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止刷新定时器
            self.refresh_timer.stop()
            self.time_timer.stop()
            
            # 隐藏到系统托盘
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage(
                    "系统提示",
                    "系统已最小化到托盘，双击托盘图标可重新打开。",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
                self.hide()
                event.ignore()
            else:
                event.accept()
        else:
            event.ignore()
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_F5:
            self.on_refresh()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)
