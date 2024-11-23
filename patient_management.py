from database_utils import DatabaseManager
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatientManagementSystem:
    def __init__(self):
        self.db = DatabaseManager()

    def add_patient(self, first_name: str, last_name: str, date_of_birth: str, 
                   gender: str, contact_number: str, address: str) -> int:
        """Add a new patient to the system"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO patients (first_name, last_name, date_of_birth, gender, contact_number, address)
                VALUES (:first_name, :last_name, :dob, :gender, :contact, :address)
                RETURNING patient_id;
                """),
                {
                    'first_name': first_name,
                    'last_name': last_name,
                    'dob': date_of_birth,
                    'gender': gender,
                    'contact': contact_number,
                    'address': address
                }
            )
            patient_id = result.scalar()
            logger.info(f"Added new patient: {first_name} {last_name} with ID: {patient_id}")
            return patient_id

    def find_available_bed(self, department_id: int, conn) -> Optional[int]:
        """Find an available bed in the specified department"""
        result = conn.execute(
            text("""
            SELECT bed_id 
            FROM beds 
            WHERE department_id = :dept_id 
            AND status = 'available' 
            LIMIT 1;
            """),
            {'dept_id': department_id}
        )
        return result.scalar()

    def admit_patient(self, patient_id: int, department_id: int, 
                     admission_type: str) -> Dict:
        """Admit a patient to the hospital"""
        with self.db.engine.begin() as conn:
            # First check if patient exists
            patient_check = conn.execute(
                text("SELECT patient_id FROM patients WHERE patient_id = :pid"),
                {'pid': patient_id}
            ).scalar()
            
            if not patient_check:
                raise ValueError(f"Patient with ID {patient_id} not found")

            # Find available bed
            bed_id = self.find_available_bed(department_id, conn)
            if not bed_id:
                raise ValueError(f"No available beds in department {department_id}")

            # Update bed status
            conn.execute(
                text("""
                UPDATE beds 
                SET status = 'occupied' 
                WHERE bed_id = :bed_id
                """),
                {'bed_id': bed_id}
            )

            # Create admission record
            result = conn.execute(
                text("""
                INSERT INTO admissions (
                    patient_id, department_id, bed_id, 
                    admission_date, admission_type, status
                )
                VALUES (
                    :patient_id, :department_id, :bed_id, 
                    CURRENT_TIMESTAMP, :admission_type, 'active'
                )
                RETURNING admission_id, admission_date;
                """),
                {
                    'patient_id': patient_id,
                    'department_id': department_id,
                    'bed_id': bed_id,
                    'admission_type': admission_type
                }
            )
            
            admission_data = result.fetchone()
            
            return {
                'admission_id': admission_data[0],
                'admission_date': admission_data[1],
                'bed_id': bed_id,
                'department_id': department_id
            }

    def discharge_patient(self, admission_id: int) -> Dict:
        """Discharge a patient"""
        with self.db.engine.begin() as conn:
            # Get admission details
            admission = conn.execute(
                text("""
                SELECT bed_id, patient_id 
                FROM admissions 
                WHERE admission_id = :admission_id 
                AND status = 'active'
                """),
                {'admission_id': admission_id}
            ).fetchone()

            if not admission:
                raise ValueError(f"No active admission found with ID {admission_id}")

            # Update admission record
            conn.execute(
                text("""
                UPDATE admissions 
                SET discharge_date = CURRENT_TIMESTAMP,
                    status = 'discharged'
                WHERE admission_id = :admission_id
                """),
                {'admission_id': admission_id}
            )

            # Free up the bed
            conn.execute(
                text("""
                UPDATE beds 
                SET status = 'available' 
                WHERE bed_id = :bed_id
                """),
                {'bed_id': admission[0]}
            )

            return {
                'admission_id': admission_id,
                'patient_id': admission[1],
                'discharge_date': datetime.now(),
                'bed_id': admission[0]
            }

    def get_department_status(self, department_id: int) -> Dict:
        """Get current status of a department"""
        with self.db.engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT 
                    d.name as department_name,
                    d.bed_capacity as total_beds,
                    COUNT(DISTINCT CASE WHEN b.status = 'occupied' THEN b.bed_id END) as occupied_beds,
                    COUNT(DISTINCT CASE WHEN b.status = 'available' THEN b.bed_id END) as available_beds,
                    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.admission_id END) as active_patients
                FROM departments d
                LEFT JOIN beds b ON d.department_id = b.department_id
                LEFT JOIN admissions a ON b.bed_id = a.bed_id AND a.status = 'active'
                WHERE d.department_id = :dept_id
                GROUP BY d.department_id, d.name, d.bed_capacity;
                """),
                {'dept_id': department_id}
            ).fetchone()
            
            return {
                'department_name': result[0],
                'total_beds': result[1],
                'occupied_beds': result[2],
                'available_beds': result[3],
                'active_patients': result[4],
                'occupancy_rate': round((result[2] / result[1]) * 100, 2) if result[1] > 0 else 0
            }

    def get_patient_history(self, patient_id: int) -> List[Dict]:
        """Get admission history for a patient"""
        with self.db.engine.connect() as conn:
            results = conn.execute(
                text("""
                SELECT 
                    a.admission_id,
                    a.admission_date,
                    a.discharge_date,
                    a.admission_type,
                    d.name as department_name,
                    a.status
                FROM admissions a
                JOIN departments d ON a.department_id = d.department_id
                WHERE a.patient_id = :patient_id
                ORDER BY a.admission_date DESC;
                """),
                {'patient_id': patient_id}
            ).fetchall()
            
            return [{
                'admission_id': row[0],
                'admission_date': row[1],
                'discharge_date': row[2],
                'admission_type': row[3],
                'department': row[4],
                'status': row[5]
            } for row in results]

    def verify_patient_exists(self, patient_id: int) -> bool:
        """Verify if a patient exists in the system"""
        with self.db.engine.connect() as conn:
            result = conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM patients WHERE patient_id = :pid)"),
                {'pid': patient_id}
            ).scalar()
            return result