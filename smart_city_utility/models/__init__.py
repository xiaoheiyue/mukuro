"""
Smart City Utility Platform - SQLAlchemy ORM Models
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Numeric, Text, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class TblUser(Base):
    """用户表"""
    __tablename__ = 'tbl_user'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_name = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=False, unique=True)
    address = Column(String(255), nullable=False)
    account_balance = Column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    notification_channel = Column(Integer, nullable=False, default=1)  # 1:短信，2:APP站内信
    status = Column(Integer, nullable=False, default=0)  # 0:正常，1:欠费停供，2:销户

    # Relationships
    meters = relationship("TblMeter", back_populates="user")
    bills = relationship("TblBill", back_populates="user")
    payments = relationship("TblPayment", back_populates="user")

    def __repr__(self):
        return f"<TblUser(id={self.id}, user_name='{self.user_name}')>"


class TblMeter(Base):
    """表具表"""
    __tablename__ = 'tbl_meter'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    imei = Column(String(32), nullable=False, unique=True)
    user_id = Column(BigInteger, ForeignKey('tbl_user.id'), nullable=False)
    meter_type = Column(Integer, nullable=False, default=1)  # 1:水，2:电
    install_address = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False, default=0)  # 0:在线，1:离线，2:故障
    last_reading = Column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    offline_threshold = Column(Integer, nullable=False, default=24)

    # Relationships
    user = relationship("TblUser", back_populates="meters")
    readings = relationship("TblMeterReading", back_populates="meter")
    bills = relationship("TblBill", back_populates="meter")
    work_orders = relationship("TblWorkOrder", back_populates="meter")

    def __repr__(self):
        return f"<TblMeter(id={self.id}, imei='{self.imei}', type={self.meter_type})>"


class TblMeterReading(Base):
    """表具读数表"""
    __tablename__ = 'tbl_meter_reading'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meter_id = Column(BigInteger, ForeignKey('tbl_meter.id'), nullable=False)
    reading_value = Column(Numeric(10, 2), nullable=False)
    reading_time = Column(DateTime, nullable=False)
    is_valid = Column(Integer, nullable=False, default=1)  # 1:有效，0:异常/估算
    upload_source = Column(String(20), nullable=False, default='IoT')  # IoT/Manual
    photo_url = Column(String(255), nullable=True)

    # Relationships
    meter = relationship("TblMeter", back_populates="readings")

    def __repr__(self):
        return f"<TblMeterReading(id={self.id}, meter_id={self.meter_id}, value={self.reading_value})>"


class TblFeeRule(Base):
    """费率规则表"""
    __tablename__ = 'tbl_fee_rule'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meter_type = Column(Integer, nullable=False, default=1)  # 1:水，2:电
    tier_start = Column(Numeric(10, 2), nullable=False)
    tier_end = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 4), nullable=False)
    penalty_rate = Column(Numeric(10, 4), nullable=False, default=Decimal('0.0000'))
    effective_date = Column(Date, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)  # 1:是，0:否

    def __repr__(self):
        return f"<TblFeeRule(id={self.id}, type={self.meter_type}, price={self.unit_price})>"


class TblBill(Base):
    """账单表"""
    __tablename__ = 'tbl_bill'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('tbl_user.id'), nullable=False)
    meter_id = Column(BigInteger, ForeignKey('tbl_meter.id'), nullable=False)
    billing_period = Column(String(7), nullable=False)  # YYYY-MM
    start_reading = Column(Numeric(10, 2), nullable=False)
    end_reading = Column(Numeric(10, 2), nullable=False)
    consumption = Column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    total_amount = Column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    penalty_amount = Column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    status = Column(Integer, nullable=False, default=0)  # 0:草稿，1:已发布，2:已支付
    generated_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("TblUser", back_populates="bills")
    meter = relationship("TblMeter", back_populates="bills")
    payments = relationship("TblPayment", back_populates="bill")

    def __repr__(self):
        return f"<TblBill(id={self.id}, period='{self.billing_period}', amount={self.total_amount})>"


class TblPayment(Base):
    """支付记录表"""
    __tablename__ = 'tbl_payment'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bill_id = Column(BigInteger, ForeignKey('tbl_bill.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('tbl_user.id'), nullable=False)
    payment_amount = Column(Numeric(10, 2), nullable=False)
    third_party_order_id = Column(String(64), nullable=False, unique=True)
    payment_status = Column(Integer, nullable=False, default=0)  # 0:处理中，1:成功，2:失败
    payment_time = Column(DateTime, nullable=True)
    callback_data = Column(Text, nullable=True)

    # Relationships
    bill = relationship("TblBill", back_populates="payments")
    user = relationship("TblUser", back_populates="payments")

    def __repr__(self):
        return f"<TblPayment(id={self.id}, bill_id={self.bill_id}, status={self.payment_status})>"


class TblWorkOrder(Base):
    """工单表"""
    __tablename__ = 'tbl_work_order'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meter_id = Column(BigInteger, ForeignKey('tbl_meter.id'), nullable=False)
    order_type = Column(Integer, nullable=False, default=1)  # 1:异常读数，2:设备故障，3:巡检
    severity_level = Column(Integer, nullable=False, default=1)  # 1:轻度，2:重度
    description = Column(String(500), nullable=False)
    assignee_id = Column(BigInteger, nullable=True)
    status = Column(Integer, nullable=False, default=0)  # 0:待处理，1:处理中，2:已完成
    created_at = Column(DateTime, nullable=False)

    # Relationships
    meter = relationship("TblMeter", back_populates="work_orders")

    def __repr__(self):
        return f"<TblWorkOrder(id={self.id}, type={self.order_type}, status={self.status})>"
