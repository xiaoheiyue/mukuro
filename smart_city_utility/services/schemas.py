"""
Smart City Utility Platform - Pydantic Models for Data Validation
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ============== User Models ==============
class UserBase(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=50)
    phone_number: str = Field(..., min_length=1, max_length=20)
    address: str = Field(..., min_length=1, max_length=255)
    account_balance: Decimal = Field(default=Decimal('0.00'))
    notification_channel: int = Field(default=1)
    status: int = Field(default=0)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    account_balance: Optional[Decimal] = None
    notification_channel: Optional[int] = None
    status: Optional[int] = None


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


# ============== Meter Models ==============
class MeterBase(BaseModel):
    imei: str = Field(..., min_length=1, max_length=32)
    user_id: int
    meter_type: int = Field(default=1)
    install_address: str = Field(..., min_length=1, max_length=255)
    status: int = Field(default=0)
    last_reading: Decimal = Field(default=Decimal('0.00'))
    offline_threshold: int = Field(default=24)


class MeterCreate(MeterBase):
    pass


class MeterUpdate(BaseModel):
    imei: Optional[str] = None
    user_id: Optional[int] = None
    meter_type: Optional[int] = None
    install_address: Optional[str] = None
    status: Optional[int] = None
    last_reading: Optional[Decimal] = None
    offline_threshold: Optional[int] = None


class MeterResponse(MeterBase):
    id: int

    class Config:
        from_attributes = True


# ============== Meter Reading Models ==============
class MeterReadingBase(BaseModel):
    meter_id: int
    reading_value: Decimal
    reading_time: datetime
    is_valid: int = Field(default=1)
    upload_source: str = Field(default='IoT')
    photo_url: Optional[str] = None


class MeterReadingCreate(MeterReadingBase):
    pass


class MeterReadingResponse(MeterReadingBase):
    id: int

    class Config:
        from_attributes = True


# ============== Fee Rule Models ==============
class FeeRuleBase(BaseModel):
    meter_type: int = Field(default=1)
    tier_start: Decimal
    tier_end: Decimal
    unit_price: Decimal
    penalty_rate: Decimal = Field(default=Decimal('0.0000'))
    effective_date: date
    is_active: int = Field(default=1)


class FeeRuleCreate(FeeRuleBase):
    pass


class FeeRuleUpdate(BaseModel):
    meter_type: Optional[int] = None
    tier_start: Optional[Decimal] = None
    tier_end: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    penalty_rate: Optional[Decimal] = None
    effective_date: Optional[date] = None
    is_active: Optional[int] = None


class FeeRuleResponse(FeeRuleBase):
    id: int

    class Config:
        from_attributes = True


# ============== Bill Models ==============
class BillBase(BaseModel):
    user_id: int
    meter_id: int
    billing_period: str = Field(..., min_length=7, max_length=7)  # YYYY-MM
    start_reading: Decimal
    end_reading: Decimal
    consumption: Decimal = Field(default=Decimal('0.00'))
    total_amount: Decimal = Field(default=Decimal('0.00'))
    penalty_amount: Decimal = Field(default=Decimal('0.00'))
    status: int = Field(default=0)
    generated_at: datetime


class BillCreate(BillBase):
    pass


class BillUpdate(BaseModel):
    user_id: Optional[int] = None
    meter_id: Optional[int] = None
    billing_period: Optional[str] = None
    start_reading: Optional[Decimal] = None
    end_reading: Optional[Decimal] = None
    consumption: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    penalty_amount: Optional[Decimal] = None
    status: Optional[int] = None
    generated_at: Optional[datetime] = None


class BillResponse(BillBase):
    id: int

    class Config:
        from_attributes = True


# ============== Payment Models ==============
class PaymentBase(BaseModel):
    bill_id: int
    user_id: int
    payment_amount: Decimal
    third_party_order_id: str = Field(..., min_length=1, max_length=64)
    payment_status: int = Field(default=0)
    payment_time: Optional[datetime] = None
    callback_data: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    bill_id: Optional[int] = None
    user_id: Optional[int] = None
    payment_amount: Optional[Decimal] = None
    third_party_order_id: Optional[str] = None
    payment_status: Optional[int] = None
    payment_time: Optional[datetime] = None
    callback_data: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: int

    class Config:
        from_attributes = True


# ============== Work Order Models ==============
class WorkOrderBase(BaseModel):
    meter_id: int
    order_type: int = Field(default=1)
    severity_level: int = Field(default=1)
    description: str = Field(..., min_length=1, max_length=500)
    assignee_id: Optional[int] = None
    status: int = Field(default=0)
    created_at: datetime


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    meter_id: Optional[int] = None
    order_type: Optional[int] = None
    severity_level: Optional[int] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[int] = None
    created_at: Optional[datetime] = None


class WorkOrderResponse(WorkOrderBase):
    id: int

    class Config:
        from_attributes = True


# ============== IoT Reading Input Models ==============
class IoTReadingInput(BaseModel):
    imei: str
    reading_value: Decimal
    timestamp: datetime
    signal_strength: Optional[int] = None

    class Config:
        from_attributes = True


# ============== Dashboard Statistics Models ==============
class DashboardStats(BaseModel):
    total_users: int = 0
    total_meters: int = 0
    online_meters: int = 0
    offline_meters: int = 0
    pending_bills: int = 0
    unpaid_amount: Decimal = Decimal('0.00')
    pending_work_orders: int = 0


# ============== Anomaly Detection Models ==============
class AnomalyDetectionResult(BaseModel):
    meter_id: int
    anomaly_type: str  # 'sudden_increase', 'zero_reading', 'offline'
    severity: str  # 'light', 'heavy'
    current_value: Decimal
    expected_range_min: Decimal
    expected_range_max: Decimal
    description: str
