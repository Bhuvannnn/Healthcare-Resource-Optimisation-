import logging
from patient_management import PatientManagementSystem
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_patient_system():
    """Test the patient management system functionality"""
    patient_system = PatientManagementSystem()
    
    try:
        # Clean up any existing test data
        with patient_system.db.engine.begin() as conn:
            conn.execute(text("TRUNCATE patients, admissions RESTART IDENTITY CASCADE;"))
        
        # 1. Add test patients
        logger.info("\nAdding test patients...")
        patient_ids = []
        test_patients = [
            ("Alice", "Smith", "1990-05-15", "Female", "111-222-3333", "456 Oak St"),
            ("Bob", "Johnson", "1985-08-22", "Male", "444-555-6666", "789 Pine St"),
            ("Carol", "Williams", "1995-03-10", "Female", "777-888-9999", "321 Elm St")
        ]
        
        for patient in test_patients:
            patient_id = patient_system.add_patient(*patient)
            patient_ids.append(patient_id)
            logger.info(f"Added patient with ID: {patient_id}")

        # Verify patients were added
        for patient_id in patient_ids:
            exists = patient_system.verify_patient_exists(patient_id)
            logger.info(f"Patient {patient_id} exists in system: {exists}")

        # 2. Test department status before admissions
        logger.info("\nChecking initial department status...")
        for dept_id in range(1, 5):
            status = patient_system.get_department_status(dept_id)
            logger.info(f"Department {status['department_name']}: {status['available_beds']} beds available")

        # 3. Test patient admissions
        logger.info("\nTesting patient admissions...")
        admissions = []
        
        # Admit patients to different departments
        admission_data = [
            (patient_ids[0], 1, "Emergency"),  # Alice to Emergency
            (patient_ids[1], 2, "Regular"),    # Bob to ICU
            (patient_ids[2], 3, "Regular")     # Carol to General Medicine
        ]
        
        for patient_id, dept_id, adm_type in admission_data:
            try:
                admission = patient_system.admit_patient(
                    patient_id=patient_id,
                    department_id=dept_id,
                    admission_type=adm_type
                )
                admissions.append(admission)
                logger.info(f"Successfully admitted patient {patient_id} to department {dept_id}")
            except Exception as e:
                logger.error(f"Failed to admit patient {patient_id}: {str(e)}")

        # 4. Verify admissions
        logger.info("\nVerifying admissions...")
        for patient_id in patient_ids:
            history = patient_system.get_patient_history(patient_id)
            logger.info(f"Patient {patient_id} admission records: {history}")

        # 5. Check department status after admissions
        logger.info("\nChecking department status after admissions...")
        for dept_id in range(1, 5):
            status = patient_system.get_department_status(dept_id)
            logger.info(
                f"Department {status['department_name']}: "
                f"{status['occupied_beds']} occupied, "
                f"{status['available_beds']} available"
            )

        # 6. Test patient discharge
        logger.info("\nTesting patient discharge...")
        for admission in admissions:
            try:
                discharge = patient_system.discharge_patient(admission['admission_id'])
                logger.info(f"Successfully discharged patient from admission {admission['admission_id']}")
            except Exception as e:
                logger.error(f"Failed to discharge admission {admission['admission_id']}: {str(e)}")

        # 7. Final verification
        logger.info("\nFinal department status check...")
        for dept_id in range(1, 5):
            status = patient_system.get_department_status(dept_id)
            logger.info(
                f"Department {status['department_name']}: "
                f"{status['available_beds']} available, "
                f"{status['occupied_beds']} occupied, "
                f"Occupancy rate: {status['occupancy_rate']}%"
            )

        logger.info("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    from sqlalchemy import text
    test_patient_system()