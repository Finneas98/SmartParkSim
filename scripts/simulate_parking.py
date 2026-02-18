# TUS Parking Simulation Script
# @author  Fionnán Ó Cualáin
# @date    17-02-2026
import os
import json
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import sumolib
import traci

from data.parking_lot import ParkingLot

cred = credentials.Certificate('smartpark-ece66-firebase-adminsdk-fbsvc-3bbe69f955.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

SUMO_BINARY = "sumo-gui"  # Use "sumo" for command-line mode
# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the SUMO config file
SUMO_CONFIG = os.path.join(script_dir, "..", "osm.sumocfg")
SUMO_CONFIG = os.path.abspath(SUMO_CONFIG)  # normalize to full path

lots = [
    ParkingLot(lot_id="A",
               parking_area_ids=["pa_0", "pa_1", "pa_2", "pa_3", "pa_4"],
               total_capacity=75
               ),
    # Add more lots later:
    # ParkingLot("B", ["pa_5", "pa_6"], total_capacity=40),
]

def clear_occupancy_records():
    print("Clearing all previous occupancy records...")
    for parking_lot in lots:
        parking_lot_ref = db.collection('parking_lots').document(parking_lot.lot_id)
        occupancy_records_ref = parking_lot_ref.collection('occupancy_records')

        # Get all documents in the subcollection
        docs = occupancy_records_ref.stream()

        # Delete documents in a batch for efficiency
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0: # Commit batch every 500 deletions (Firestore limit)
                batch.commit()
                batch = db.batch() # Start a new batch
        batch.commit() # Commit any remaining deletions
        print(f"Cleared {count} records for parking area: {parking_lot.lot_id}")
    print("All occupancy records cleared.")


def update_parking_occupancy(parking_area_id, occupied_count, total_cap):
    now = datetime.datetime.now()
    timestamp_ms = int(now.timestamp() * 1000) # Milliseconds for Firestore document ID

    # Reference to the specific parking lot document
    parking_lot_ref = db.collection('parking_lots').document(parking_area_id)

    # Reference to the occupancy_records subcollection for this parking lot
    occupancy_ref = parking_lot_ref.collection('occupancy_records').document(str(timestamp_ms))

    # Data to be written
    data = {
        'timestamp': now,
        'occupied_spaces': occupied_count,
        'total_capacity': total_cap
    }

    # Add the data to Firestore
    occupancy_ref.set(data)
    print(f"Occupancy for {parking_area_id} recorded at {now}: {occupied_count} occupied.")

# Example usage within your simulation loop:
# Replace traci.parkingarea.getVehicleCount(x) with your actual occupancy retrieval
# This would run every 30 seconds
# for x in parking_lot_stopping_places:
#     current_occupancy = traci.parkingarea.getVehicleCount(x)
#     update_parking_occupancy(x, current_occupancy, parking_lot_total_capacity)


# Connect to SUMO and run the simulation
def run_sumo(route_file):
    traci.start([SUMO_BINARY, "-c", SUMO_CONFIG, "-r", route_file],
                port=sumolib.miscutils.getFreeSocketPort())

    # wipe historical occupancy records from firestore on start
    clear_occupancy_records()

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1
        now = traci.simulation.getTime()

        if step % 60 == 0:
            for lot in lots:
                update_parking_occupancy(lot.lot_id, lot.total_occupancy(), lot.total_capacity)

    traci.close()

if __name__ == "__main__":
    import argparse
    ROUTES_DIR = os.path.abspath(os.path.join(script_dir, "..", "routes"))
    rush_route    = os.path.join(ROUTES_DIR, "rush.rou.xml")
    quiet_route   = os.path.join(ROUTES_DIR, "quiet.rou.xml")
    default_route = os.path.join(ROUTES_DIR, "default_with_parking.rou.xml")

    parser = argparse.ArgumentParser()
    parser.add_argument("--route-quiet", action="store_true", help="Quiet traffic")
    parser.add_argument("--route-rush", action="store_true", help="Rush hour traffic")

    args = parser.parse_args()

    if args.route_rush:
        run_sumo(rush_route)
    elif args.route_quiet:
        run_sumo(quiet_route)
    else:
        run_sumo(default_route)
