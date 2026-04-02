from types import SimpleNamespace
import scripts.simulate_parking as simulate_parking


class FakeDocumentRef:
    def __init__(self):
        self.set_calls = []
        self.subcollections = {}

    def set(self, payload, merge=False):
        self.set_calls.append((payload, merge))

    def collection(self, name):
        if name not in self.subcollections:
            self.subcollections[name] = FakeCollectionRef()
        return self.subcollections[name]


class FakeCollectionRef:
    def __init__(self):
        self.documents = {}

    def document(self, name=None):
        key = name if name is not None else f"auto_{len(self.documents)}"
        if key not in self.documents:
            self.documents[key] = FakeDocumentRef()
        return self.documents[key]

    def stream(self):
        return []


class FakeBatch:
    def __init__(self):
        self.deleted = []
        self.commit_count = 0

    def delete(self, reference):
        self.deleted.append(reference)

    def commit(self):
        self.commit_count += 1


class FakeDB:
    def __init__(self):
        self.collections = {}
        self.batches = []

    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = FakeCollectionRef()
        return self.collections[name]

    def batch(self):
        batch = FakeBatch()
        self.batches.append(batch)
        return batch


def test_update_parking_occupancy_writes_expected_payload(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(simulate_parking, "db", fake_db)

    lot = simulate_parking.ParkingLot(
        lot_id="CP_Test",
        name="Test Lot",
        campus_id="TUS_MOY",
        campus_name="TUS Moylish",
        parking_area_ids=["pa_1", "pa_2"],
        latitude=52.1,
        longitude=-8.1,
        total_capacity=50,
    )

    expected_payload = {
        "id": "CP_Test",
        "name": "Test Lot",
        "campus_id": "TUS_MOY",
        "campus_name": "TUS Moylish",
        "total_capacity": 50,
        "occupied_spaces": 18,
        "available_spaces": 32,
    }

    monkeypatch.setattr(
        simulate_parking,
        "build_parking_lot_payload",
        lambda lot, occupied_count: expected_payload
    )

    simulate_parking.update_parking_occupancy(lot, 18)

    doc = fake_db.collection("parking_lots").document("Test Lot")
    payload, merge = doc.set_calls[0]

    assert payload == expected_payload
    assert merge is True


def test_update_campus_stats_writes_summary_and_history(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(simulate_parking, "db", fake_db)
    monkeypatch.setattr(
        simulate_parking,
        "firestore",
        SimpleNamespace(SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    )

    campus = simulate_parking.Campus(
        id="TUS_MOY",
        name="TUS Moylish",
        latitude=52.67,
        longitude=-8.64,
    )

    expected_payload = {
        "id": "TUS_MOY",
        "name": "TUS Moylish",
        "total_occupancy": 100,
        "total_capacity": 200,
        "total_available": 100,
    }

    monkeypatch.setattr(
        simulate_parking,
        "build_campus_payload",
        lambda campus, total_occupancy, total_capacity: expected_payload
    )

    simulate_parking.update_campus_stats(campus, 100, 200)

    campus_doc = fake_db.collection("campus").document("TUS Moylish")
    summary_payload, merge = campus_doc.set_calls[0]

    assert summary_payload == expected_payload
    assert merge is True

    history_collection = campus_doc.subcollections["occupancy_records"]
    assert len(history_collection.documents) == 1

    history_doc = next(iter(history_collection.documents.values()))
    history_payload, history_merge = history_doc.set_calls[0]

    assert history_payload["occupied_spaces"] == 100
    assert history_payload["total_capacity"] == 200
    assert history_payload["available_spaces"] == 100
    assert history_payload["timestamp"] == "SERVER_TIMESTAMP"
    assert history_merge is False


def test_clear_occupancy_records_commits_batch_even_when_empty(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(simulate_parking, "db", fake_db)

    fake_campuses = [
        simulate_parking.Campus(
            id="TUS_MOY",
            name="TUS Moylish",
            latitude=52.67,
            longitude=-8.64,
        )
    ]
    monkeypatch.setattr(simulate_parking, "campuses", fake_campuses)

    simulate_parking.clear_occupancy_records()

    assert len(fake_db.batches) == 1
    assert fake_db.batches[0].commit_count == 1


def test_run_sumo_updates_every_60_steps(monkeypatch):
    step_counter = {"count": 0}

    monkeypatch.setattr(simulate_parking.traci, "start", lambda *args, **kwargs: None)
    monkeypatch.setattr(simulate_parking.traci, "close", lambda: None)
    monkeypatch.setattr(simulate_parking, "clear_occupancy_records", lambda: None)
    monkeypatch.setattr(simulate_parking.sumolib.miscutils, "getFreeSocketPort", lambda: 12345)

    def fake_get_min_expected_number():
        return 1 if step_counter["count"] < 60 else 0

    def fake_simulation_step():
        step_counter["count"] += 1

    monkeypatch.setattr(
        simulate_parking.traci,
        "simulation",
        SimpleNamespace(
            getMinExpectedNumber=fake_get_min_expected_number,
            getTime=lambda: step_counter["count"]
        )
    )
    monkeypatch.setattr(simulate_parking.traci, "simulationStep", fake_simulation_step)

    class FakeLot:
        def __init__(self, cap, occ):
            self.total_capacity = cap
            self._occ = occ

        def total_occupancy(self):
            return self._occ

    fake_lots = [FakeLot(50, 10), FakeLot(30, 5)]
    fake_campuses = [
        simulate_parking.Campus(
            id="TUS_MOY",
            name="TUS Moylish",
            latitude=0,
            longitude=0,
        )
    ]

    monkeypatch.setattr(simulate_parking, "lots", fake_lots)
    monkeypatch.setattr(simulate_parking, "campuses", fake_campuses)

    lot_updates = []
    campus_updates = []

    monkeypatch.setattr(
        simulate_parking,
        "update_parking_occupancy",
        lambda lot, occ: lot_updates.append((lot, occ))
    )
    monkeypatch.setattr(
        simulate_parking,
        "update_campus_stats",
        lambda campus, total_occ, total_cap: campus_updates.append((campus, total_occ, total_cap))
    )

    simulate_parking.run_sumo("dummy.rou.xml")

    assert len(lot_updates) == 2
    assert len(campus_updates) == 1
    assert campus_updates[0][1] == 15
    assert campus_updates[0][2] == 80