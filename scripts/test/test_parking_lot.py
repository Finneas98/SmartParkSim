from scripts.data.parking_lot import ParkingLot

def test_total_occupancy_sums_all_parking_areas(monkeypatch):
    counts = {
        "pa_1": 3,
        "pa_2": 5,
        "pa_3": 2,
    }

    def fake_get_vehicle_count(pa_id):
        return counts[pa_id]

    monkeypatch.setattr(
        "scripts.data.parking_lot.traci.parkingarea.getVehicleCount",
        fake_get_vehicle_count
    )

    lot = ParkingLot(
        lot_id="CP_Test",
        name="Test Lot",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_1", "pa_2", "pa_3"],
        latitude=52.0,
        longitude=-8.0,
        total_capacity=20,
    )

    assert lot.total_occupancy() == 10


def test_availability_returns_capacity_minus_occupancy(monkeypatch):
    monkeypatch.setattr(ParkingLot, "total_occupancy", lambda self: 12)

    lot = ParkingLot(
        lot_id="CP_Test",
        name="Test Lot",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_1"],
        latitude=52.0,
        longitude=-8.0,
        total_capacity=20,
    )

    assert lot.availability() == 8


def test_availability_never_returns_negative(monkeypatch):
    monkeypatch.setattr(ParkingLot, "total_occupancy", lambda self: 30)

    lot = ParkingLot(
        lot_id="CP_Test",
        name="Test Lot",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_1"],
        latitude=52.0,
        longitude=-8.0,
        total_capacity=20,
    )

    assert lot.availability() == 0