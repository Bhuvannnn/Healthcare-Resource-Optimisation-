from flask import Blueprint, render_template, jsonify
from app.database import get_analytics_data
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/api/data')
def get_data():
    try:
        data = get_analytics_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500