from dataclasses import dataclass
from typing import List
import traci

@dataclass(frozen=True)
class ParkingLot:
    lot_id: str
    name: str
    parking_area_ids: List[str] # e.g. ["pa_0", "pa_1", ...]
    latitude: float
    longitude: float
    total_capacity: int | None = None
    last_updated: str | None = None
    occupied_spaces: int = 0


    def total_occupancy(self) -> int:
        """Sum occupancy across all parking areas in this lot."""
        return sum(traci.parkingarea.getVehicleCount(pa_id) for pa_id in self.parking_area_ids)

    def availability(self) -> int:
        """How many spaces are available (not below zero)."""
        return max(0, self.total_capacity - self.total_occupancy())

