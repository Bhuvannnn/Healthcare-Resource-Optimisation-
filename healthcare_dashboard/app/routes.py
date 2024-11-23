# app/routes.py
from flask import Blueprint, render_template, jsonify
from app.analytics.analytics_and_reporting_system import HealthcareAnalytics
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/api/data')  # Add this route
def get_data():
    """Main data endpoint for dashboard"""
    try:
        analytics = HealthcareAnalytics()
        data = {
            'bed_occupancy': analytics.get_bed_occupancy_trends(),
            'staff_workload': analytics.analyze_staff_workload(
                datetime.now() - timedelta(days=30),
                datetime.now()
            ),
            'equipment_utilization': analytics.analyze_equipment_utilization(),
            'supplies': analytics.analyze_supply_consumption()
        }
        logger.info("Data fetched successfully")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/debug')  # Keep this for debugging
def debug_data():
    """Debug endpoint to verify data access"""
    try:
        analytics = HealthcareAnalytics()
        data = {
            'bed_occupancy': analytics.get_bed_occupancy_trends(),
            'staff_workload': analytics.analyze_staff_workload(
                datetime.now() - timedelta(days=30),
                datetime.now()
            ),
            'equipment_utilization': analytics.analyze_equipment_utilization(),
            'supplies': analytics.analyze_supply_consumption()
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in debug route: {str(e)}")
        return jsonify({'error': str(e)}), 500