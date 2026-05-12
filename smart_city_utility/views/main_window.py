"""
Smart City Utility Platform - Main Window
PyQt6 UI with MVVM architecture
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit, QMessageBox,
    QGroupBox, QSpinBox, QDoubleSpinBox, QFrame, QScrollArea, QStatusBar,
    QMenuBar, QMenu, QAction, QDialog, QDialogButtonBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon

from decimal import Decimal
from datetime import datetime, date
from typing import Optional

import sys
sys.path.insert(0, '/workspace/smart_city_utility')

from models.database import SessionLocal, engine, Base
from models import TblUser, TblMeter, TblMeterReading, TblFeeRule, TblBill, TblPayment, TblWorkOrder
from services import (
    DashboardService, MeterReadingService, BillingService, 
    PaymentService, WorkOrderService
)
from controllers import (
    DashboardViewModel, MeterViewModel, BillViewModel,
    PaymentViewModel, WorkOrderViewModel, ReadingViewModel,
    DBWorkerThread
)


class DashboardWidget(QWidget):
    """Dashboard Widget - Shows system statistics"""
    
    def __init__(self, view_model: DashboardViewModel):
        super().__init__()
        self.view_model = view_model
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 系统概览")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QHBoxLayout()
        
        # User stats
        self.user_card = self._create_stat_card("👥 总用户数", "0")
        stats_layout.addWidget(self.user_card)
        
        # Meter stats
        self.meter_card = self._create_stat_card("📟 表具总数", "0")
        stats_layout.addWidget(self.meter_card)
        
        # Online meters
        self.online_card = self._create_stat_card("🟢 在线表具", "0")
        stats_layout.addWidget(self.online_card)
        
        # Pending bills
        self.bills_card = self._create_stat_card("📄 待缴费账单", "0")
        stats_layout.addWidget(self.bills_card)
        
        # Pending work orders
        self.orders_card = self._create_stat_card("🔧 待处理工单", "0")
        stats_layout.addWidget(self.orders_card)
        
        layout.addLayout(stats_layout)
        
        # Unpaid amount
        self.unpaid_label = QLabel("待收金额：¥0.00")
        self.unpaid_label.setFont(QFont("Arial", 14))
        self.unpaid_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(self.unpaid_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _create_stat_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setObjectName("statValue")
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def connect_signals(self):
        self.view_model.stats_updated.connect(self.update_stats)
        self.view_model.error_occurred.connect(self.show_error)
    
    def update_stats(self, stats):
        self.user_card.findChild(QLabel, "statValue").setText(str(stats.total_users))
        self.meter_card.findChild(QLabel, "statValue").setText(str(stats.total_meters))
        self.online_card.findChild(QLabel, "statValue").setText(str(stats.online_meters))
        self.bills_card.findChild(QLabel, "statValue").setText(str(stats.pending_bills))
        self.orders_card.findChild(QLabel, "statValue").setText(str(stats.pending_work_orders))
        self.unpaid_label.setText(f"待收金额：¥{stats.unpaid_amount}")
    
    def show_error(self, message: str):
        QMessageBox.warning(self, "错误", message)
    
    def refresh(self):
        self.view_model.load_stats()


class MeterManagementWidget(QWidget):
    """Meter Management Widget"""
    
    def __init__(self, view_model: MeterViewModel, db_session_factory):
        super().__init__()
        self.view_model = view_model
        self.db_session_factory = db_session_factory
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title and add button
        header_layout = QHBoxLayout()
        title = QLabel("📟 表具管理")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        add_btn = QPushButton("➕ 添加表具")
        add_btn.clicked.connect(self.show_add_dialog)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "IMEI", "用户ID", "类型", "安装地址", "状态", "最后读数"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        self.view_model.meters_loaded.connect(self.populate_table)
        self.view_model.error_occurred.connect(self.show_error)
    
    def populate_table(self, meters):
        self.table.setRowCount(len(meters))
        for row, meter in enumerate(meters):
            self.table.setItem(row, 0, QTableWidgetItem(str(meter.id)))
            self.table.setItem(row, 1, QTableWidgetItem(meter.imei))
            self.table.setItem(row, 2, QTableWidgetItem(str(meter.user_id)))
            meter_type = "水表" if meter.meter_type == 1 else "电表"
            self.table.setItem(row, 3, QTableWidgetItem(meter_type))
            self.table.setItem(row, 4, QTableWidgetItem(meter.install_address))
            status_map = {0: "在线", 1: "离线", 2: "故障"}
            self.table.setItem(row, 5, QTableWidgetItem(status_map.get(meter.status, "未知")))
            self.table.setItem(row, 6, QTableWidgetItem(str(meter.last_reading)))
    
    def show_error(self, message: str):
        QMessageBox.warning(self, "错误", message)
    
    def show_add_dialog(self):
        dialog = AddMeterDialog(self.db_session_factory, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.view_model.load_meters()
    
    def refresh(self):
        self.view_model.load_meters()


class AddMeterDialog(QDialog):
    """Dialog for adding new meter"""
    
    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self.db_session_factory = db_session_factory
        self.setWindowTitle("添加表具")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.imei_edit = QLineEdit()
        layout.addRow("IMEI:", self.imei_edit)
        
        self.user_id_spin = QSpinBox()
        self.user_id_spin.setMinimum(1)
        self.user_id_spin.setMaximum(999999)
        layout.addRow("用户ID:", self.user_id_spin)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("水表", 1)
        self.type_combo.addItem("电表", 2)
        layout.addRow("表具类型:", self.type_combo)
        
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        layout.addRow("安装地址:", self.address_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def accept(self):
        if not self.imei_edit.text():
            QMessageBox.warning(self, "验证失败", "请输入IMEI")
            return
        
        from models import TblMeter
        from decimal import Decimal
        
        db = self.db_session_factory()
        meter = TblMeter(
            imei=self.imei_edit.text(),
            user_id=self.user_id_spin.value(),
            meter_type=self.type_combo.currentData(),
            install_address=self.address_edit.toPlainText(),
            status=0,
            last_reading=Decimal('0.00'),
            offline_threshold=24
        )
        db.add(meter)
        db.commit()
        db.close()
        
        super().accept()


class BillManagementWidget(QWidget):
    """Bill Management Widget"""
    
    def __init__(self, billing_service, db_session_factory):
        super().__init__()
        self.view_model = BillViewModel(billing_service, db_session_factory)
        self.db_session_factory = db_session_factory
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📄 账单管理")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Generate bill section
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel("用户ID:"))
        self.user_id_spin = QSpinBox()
        self.user_id_spin.setMinimum(1)
        gen_layout.addWidget(self.user_id_spin)
        
        gen_layout.addWidget(QLabel("表具ID:"))
        self.meter_id_spin = QSpinBox()
        self.meter_id_spin.setMinimum(1)
        gen_layout.addWidget(self.meter_id_spin)
        
        gen_layout.addWidget(QLabel("计费周期:"))
        self.period_edit = QLineEdit()
        self.period_edit.setPlaceholderText("YYYY-MM")
        gen_layout.addWidget(self.period_edit)
        
        gen_btn = QPushButton("生成账单")
        gen_btn.clicked.connect(self.generate_bill)
        gen_layout.addWidget(gen_btn)
        
        layout.addLayout(gen_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "用户ID", "表具ID", "周期", "用量", "金额", "违约金", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        self.view_model.bills_loaded.connect(self.populate_table)
        self.view_model.error_occurred.connect(self.show_error)
        self.view_model.operation_completed.connect(self.show_message)
    
    def populate_table(self, bills):
        self.table.setRowCount(len(bills))
        for row, bill in enumerate(bills):
            self.table.setItem(row, 0, QTableWidgetItem(str(bill.id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(bill.user_id)))
            self.table.setItem(row, 2, QTableWidgetItem(str(bill.meter_id)))
            self.table.setItem(row, 3, QTableWidgetItem(bill.billing_period))
            self.table.setItem(row, 4, QTableWidgetItem(str(bill.consumption)))
            self.table.setItem(row, 5, QTableWidgetItem(str(bill.total_amount)))
            self.table.setItem(row, 6, QTableWidgetItem(str(bill.penalty_amount)))
            status_map = {0: "草稿", 1: "已发布", 2: "已支付"}
            self.table.setItem(row, 7, QTableWidgetItem(status_map.get(bill.status, "未知")))
    
    def generate_bill(self):
        user_id = self.user_id_spin.value()
        meter_id = self.meter_id_spin.value()
        period = self.period_edit.text()
        
        if not period:
            QMessageBox.warning(self, "验证失败", "请输入计费周期")
            return
        
        self.view_model.generate_bill(user_id, meter_id, period)
    
    def show_error(self, message: str):
        QMessageBox.warning(self, "错误", message)
    
    def show_message(self, message: str):
        QMessageBox.information(self, "提示", message)
    
    def refresh(self):
        # Load all bills for demo
        db = self.db_session_factory()
        bills = db.query(TblBill).all()
        db.close()
        self.populate_table(bills)


class PaymentWidget(QWidget):
    """Payment Widget"""
    
    def __init__(self, payment_service, db_session_factory):
        super().__init__()
        self.view_model = PaymentViewModel(payment_service)
        self.db_session_factory = db_session_factory
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("💳 支付管理")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Pay section
        pay_layout = QHBoxLayout()
        pay_layout.addWidget(QLabel("账单ID:"))
        self.bill_id_spin = QSpinBox()
        self.bill_id_spin.setMinimum(1)
        pay_layout.addWidget(self.bill_id_spin)
        
        pay_layout.addWidget(QLabel("支付金额:"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMaximum(999999.99)
        pay_layout.addWidget(self.amount_spin)
        
        pay_btn = QPushButton("立即缴费")
        pay_btn.clicked.connect(self.process_payment)
        pay_layout.addWidget(pay_btn)
        
        layout.addLayout(pay_layout)
        
        # Payment history table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "账单ID", "用户ID", "金额", "订单号", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh()
    
    def connect_signals(self):
        self.view_model.operation_completed.connect(self.show_message)
        self.view_model.error_occurred.connect(self.show_error)
    
    def process_payment(self):
        bill_id = self.bill_id_spin.value()
        amount = Decimal(str(self.amount_spin.value()))
        order_id = f"PAY_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.view_model.process_payment(bill_id, order_id, amount)
        self.refresh()
    
    def show_error(self, message: str):
        QMessageBox.warning(self, "错误", message)
    
    def show_message(self, message: str):
        QMessageBox.information(self, "提示", message)
    
    def refresh(self):
        db = self.db_session_factory()
        payments = db.query(TblPayment).all()
        db.close()
        
        self.table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self.table.setItem(row, 0, QTableWidgetItem(str(payment.id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(payment.bill_id)))
            self.table.setItem(row, 2, QTableWidgetItem(str(payment.user_id)))
            self.table.setItem(row, 3, QTableWidgetItem(str(payment.payment_amount)))
            self.table.setItem(row, 4, QTableWidgetItem(payment.third_party_order_id[:20] + "..."))
            status_map = {0: "处理中", 1: "成功", 2: "失败"}
            self.table.setItem(row, 5, QTableWidgetItem(status_map.get(payment.payment_status, "未知")))


class WorkOrderWidget(QWidget):
    """Work Order Widget"""
    
    def __init__(self, work_order_service, db_session_factory):
        super().__init__()
        self.view_model = WorkOrderViewModel(work_order_service)
        self.db_session_factory = db_session_factory
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("🔧 工单管理")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create order section
        create_layout = QHBoxLayout()
        create_layout.addWidget(QLabel("表具ID:"))
        self.meter_id_spin = QSpinBox()
        self.meter_id_spin.setMinimum(1)
        create_layout.addWidget(self.meter_id_spin)
        
        create_layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("异常读数", 1)
        self.type_combo.addItem("设备故障", 2)
        self.type_combo.addItem("巡检", 3)
        create_layout.addWidget(self.type_combo)
        
        create_layout.addWidget(QLabel("描述:"))
        self.desc_edit = QLineEdit()
        create_layout.addWidget(self.desc_edit)
        
        create_btn = QPushButton("创建工单")
        create_btn.clicked.connect(self.create_order)
        create_layout.addWidget(create_btn)
        
        layout.addLayout(create_layout)
        
        # Orders table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "表具ID", "类型", "等级", "描述", "处理人", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        self.view_model.work_orders_loaded.connect(self.populate_table)
        self.view_model.error_occurred.connect(self.show_error)
        self.view_model.operation_completed.connect(self.show_message)
    
    def populate_table(self, orders):
        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.table.setItem(row, 1, QTableWidgetItem(str(order.meter_id)))
            type_map = {1: "异常读数", 2: "设备故障", 3: "巡检"}
            self.table.setItem(row, 2, QTableWidgetItem(type_map.get(order.order_type, "未知")))
            severity_map = {1: "轻度", 2: "重度"}
            self.table.setItem(row, 3, QTableWidgetItem(severity_map.get(order.severity_level, "未知")))
            self.table.setItem(row, 4, QTableWidgetItem(order.description[:30] + "..." if len(order.description) > 30 else order.description))
            self.table.setItem(row, 5, QTableWidgetItem(str(order.assignee_id) if order.assignee_id else "未指派"))
            status_map = {0: "待处理", 1: "处理中", 2: "已完成"}
            self.table.setItem(row, 6, QTableWidgetItem(status_map.get(order.status, "未知")))
    
    def create_order(self):
        meter_id = self.meter_id_spin.value()
        order_type = self.type_combo.currentData()
        description = self.desc_edit.text()
        
        if not description:
            QMessageBox.warning(self, "验证失败", "请输入描述")
            return
        
        self.view_model.create_order(meter_id, order_type, description)
        self.refresh()
    
    def show_error(self, message: str):
        QMessageBox.warning(self, "错误", message)
    
    def show_message(self, message: str):
        QMessageBox.information(self, "提示", message)
    
    def refresh(self):
        self.view_model.load_pending_orders()


class MainWindow(QMainWindow):
    """Main Application Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智慧城市水电平台")
        self.setMinimumSize(1200, 800)
        
        # Initialize database session
        self.db_session_factory = SessionLocal
        
        # Initialize services
        self.dashboard_service = DashboardService(self.db_session_factory)
        self.reading_service = MeterReadingService(self.db_session_factory)
        self.billing_service = BillingService(self.db_session_factory)
        self.payment_service = PaymentService(self.db_session_factory)
        self.work_order_service = WorkOrderService(self.db_session_factory)
        
        # Initialize view models
        self.dashboard_vm = DashboardViewModel(self.dashboard_service)
        self.meter_vm = MeterViewModel(self.db_session_factory)
        
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()
        
        # Auto-refresh dashboard
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        
        # Initial load
        self.refresh_all()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Dashboard tab
        self.dashboard_widget = DashboardWidget(self.dashboard_vm)
        tabs.addTab(self.dashboard_widget, "📊 仪表盘")
        
        # Meter management tab
        self.meter_widget = MeterManagementWidget(self.meter_vm, self.db_session_factory)
        tabs.addTab(self.meter_widget, "📟 表具管理")
        
        # Bill management tab
        self.bill_widget = BillManagementWidget(self.billing_service, self.db_session_factory)
        tabs.addTab(self.bill_widget, "📄 账单管理")
        
        # Payment tab
        self.payment_widget = PaymentWidget(self.payment_service, self.db_session_factory)
        tabs.addTab(self.payment_widget, "💳 支付管理")
        
        # Work order tab
        self.work_order_widget = WorkOrderWidget(self.work_order_service, self.db_session_factory)
        tabs.addTab(self.work_order_widget, "🔧 工单管理")
        
        main_layout.addWidget(tabs)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("文件")
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("工具")
        
        refresh_action = QAction("刷新数据", self)
        refresh_action.triggered.connect(self.refresh_all)
        tools_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
    
    def refresh_all(self):
        """Refresh all widgets"""
        self.dashboard_widget.refresh()
        self.meter_widget.refresh()
        self.bill_widget.refresh()
        self.payment_widget.refresh()
        self.work_order_widget.refresh()
        self.statusbar.showMessage(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def show_about(self):
        QMessageBox.about(
            self,
            "关于智慧城市水电平台",
            "智慧城市水电平台 v1.0\n\n"
            "功能特性:\n"
            "• 智能表具数据采集与监控\n"
            "• 自动账单生成与阶梯费率计算\n"
            "• 在线支付与状态追踪\n"
            "• 异常检测与工单管理\n\n"
            "技术栈:\n"
            "Python 3.12 + PyQt6 + SQLAlchemy + MySQL"
        )


def main():
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
