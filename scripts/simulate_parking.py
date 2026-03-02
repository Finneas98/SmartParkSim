# TUS Parking Simulation Script
# @author  Fionnán Ó Cualáin
# @date    17-02-2026
import os
import json
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore import GeoPoint
import datetime
import sumolib
import traci

from data.parking_lot import ParkingLot
from data.campus import Campus

cred = credentials.Certificate('smartpark-ece66-firebase-adminsdk-fbsvc-3bbe69f955.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

SUMO_BINARY = "sumo-gui"  # Use "sumo" for command-line mode
# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the SUMO config file
SUMO_CONFIG = os.path.join(script_dir, "..", "osm.sumocfg")
SUMO_CONFIG = os.path.abspath(SUMO_CONFIG)  # normalize to full path

campuses = [
    Campus(
        id="TUS_MOY",
        name="TUS Moylish",
        latitude = 52.67501072630342,
        longitude = -8.648763697538072,
    )
]

lots = [
    ParkingLot(
        lot_id="CP_StudentH",
        name="Student Hub Car Park",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_0", "pa_1", "pa_2", "pa_3", "pa_4"],
        latitude=52.67467623796441,
        longitude=-8.645356246703612,
        total_capacity=75
    ),
    ParkingLot(
        lot_id="CP_Astro",
        name="Astro Car Park",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_5", "pa_6", "pa_7", "pa_8", "pa_9"],
        latitude=52.67566701644293,
        longitude=-8.646173539091807,
        total_capacity=55
    ),
    ParkingLot(
        lot_id="CP_SportsH",
        name="Sports Hub Car Park",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_10", "pa_11", "pa_12", "pa_13", "pa_14", "pa_15", "pa_16", "pa_17", "pa_18",
                         "pa_19", "pa_20", "pa_21", "pa_22", "pa_23", "pa_24", "pa_25", "pa_26", "pa_27",
                         "pa_28", "pa_29", "pa_30", "pa_31", "pa_32"],
        latitude=52.676214833295525,
        longitude=-8.648920665886697,
        total_capacity=246
    ),
    # Add more lots later:
    # ParkingLot("B", ["pa_5", "pa_6"], total_capacity=40),
]

def clear_occupancy_records():
    print("Clearing all previous occupancy records...")
    for campus in campuses:
        campus_ref = db.collection('parking_lots').document(campus.id)
        occupancy_records_ref = campus_ref.collection('occupancy_records')

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
        print(f"Cleared {count} records for campus: {campus.id}")
    print("All occupancy records cleared.")


def update_parking_occupancy(lot: ParkingLot, occupied_count: int):
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_ms = int(now.timestamp() * 1000)

    parking_lot_ref = db.collection("parking_lots").document(lot.name)

    # 1) Real-time fields stored on the parent document
    parking_lot_ref.set(
        {
            "id": lot.lot_id,
            "name": lot.name,
            "campus_id": lot.campus_id,
            "campus_name": lot.campus_name,
            "location": GeoPoint(lot.latitude, lot.longitude),
            "total_capacity": lot.total_capacity,
            "occupied_spaces": occupied_count,
            # Prefer server time for consistency across machines
            "last_updated": firestore.SERVER_TIMESTAMP,
            "available_spaces": lot.total_capacity - occupied_count,
        },
        merge=True,
    )

    print(
        f"Lot {lot.lot_id} updated: {occupied_count}/{lot.total_capacity} occupied."
    )


def update_campus_stats(campus: Campus, total_occupancy: int, total_capacity: int):
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_ms = int(now.timestamp() * 1000)

    campus_ref = db.collection("campus").document(campus.name)

    campus_ref.set(
        {
            "id": campus.id,
            "name": campus.name,
            "location": GeoPoint(campus.latitude, campus.longitude),
            "total_occupancy": total_occupancy,
            "total_capacity": total_capacity,
            "total_available": total_capacity - total_occupancy,
            "last_updated": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    # 2) Historical record in subcollection
    occupancy_ref = campus_ref.collection("occupancy_records").document(str(timestamp_ms))
    occupancy_ref.set(
        {
            "timestamp": firestore.SERVER_TIMESTAMP,
            "occupied_spaces": total_occupancy,
            "total_capacity": total_capacity,
            "available_spaces": total_capacity - total_occupancy,
        }
    )


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
            total_capacity = 0
            total_occupied = 0
            for lot in lots:
                occ = lot.total_occupancy()
                total_capacity += lot.total_capacity
                total_occupied += occ
                update_parking_occupancy(lot, occ)

            for campus in campuses:
                if campus.id == "TUS_MOY":
                    update_campus_stats(campus, total_occupied, total_capacity)


    traci.close()

if __name__ == "__main__":
    import argparse
    ROUTES_DIR = os.path.abspath(os.path.join(script_dir, "..", "routes"))
    rush_route    = os.path.join(ROUTES_DIR, "rush.rou.xml")
    quiet_route   = os.path.join(ROUTES_DIR, "quiet.rou.xml")
    default_route = os.path.join(ROUTES_DIR, "parking_default_withstops.rou.xml")

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
