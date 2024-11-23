from database_utils import DatabaseManager
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EquipmentStatus(Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    OUT_OF_SERVICE = "out_of_service"

class MaintenanceType(Enum):
    ROUTINE = "routine"
    REPAIR = "repair"
    CALIBRATION = "calibration"
    INSPECTION = "inspection"

class EquipmentTrackingSystem:
    def __init__(self):
        self.db = DatabaseManager()

    def add_equipment(self, name: str, equipment_type: str, department_id: int,
                     maintenance_interval_days: int = 90) -> int:
        """Add new equipment to the system"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO equipment (
                    name, type, department_id, status, 
                    last_maintenance_date, next_maintenance_date
                )
                VALUES (
                    :name, :type, :dept_id, 'available',
                    CURRENT_DATE, CURRENT_DATE + :maintenance_interval * INTERVAL '1 day'
                )
                RETURNING equipment_id;
                """),
                {
                    'name': name,
                    'type': equipment_type,
                    'dept_id': department_id,
                    'maintenance_interval': maintenance_interval_days
                }
            )
            equipment_id = result.scalar()
            logger.info(f"Added new equipment: {name} with ID: {equipment_id}")
            return equipment_id

    def update_equipment_status(self, equipment_id: int, status: EquipmentStatus,
                              note: str = None) -> bool:
        """Update equipment status"""
        with self.db.engine.begin() as conn:
            # First update equipment status
            result = conn.execute(
                text("""
                UPDATE equipment
                SET status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE equipment_id = :equipment_id
                RETURNING equipment_id;
                """),
                {
                    'equipment_id': equipment_id,
                    'status': status.value
                }
            )
            
            if result.rowcount > 0:
                # Log the status change
                conn.execute(
                    text("""
                    INSERT INTO equipment_usage (
                        equipment_id, status, notes, start_time
                    )
                    VALUES (:equipment_id, :status, :notes, CURRENT_TIMESTAMP);
                    """),
                    {
                        'equipment_id': equipment_id,
                        'status': status.value,
                        'notes': note
                    }
                )
                logger.info(f"Updated equipment {equipment_id} status to {status.value}")
                return True
            return False

    def assign_equipment(self, equipment_id: int, department_id: int,
                        staff_id: int, patient_id: Optional[int] = None) -> Dict:
        """Assign equipment to a department/patient"""
        with self.db.engine.begin() as conn:
            # Check if equipment is available
            equipment = conn.execute(
                text("""
                SELECT status, department_id 
                FROM equipment 
                WHERE equipment_id = :equipment_id
                """),
                {'equipment_id': equipment_id}
            ).fetchone()
            
            if not equipment:
                raise ValueError(f"Equipment {equipment_id} not found")
            
            if equipment[0] != EquipmentStatus.AVAILABLE.value:
                raise ValueError(f"Equipment {equipment_id} is not available")

            # Create usage record
            result = conn.execute(
                text("""
                INSERT INTO equipment_usage (
                    equipment_id, department_id, staff_id, patient_id,
                    start_time, status
                )
                VALUES (
                    :equipment_id, :department_id, :staff_id, :patient_id,
                    CURRENT_TIMESTAMP, 'in_use'
                )
                RETURNING usage_id;
                """),
                {
                    'equipment_id': equipment_id,
                    'department_id': department_id,
                    'staff_id': staff_id,
                    'patient_id': patient_id
                }
            )
            usage_id = result.scalar()

            # Update equipment status
            conn.execute(
                text("""
                UPDATE equipment 
                SET status = 'in_use',
                    department_id = :department_id,
                    updated_at = CURRENT_TIMESTAMP
                WHERE equipment_id = :equipment_id;
                """),
                {
                    'equipment_id': equipment_id,
                    'department_id': department_id
                }
            )

            return {
                'usage_id': usage_id,
                'equipment_id': equipment_id,
                'department_id': department_id,
                'start_time': datetime.now()
            }

    def add_equipment(self, name: str, equipment_type: str, department_id: int,
                     maintenance_interval_days: int = 90) -> int:
        """Add new equipment to the system"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO equipment (
                    name, type, department_id, status, 
                    last_maintenance_date, next_maintenance_date
                )
                VALUES (
                    :name, :type, :dept_id, 'available',
                    CURRENT_DATE, CURRENT_DATE + :maintenance_interval * INTERVAL '1 day'
                )
                RETURNING equipment_id;
                """),
                {
                    'name': name,
                    'type': equipment_type,
                    'dept_id': department_id,
                    'maintenance_interval': maintenance_interval_days
                }
            )
            equipment_id = result.scalar()
            logger.info(f"Added new equipment: {name} with ID: {equipment_id}")
            return equipment_id    

    def release_equipment(self, usage_id: int) -> Dict:
        """Release equipment from current assignment"""
        with self.db.engine.begin() as conn:
            # Update usage record
            usage = conn.execute(
                text("""
                UPDATE equipment_usage
                SET end_time = CURRENT_TIMESTAMP,
                    status = 'completed'
                WHERE usage_id = :usage_id
                AND end_time IS NULL
                RETURNING equipment_id;
                """),
                {'usage_id': usage_id}
            ).fetchone()
            
            if not usage:
                raise ValueError(f"Usage record {usage_id} not found or already completed")

            # Update equipment status
            conn.execute(
                text("""
                UPDATE equipment
                SET status = 'available',
                    updated_at = CURRENT_TIMESTAMP
                WHERE equipment_id = :equipment_id;
                """),
                {'equipment_id': usage[0]}
            )

            return {
                'usage_id': usage_id,
                'equipment_id': usage[0],
                'release_time': datetime.now()
            }

    def schedule_maintenance(self, equipment_id: int, 
                           maintenance_type: MaintenanceType,
                           scheduled_date: datetime,
                           notes: str = None) -> int:
        """Schedule maintenance for equipment"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO equipment_maintenance (
                    equipment_id, maintenance_type, scheduled_date,
                    status, notes
                )
                VALUES (
                    :equipment_id, :maintenance_type, :scheduled_date,
                    'scheduled', :notes
                )
                RETURNING maintenance_id;
                """),
                {
                    'equipment_id': equipment_id,
                    'maintenance_type': maintenance_type.value,
                    'scheduled_date': scheduled_date,
                    'notes': notes
                }
            )
            maintenance_id = result.scalar()
            
            # Update equipment next maintenance date
            conn.execute(
                text("""
                UPDATE equipment
                SET next_maintenance_date = :scheduled_date
                WHERE equipment_id = :equipment_id;
                """),
                {
                    'equipment_id': equipment_id,
                    'scheduled_date': scheduled_date
                }
            )
            
            return maintenance_id

    def get_equipment_history(self, equipment_id: int) -> List[Dict]:
        """Get usage and maintenance history for equipment"""
        with self.db.engine.connect() as conn:
            # Get usage history
            usage_history = conn.execute(
                text("""
                SELECT 
                    u.usage_id,
                    u.start_time,
                    u.end_time,
                    u.status,
                    d.name as department,
                    s.first_name || ' ' || s.last_name as staff_name,
                    p.first_name || ' ' || p.last_name as patient_name
                FROM equipment_usage u
                LEFT JOIN departments d ON u.department_id = d.department_id
                LEFT JOIN staff s ON u.staff_id = s.staff_id
                LEFT JOIN patients p ON u.patient_id = p.patient_id
                WHERE u.equipment_id = :equipment_id
                ORDER BY u.start_time DESC;
                """),
                {'equipment_id': equipment_id}
            ).fetchall()

            # Get maintenance history
            maintenance_history = conn.execute(
                text("""
                SELECT 
                    maintenance_id,
                    maintenance_type,
                    scheduled_date,
                    completed_date,
                    status,
                    notes
                FROM equipment_maintenance
                WHERE equipment_id = :equipment_id
                ORDER BY scheduled_date DESC;
                """),
                {'equipment_id': equipment_id}
            ).fetchall()

            return {
                'usage_history': [{
                    'usage_id': u[0],
                    'start_time': u[1],
                    'end_time': u[2],
                    'status': u[3],
                    'department': u[4],
                    'staff': u[5],
                    'patient': u[6]
                } for u in usage_history],
                'maintenance_history': [{
                    'maintenance_id': m[0],
                    'type': m[1],
                    'scheduled_date': m[2],
                    'completed_date': m[3],
                    'status': m[4],
                    'notes': m[5]
                } for m in maintenance_history]
            }

    def get_department_equipment(self, department_id: int) -> List[Dict]:
        """Get all equipment in a department with their status"""
        with self.db.engine.connect() as conn:
            results = conn.execute(
                text("""
                SELECT 
                    e.equipment_id,
                    e.name,
                    e.type,
                    e.status,
                    e.last_maintenance_date,
                    e.next_maintenance_date,
                    COUNT(DISTINCT eu.usage_id) as total_uses
                FROM equipment e
                LEFT JOIN equipment_usage eu ON e.equipment_id = eu.equipment_id
                WHERE e.department_id = :dept_id
                GROUP BY e.equipment_id
                ORDER BY e.type, e.name;
                """),
                {'dept_id': department_id}
            ).fetchall()

            return [{
                'equipment_id': r[0],
                'name': r[1],
                'type': r[2],
                'status': r[3],
                'last_maintenance': r[4],
                'next_maintenance': r[5],
                'total_uses': r[6]
            } for r in results]