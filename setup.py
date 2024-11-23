import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database():
    """Create the healthcare database if it doesn't exist"""
    try:
        # Connect to default PostgreSQL database first
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='healthcare_db'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE healthcare_db")
            logger.info("Database 'healthcare_db' created successfully")
        else:
            logger.info("Database 'healthcare_db' already exists")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise

def test_connection():
    """Test connection to the healthcare database"""
    try:
        conn = psycopg2.connect(
            dbname="healthcare_db",
            user=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        logger.info("Successfully connected to healthcare_db")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False

def setup_database():
    """Main setup function"""
    try:
        # Create .env file if it doesn't exist
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                f.write("""DB_USERNAME=postgres
DB_PASSWORD=95122
DB_HOST=localhost
DB_PORT=5432
DB_NAME=healthcare_db""")
            logger.info("Created .env file - please update with your database password")
            return False
            
        # Load environment variables
        load_dotenv()
        
        # Create database
        create_database()
        
        # Test connection
        if test_connection():
            logger.info("Database setup completed successfully")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database()