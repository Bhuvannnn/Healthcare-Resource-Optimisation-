# Healthcare Resource Dashboard

A comprehensive web-based dashboard for monitoring and managing healthcare facility resources in real time. This system helps healthcare administrators track bed occupancy, staff workload, equipment utilization, and supply status across different departments.

---

## 🌟 Features

### Real-time Monitoring
- **Bed Occupancy Tracking**: Visual representation of bed availability and usage across departments.
- **Staff Workload Analysis**: Monitor staff hours and distribution across departments.
- **Equipment Usage Tracking**: Track utilization of medical equipment.
- **Supply Chain Management**: Monitor inventory levels and supply transactions.

### Technical Features
- Real-time data updates.
- Interactive charts and visualizations.
- Responsive design for all device sizes.
- Debug mode for development.
- RESTful API endpoints.
- PostgreSQL database integration.

---

## 🛠 Technology Stack

### Frontend
- **HTML5**
- **TailwindCSS**
- **Chart.js** for data visualization.
- **JavaScript (ES6+)**

### Backend
- **Python 3.9**
- **Flask Framework**
- **SQLAlchemy ORM**
- **PostgreSQL Database**
- **Docker**

---

## 📋 Prerequisites

- **Python** 3.9 or higher.
- **PostgreSQL** 12 or higher.
- **Docker** (optional).
- **Node.js and npm** (for frontend development).

---

## 🚀 Installation

### Using Docker

1. Clone the repository:  
   ```bash
   git clone https://github.com/yourusername/healthcare-resource-dashboard.git
   cd healthcare-resource-dashboard

Build and run using Docker:
bash
Copy code
docker build -t healthcare-dashboard .
docker run -p 5000:5000 healthcare-dashboard
Manual Installation
Create a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up environment variables:
Create a .env file with the following variables:

makefile
Copy code
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
FLASK_ENV=development
Initialize the database:

bash
Copy code
python setup.py
Run the application:

bash
Copy code
python run.py

📊 Database Schema
The system uses a PostgreSQL database with the following main tables:

Departments
Staff
Equipment
Supplies
Beds
Admissions
Supply Orders
Equipment Usage

🔌 API Endpoints
Main Endpoints
GET /api/data: Fetch all dashboard data.
GET /api/departments/status: Get current department status.
GET /api/dashboard/summary: Get summary statistics.

📈 Dashboard Components
Bed Occupancy Chart

Bar chart showing occupancy rates by department.
Real-time updates.
Percentage-based visualization.
Staff Workload Chart

Pie chart displaying workload distribution.
Department-wise breakdown.
Hour-based metrics.
Equipment Usage Chart

Doughnut chart showing equipment utilization.
Category-wise distribution.
Usage tracking.
Supply Status Chart

Bar chart displaying supply transactions.
Category-wise inventory status.
Transaction tracking.

🔒 Security Considerations
Development server warnings implemented.
Database connection security.
Environment variable protection.
Docker security configurations.

🧪 Testing
The system includes comprehensive logging for testing and debugging:

Equipment tracking tests.
Patient admission tests.
Supply management tests.
Database connection tests.
📝 Logging
Detailed logging system implemented with:

Database operations logging.
System events tracking.
Error logging.
Performance monitoring.

🤝 Contributing
Fork the repository.
Create your feature branch (git checkout -b feature/AmazingFeature).
Commit your changes (git commit -m 'Add some AmazingFeature').
Push to the branch (git push origin feature/AmazingFeature).
Open a Pull Request.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

👥 Authors
Bhuvan Shah - Initial work

🙏 Acknowledgments
Chart.js for visualization components.
TailwindCSS for styling.
