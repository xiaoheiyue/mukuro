"""
Smart City Utility Platform - Database Initialization Script
Creates database tables and initializes with sample data
"""
import sys
sys.path.insert(0, '/workspace/smart_city_utility')

from decimal import Decimal
from datetime import datetime, date, timedelta

from models.database import engine, Base, SessionLocal
from models import TblUser, TblMeter, TblMeterReading, TblFeeRule, TblBill, TblPayment, TblWorkOrder


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def init_sample_data():
    """Initialize database with sample data for testing"""
    print("Initializing sample data...")
    
    db = SessionLocal()
    
    try:
        # Create sample users
        users = [
            TblUser(user_name="张三", phone_number="13800138001", address="北京市朝阳区XX路1号", account_balance=Decimal('100.00'), notification_channel=1, status=0),
            TblUser(user_name="李四", phone_number="13800138002", address="北京市海淀区XX路2号", account_balance=Decimal('50.00'), notification_channel=2, status=0),
            TblUser(user_name="王五", phone_number="13800138003", address="北京市东城区XX路3号", account_balance=Decimal('0.00'), notification_channel=1, status=1),
        ]
        
        for user in users:
            existing = db.query(TblUser).filter(TblUser.phone_number == user.phone_number).first()
            if not existing:
                db.add(user)
                print(f"  Created user: {user.user_name}")
        
        db.commit()
        
        # Get user IDs
        user1 = db.query(TblUser).filter(TblUser.user_name == "张三").first()
        user2 = db.query(TblUser).filter(TblUser.user_name == "李四").first()
        
        # Create sample meters
        meters = [
            TblMeter(imei="WATER001234567890", user_id=user1.id, meter_type=1, install_address="北京市朝阳区XX路1号厨房", status=0, last_reading=Decimal('1250.50'), offline_threshold=24),
            TblMeter(imei="ELEC001234567890", user_id=user1.id, meter_type=2, install_address="北京市朝阳区XX路1号电表箱", status=0, last_reading=Decimal('3580.00'), offline_threshold=24),
            TblMeter(imei="WATER001234567891", user_id=user2.id, meter_type=1, install_address="北京市海淀区XX路2号卫生间", status=0, last_reading=Decimal('890.25'), offline_threshold=24),
            TblMeter(imei="ELEC001234567891", user_id=user2.id, meter_type=2, install_address="北京市海淀区XX路2号配电箱", status=1, last_reading=Decimal('2100.00'), offline_threshold=24),
        ]
        
        for meter in meters:
            existing = db.query(TblMeter).filter(TblMeter.imei == meter.imei).first()
            if not existing:
                db.add(meter)
                print(f"  Created meter: {meter.imei}")
        
        db.commit()
        
        # Get meter IDs
        water_meter1 = db.query(TblMeter).filter(TblMeter.imei == "WATER001234567890").first()
        elec_meter1 = db.query(TblMeter).filter(TblMeter.imei == "ELEC001234567890").first()
        
        # Create sample meter readings (last 7 days)
        today = datetime.now()
        for i in range(7):
            reading_date = today - timedelta(days=i)
            
            # Water readings
            water_reading = TblMeterReading(
                meter_id=water_meter1.id,
                reading_value=Decimal(f'{1250.50 + i * 0.5:.2f}'),
                reading_time=reading_date.replace(hour=8, minute=0, second=0),
                is_valid=1,
                upload_source='IoT'
            )
            db.add(water_reading)
            
            # Electric readings
            elec_reading = TblMeterReading(
                meter_id=elec_meter1.id,
                reading_value=Decimal(f'{3580.00 + i * 5:.2f}'),
                reading_time=reading_date.replace(hour=8, minute=0, second=0),
                is_valid=1,
                upload_source='IoT'
            )
            db.add(elec_reading)
        
        db.commit()
        print("  Created meter readings for last 7 days")
        
        # Create fee rules
        fee_rules = [
            # Water fee rules (tiered pricing)
            TblFeeRule(meter_type=1, tier_start=Decimal('0'), tier_end=Decimal('15'), unit_price=Decimal('3.5000'), penalty_rate=Decimal('0.0005'), effective_date=date(2024, 1, 1), is_active=1),
            TblFeeRule(meter_type=1, tier_start=Decimal('15'), tier_end=Decimal('25'), unit_price=Decimal('4.5000'), penalty_rate=Decimal('0.0005'), effective_date=date(2024, 1, 1), is_active=1),
            TblFeeRule(meter_type=1, tier_start=Decimal('25'), tier_end=Decimal('9999'), unit_price=Decimal('6.0000'), penalty_rate=Decimal('0.0005'), effective_date=date(2024, 1, 1), is_active=1),
            # Electric fee rules (tiered pricing)
            TblFeeRule(meter_type=2, tier_start=Decimal('0'), tier_end=Decimal('220'), unit_price=Decimal('0.4883'), penalty_rate=Decimal('0.001'), effective_date=date(2024, 1, 1), is_active=1),
            TblFeeRule(meter_type=2, tier_start=Decimal('220'), tier_end=Decimal('400'), unit_price=Decimal('0.5383'), penalty_rate=Decimal('0.001'), effective_date=date(2024, 1, 1), is_active=1),
            TblFeeRule(meter_type=2, tier_start=Decimal('400'), tier_end=Decimal('9999'), unit_price=Decimal('0.7883'), penalty_rate=Decimal('0.001'), effective_date=date(2024, 1, 1), is_active=1),
        ]
        
        for rule in fee_rules:
            existing = db.query(TblFeeRule).filter(
                TblFeeRule.meter_type == rule.meter_type,
                TblFeeRule.tier_start == rule.tier_start,
                TblFeeRule.effective_date == rule.effective_date
            ).first()
            if not existing:
                db.add(rule)
                print(f"  Created fee rule: type={rule.meter_type}, price={rule.unit_price}")
        
        db.commit()
        
        # Create a sample bill
        current_period = today.strftime("%Y-%m")
        bill = TblBill(
            user_id=user1.id,
            meter_id=water_meter1.id,
            billing_period=current_period,
            start_reading=Decimal('1200.00'),
            end_reading=Decimal('1250.50'),
            consumption=Decimal('50.50'),
            total_amount=Decimal('200.00'),
            penalty_amount=Decimal('0.10'),
            status=1,
            generated_at=datetime.now()
        )
        
        existing_bill = db.query(TblBill).filter(
            TblBill.user_id == user1.id,
            TblBill.meter_id == water_meter1.id,
            TblBill.billing_period == current_period
        ).first()
        
        if not existing_bill:
            db.add(bill)
            db.commit()
            print("  Created sample bill")
        
        # Create a sample work order
        work_order = TblWorkOrder(
            meter_id=elec_meter1.id,
            order_type=2,
            severity_level=1,
            description="表具离线超过24小时，需要现场巡检",
            assignee_id=None,
            status=0,
            created_at=datetime.now()
        )
        
        existing_order = db.query(TblWorkOrder).filter(
            TblWorkOrder.meter_id == elec_meter1.id,
            TblWorkOrder.status == 0
        ).first()
        
        if not existing_order:
            db.add(work_order)
            db.commit()
            print("  Created sample work order")
        
        print("Sample data initialization completed!")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    init_sample_data()
    print("\nDatabase initialization complete!")
    print("You can now run the application with: python main.py")
