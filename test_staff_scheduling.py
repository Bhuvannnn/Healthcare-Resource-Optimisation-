import logging
from staff_scheduling import StaffSchedulingSystem
from datetime import datetime, timedelta
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_staff_scheduling():
    """Test the staff scheduling system functionality"""
    scheduler = StaffSchedulingSystem()
    
    try:
        logger.info("\nTesting Staff Scheduling System...")

        # 1. Add test staff members
        test_staff = [
            ("John", "Doe", "Nurse", "Emergency", "RN"),
            ("Jane", "Smith", "Doctor", "ICU", "MD"),
            ("Mike", "Johnson", "Nurse", "General Medicine", "RN")
        ]
        
        staff_ids = []
        for staff in test_staff:
            staff_id = scheduler.add_staff_member(*staff)
            staff_ids.append(staff_id)
            logger.info(f"Added staff member: {staff[0]} {staff[1]} with ID: {staff_id}")

        # 2. Schedule shifts for next week
        logger.info("\nScheduling shifts...")
        now = datetime.now()
        shifts = []
        
        # Morning shift (7 AM - 3 PM)
        shift_start = datetime(now.year, now.month, now.day, 7, 0) + timedelta(days=1)
        shift_end = shift_start + timedelta(hours=8)
        
        for staff_id in staff_ids:
            try:
                schedule_id = scheduler.schedule_shift(
                    staff_id=staff_id,
                    department_id=1,  # Emergency department
                    shift_start=shift_start,
                    shift_end=shift_end
                )
                shifts.append(schedule_id)
                logger.info(f"Scheduled shift {schedule_id} for staff {staff_id}")
                
                # Schedule next day afternoon shift
                next_day = shift_start + timedelta(days=1)
                afternoon_start = datetime(next_day.year, next_day.month, next_day.day, 15, 0)
                schedule_id = scheduler.schedule_shift(
                    staff_id=staff_id,
                    department_id=1,
                    shift_start=afternoon_start,
                    shift_end=afternoon_start + timedelta(hours=8)
                )
                shifts.append(schedule_id)
                logger.info(f"Scheduled afternoon shift {schedule_id} for staff {staff_id}")
                
            except Exception as e:
                logger.error(f"Failed to schedule shift for staff {staff_id}: {str(e)}")

        # 3. Test schedule retrieval
        logger.info("\nRetrieving schedules...")
        for staff_id in staff_ids:
            schedule = scheduler.get_staff_schedule(
                staff_id=staff_id,
                start_date=now,
                end_date=now + timedelta(days=7)
            )
            logger.info(f"Staff {staff_id} has {len(schedule)} scheduled shifts")

        # 4. Test department schedule
        logger.info("\nChecking department schedule...")
        dept_schedule = scheduler.get_department_schedule(
            department_id=1,
            date=shift_start
        )
        logger.info(f"Department has {len(dept_schedule)} staff scheduled for {shift_start.date()}")

        # 5. Test workload analysis
        logger.info("\nAnalyzing staff workload...")
        for staff_id in staff_ids:
            workload = scheduler.get_staff_workload(
                staff_id=staff_id,
                start_date=now,
                end_date=now + timedelta(days=7)
            )
            logger.info(f"Staff {staff_id} workload: {workload}")

        # 6. Test schedule optimization
        logger.info("\nTesting schedule optimization...")
        optimization = scheduler.optimize_schedule(
            department_id=1,
            date=shift_start
        )
        logger.info(f"Schedule optimization results: {optimization}")

        # 7. Test shift status updates
        logger.info("\nUpdating shift statuses...")
        for schedule_id in shifts[:2]:  # Mark first two shifts as completed
            success = scheduler.update_shift_status(schedule_id, "completed")
            logger.info(f"Updated shift {schedule_id} status: {success}")

        logger.info("\nAll staff scheduling tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_staff_scheduling()