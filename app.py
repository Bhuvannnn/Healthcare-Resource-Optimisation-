from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from analytics_and_reporting_system import HealthcareAnalytics
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
analytics = HealthcareAnalytics()

@app.route('/api/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get summary statistics for dashboard"""
    try:
        # Get bed occupancy
        occupancy = analytics.get_bed_occupancy_trends()
        
        # Get staff workload
        workload = analytics.analyze_staff_workload(
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        # Get equipment utilization
        equipment = analytics.analyze_equipment_utilization()
        
        # Get alerts
        alerts = analytics.generate_system_alerts()
        
        return jsonify({
            'bed_occupancy': occupancy['statistics'],
            'staff_workload': workload['department_statistics'],
            'equipment_utilization': equipment['type_statistics'],
            'alerts': alerts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/departments/status', methods=['GET'])
def get_department_status():
    """Get current status of all departments"""
    try:
        departments = []
        for dept_id in range(1, 5):  # Assuming 4 departments
            status = analytics.get_department_status(dept_id)
            departments.append(status)
        return jsonify(departments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/equipment/status', methods=['GET'])
def get_equipment_status():
    """Get current status of all equipment"""
    try:
        equipment_usage = analytics.analyze_equipment_utilization()
        return jsonify(equipment_usage)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/supplies/status', methods=['GET'])
def get_supplies_status():
    """Get current status of supplies"""
    try:
        supply_status = analytics.analyze_supply_consumption()
        return jsonify(supply_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get current system alerts"""
    try:
        alerts = analytics.generate_system_alerts()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)