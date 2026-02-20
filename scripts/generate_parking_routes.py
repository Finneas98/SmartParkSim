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
        "period": 5,
        "park_rate": 0.70,
        "dur_min": 300,
        "dur_max": 1200,
    },
    "default": {
        "period": 10,
        "park_rate": 0.50,
        "dur_min": 600,
        "dur_max": 1800,
    },
    "quiet": {
        "period": 15,
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


def parse_parking_areas(additional_path: Path):
    tree = ET.parse(additional_path)
    root = tree.getroot()

    ids = []
    weights = []

    for pa in root.findall(".//parkingArea"):
        pa_id = pa.get("id")
        if not pa_id:
            continue

        cap = pa.get("roadsideCapacity") or pa.get("capacity")
        w = int(cap) if cap and cap.isdigit() else 1

        ids.append(pa_id)
        weights.append(w)

    if not ids:
        raise ValueError("No parkingArea elements found.")

    print(f"Detected {len(ids)} parking areas: {ids}")
    return ids, weights


def choose_weighted(rng, items, weights):
    total = sum(weights)
    r = rng.uniform(0, total)
    upto = 0
    for item, w in zip(items, weights):
        upto += w
        if upto >= r:
            return item
    return items[-1]


def inject_parking_stops(route_in, route_out, parking_ids, parking_weights,
                         park_rate, dur_min, dur_max, seed):
    rng = random.Random(seed)

    tree = ET.parse(route_in)
    root = tree.getroot()

    vehicles = root.findall(".//vehicle")
    injected = 0

    for v in vehicles:
        if v.find("stop") is not None:
            continue

        if rng.random() <= park_rate:
            pa = choose_weighted(rng, parking_ids, parking_weights)
            dur = rng.randint(dur_min, dur_max)
            v.append(ET.Element("stop", {
                "parkingArea": pa,
                "duration": str(dur)
            }))
            injected += 1

    try:
        ET.indent(tree, space="  ", level=0)
    except AttributeError:
        pass

    tree.write(route_out, encoding="utf-8", xml_declaration=True)

    print(f"Injected {injected} parking stops into {route_out}")


# =========================
# Main Pipeline
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base_seed = args.seed

    ensure_dirs()

    parking_ids, parking_weights = parse_parking_areas(Path(PARKING_ADD_FILE))

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

        # 3) Inject parking stops
        scenario_seed = base_seed + index * 1000

        inject_parking_stops(
            route_in=routes_tmp,
            route_out=routes_final,
            parking_ids=parking_ids,
            parking_weights=parking_weights,
            park_rate=cfg["park_rate"],
            dur_min=cfg["dur_min"],
            dur_max=cfg["dur_max"],
            seed=scenario_seed
        )

    print("\nAll scenarios generated successfully.")


if __name__ == "__main__":
    main()