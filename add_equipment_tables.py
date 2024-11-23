from database_utils import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_equipment_tables():
    db = DatabaseManager()
    
    try:
        with db.engine.begin() as conn:
            # First drop existing tables if they exist
            logger.info("Dropping existing tables...")
            conn.execute(text("""
                DROP TABLE IF EXISTS equipment_maintenance CASCADE;
                DROP TABLE IF EXISTS equipment_usage CASCADE;
            """))

            logger.info("Adding equipment maintenance table...")
            conn.execute(text("""
                CREATE TABLE equipment_maintenance (
                    maintenance_id SERIAL PRIMARY KEY,
                    equipment_id INTEGER REFERENCES equipment(equipment_id),
                    maintenance_type VARCHAR(50) NOT NULL,
                    scheduled_date TIMESTAMP NOT NULL,
                    completed_date TIMESTAMP,
                    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            logger.info("Adding equipment usage tracking table...")
            conn.execute(text("""
                CREATE TABLE equipment_usage (
                    usage_id SERIAL PRIMARY KEY,
                    equipment_id INTEGER REFERENCES equipment(equipment_id),
                    department_id INTEGER REFERENCES departments(department_id),
                    staff_id INTEGER REFERENCES staff(staff_id),
                    patient_id INTEGER REFERENCES patients(patient_id),
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status VARCHAR(20) NOT NULL DEFAULT 'in_use',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # Add new columns to equipment table if they don't exist
            logger.info("Adding new columns to equipment table...")
            conn.execute(text("""
                DO $$ 
                BEGIN 
                    BEGIN
                        ALTER TABLE equipment ADD COLUMN last_maintenance_date DATE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    BEGIN
                        ALTER TABLE equipment ADD COLUMN next_maintenance_date DATE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    BEGIN
                        ALTER TABLE equipment ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    
                    BEGIN
                        ALTER TABLE equipment ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;
            """))

            # Create indexes for better performance
            logger.info("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_equipment_maintenance_equipment_id 
                ON equipment_maintenance(equipment_id);
                
                CREATE INDEX IF NOT EXISTS idx_equipment_maintenance_status 
                ON equipment_maintenance(status);
                
                CREATE INDEX IF NOT EXISTS idx_equipment_usage_equipment_id 
                ON equipment_usage(equipment_id);
                
                CREATE INDEX IF NOT EXISTS idx_equipment_usage_department_id 
                ON equipment_usage(department_id);
                
                CREATE INDEX IF NOT EXISTS idx_equipment_status 
                ON equipment(status);
            """))

            # Create trigger for updating timestamps
            logger.info("Creating triggers for timestamp updates...")
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_timestamp_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_equipment_timestamp ON equipment;
                CREATE TRIGGER update_equipment_timestamp
                    BEFORE UPDATE ON equipment
                    FOR EACH ROW
                    EXECUTE FUNCTION update_timestamp_column();
                    
                DROP TRIGGER IF EXISTS update_maintenance_timestamp ON equipment_maintenance;
                CREATE TRIGGER update_maintenance_timestamp
                    BEFORE UPDATE ON equipment_maintenance
                    FOR EACH ROW
                    EXECUTE FUNCTION update_timestamp_column();
            """))

            logger.info("Successfully added equipment tracking tables and modifications!")

    except Exception as e:
        logger.error(f"Error adding equipment tables: {str(e)}")
        raise

if __name__ == "__main__":
    add_equipment_tables()