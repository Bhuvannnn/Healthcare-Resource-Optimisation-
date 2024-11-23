from database_utils import DatabaseManager
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShiftType(Enum):
    MORNING = "morning"    # e.g., 7 AM - 3 PM
    AFTERNOON = "afternoon"  # e.g., 3 PM - 11 PM
    NIGHT = "night"      # e.g., 11 PM - 7 AM

class StaffSchedulingSystem:
    def __init__(self):
        self.db = DatabaseManager()

    def add_staff_member(self, first_name: str, last_name: str, role: str, 
                        department: str, qualification: str) -> int:
        """Add a new staff member"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO staff (first_name, last_name, role, department, 
                                qualification, hire_date, status)
                VALUES (:first_name, :last_name, :role, :department, 
                        :qualification, CURRENT_DATE, 'active')
                RETURNING staff_id;
                """),
                {
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role,
                    'department': department,
                    'qualification': qualification
                }
            )
            staff_id = result.scalar()
            logger.info(f"Added new staff member: {first_name} {last_name} with ID: {staff_id}")
            return staff_id

    def schedule_shift(self, staff_id: int, department_id: int, 
                      shift_start: datetime, shift_end: datetime) -> int:
        """Schedule a shift for a staff member"""
        with self.db.engine.begin() as conn:
            # Verify staff member exists and is active
            staff = conn.execute(
                text("SELECT status FROM staff WHERE staff_id = :staff_id"),
                {'staff_id': staff_id}
            ).fetchone()
            
            if not staff:
                raise ValueError(f"Staff member {staff_id} not found")
            if staff[0] != 'active':
                raise ValueError(f"Staff member {staff_id} is not active")

            # Check for overlapping shifts
            overlap = conn.execute(
                text("""
                SELECT COUNT(*) FROM staff_schedules
                WHERE staff_id = :staff_id
                AND (
                    (shift_start <= :end AND shift_end >= :start)
                    OR
                    (shift_start <= :start AND shift_end >= :start)
                )
                AND status != 'cancelled'
                """),
                {
                    'staff_id': staff_id,
                    'start': shift_start,
                    'end': shift_end
                }
            ).scalar()

            if overlap > 0:
                raise ValueError(f"Overlapping shift found for staff member {staff_id}")

            # Create the schedule
            result = conn.execute(
                text("""
                INSERT INTO staff_schedules 
                (staff_id, department_id, shift_start, shift_end, status)
                VALUES (:staff_id, :dept_id, :start, :end, 'scheduled')
                RETURNING schedule_id;
                """),
                {
                    'staff_id': staff_id,
                    'dept_id': department_id,
                    'start': shift_start,
                    'end': shift_end
                }
            )
            
            schedule_id = result.scalar()
            logger.info(f"Scheduled shift {schedule_id} for staff member {staff_id}")
            return schedule_id

    def get_staff_schedule(self, staff_id: int, start_date: datetime, 
                         end_date: datetime) -> List[Dict]:
        """Get schedule for a staff member within a date range"""
        with self.db.engine.connect() as conn:
            results = conn.execute(
                text("""
                SELECT 
                    ss.schedule_id,
                    ss.shift_start,
                    ss.shift_end,
                    d.name as department_name,
                    ss.status
                FROM staff_schedules ss
                JOIN departments d ON ss.department_id = d.department_id
                WHERE ss.staff_id = :staff_id
                AND ss.shift_start >= :start_date
                AND ss.shift_start < :end_date
                ORDER BY ss.shift_start;
                """),
                {
                    'staff_id': staff_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            ).fetchall()

            return [{
                'schedule_id': row[0],
                'shift_start': row[1],
                'shift_end': row[2],
                'department': row[3],
                'status': row[4]
            } for row in results]

    def get_department_schedule(self, department_id: int, date: datetime) -> List[Dict]:
        """Get all staff scheduled for a department on a specific date"""
        with self.db.engine.connect() as conn:
            results = conn.execute(
                text("""
                SELECT 
                    s.staff_id,
                    s.first_name,
                    s.last_name,
                    s.role,
                    ss.shift_start,
                    ss.shift_end,
                    ss.status
                FROM staff_schedules ss
                JOIN staff s ON ss.staff_id = s.staff_id
                WHERE ss.department_id = :dept_id
                AND DATE(ss.shift_start) = DATE(:date)
                AND ss.status = 'scheduled'
                ORDER BY ss.shift_start;
                """),
                {
                    'dept_id': department_id,
                    'date': date
                }
            ).fetchall()

            return [{
                'staff_id': row[0],
                'name': f"{row[1]} {row[2]}",
                'role': row[3],
                'shift_start': row[4],
                'shift_end': row[5],
                'status': row[6]
            } for row in results]

    def update_shift_status(self, schedule_id: int, status: str) -> bool:
        """Update the status of a scheduled shift"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                UPDATE staff_schedules
                SET status = :status
                WHERE schedule_id = :schedule_id
                RETURNING schedule_id;
                """),
                {
                    'schedule_id': schedule_id,
                    'status': status
                }
            ).scalar()
            
            success = result is not None
            if success:
                logger.info(f"Updated shift {schedule_id} status to {status}")
            return success

    def get_staff_workload(self, staff_id: int, start_date: datetime, 
                          end_date: datetime) -> Dict:
        """Get workload statistics for a staff member"""
        with self.db.engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT 
                    COUNT(*) as total_shifts,
                    SUM(EXTRACT(EPOCH FROM (shift_end - shift_start))/3600) as total_hours,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_shifts,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_shifts
                FROM staff_schedules
                WHERE staff_id = :staff_id
                AND shift_start >= :start_date
                AND shift_start < :end_date;
                """),
                {
                    'staff_id': staff_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            ).fetchone()

            return {
                'total_shifts': result[0],
                'total_hours': round(result[1] if result[1] else 0, 2),
                'completed_shifts': result[2],
                'cancelled_shifts': result[3],
                'average_hours_per_shift': round(result[1] / result[0] if result[0] > 0 else 0, 2)
            }

    def optimize_schedule(self, department_id: int, date: datetime) -> List[Dict]:
        """Optimize staff schedule based on department needs"""
        with self.db.engine.connect() as conn:
            # Get department staffing requirements
            dept_info = conn.execute(
                text("""
                SELECT bed_capacity, name
                FROM departments
                WHERE department_id = :dept_id;
                """),
                {'dept_id': department_id}
            ).fetchone()

            if not dept_info:
                raise ValueError(f"Department {department_id} not found")

            bed_capacity = dept_info[0]
            
            # Calculate minimum staff needed based on bed capacity
            # Example: 1 nurse per 4 beds per shift
            min_nurses_per_shift = max(2, bed_capacity // 4)
            
            # Get current schedule
            current_schedule = self.get_department_schedule(department_id, date)
            
            # Analyze current coverage
            shifts_coverage = {
                'morning': 0,
                'afternoon': 0,
                'night': 0
            }
            
            for shift in current_schedule:
                shift_hour = shift['shift_start'].hour
                if 7 <= shift_hour < 15:
                    shifts_coverage['morning'] += 1
                elif 15 <= shift_hour < 23:
                    shifts_coverage['afternoon'] += 1
                else:
                    shifts_coverage['night'] += 1

            # Generate recommendations
            recommendations = []
            for shift_type, count in shifts_coverage.items():
                if count < min_nurses_per_shift:
                    recommendations.append({
                        'shift_type': shift_type,
                        'additional_staff_needed': min_nurses_per_shift - count,
                        'priority': 'High' if count < min_nurses_per_shift - 1 else 'Medium'
                    })

            return {
                'department': dept_info[1],
                'date': date,
                'current_coverage': shifts_coverage,
                'minimum_required': min_nurses_per_shift,
                'recommendations': recommendations
            }