from database_utils import DatabaseManager
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupplyStatus(Enum):
    ADEQUATE = "adequate"
    LOW_STOCK = "low_stock"
    CRITICAL = "critical"
    OUT_OF_STOCK = "out_of_stock"

class SupplyManagementSystem:
    def __init__(self):
        self.db = DatabaseManager()

    def add_supply(self, name: str, category: str, current_quantity: int,
                  minimum_quantity: int, unit: str, cost_per_unit: float) -> int:
        """Add a new supply item to inventory"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO supplies (
                    name, category, current_quantity, minimum_quantity,
                    unit, cost_per_unit
                )
                VALUES (
                    :name, :category, :current_quantity, :minimum_quantity,
                    :unit, :cost_per_unit
                )
                RETURNING supply_id;
                """),
                {
                    'name': name,
                    'category': category,
                    'current_quantity': current_quantity,
                    'minimum_quantity': minimum_quantity,
                    'unit': unit,
                    'cost_per_unit': cost_per_unit
                }
            )
            supply_id = result.scalar()
            logger.info(f"Added new supply: {name} with ID: {supply_id}")
            return supply_id

    def update_supply_quantity(self, supply_id: int, quantity_change: int,
                             transaction_type: str, department_id: int,
                             staff_id: int) -> Dict:
        """Update supply quantity (positive for additions, negative for usage)"""
        with self.db.engine.begin() as conn:
            # Get current supply information
            current_supply = conn.execute(
                text("""
                SELECT current_quantity, minimum_quantity, name
                FROM supplies
                WHERE supply_id = :supply_id
                """),
                {'supply_id': supply_id}
            ).fetchone()

            if not current_supply:
                raise ValueError(f"Supply with ID {supply_id} not found")

            new_quantity = current_supply[0] + quantity_change
            if new_quantity < 0:
                raise ValueError("Cannot reduce quantity below 0")

            # Update supply quantity
            conn.execute(
                text("""
                UPDATE supplies
                SET current_quantity = :new_quantity,
                    updated_at = CURRENT_TIMESTAMP
                WHERE supply_id = :supply_id
                """),
                {
                    'supply_id': supply_id,
                    'new_quantity': new_quantity
                }
            )

            # Record transaction
            result = conn.execute(
                text("""
                INSERT INTO supply_transactions (
                    supply_id, department_id, transaction_type,
                    quantity, created_by
                )
                VALUES (
                    :supply_id, :department_id, :transaction_type,
                    :quantity, :staff_id
                )
                RETURNING transaction_id;
                """),
                {
                    'supply_id': supply_id,
                    'department_id': department_id,
                    'transaction_type': transaction_type,
                    'quantity': abs(quantity_change),
                    'staff_id': staff_id
                }
            )
            
            # Check if we need to create an order
            if new_quantity <= current_supply[1]:  # If below minimum quantity
                self.create_supply_order(supply_id, current_supply[1] * 2 - new_quantity)

            return {
                'supply_id': supply_id,
                'name': current_supply[2],
                'previous_quantity': current_supply[0],
                'new_quantity': new_quantity,
                'transaction_id': result.scalar()
            }

    def create_supply_order(self, supply_id: int, quantity: int) -> int:
        """Create a supply order"""
        with self.db.engine.begin() as conn:
            result = conn.execute(
                text("""
                INSERT INTO supply_orders (
                    supply_id, quantity_ordered, status,
                    order_date, expected_delivery
                )
                VALUES (
                    :supply_id, :quantity, 'pending',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '3 days'
                )
                RETURNING order_id;
                """),
                {
                    'supply_id': supply_id,
                    'quantity': quantity
                }
            )
            order_id = result.scalar()
            logger.info(f"Created supply order {order_id} for supply {supply_id}")
            return order_id

    def get_supply_status(self, supply_id: Optional[int] = None) -> List[Dict]:
        """Get status of supplies"""
        with self.db.engine.connect() as conn:
            query = """
            SELECT 
                s.supply_id,
                s.name,
                s.category,
                s.current_quantity,
                s.minimum_quantity,
                s.unit,
                s.cost_per_unit,
                CASE 
                    WHEN s.current_quantity = 0 THEN 'out_of_stock'
                    WHEN s.current_quantity <= s.minimum_quantity * 0.5 THEN 'critical'
                    WHEN s.current_quantity <= s.minimum_quantity THEN 'low_stock'
                    ELSE 'adequate'
                END as status,
                COALESCE(so.pending_orders, 0) as pending_orders
            FROM supplies s
            LEFT JOIN (
                SELECT supply_id, COUNT(*) as pending_orders
                FROM supply_orders
                WHERE status = 'pending'
                GROUP BY supply_id
            ) so ON s.supply_id = so.supply_id
            """
            
            if supply_id:
                query += " WHERE s.supply_id = :supply_id"
                results = conn.execute(text(query), {'supply_id': supply_id}).fetchall()
            else:
                results = conn.execute(text(query)).fetchall()

            return [{
                'supply_id': r[0],
                'name': r[1],
                'category': r[2],
                'current_quantity': r[3],
                'minimum_quantity': r[4],
                'unit': r[5],
                'cost_per_unit': r[6],
                'status': r[7],
                'pending_orders': r[8]
            } for r in results]

    def get_department_usage(self, department_id: int, 
                           start_date: datetime,
                           end_date: datetime) -> List[Dict]:
        """Get supply usage statistics for a department"""
        with self.db.engine.connect() as conn:
            results = conn.execute(
                text("""
                SELECT 
                    s.name,
                    s.category,
                    COUNT(st.transaction_id) as transaction_count,
                    SUM(st.quantity) as total_quantity,
                    SUM(st.quantity * s.cost_per_unit) as total_cost
                FROM supply_transactions st
                JOIN supplies s ON st.supply_id = s.supply_id
                WHERE st.department_id = :dept_id
                AND st.transaction_date BETWEEN :start_date AND :end_date
                GROUP BY s.supply_id, s.name, s.category
                ORDER BY total_cost DESC;
                """),
                {
                    'dept_id': department_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            ).fetchall()

            return [{
                'supply_name': r[0],
                'category': r[1],
                'transaction_count': r[2],
                'total_quantity': r[3],
                'total_cost': r[4]
            } for r in results]

    def get_low_stock_alerts(self) -> List[Dict]:
        """Get alerts for supplies that need reordering"""
        with self.db.engine.connect() as conn:
            results = conn.execute(
                text("""
                SELECT 
                    supply_id,
                    name,
                    category,
                    current_quantity,
                    minimum_quantity,
                    CASE 
                        WHEN current_quantity = 0 THEN 'out_of_stock'
                        WHEN current_quantity <= minimum_quantity * 0.5 THEN 'critical'
                        WHEN current_quantity <= minimum_quantity THEN 'low_stock'
                    END as alert_level
                FROM supplies
                WHERE current_quantity <= minimum_quantity
                ORDER BY 
                    CASE 
                        WHEN current_quantity = 0 THEN 1
                        WHEN current_quantity <= minimum_quantity * 0.5 THEN 2
                        ELSE 3
                    END;
                """)
            ).fetchall()

            return [{
                'supply_id': r[0],
                'name': r[1],
                'category': r[2],
                'current_quantity': r[3],
                'minimum_quantity': r[4],
                'alert_level': r[5]
            } for r in results]