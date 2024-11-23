import os
from dotenv import load_dotenv
import psycopg2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_schema():
    """Run the database schema creation script"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Connect to the database
        conn = psycopg2.connect(
            dbname="healthcare_db",
            user=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Read the schema SQL from our previous artifact
        schema_sql = """
-- Create tables for core entities

-- Staff table to store healthcare worker information
CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL,
    department VARCHAR(50) NOT NULL,
    qualification VARCHAR(100),
    hire_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments table
CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    bed_capacity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Equipment inventory
CREATE TABLE equipment (
    equipment_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    department_id INTEGER REFERENCES departments(department_id),
    status VARCHAR(20) DEFAULT 'available',
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical supplies inventory
CREATE TABLE supplies (
    supply_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    current_quantity INTEGER NOT NULL,
    minimum_quantity INTEGER NOT NULL,
    unit VARCHAR(20) NOT NULL,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patient information
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    contact_number VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bed management
CREATE TABLE beds (
    bed_id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(department_id),
    bed_number VARCHAR(20) NOT NULL,
    bed_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staff schedules
CREATE TABLE staff_schedules (
    schedule_id SERIAL PRIMARY KEY,
    staff_id INTEGER REFERENCES staff(staff_id),
    department_id INTEGER REFERENCES departments(department_id),
    shift_start TIMESTAMP NOT NULL,
    shift_end TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patient admissions
CREATE TABLE admissions (
    admission_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    department_id INTEGER REFERENCES departments(department_id),
    bed_id INTEGER REFERENCES beds(bed_id),
    admission_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP,
    admission_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supply transactions
CREATE TABLE supply_transactions (
    transaction_id SERIAL PRIMARY KEY,
    supply_id INTEGER REFERENCES supplies(supply_id),
    department_id INTEGER REFERENCES departments(department_id),
    transaction_type VARCHAR(20) NOT NULL, -- 'in' or 'out'
    quantity INTEGER NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES staff(staff_id)
);

-- Equipment usage logs
CREATE TABLE equipment_usage (
    usage_id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(equipment_id),
    department_id INTEGER REFERENCES departments(department_id),
    staff_id INTEGER REFERENCES staff(staff_id),
    patient_id INTEGER REFERENCES patients(patient_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'in_use',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for frequently accessed columns
CREATE INDEX idx_staff_department ON staff(department);
CREATE INDEX idx_admission_dates ON admissions(admission_date, discharge_date);
CREATE INDEX idx_bed_status ON beds(status);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_supply_quantity ON supplies(current_quantity);
        """
        
        # Execute the schema SQL
        cursor.execute(schema_sql)
        
        # Commit the changes
        conn.commit()
        
        logger.info("Schema created successfully")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating schema: {str(e)}")
        raise

if __name__ == "__main__":
    run_schema()