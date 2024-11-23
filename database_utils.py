import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('healthcare_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        """Initialize database connection using environment variables"""
        load_dotenv()
        
        # Construct connection string from environment variables
        connection_string = f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        
        try:
            self.engine = create_engine(connection_string)
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def execute_query(self, query, params=None):
        """Execute a SQL query"""
        try:
            with self.engine.connect() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                return result
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    # Staff Management Functions
    def add_staff_member(self, first_name, last_name, role, department, qualification=None):
        """Add a new staff member"""
        query = """
        INSERT INTO staff (first_name, last_name, role, department, qualification, hire_date)
        VALUES (:first_name, :last_name, :role, :department, :qualification, CURRENT_DATE)
        RETURNING staff_id
        """
        params = {
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'department': department,
            'qualification': qualification
        }
        return self.execute_query(query, params).fetchone()[0]

    def get_staff_schedule(self, staff_id):
        """Get schedule for a specific staff member"""
        query = """
        SELECT shift_start, shift_end, department_id
        FROM staff_schedules
        WHERE staff_id = :staff_id AND shift_start >= CURRENT_DATE
        ORDER BY shift_start
        """
        return self.execute_query(query, {'staff_id': staff_id}).fetchall()

    # Equipment Management Functions
    def add_equipment(self, name, type, department_id):
        """Add new equipment"""
        query = """
        INSERT INTO equipment (name, type, department_id, status)
        VALUES (:name, :type, :department_id, 'available')
        RETURNING equipment_id
        """
        params = {'name': name, 'type': type, 'department_id': department_id}
        return self.execute_query(query, params).fetchone()[0]

    def update_equipment_status(self, equipment_id, status):
        """Update equipment status"""
        query = """
        UPDATE equipment
        SET status = :status, updated_at = CURRENT_TIMESTAMP
        WHERE equipment_id = :equipment_id
        """
        self.execute_query(query, {'equipment_id': equipment_id, 'status': status})

    # Patient Management Functions
    def admit_patient(self, patient_id, department_id, bed_id, admission_type):
        """Admit a patient"""
        query = """
        INSERT INTO admissions (patient_id, department_id, bed_id, admission_date, admission_type)
        VALUES (:patient_id, :department_id, :bed_id, CURRENT_TIMESTAMP, :admission_type)
        RETURNING admission_id
        """
        params = {
            'patient_id': patient_id,
            'department_id': department_id,
            'bed_id': bed_id,
            'admission_type': admission_type
        }
        return self.execute_query(query, params).fetchone()[0]

    def discharge_patient(self, admission_id):
        """Discharge a patient"""
        query = """
        UPDATE admissions
        SET discharge_date = CURRENT_TIMESTAMP,
            status = 'discharged'
        WHERE admission_id = :admission_id
        """
        self.execute_query(query, {'admission_id': admission_id})

    # Resource Utilization Functions
    def get_bed_occupancy(self, department_id=None):
        """Get bed occupancy rates"""
        query = """
        SELECT 
            d.name as department,
            COUNT(b.bed_id) as total_beds,
            COUNT(CASE WHEN b.status = 'occupied' THEN 1 END) as occupied_beds,
            ROUND(COUNT(CASE WHEN b.status = 'occupied' THEN 1 END)::FLOAT / 
                  COUNT(b.bed_id) * 100, 2) as occupancy_rate
        FROM departments d
        LEFT JOIN beds b ON d.department_id = b.department_id
        """
        if department_id:
            query += " WHERE d.department_id = :department_id"
            query += " GROUP BY d.name"
            return self.execute_query(query, {'department_id': department_id}).fetchall()
        else:
            query += " GROUP BY d.name"
            return self.execute_query(query).fetchall()

    def get_supply_levels(self):
        """Get current supply levels"""
        query = """
        SELECT 
            name,
            category,
            current_quantity,
            minimum_quantity,
            CASE 
                WHEN current_quantity <= minimum_quantity THEN 'Reorder Required'
                WHEN current_quantity <= minimum_quantity * 1.5 THEN 'Low Stock'
                ELSE 'Adequate'
            END as stock_status
        FROM supplies
        ORDER BY 
            CASE 
                WHEN current_quantity <= minimum_quantity THEN 1
                WHEN current_quantity <= minimum_quantity * 1.5 THEN 2
                ELSE 3
            END,
            name
        """
        return self.execute_query(query).fetchall()

# Test the connection if run directly
if __name__ == "__main__":
    db = DatabaseManager()
    try:
        db.execute_query("SELECT 1")
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {str(e)}")