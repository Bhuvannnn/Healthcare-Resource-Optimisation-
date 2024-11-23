import logging
from equipment_tracking import (
    EquipmentTrackingSystem, 
    EquipmentStatus, 
    MaintenanceType
)
from datetime import datetime, timedelta
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_equipment_tracking():
    """Test the equipment tracking system functionality"""
    tracker = EquipmentTrackingSystem()
    
    try:
        logger.info("\nTesting Equipment Tracking System...")

        # 1. Add test equipment
        test_equipment = [
            ("Ventilator X100", "Ventilator", 1),  # Emergency department
            ("MRI Scanner", "Imaging", 2),         # ICU
            ("Patient Monitor", "Monitor", 1)      # Emergency department
        ]
        
        equipment_ids = []
        for name, eq_type, dept_id in test_equipment:
            equipment_id = tracker.add_equipment(
                name=name,
                equipment_type=eq_type,
                department_id=dept_id,
                maintenance_interval_days=90
            )
            equipment_ids.append(equipment_id)
            logger.info(f"Added equipment: {name} with ID: {equipment_id}")

        # 2. Test equipment assignment
        logger.info("\nTesting equipment assignment...")
        assignments = []
        for equipment_id in equipment_ids:
            try:
                assignment = tracker.assign_equipment(
                    equipment_id=equipment_id,
                    department_id=1,  # Emergency department
                    staff_id=1,       # Assuming staff ID 1 exists
                    patient_id=1      # Assuming patient ID 1 exists
                )
                assignments.append(assignment)
                logger.info(f"Assigned equipment {equipment_id}: {assignment}")
            except Exception as e:
                logger.error(f"Failed to assign equipment {equipment_id}: {str(e)}")

        # 3. Test equipment status updates
        logger.info("\nTesting status updates...")
        for equipment_id in equipment_ids[:2]:  # Update first two equipment
            success = tracker.update_equipment_status(
                equipment_id=equipment_id,
                status=EquipmentStatus.IN_USE,
                note="In use for patient care"
            )
            logger.info(f"Updated equipment {equipment_id} status: {success}")

        # 4. Schedule maintenance
        logger.info("\nScheduling maintenance...")
        maintenance_date = datetime.now() + timedelta(days=30)
        for equipment_id in equipment_ids:
            maintenance_id = tracker.schedule_maintenance(
                equipment_id=equipment_id,
                maintenance_type=MaintenanceType.ROUTINE,
                scheduled_date=maintenance_date,
                notes="Regular maintenance check"
            )
            logger.info(f"Scheduled maintenance {maintenance_id} for equipment {equipment_id}")

        # 5. Test equipment release
        logger.info("\nTesting equipment release...")
        for assignment in assignments:
            try:
                release = tracker.release_equipment(assignment['usage_id'])
                logger.info(f"Released equipment: {release}")
            except Exception as e:
                logger.error(f"Failed to release equipment: {str(e)}")

        # 6. Get equipment history
        logger.info("\nChecking equipment history...")
        for equipment_id in equipment_ids:
            history = tracker.get_equipment_history(equipment_id)
            logger.info(f"Equipment {equipment_id} history:")
            logger.info(f"- Usage records: {len(history['usage_history'])}")
            logger.info(f"- Maintenance records: {len(history['maintenance_history'])}")

        # 7. Check department equipment
        logger.info("\nChecking department equipment...")
        dept_equipment = tracker.get_department_equipment(1)  # Emergency department
        logger.info(f"Department 1 has {len(dept_equipment)} equipment items:")
        for equip in dept_equipment:
            logger.info(f"- {equip['name']} ({equip['status']})")

        logger.info("\nAll equipment tracking tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_equipment_tracking()