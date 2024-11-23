// app/static/js/dashboard.js
async function fetchDashboardData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        // Update dashboard components
        updateBedOccupancy(data.bed_occupancy);
        updateStaffWorkload(data.staff_workload);
        updateEquipmentUtilization(data.equipment_utilization);
        updateSupplies(data.supplies);
        updateAlerts(data.alerts);
        
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        displayError('Failed to load dashboard data');
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    fetchDashboardData();
    // Refresh every 5 minutes
    setInterval(fetchDashboardData, 300000);
});