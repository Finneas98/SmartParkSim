import argparse
import random
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


# =========================
# FIXED PROJECT SETTINGS
# =========================

NET_FILE = "osm.net.xml"
RANDOM_TRIPS_SCRIPT = "scripts/randomTrips.py"
PROB_PREFIX = "prob/prob"  # expects prob/prob.src.xml etc.
PARKING_ADD_FILE = "additionals/parkingAreas.add.xml"

SIM_END = 6000

TRIPS_DIR = "trips"
ROUTES_DIR = "routes"

# randomTrips period (smaller = busier)
SCENARIOS = {
    "busy": {
        "period": 3,
        "park_rate": 0.70,
        "dur_min": 300,
        "dur_max": 1200,
    },
    "default": {
        "period": 6,
        "park_rate": 0.50,
        "dur_min": 600,
        "dur_max": 1800,
    },
    "quiet": {
        "period": 9,
        "park_rate": 0.30,
        "dur_min": 900,
        "dur_max": 2400,
    },
}


# =========================
# Utility Functions
# =========================

def run_command(command: str):
    print(f"\n>>> {command}")
    subprocess.run(command, check=True, shell=True)


def ensure_dirs():
    Path(TRIPS_DIR).mkdir(parents=True, exist_ok=True)
    Path(ROUTES_DIR).mkdir(parents=True, exist_ok=True)


def edge_from_lane(lane_id: str) -> str:
    """
    lane id format: "<edge>_<laneIndex>"
    edge may contain dots/#, so split from the right.
    """
    return lane_id.rsplit("_", 1)[0]


def parse_parking_areas(additional_path: Path):
    """
    Returns a list of parking areas with their edge and weight:
    [
      {"id": "pa_0", "edge": "213545293.15", "weight": 16},
      ...
    ]
    """
    tree = ET.parse(additional_path)
    root = tree.getroot()

    parking = []

    for pa in root.findall(".//parkingArea"):
        pa_id = pa.get("id")
        lane = pa.get("lane")
        if not pa_id or not lane:
            continue

        edge = edge_from_lane(lane)

        cap = pa.get("roadsideCapacity") or pa.get("capacity")
        weight = int(cap) if cap and cap.isdigit() else 1

        parking.append({"id": pa_id, "edge": edge, "weight": weight})

    if not parking:
        raise ValueError("No parkingArea elements found (with id + lane).")

    print(f"Detected {len(parking)} parking areas.")
    # optional: print the ids
    # print([p["id"] for p in parking])
    return parking


def choose_weighted(rng, items, weights):
    total = sum(weights)
    r = rng.uniform(0, total)
    upto = 0
    for item, w in zip(items, weights):
        upto += w
        if upto >= r:
            return item
    return items[-1]


def inject_parking_stops(route_in, route_out, parking_areas,
                         park_rate, dur_min, dur_max, seed):
    """
    Route-aware injection:
    only assigns a parkingArea if its EDGE appears in the vehicle's route edges.
    This prevents "parkingArea is not downstream the current route" warnings.
    """
    rng = random.Random(seed)

    tree = ET.parse(route_in)
    root = tree.getroot()

    vehicles = root.findall(".//vehicle")
    injected = 0
    skipped_no_match = 0
    skipped_no_route = 0
    already_had_stop = 0

    for v in vehicles:
        if v.find("stop") is not None:
            already_had_stop += 1
            continue

        if rng.random() > park_rate:
            continue

        route_el = v.find("route")
        if route_el is None:
            skipped_no_route += 1
            continue

        edges_str = route_el.get("edges", "")
        route_edges = edges_str.split()
        if not route_edges:
            skipped_no_route += 1
            continue

        # Only choose parking areas that are on this route
        compatible = [p for p in parking_areas if p["edge"] in route_edges]

        if not compatible:
            skipped_no_match += 1
            continue

        pa_ids = [p["id"] for p in compatible]
        weights = [p["weight"] for p in compatible]

        chosen_pa = choose_weighted(rng, pa_ids, weights)
        dur = rng.randint(dur_min, dur_max)

        v.append(ET.Element("stop", {"parkingArea": chosen_pa, "duration": str(dur)}))
        injected += 1

    try:
        ET.indent(tree, space="  ", level=0)
    except AttributeError:
        pass

    tree.write(route_out, encoding="utf-8", xml_declaration=True)

    print(f"Injected {injected} parking stops into {route_out}")
    print(f"Skipped (no compatible parking on route): {skipped_no_match}")
    print(f"Skipped (missing/empty route): {skipped_no_route}")
    if already_had_stop:
        print(f"Vehicles that already had a stop: {already_had_stop}")


# =========================
# Main Pipeline
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base_seed = args.seed

    ensure_dirs()

    parking_areas = parse_parking_areas(Path(PARKING_ADD_FILE))

    for index, (name, cfg) in enumerate(SCENARIOS.items()):
        print(f"\n========== GENERATING {name.upper()} SCENARIO ==========")

        trips_out = f"{TRIPS_DIR}/car_parking_{name}.trips.xml"
        routes_tmp = f"{ROUTES_DIR}/parking_{name}.rou.xml"
        routes_final = f"{ROUTES_DIR}/parking_{name}_withstops.rou.xml"

        prefix = f"cp_{name}_"

        # 1) Generate trips with weighted probabilities
        trip_command = (
            f"python {RANDOM_TRIPS_SCRIPT} "
            f"-n {NET_FILE} "
            f"-o {trips_out} "
            f"-p {cfg['period']} "
            f"-e {SIM_END} "
            f"--prefix {prefix} "
            f"--vehicle-class passenger "
            f"--trip-attributes \"guiShape='passenger'\" "
            f"--weights-prefix {PROB_PREFIX} "
            f"--intermediate 1"
        )
        run_command(trip_command)

        # 2) Convert trips to routes
        route_command = (
            f"duarouter "
            f"-n {NET_FILE} "
            f"--route-files {trips_out} "
            f"-o {routes_tmp} "
            f"--remove-loops "
            f"--ignore-errors"
        )
        run_command(route_command)

        # 3) Inject parking stops (route-aware)
        scenario_seed = base_seed + index * 1000

        inject_parking_stops(
            route_in=routes_tmp,
            route_out=routes_final,
            parking_areas=parking_areas,
            park_rate=cfg["park_rate"],
            dur_min=cfg["dur_min"],
            dur_max=cfg["dur_max"],
            seed=scenario_seed
        )

    print("\nAll scenarios generated successfully.")


if __name__ == "__main__":
    main()