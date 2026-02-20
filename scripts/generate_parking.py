import subprocess

# Define files
SUMO_CONFIG = "osm.sumocfg"
NET_FILE = "osm.net.xml"
RANDOM_SCRIPT = "scripts/randomTrips.py"
PROB_PREFIX = "prob/prob"

ROUTE_FILES = {
    "busy": "routes/parking_busy.rou.xml",
    "quiet": "routes/parking_quiet.rou.xml",
    "default": "routes/parking_default.rou.xml",
}

TRIP_FILES = {
    "car_parking_busy": "trips/car_parking_busy.trips.xml",
    "car_parking_quiet": "trips/car_parking_quiet.trips.xml",
    "car_parking_default": "trips/car_parking_default.trips.xml",
}

# Create trip files
TRIP_COMMANDS = [
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['car_parking_busy']} -p 1 -e 6000 --prefix c_ --vehicle-class passenger --trip-attributes \"guiShape='passenger'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['car_parking_quiet']} -p 3 -e 6000 --prefix c_ --vehicle-class passenger --trip-attributes \"guiShape='passenger'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['car_parking_default']} -p 2 -e 6000 --prefix c_ --vehicle-class passenger --trip-attributes \"guiShape='passenger'\"",
]

# Create route files
ROUTE_COMMANDS = [
    f"duarouter -n {NET_FILE} --route-files {','.join([TRIP_FILES['car_parking_busy']])} -o {ROUTE_FILES['busy']} --remove-loops --ignore-errors",
    f"duarouter -n {NET_FILE} --route-files {','.join([TRIP_FILES['car_parking_quiet']])} -o {ROUTE_FILES['quiet']} --remove-loops --ignore-errors",
    f"duarouter -n {NET_FILE} --route-files {','.join([TRIP_FILES['car_parking_default']])} -o {ROUTE_FILES['default']} --remove-loops --ignore-errors",
]

# Run commands
def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}\nError: {e}")

def generate_trips_and_routes():
    for cmd in TRIP_COMMANDS:
        run_command(cmd)
    for cmd in ROUTE_COMMANDS:
        run_command(cmd)


# Main method with debugging print statements
def main():
    generate_trips_and_routes()


if __name__ == "__main__":
    main()

