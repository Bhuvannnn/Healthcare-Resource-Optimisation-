from database_utils import DatabaseManager
from datetime import datetime, timedelta
import random
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_sample_data():
    db = DatabaseManager()
    
    try:
        with db.engine.begin() as conn:
            # Generate sample admissions
            logger.info("Generating sample admissions...")
            for _ in range(50):  # Generate 50 admissions
                admission_date = datetime.now() - timedelta(days=random.randint(0, 30))
                department_id = random.randint(1, 4)
                
                # Get available bed in department
                bed = conn.execute(
                    text("""
                    SELECT bed_id FROM beds 
                    WHERE department_id = :dept_id AND status = 'available' 
                    LIMIT 1
                    """),
                    {'dept_id': department_id}
                ).fetchone()
                
                if bed:
                    # Create admission
                    conn.execute(
                        text("""
                        INSERT INTO admissions (
                            patient_id, department_id, bed_id, 
                            admission_date, admission_type, status
                        )
                        VALUES (
                            :patient_id, :department_id, :bed_id,
                            :admission_date, :admission_type, 'active'
                        )
                        """),
                        {
                            'patient_id': random.randint(1, 3),  # Using existing patients
                            'department_id': department_id,
                            'bed_id': bed[0],
                            'admission_date': admission_date,
                            'admission_type': random.choice(['Emergency', 'Regular', 'ICU'])
                        }
                    )
                    
                    # Update bed status
                    conn.execute(
                        text("""
                        UPDATE beds SET status = 'occupied'
                        WHERE bed_id = :bed_id
                        """),
                        {'bed_id': bed[0]}
                    )

            # Generate staff schedules
            logger.info("Generating staff schedules...")
            for staff_id in range(1, 5):  # For each staff member
                for day in range(30):  # Last 30 days
                    shift_date = datetime.now() - timedelta(days=day)
                    shift_start = datetime(shift_date.year, shift_date.month, shift_date.day, 
                                        random.choice([7, 15, 23]))  # 7am, 3pm, or 11pm shifts
                    
                    conn.execute(
                        text("""
                        INSERT INTO staff_schedules (
                            staff_id, department_id, shift_start, shift_end, status
                        )
                        VALUES (
                            :staff_id, :dept_id, :shift_start, 
                            :shift_start + INTERVAL '8 hours',
                            :status
                        )
                        """),
                        {
                            'staff_id': staff_id,
                            'dept_id': random.randint(1, 4),
                            'shift_start': shift_start,
                            'status': random.choice(['completed', 'scheduled', 'cancelled'])
                        }
                    )

            # Generate equipment usage
            logger.info("Generating equipment usage...")
            equipment_ids = [r[0] for r in conn.execute(text("SELECT equipment_id FROM equipment")).fetchall()]
            
            for equipment_id in equipment_ids:
                for _ in range(random.randint(5, 15)):  # 5-15 uses per equipment
                    start_time = datetime.now() - timedelta(days=random.randint(1, 30),
                                                          hours=random.randint(1, 24))
                    duration = random.randint(1, 8)  # 1-8 hours usage
                    
                    conn.execute(
                        text("""
                        INSERT INTO equipment_usage (
                            equipment_id, department_id, staff_id, patient_id,
                            start_time, end_time, status
                        )
                        VALUES (
                            :equipment_id, :dept_id, :staff_id, :patient_id,
                            :start_time, :start_time + :duration * INTERVAL '1 hour',
                            'completed'
                        )
                        """),
                        {
                            'equipment_id': equipment_id,
                            'dept_id': random.randint(1, 4),
                            'staff_id': random.randint(1, 4),
                            'patient_id': random.randint(1, 3),
                            'start_time': start_time,
                            'duration': duration
                        }
                    )

            # Generate supply transactions
            logger.info("Generating supply transactions...")
            supply_ids = [r[0] for r in conn.execute(text("SELECT supply_id FROM supplies")).fetchall()]
            
            for supply_id in supply_ids:
                for _ in range(random.randint(10, 20)):  # 10-20 transactions per supply
                    quantity = random.randint(1, 50)
                    
                    conn.execute(
                        text("""
                        INSERT INTO supply_transactions (
                            supply_id, department_id, transaction_type,
                            quantity, created_by
                        )
                        VALUES (
                            :supply_id, :dept_id, 'out',
                            :quantity, :staff_id
                        )
                        """),
                        {
                            'supply_id': supply_id,
                            'dept_id': random.randint(1, 4),
                            'quantity': quantity,
                            'staff_id': random.randint(1, 4)
                        }
                    )
                    
                    # Update supply quantity
                    conn.execute(
                        text("""
                        UPDATE supplies
                        SET current_quantity = current_quantity - :quantity
                        WHERE supply_id = :supply_id
                        """),
                        {
                            'supply_id': supply_id,
                            'quantity': quantity
                        }
                    )

            logger.info("Sample data generation completed successfully!")

    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        raise

if __name__ == "__main__":
    generate_sample_data()