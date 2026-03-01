from dataclasses import dataclass

@dataclass(frozen=True)
class Campus:
    id: str
    name: str
    total_capacity: int | None = None
    last_updated: str | None = None
    occupied_spaces: int = 0
    available_spaces: int = 0



