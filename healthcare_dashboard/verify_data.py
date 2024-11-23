# verify_data.py
from app.database_utils import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database_data():
    db = DatabaseManager()
    
    try:
        with db.engine.connect() as conn:
            # Check departments
            dept_count = conn.execute(text("SELECT COUNT(*) FROM departments")).scalar()
            logger.info(f"Number of departments: {dept_count}")

            # Check staff
            staff_count = conn.execute(text("SELECT COUNT(*) FROM staff")).scalar()
            logger.info(f"Number of staff members: {staff_count}")

            # Check equipment
            equip_count = conn.execute(text("SELECT COUNT(*) FROM equipment")).scalar()
            logger.info(f"Number of equipment: {equip_count}")

            # Check supplies
            supply_count = conn.execute(text("SELECT COUNT(*) FROM supplies")).scalar()
            logger.info(f"Number of supplies: {supply_count}")

            # Check admissions
            admission_count = conn.execute(text("SELECT COUNT(*) FROM admissions")).scalar()
            logger.info(f"Number of admissions: {admission_count}")

            # Sample data from each table
            logger.info("\nSample Department Data:")
            departments = conn.execute(text("SELECT * FROM departments LIMIT 3")).fetchall()
            for dept in departments:
                logger.info(dept)

            logger.info("\nSample Equipment Data:")
            equipment = conn.execute(text("SELECT * FROM equipment LIMIT 3")).fetchall()
            for equip in equipment:
                logger.info(equip)

    except Exception as e:
        logger.error(f"Error verifying data: {str(e)}")
        raise

if __name__ == "__main__":
    verify_database_data()