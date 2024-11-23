from database_utils import DatabaseManager

db = DatabaseManager()

# Test various functionalities
def run_tests():
    print("\n=== Testing System Functionalities ===\n")
    
    # Check bed occupancy
    print("Bed Occupancy by Department:")
    occupancy = db.get_bed_occupancy()
    for row in occupancy:
        print(f"Department: {row[0]}, Total Beds: {row[1]}, Occupied: {row[2]}, Rate: {row[3]}%")
    
    # Check supply levels
    print("\nCurrent Supply Levels:")
    supplies = db.get_supply_levels()
    for supply in supplies:
        print(f"Item: {supply[0]}, Status: {supply[4]}, Current Quantity: {supply[2]}")

if __name__ == "__main__":
    run_tests()