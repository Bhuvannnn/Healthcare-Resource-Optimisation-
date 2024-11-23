from database_utils import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_supply_schema():
    db = DatabaseManager()
    
    try:
        with db.engine.begin() as conn:
            logger.info("Updating supplies table...")
            conn.execute(text("""
                ALTER TABLE supplies
                ADD COLUMN IF NOT EXISTS cost_per_unit DECIMAL(10,2),
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            """))

            logger.info("Creating supply orders table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS supply_orders (
                    order_id SERIAL PRIMARY KEY,
                    supply_id INTEGER REFERENCES supplies(supply_id),
                    quantity_ordered INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    order_date TIMESTAMP NOT NULL,
                    expected_delivery TIMESTAMP,
                    actual_delivery TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            logger.info("Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_supply_transactions_date 
                ON supply_transactions(transaction_date);
                
                CREATE INDEX IF NOT EXISTS idx_supply_transactions_department 
                ON supply_transactions(department_id);
                
                CREATE INDEX IF NOT EXISTS idx_supply_orders_status 
                ON supply_orders(status);
                
                CREATE INDEX IF NOT EXISTS idx_supplies_quantity 
                ON supplies(current_quantity);
            """))

            logger.info("Supply management schema updated successfully!")
            
    except Exception as e:
        logger.error(f"Error updating supply schema: {str(e)}")
        raise

if __name__ == "__main__":
    update_supply_schema()