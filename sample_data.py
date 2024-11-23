from database_utils import DatabaseManager
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database(db):
    """Reset database sequences and clear all data"""
    reset_queries = """
    TRUNCATE departments, staff, equipment, beds, supplies RESTART IDENTITY CASCADE;
    ALTER SEQUENCE departments_department_id_seq RESTART WITH 1;
    ALTER SEQUENCE staff_staff_id_seq RESTART WITH 1;
    ALTER SEQUENCE equipment_equipment_id_seq RESTART WITH 1;
    ALTER SEQUENCE beds_bed_id_seq RESTART WITH 1;
    ALTER SEQUENCE supplies_supply_id_seq RESTART WITH 1;
    """
    with db.engine.begin() as conn:
        conn.execute(text(reset_queries))
    logger.info("Database reset completed")

def insert_sample_data():
    db = DatabaseManager()
    
    try:
        # Reset database
        reset_database(db)
        
        with db.engine.begin() as conn:
            # Add departments
            logger.info("Adding departments...")
            departments_data = [
                ('Emergency', 'First Floor', 20),
                ('ICU', 'Second Floor', 10),
                ('General Medicine', 'Third Floor', 30),
                ('Pediatrics', 'First Floor', 15)
            ]
            
            dept_ids = []
            for name, location, capacity in departments_data:
                result = conn.execute(
                    text("""
                    INSERT INTO departments (name, location, bed_capacity)
                    VALUES (:name, :location, :capacity)
                    RETURNING department_id;
                    """),
                    {"name": name, "location": location, "capacity": capacity}
                )
                dept_id = result.scalar()
                dept_ids.append(dept_id)
                logger.info(f"Added department {name} with ID: {dept_id}")

            # Add staff
            logger.info("Adding staff...")
            for i, dept_id in enumerate(dept_ids):
                result = conn.execute(
                    text("""
                    INSERT INTO staff (first_name, last_name, role, department, qualification, hire_date)
                    VALUES (:first_name, :last_name, :role, :department, :qualification, CURRENT_DATE)
                    RETURNING staff_id;
                    """),
                    {
                        "first_name": f"Doctor{i+1}",
                        "last_name": f"Smith{i+1}",
                        "role": "Doctor",
                        "department": departments_data[i][0],
                        "qualification": "MD"
                    }
                )
                staff_id = result.scalar()
                logger.info(f"Added staff member with ID: {staff_id}")

            # Add equipment
            logger.info("Adding equipment...")
            equipment_types = ['Ventilator', 'X-Ray Machine', 'ECG Monitor', 'Defibrillator']
            
            for dept_id in dept_ids:
                for eq_type in equipment_types:
                    result = conn.execute(
                        text("""
                        INSERT INTO equipment (name, type, department_id, status)
                        VALUES (:name, :type, :department_id, 'available')
                        RETURNING equipment_id;
                        """),
                        {
                            "name": f"{eq_type} - Dept {dept_id}",
                            "type": eq_type,
                            "department_id": dept_id
                        }
                    )
                    eq_id = result.scalar()
                    logger.info(f"Added {eq_type} to department {dept_id} with ID: {eq_id}")

            # Add beds
            logger.info("Adding beds...")
            for i, dept_id in enumerate(dept_ids):
                capacity = departments_data[i][2]
                for bed_num in range(1, capacity + 1):
                    result = conn.execute(
                        text("""
                        INSERT INTO beds (department_id, bed_number, bed_type, status)
                        VALUES (:dept_id, :bed_number, :bed_type, 'available')
                        RETURNING bed_id;
                        """),
                        {
                            "dept_id": dept_id,
                            "bed_number": f"BED-{dept_id}-{bed_num}",
                            "bed_type": 'ICU Bed' if departments_data[i][0] == 'ICU' else 'Standard Bed'
                        }
                    )
                    bed_id = result.scalar()
                    logger.info(f"Added bed {bed_num} to department {dept_id}")

            # Add supplies
            logger.info("Adding supplies...")
            supplies_data = [
                ('Surgical Masks', 'PPE', 1000, 200, 'pieces'),
                ('Hand Sanitizer', 'Hygiene', 500, 100, 'bottles'),
                ('Surgical Gloves', 'PPE', 2000, 500, 'pairs'),
                ('Bandages', 'First Aid', 1500, 300, 'pieces')
            ]
            
            for name, category, qty, min_qty, unit in supplies_data:
                result = conn.execute(
                    text("""
                    INSERT INTO supplies (name, category, current_quantity, minimum_quantity, unit)
                    VALUES (:name, :category, :qty, :min_qty, :unit)
                    RETURNING supply_id;
                    """),
                    {
                        "name": name,
                        "category": category,
                        "qty": qty,
                        "min_qty": min_qty,
                        "unit": unit
                    }
                )
                supply_id = result.scalar()
                logger.info(f"Added supply {name} with ID: {supply_id}")

        # Verify data after transaction
        with db.engine.connect() as conn:
            for table in ['departments', 'staff', 'equipment', 'beds', 'supplies']:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                logger.info(f"Total {table}: {count}")

        logger.info("Sample data inserted successfully!")
        
    except Exception as e:
        logger.error(f"Error inserting sample data: {str(e)}")
        raise

if __name__ == "__main__":
    insert_sample_data()