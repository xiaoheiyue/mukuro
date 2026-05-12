"""
Smart City Utility Platform - Services Layer
Handles business logic for meter readings, billing, payments, and work orders
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

import sys
sys.path.insert(0, '/workspace/smart_city_utility')

from models import (
    TblUser, TblMeter, TblMeterReading, TblFeeRule, 
    TblBill, TblPayment, TblWorkOrder
)
from services.schemas import (
    DashboardStats, AnomalyDetectionResult, IoTReadingInput
)


class MeterReadingService:
    """表具读数服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def receive_iot_reading(self, reading_input: IoTReadingInput) -> Tuple[bool, str]:
        """
        接收智能表具上传的读数
        校验IMEI合法性与时间戳偏差（允许±5分钟）
        """
        # 查找表具
        meter = self.db.query(TblMeter).filter(TblMeter.imei == reading_input.imei).first()
        if not meter:
            return False, f"表具IMEI不存在：{reading_input.imei}"
        
        # 校验时间戳偏差（允许±5分钟）
        now = datetime.now()
        time_diff = abs((now - reading_input.timestamp).total_seconds())
        if time_diff > 300:  # 5 minutes
            return False, f"时间戳偏差过大：{time_diff}秒"
        
        # 创建读数记录
        reading = TblMeterReading(
            meter_id=meter.id,
            reading_value=reading_input.reading_value,
            reading_time=reading_input.timestamp,
            is_valid=1,
            upload_source='IoT'
        )
        
        # 更新表具最后读数
        meter.last_reading = reading_input.reading_value
        meter.status = 0  # 在线
        
        self.db.add(reading)
        self.db.commit()
        
        # 检查异常
        anomalies = self._detect_anomalies(meter.id)
        if anomalies:
            for anomaly in anomalies:
                self._create_work_order_from_anomaly(meter, anomaly)
        
        return True, "读数接收成功"
    
    def _detect_anomalies(self, meter_id: int) -> List[AnomalyDetectionResult]:
        """检测读数异常"""
        anomalies = []
        
        # 获取最近7天的读数
        seven_days_ago = datetime.now() - timedelta(days=7)
        readings = self.db.query(TblMeterReading).filter(
            and_(
                TblMeterReading.meter_id == meter_id,
                TblMeterReading.reading_time >= seven_days_ago,
                TblMeterReading.is_valid == 1
            )
        ).order_by(TblMeterReading.reading_time.desc()).limit(8).all()
        
        if len(readings) < 2:
            return anomalies
        
        # 计算日均用量
        latest = readings[0]
        previous = readings[1] if len(readings) > 1 else None
        
        if previous:
            daily_consumption = float(latest.reading_value - previous.reading_value)
            
            # 计算历史平均
            if len(readings) > 2:
                historical_avg = sum(
                    float(readings[i].reading_value - readings[i+1].reading_value) 
                    for i in range(len(readings)-1)
                ) / (len(readings) - 1)
            else:
                historical_avg = daily_consumption
            
            # 检测突增（超过50%）
            if historical_avg > 0 and daily_consumption > historical_avg * 1.5:
                anomalies.append(AnomalyDetectionResult(
                    meter_id=meter_id,
                    anomaly_type='sudden_increase',
                    severity='heavy' if daily_consumption > historical_avg * 2 else 'light',
                    current_value=latest.reading_value,
                    expected_range_min=Decimal(str(historical_avg * 0.5)),
                    expected_range_max=Decimal(str(historical_avg * 1.5)),
                    description=f"用量突增：当前日用量{daily_consumption:.2f}，历史平均{historical_avg:.2f}"
                ))
            
            # 检测零值
            if daily_consumption == 0:
                anomalies.append(AnomalyDetectionResult(
                    meter_id=meter_id,
                    anomaly_type='zero_reading',
                    severity='light',
                    current_value=latest.reading_value,
                    expected_range_min=Decimal('0'),
                    expected_range_max=Decimal(str(historical_avg * 0.1)),
                    description="零用量读数，可能表具故障"
                ))
        
        return anomalies
    
    def _create_work_order_from_anomaly(self, meter: TblMeter, anomaly: AnomalyDetectionResult):
        """根据异常创建工单"""
        order_type = 1  # 异常读数
        severity = 2 if anomaly.severity == 'heavy' else 1
        
        work_order = TblWorkOrder(
            meter_id=meter.id,
            order_type=order_type,
            severity_level=severity,
            description=anomaly.description,
            status=0,
            created_at=datetime.now()
        )
        
        self.db.add(work_order)
        self.db.commit()
    
    def get_meter_readings(self, meter_id: int, days: int = 30) -> List[TblMeterReading]:
        """获取表具历史读数"""
        start_date = datetime.now() - timedelta(days=days)
        return self.db.query(TblMeterReading).filter(
            and_(
                TblMeterReading.meter_id == meter_id,
                TblMeterReading.reading_time >= start_date
            )
        ).order_by(TblMeterReading.reading_time.desc()).all()


class BillingService:
    """账单生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_monthly_bill(self, user_id: int, meter_id: int, billing_period: str) -> Optional[TblBill]:
        """
        生成月度账单
        读取上月末底数与本月读数，应用阶梯电价/水价规则计算费用
        """
        # 解析计费周期
        try:
            period_date = datetime.strptime(billing_period, "%Y-%m")
        except ValueError:
            return None
        
        # 获取表具
        meter = self.db.query(TblMeter).filter(
            and_(TblMeter.id == meter_id, TblMeter.user_id == user_id)
        ).first()
        if not meter:
            return None
        
        # 检查是否已存在该周期账单
        existing_bill = self.db.query(TblBill).filter(
            and_(
                TblBill.user_id == user_id,
                TblBill.meter_id == meter_id,
                TblBill.billing_period == billing_period
            )
        ).first()
        if existing_bill:
            return existing_bill
        
        # 获取期初读数（上月末）
        last_day_of_prev_month = period_date.replace(day=1) - timedelta(days=1)
        start_reading_record = self.db.query(TblMeterReading).filter(
            and_(
                TblMeterReading.meter_id == meter_id,
                TblMeterReading.reading_time <= last_day_of_prev_month,
                TblMeterReading.is_valid == 1
            )
        ).order_by(TblMeterReading.reading_time.desc()).first()
        
        # 获取期末读数（本月末）
        last_day_of_month = (period_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_reading_record = self.db.query(TblMeterReading).filter(
            and_(
                TblMeterReading.meter_id == meter_id,
                TblMeterReading.reading_time <= last_day_of_month,
                TblMeterReading.is_valid == 1
            )
        ).order_by(TblMeterReading.reading_time.desc()).first()
        
        if not start_reading_record or not end_reading_record:
            # 使用估算值
            start_reading = meter.last_reading
            end_reading = meter.last_reading
            is_estimated = True
        else:
            start_reading = start_reading_record.reading_value
            end_reading = end_reading_record.reading_value
            is_estimated = False
        
        consumption = end_reading - start_reading
        if consumption < 0:
            consumption = Decimal('0')
        
        # 计算费用
        total_amount, penalty_amount = self._calculate_fee(meter.meter_type, consumption, billing_period)
        
        # 创建账单
        bill = TblBill(
            user_id=user_id,
            meter_id=meter_id,
            billing_period=billing_period,
            start_reading=start_reading,
            end_reading=end_reading,
            consumption=consumption,
            total_amount=total_amount,
            penalty_amount=penalty_amount,
            status=1,  # 已发布
            generated_at=datetime.now()
        )
        
        self.db.add(bill)
        self.db.commit()
        self.db.refresh(bill)
        
        return bill
    
    def _calculate_fee(self, meter_type: int, consumption: Decimal, billing_period: str) -> Tuple[Decimal, Decimal]:
        """
        根据阶梯费率计算费用
        锁定旧版费率快照
        """
        # 获取生效的费率规则
        period_date = datetime.strptime(billing_period, "%Y-%m")
        rules = self.db.query(TblFeeRule).filter(
            and_(
                TblFeeRule.meter_type == meter_type,
                TblFeeRule.is_active == 1,
                TblFeeRule.effective_date <= period_date
            )
        ).order_by(TblFeeRule.effective_date.desc()).all()
        
        if not rules:
            return Decimal('0.00'), Decimal('0.00')
        
        total_amount = Decimal('0.00')
        remaining_consumption = consumption
        
        # 阶梯分段累加计算
        for rule in rules:
            if remaining_consumption <= 0:
                break
            
            tier_range = rule.tier_end - rule.tier_start
            if tier_range <= 0:
                continue
            
            consumption_in_tier = min(remaining_consumption, tier_range)
            if consumption_in_tier > 0:
                total_amount += consumption_in_tier * rule.unit_price
                remaining_consumption -= consumption_in_tier
        
        # 违约金计算
        penalty_amount = total_amount * rules[0].penalty_rate if rules else Decimal('0.0000')
        
        return total_amount.quantize(Decimal('0.01')), penalty_amount.quantize(Decimal('0.01'))
    
    def get_user_bills(self, user_id: int, status: Optional[int] = None) -> List[TblBill]:
        """获取用户账单列表"""
        query = self.db.query(TblBill).filter(TblBill.user_id == user_id)
        if status is not None:
            query = query.filter(TblBill.status == status)
        return query.order_by(TblBill.generated_at.desc()).all()
    
    def get_bill_details(self, bill_id: int) -> Optional[TblBill]:
        """获取账单详情"""
        return self.db.query(TblBill).filter(TblBill.id == bill_id).first()


class PaymentService:
    """支付服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_payment(self, bill_id: int, third_party_order_id: str, amount: Decimal) -> Tuple[bool, str]:
        """
        处理用户支付
        调用第三方支付接口发起扣款请求（模拟）
        """
        # 获取账单
        bill = self.db.query(TblBill).filter(TblBill.id == bill_id).first()
        if not bill:
            return False, "账单不存在"
        
        if bill.status == 2:  # 已支付
            return False, "账单已支付"
        
        # 检查金额匹配
        total_due = bill.total_amount + bill.penalty_amount
        if amount < total_due:
            return False, f"支付金额不足，应付：{total_due}"
        
        # 创建支付记录
        payment = TblPayment(
            bill_id=bill_id,
            user_id=bill.user_id,
            payment_amount=amount,
            third_party_order_id=third_party_order_id,
            payment_status=0,  # 处理中
            payment_time=None
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        # 模拟第三方支付回调（实际应异步处理）
        # 这里假设支付成功
        self._simulate_payment_callback(payment.id, True)
        
        return True, "支付处理成功"
    
    def _simulate_payment_callback(self, payment_id: int, success: bool):
        """模拟支付网关回调"""
        payment = self.db.query(TblPayment).filter(TblPayment.id == payment_id).first()
        if not payment:
            return
        
        callback_data = '{"status": "success", "channel": "mock"}' if success else '{"status": "failed"}'
        
        if success:
            payment.payment_status = 1
            payment.payment_time = datetime.now()
            payment.callback_data = callback_data
            
            # 更新账单状态
            bill = self.db.query(TblBill).filter(TblBill.id == payment.bill_id).first()
            if bill:
                bill.status = 2  # 已支付
            
            # 更新用户余额
            user = self.db.query(TblUser).filter(TblUser.id == payment.user_id).first()
            if user:
                user.account_balance += payment.payment_amount
        else:
            payment.payment_status = 2
            payment.callback_data = callback_data
        
        self.db.commit()
    
    def get_payment_status(self, payment_id: int) -> Optional[TblPayment]:
        """获取支付状态"""
        return self.db.query(TblPayment).filter(TblPayment.id == payment_id).first()
    
    def get_user_payments(self, user_id: int) -> List[TblPayment]:
        """获取用户支付记录"""
        return self.db.query(TblPayment).filter(TblPayment.user_id == user_id).order_by(
            TblPayment.payment_time.desc()
        ).all()


class WorkOrderService:
    """工单服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_work_order(self, meter_id: int, order_type: int, description: str, 
                         severity_level: int = 1, assignee_id: Optional[int] = None) -> TblWorkOrder:
        """创建工单"""
        work_order = TblWorkOrder(
            meter_id=meter_id,
            order_type=order_type,
            severity_level=severity_level,
            description=description,
            assignee_id=assignee_id,
            status=0,
            created_at=datetime.now()
        )
        
        self.db.add(work_order)
        self.db.commit()
        self.db.refresh(work_order)
        
        return work_order
    
    def update_work_order_status(self, work_order_id: int, status: int) -> Optional[TblWorkOrder]:
        """更新工单状态"""
        work_order = self.db.query(TblWorkOrder).filter(TblWorkOrder.id == work_order_id).first()
        if work_order:
            work_order.status = status
            self.db.commit()
            self.db.refresh(work_order)
        return work_order
    
    def assign_work_order(self, work_order_id: int, assignee_id: int) -> Optional[TblWorkOrder]:
        """指派工单"""
        work_order = self.db.query(TblWorkOrder).filter(TblWorkOrder.id == work_order_id).first()
        if work_order:
            work_order.assignee_id = assignee_id
            work_order.status = 1  # 处理中
            self.db.commit()
            self.db.refresh(work_order)
        return work_order
    
    def get_pending_work_orders(self) -> List[TblWorkOrder]:
        """获取待处理工单"""
        return self.db.query(TblWorkOrder).filter(TblWorkOrder.status == 0).order_by(
            TblWorkOrder.created_at.desc()
        ).all()
    
    def get_meter_work_orders(self, meter_id: int) -> List[TblWorkOrder]:
        """获取表具相关工单"""
        return self.db.query(TblWorkOrder).filter(TblWorkOrder.meter_id == meter_id).order_by(
            TblWorkOrder.created_at.desc()
        ).all()


class DashboardService:
    """仪表盘统计服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self) -> DashboardStats:
        """获取仪表盘统计数据"""
        stats = DashboardStats()
        
        # 总用户数
        stats.total_users = self.db.query(func.count(TblUser.id)).scalar() or 0
        
        # 表具统计
        stats.total_meters = self.db.query(func.count(TblMeter.id)).scalar() or 0
        stats.online_meters = self.db.query(func.count(TblMeter.id)).filter(
            TblMeter.status == 0
        ).scalar() or 0
        stats.offline_meters = self.db.query(func.count(TblMeter.id)).filter(
            TblMeter.status == 1
        ).scalar() or 0
        
        # 账单统计
        stats.pending_bills = self.db.query(func.count(TblBill.id)).filter(
            TblBill.status == 1  # 已发布未支付
        ).scalar() or 0
        
        unpaid_result = self.db.query(func.sum(TblBill.total_amount + TblBill.penalty_amount)).filter(
            TblBill.status == 1
        ).scalar()
        stats.unpaid_amount = unpaid_result or Decimal('0.00')
        
        # 工单统计
        stats.pending_work_orders = self.db.query(func.count(TblWorkOrder.id)).filter(
            TblWorkOrder.status == 0
        ).scalar() or 0
        
        return stats
