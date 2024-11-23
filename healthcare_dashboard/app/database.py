from app import db
from datetime import datetime, timedelta
from app.analytics.analytics_and_reporting_system import HealthcareAnalytics

def get_analytics_data():
    analytics = HealthcareAnalytics()
    
    # Get all required data
    occupancy = analytics.get_bed_occupancy_trends()
    workload = analytics.analyze_staff_workload(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    equipment = analytics.analyze_equipment_utilization()
    alerts = analytics.generate_system_alerts()
    supplies = analytics.analyze_supply_consumption()
    
    return {
        'bed_occupancy': occupancy,
        'staff_workload': workload,
        'equipment_utilization': equipment,
        'alerts': alerts,
        'supplies': supplies
    }