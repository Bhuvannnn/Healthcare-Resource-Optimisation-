from app.database_utils import DatabaseManager
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
import pandas as pd
from decimal import Decimal
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class HealthcareAnalytics:
    def __init__(self):
        self.db = DatabaseManager()

    def convert_decimal_to_float(self, data: Dict) -> Dict:
        """Convert all Decimal values to float in a dictionary"""
        if isinstance(data, dict):
            return {k: self.convert_decimal_to_float(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_decimal_to_float(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        return data

    def get_bed_occupancy_trends(self, department_id: Optional[int] = None,
                                days: int = 30) -> Dict:
        """Analyze bed occupancy trends"""
        with self.db.engine.connect() as conn:
            query = """
            WITH daily_stats AS (
                SELECT 
                    d.department_id,
                    d.name as department_name,
                    DATE(a.admission_date) as date,
                    COUNT(DISTINCT a.bed_id) as occupied_beds,
                    d.bed_capacity as total_beds
                FROM departments d
                LEFT JOIN admissions a ON d.department_id = a.department_id
                    AND a.status = 'active'
                    AND a.admission_date >= CURRENT_DATE - :days * INTERVAL '1 day'
                WHERE 1=1
            """
            
            params = {'days': days}
            if department_id:
                query += " AND d.department_id = :dept_id"
                params['dept_id'] = department_id
                
            query += """
                GROUP BY d.department_id, d.name, DATE(a.admission_date)
                ORDER BY date
            )
            SELECT 
                department_name,
                date,
                occupied_beds,
                total_beds,
                ROUND((occupied_beds::float / NULLIF(total_beds, 0) * 100)::numeric, 2) as occupancy_rate
            FROM daily_stats;
            """
            
            results = conn.execute(text(query), params).fetchall()
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(results, columns=['department', 'date', 'occupied_beds', 
                                              'total_beds', 'occupancy_rate'])
            
            # Calculate statistics
            stats = {
                'average_occupancy_rate': float(df['occupancy_rate'].mean() or 0),
                'peak_occupancy_rate': float(df['occupancy_rate'].max() or 0),
                'lowest_occupancy_rate': float(df['occupancy_rate'].min() or 0),
                'days_above_90_percent': int(len(df[df['occupancy_rate'] > 90])),
                'trend_by_department': {k: float(v) for k, v in df.groupby('department')['occupancy_rate'].mean().to_dict().items()}
            }
            
            return {
                'daily_data': df.to_dict('records'),
                'statistics': stats
            }

    def analyze_staff_workload(self, start_date: datetime,
                             end_date: datetime) -> Dict:
        """Analyze staff workload and scheduling patterns"""
        with self.db.engine.connect() as conn:
            query = """
            SELECT 
                s.staff_id,
                s.first_name || ' ' || s.last_name as staff_name,
                s.role,
                s.department,
                COUNT(DISTINCT ss.schedule_id) as total_shifts,
                SUM(EXTRACT(EPOCH FROM (ss.shift_end - ss.shift_start))/3600) as total_hours,
                COUNT(DISTINCT CASE WHEN ss.status = 'completed' THEN ss.schedule_id END) as completed_shifts,
                COUNT(DISTINCT CASE WHEN ss.status = 'cancelled' THEN ss.schedule_id END) as cancelled_shifts
            FROM staff s
            LEFT JOIN staff_schedules ss ON s.staff_id = ss.staff_id
                AND ss.shift_start BETWEEN :start_date AND :end_date
            GROUP BY s.staff_id, s.first_name, s.last_name, s.role, s.department
            """
            
            results = conn.execute(text(query), {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            workload_data = [{
                'staff_id': r[0],
                'name': r[1],
                'role': r[2],
                'department': r[3],
                'total_shifts': r[4],
                'total_hours': round(r[5] if r[5] else 0, 2),
                'completed_shifts': r[6],
                'cancelled_shifts': r[7],
                'average_hours_per_shift': round(r[5]/r[4] if r[4] > 0 else 0, 2)
            } for r in results]
            
            # Calculate department-wise statistics
            df = pd.DataFrame(workload_data)
            if not df.empty:
                dept_stats = df.groupby('department').agg({
                    'total_hours': 'sum',
                    'total_shifts': 'sum',
                    'completed_shifts': 'sum'
                }).to_dict('index')
                dept_stats = {k: {k2: float(v2) for k2, v2 in v.items()} 
                            for k, v in dept_stats.items()}
            else:
                dept_stats = {}
            
            return {
                'staff_workload': workload_data,
                'department_statistics': dept_stats
            }

    def analyze_equipment_utilization(self, days: int = 30) -> Dict:
        """Analyze equipment utilization patterns"""
        with self.db.engine.connect() as conn:
            query = """
            SELECT 
                e.equipment_id,
                e.name,
                e.type,
                d.name as department,
                COUNT(eu.usage_id) as total_uses,
                AVG(EXTRACT(EPOCH FROM (eu.end_time - eu.start_time))/3600) as avg_usage_hours,
                SUM(CASE WHEN eu.end_time IS NULL THEN 1 ELSE 0 END) as current_in_use,
                MAX(eu.end_time) as last_used,
                e.last_maintenance_date,
                e.next_maintenance_date
            FROM equipment e
            LEFT JOIN departments d ON e.department_id = d.department_id
            LEFT JOIN equipment_usage eu ON e.equipment_id = eu.equipment_id
                AND eu.start_time >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY e.equipment_id, e.name, e.type, d.name, 
                     e.last_maintenance_date, e.next_maintenance_date
            """
            
            results = conn.execute(text(query), {'days': days}).fetchall()
            
            equipment_data = [{
                'equipment_id': r[0],
                'name': r[1],
                'type': r[2],
                'department': r[3],
                'total_uses': r[4],
                'avg_usage_hours': round(r[5] if r[5] else 0, 2),
                'currently_in_use': bool(r[6]),
                'last_used': r[7],
                'last_maintenance': r[8],
                'next_maintenance': r[9]
            } for r in results]
            
            # Calculate utilization statistics
            df = pd.DataFrame(equipment_data)
            type_stats = df.groupby('type').agg({
                'total_uses': 'sum',
                'avg_usage_hours': 'mean'
            }).to_dict('index')
            
            return {
                'equipment_utilization': equipment_data,
                'type_statistics': type_stats
            }

    def analyze_supply_consumption(self, days: int = 30) -> Dict:
        """Analyze supply consumption patterns"""
        with self.db.engine.connect() as conn:
            query = """
            SELECT 
                s.supply_id,
                s.name,
                s.category,
                s.current_quantity,
                s.minimum_quantity,
                COUNT(st.transaction_id) as total_transactions,
                SUM(st.quantity) as total_quantity_used,
                SUM(st.quantity * s.cost_per_unit) as total_cost,
                COUNT(DISTINCT st.department_id) as departments_using
            FROM supplies s
            LEFT JOIN supply_transactions st ON s.supply_id = st.supply_id
                AND st.transaction_date >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY s.supply_id, s.name, s.category, 
                     s.current_quantity, s.minimum_quantity
            """
            
            results = conn.execute(text(query), {'days': days}).fetchall()
            
            supply_data = [{
                'supply_id': r[0],
                'name': r[1],
                'category': r[2],
                'current_quantity': r[3],
                'minimum_quantity': r[4],
                'total_transactions': r[5],
                'total_quantity_used': r[6],
                'total_cost': round(float(r[7]) if r[7] else 0, 2),
                'departments_using': r[8]
            } for r in results]
            
            # Calculate category-wise statistics
            df = pd.DataFrame(supply_data)
            category_stats = df.groupby('category').agg({
                'total_transactions': 'sum',
                'total_cost': 'sum'
            }).to_dict('index')
            
            return {
                'supply_consumption': supply_data,
                'category_statistics': category_stats
            }

    def generate_system_alerts(self) -> Dict:
        """Generate system-wide alerts and recommendations"""
        alerts = {
            'critical': [],
            'warning': [],
            'info': []
        }
        
        with self.db.engine.connect() as conn:
            # Check bed capacity alerts
            bed_results = conn.execute(text("""
                SELECT 
                    d.name,
                    d.bed_capacity,
                    COUNT(DISTINCT CASE WHEN b.status = 'occupied' THEN b.bed_id END) as occupied_beds
                FROM departments d
                LEFT JOIN beds b ON d.department_id = b.department_id
                GROUP BY d.name, d.bed_capacity
                HAVING COUNT(DISTINCT CASE WHEN b.status = 'occupied' THEN b.bed_id END)::float / 
                       d.bed_capacity > 0.85
            """)).fetchall()
            
            for dept in bed_results:
                occupancy_rate = (dept[2] / dept[1]) * 100
                if occupancy_rate > 95:
                    alerts['critical'].append(
                        f"Critical: {dept[0]} at {occupancy_rate:.1f}% capacity"
                    )
                elif occupancy_rate > 85:
                    alerts['warning'].append(
                        f"Warning: {dept[0]} at {occupancy_rate:.1f}% capacity"
                    )

            # Check supply alerts
            supply_results = conn.execute(text("""
                SELECT 
                    name,
                    current_quantity,
                    minimum_quantity
                FROM supplies
                WHERE current_quantity <= minimum_quantity
            """)).fetchall()
            
            for supply in supply_results:
                if supply[1] == 0:
                    alerts['critical'].append(f"Critical: {supply[0]} is out of stock")
                elif supply[1] <= supply[2] * 0.5:
                    alerts['warning'].append(
                        f"Warning: {supply[0]} is critically low ({supply[1]} remaining)"
                    )
                else:
                    alerts['info'].append(
                        f"Info: {supply[0]} is running low ({supply[1]} remaining)"
                    )

            # Check equipment maintenance alerts
            equipment_results = conn.execute(text("""
                SELECT 
                    name,
                    next_maintenance_date
                FROM equipment
                WHERE next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days'
            """)).fetchall()
            
            for equipment in equipment_results:
                if equipment[1] <= datetime.now():
                    alerts['critical'].append(
                        f"Critical: {equipment[0]} maintenance overdue"
                    )
                else:
                    alerts['warning'].append(
                        f"Warning: {equipment[0]} maintenance due soon"
                    )

        return alerts

    def generate_optimization_recommendations(self) -> Dict:
        """Generate system-wide optimization recommendations"""
        recommendations = {
            'staffing': [],
            'equipment': [],
            'supplies': [],
            'bed_management': []
        }
        
        with self.db.engine.connect() as conn:
            # Analyze staff scheduling patterns
            staff_results = conn.execute(text("""
                SELECT 
                    d.name as department,
                    COUNT(DISTINCT ss.staff_id) as staff_count,
                    COUNT(DISTINCT a.admission_id) as patient_count
                FROM departments d
                LEFT JOIN staff_schedules ss ON d.department_id = ss.department_id
                    AND ss.shift_start >= CURRENT_DATE
                    AND ss.shift_start < CURRENT_DATE + INTERVAL '1 day'
                LEFT JOIN admissions a ON d.department_id = a.department_id
                    AND a.status = 'active'
                GROUP BY d.name
            """)).fetchall()
            
            for dept in staff_results:
                if dept[2] > 0 and dept[1] > 0:
                    ratio = dept[2] / dept[1]
                    if ratio > 4:
                        recommendations['staffing'].append(
                            f"Consider adding more staff to {dept[0]} (current patient/staff ratio: {ratio:.1f})"
                        )

            # Analyze equipment usage patterns
            equipment_results = conn.execute(text("""
                SELECT 
                    e.name,
                    e.type,
                    d.name as department,
                    COUNT(eu.usage_id) as usage_count
                FROM equipment e
                JOIN departments d ON e.department_id = d.department_id
                LEFT JOIN equipment_usage eu ON e.equipment_id = eu.equipment_id
                    AND eu.start_time >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY e.name, e.type, d.name
                HAVING COUNT(eu.usage_id) < 5
            """)).fetchall()
            
            for equipment in equipment_results:
                recommendations['equipment'].append(
                    f"Consider relocating {equipment[0]} from {equipment[2]} (low usage: {equipment[3]} times in 30 days)"
                )

            # Analyze supply ordering patterns
            supply_results = conn.execute(text("""
                SELECT 
                    s.name,
                    s.current_quantity,
                    s.minimum_quantity,
                    AVG(st.quantity) as avg_usage
                FROM supplies s
                LEFT JOIN supply_transactions st ON s.supply_id = st.supply_id
                    AND st.transaction_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY s.name, s.current_quantity, s.minimum_quantity
                HAVING s.minimum_quantity < AVG(st.quantity) * 2
            """)).fetchall()
            
            for supply in supply_results:
                recommendations['supplies'].append(
                    f"Consider increasing minimum stock level for {supply[0]}"
                )

        return recommendations
    
if __name__ == "__main__":
    analytics = HealthcareAnalytics()
    
    # Test analytics functionality
    print("\nTesting Analytics System...")
    
    # Test bed occupancy analysis
    occupancy = analytics.get_bed_occupancy_trends()
    print("\nBed Occupancy Analysis:", json.dumps(occupancy['statistics'], indent=2, cls=DecimalEncoder))
    
    # Test staff workload analysis
    workload = analytics.analyze_staff_workload(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
    print("\nStaff Workload Analysis:", json.dumps(workload['department_statistics'], indent=2))
    
    # Test alerts
    alerts = analytics.generate_system_alerts()
    print("\nSystem Alerts:", json.dumps(alerts, indent=2))
    
    # Test equipment utilization
    equipment_usage = analytics.analyze_equipment_utilization()
    print("\nEquipment Utilization:", json.dumps(equipment_usage['type_statistics'], indent=2))
    
    # Test supply consumption
    supply_analysis = analytics.analyze_supply_consumption()
    print("\nSupply Consumption:", json.dumps(supply_analysis['category_statistics'], indent=2))
    
    # Test optimization recommendations
    recommendations = analytics.generate_optimization_recommendations()
    print("\nOptimization Recommendations:", json.dumps(recommendations, indent=2))