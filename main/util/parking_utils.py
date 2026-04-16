from firebase_admin import firestore
from google.cloud.firestore import GeoPoint

from main.data.parking_lot import ParkingLot
from main.data.campus import Campus



def build_parking_lot_payload(lot: ParkingLot, occupied_count: int) -> dict:
    return {
        "id": lot.lot_id,
        "name": lot.name,
        "campus_id": lot.campus_id,
        "campus_name": lot.campus_name,
        "location": GeoPoint(lot.latitude, lot.longitude),
        "total_capacity": lot.total_capacity,
        "occupied_spaces": occupied_count,
        "last_updated": firestore.SERVER_TIMESTAMP,
        "available_spaces": lot.total_capacity - occupied_count,
    }

def build_campus_payload(campus: Campus, total_occupancy: int, total_capacity: int) -> dict:
    return {
        "id": campus.id,
        "name": campus.name,
        "location": GeoPoint(campus.latitude, campus.longitude),
        "total_occupancy": total_occupancy,
        "total_capacity": total_capacity,
        "total_available": total_capacity - total_occupancy,
        "last_updated": firestore.SERVER_TIMESTAMP,
    }