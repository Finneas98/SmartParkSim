import argparse
import random
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_parking_areas(additional_path: Path):
    """
    Returns (ids, weights) where weights are based on capacity if available,
    otherwise all weights = 1.
    """
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
        raise ValueError(f"No <parkingArea> elements found in {additional_path}")

    return ids, weights


def choose_weighted(rng: random.Random, items, weights):
    # random.choices exists in 3.6+, but keep it explicit/clear:
    total = sum(weights)
    r = rng.uniform(0, total)
    upto = 0
    for item, w in zip(items, weights):
        upto += w
        if upto >= r:
            return item
    return items[-1]


def inject_stops(route_path: Path, out_path: Path, parking_ids, parking_weights,
                 rate: float, dur_min: int, dur_max: int, seed: int):
    rng = random.Random(seed)

    tree = ET.parse(route_path)
    root = tree.getroot()

    # Vehicles can be direct children, but also sometimes under <routes> etc.
    vehicles = root.findall(".//vehicle")
    if not vehicles:
        raise ValueError(f"No <vehicle> elements found in {route_path}")

    injected = 0
    for v in vehicles:
        # Skip if it already has a stop
        if v.find("stop") is not None:
            continue

        if rng.random() <= rate:
            pa = choose_weighted(rng, parking_ids, parking_weights)
            dur = rng.randint(dur_min, dur_max)

            stop_el = ET.Element("stop", {
                "parkingArea": pa,
                "duration": str(dur)
            })
            v.append(stop_el)
            injected += 1

    # Pretty print (Python 3.9+)
    try:
        ET.indent(tree, space="  ", level=0)
    except AttributeError:
        pass

    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return len(vehicles), injected


def main():
    ap = argparse.ArgumentParser(description="Inject SUMO parking stops into a .rou.xml")
    ap.add_argument("--routes", required=True, help="Input route file (.rou.xml)")
    ap.add_argument("--add", required=True, help="Parking areas additional file (.add.xml)")
    ap.add_argument("--out", required=True, help="Output route file (.rou.xml)")
    ap.add_argument("--rate", type=float, default=0.5, help="Fraction of vehicles to park (0-1). Default 0.5")
    ap.add_argument("--dur-min", type=int, default=500, help="Min parking duration (seconds). Default 500")
    ap.add_argument("--dur-max", type=int, default=3000, help="Max parking duration (seconds). Default 3000")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for repeatability. Default 42")

    args = ap.parse_args()

    routes = Path(args.routes)
    add = Path(args.add)
    out = Path(args.out)

    parking_ids, weights = parse_parking_areas(add)

    total, injected = inject_stops(
        route_path=routes,
        out_path=out,
        parking_ids=parking_ids,
        parking_weights=weights,
        rate=args.rate,
        dur_min=args.dur_min,
        dur_max=args.dur_max,
        seed=args.seed
    )

    print(f"Vehicles found: {total}")
    print(f"Parking stops injected: {injected} ({(injected/total)*100:.1f}%)")
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
