"""
Smart City Utility Platform - View Models (MVVM Pattern)
Handles data binding between views and services using PyQt6 signals
"""
from decimal import Decimal
from datetime import datetime, date
from typing import List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread


class ViewModelBase(QObject):
    """Base ViewModel class"""
    error_occurred = pyqtSignal(str)
    data_loaded = pyqtSignal(object)
    operation_completed = pyqtSignal(str)


class DashboardViewModel(ViewModelBase):
    """Dashboard View Model"""
    stats_updated = pyqtSignal(object)
    
    def __init__(self, dashboard_service):
        super().__init__()
        self.dashboard_service = dashboard_service
    
    def load_stats(self):
        """Load dashboard statistics"""
        try:
            stats = self.dashboard_service.get_dashboard_stats()
            self.stats_updated.emit(stats)
            self.data_loaded.emit(stats)
        except Exception as e:
            self.error_occurred.emit(f"加载统计数据失败：{str(e)}")


class MeterViewModel(ViewModelBase):
    """Meter Management View Model"""
    meters_loaded = pyqtSignal(list)
    meter_added = pyqtSignal(object)
    meter_updated = pyqtSignal(object)
    
    def __init__(self, db_session_factory):
        super().__init__()
        self.db_session_factory = db_session_factory
    
    def load_meters(self):
        """Load all meters"""
        try:
            from models import TblMeter
            db = self.db_session_factory()
            meters = db.query(TblMeter).all()
            db.close()
            self.meters_loaded.emit(meters)
            self.data_loaded.emit(meters)
        except Exception as e:
            self.error_occurred.emit(f"加载表具列表失败：{str(e)}")
    
    def add_meter(self, meter_data: dict):
        """Add new meter"""
        try:
            from models import TblMeter
            from decimal import Decimal
            
            db = self.db_session_factory()
            meter = TblMeter(
                imei=meter_data.get('imei'),
                user_id=meter_data.get('user_id'),
                meter_type=meter_data.get('meter_type', 1),
                install_address=meter_data.get('install_address'),
                status=meter_data.get('status', 0),
                last_reading=Decimal(str(meter_data.get('last_reading', 0))),
                offline_threshold=meter_data.get('offline_threshold', 24)
            )
            db.add(meter)
            db.commit()
            db.refresh(meter)
            db.close()
            self.meter_added.emit(meter)
            self.operation_completed.emit("表具添加成功")
        except Exception as e:
            self.error_occurred.emit(f"添加表具失败：{str(e)}")


class BillViewModel(ViewModelBase):
    """Bill Management View Model"""
    bills_loaded = pyqtSignal(list)
    bill_generated = pyqtSignal(object)
    
    def __init__(self, billing_service, db_session_factory):
        super().__init__()
        self.billing_service = billing_service
        self.db_session_factory = db_session_factory
    
    def load_user_bills(self, user_id: int, status: Optional[int] = None):
        """Load user bills"""
        try:
            bills = self.billing_service.get_user_bills(user_id, status)
            self.bills_loaded.emit(bills)
            self.data_loaded.emit(bills)
        except Exception as e:
            self.error_occurred.emit(f"加载账单列表失败：{str(e)}")
    
    def generate_bill(self, user_id: int, meter_id: int, billing_period: str):
        """Generate monthly bill"""
        try:
            bill = self.billing_service.generate_monthly_bill(user_id, meter_id, billing_period)
            if bill:
                self.bill_generated.emit(bill)
                self.operation_completed.emit("账单生成成功")
            else:
                self.error_occurred.emit("账单生成失败")
        except Exception as e:
            self.error_occurred.emit(f"生成账单失败：{str(e)}")


class PaymentViewModel(ViewModelBase):
    """Payment View Model"""
    payment_processed = pyqtSignal(object)
    payment_status_updated = pyqtSignal(object)
    
    def __init__(self, payment_service):
        super().__init__()
        self.payment_service = payment_service
    
    def process_payment(self, bill_id: int, order_id: str, amount: Decimal):
        """Process payment"""
        try:
            success, message = self.payment_service.process_payment(bill_id, order_id, amount)
            if success:
                self.operation_completed.emit(message)
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            self.error_occurred.emit(f"支付处理失败：{str(e)}")


class WorkOrderViewModel(ViewModelBase):
    """Work Order View Model"""
    work_orders_loaded = pyqtSignal(list)
    work_order_created = pyqtSignal(object)
    work_order_updated = pyqtSignal(object)
    
    def __init__(self, work_order_service):
        super().__init__()
        self.work_order_service = work_order_service
    
    def load_pending_orders(self):
        """Load pending work orders"""
        try:
            orders = self.work_order_service.get_pending_work_orders()
            self.work_orders_loaded.emit(orders)
            self.data_loaded.emit(orders)
        except Exception as e:
            self.error_occurred.emit(f"加载工单列表失败：{str(e)}")
    
    def create_order(self, meter_id: int, order_type: int, description: str, 
                    severity_level: int = 1, assignee_id: Optional[int] = None):
        """Create work order"""
        try:
            order = self.work_order_service.create_work_order(
                meter_id, order_type, description, severity_level, assignee_id
            )
            self.work_order_created.emit(order)
            self.operation_completed.emit("工单创建成功")
        except Exception as e:
            self.error_occurred.emit(f"创建工单失败：{str(e)}")
    
    def update_order_status(self, order_id: int, status: int):
        """Update work order status"""
        try:
            order = self.work_order_service.update_work_order_status(order_id, status)
            if order:
                self.work_order_updated.emit(order)
                self.operation_completed.emit("工单状态更新成功")
        except Exception as e:
            self.error_occurred.emit(f"更新工单状态失败：{str(e)}")


class ReadingViewModel(ViewModelBase):
    """Meter Reading View Model"""
    readings_loaded = pyqtSignal(list)
    reading_received = pyqtSignal(bool, str)
    
    def __init__(self, reading_service):
        super().__init__()
        self.reading_service = reading_service
    
    def load_readings(self, meter_id: int, days: int = 30):
        """Load meter readings"""
        try:
            readings = self.reading_service.get_meter_readings(meter_id, days)
            self.readings_loaded.emit(readings)
            self.data_loaded.emit(readings)
        except Exception as e:
            self.error_occurred.emit(f"加载读数历史失败：{str(e)}")
    
    def receive_iot_reading(self, imei: str, value: Decimal, timestamp: datetime):
        """Receive IoT reading"""
        try:
            from services.schemas import IoTReadingInput
            reading_input = IoTReadingInput(
                imei=imei,
                reading_value=value,
                timestamp=timestamp
            )
            success, message = self.reading_service.receive_iot_reading(reading_input)
            self.reading_received.emit(success, message)
            if success:
                self.operation_completed.emit(message)
            else:
                self.error_occurred.emit(message)
        except Exception as e:
            self.error_occurred.emit(f"接收读数失败：{str(e)}")


# Background worker thread for database operations
class DBWorkerThread(QThread):
    """Database worker thread to keep UI responsive"""
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
