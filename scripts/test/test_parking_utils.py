from types import SimpleNamespace
from scripts.data.parking_lot import ParkingLot
from scripts.data.campus import Campus
import scripts.util.parking_utils as parking_utils


def test_build_parking_lot_payload_returns_expected_structure(monkeypatch):
    monkeypatch.setattr(parking_utils, "GeoPoint", lambda lat, lon: ("GeoPoint", lat, lon))
    monkeypatch.setattr(
        parking_utils,
        "firestore",
        SimpleNamespace(SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    )

    lot = ParkingLot(
        lot_id="CP_Test",
        name="Test Lot",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_1", "pa_2"],
        latitude=52.1,
        longitude=-8.1,
        total_capacity=50,
    )

    payload = parking_utils.build_parking_lot_payload(lot, 18)

    assert payload["id"] == "CP_Test"
    assert payload["name"] == "Test Lot"
    assert payload["campus_id"] == "TUS_MOY"
    assert payload["campus_name"] == "TUS Moylish"
    assert payload["location"] == ("GeoPoint", 52.1, -8.1)
    assert payload["total_capacity"] == 50
    assert payload["occupied_spaces"] == 18
    assert payload["available_spaces"] == 32
    assert payload["last_updated"] == "SERVER_TIMESTAMP"


def test_build_campus_payload_returns_expected_structure(monkeypatch):
    monkeypatch.setattr(parking_utils, "GeoPoint", lambda lat, lon: ("GeoPoint", lat, lon))
    monkeypatch.setattr(
        parking_utils,
        "firestore",
        SimpleNamespace(SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    )

    campus = Campus(
        id="TUS_MOY",
        name="TUS Moylish",
        latitude=52.67,
        longitude=-8.64,
    )

    payload = parking_utils.build_campus_payload(campus, 100, 200)

    assert payload["id"] == "TUS_MOY"
    assert payload["name"] == "TUS Moylish"
    assert payload["location"] == ("GeoPoint", 52.67, -8.64)
    assert payload["total_occupancy"] == 100
    assert payload["total_capacity"] == 200
    assert payload["total_available"] == 100
    assert payload["last_updated"] == "SERVER_TIMESTAMP"