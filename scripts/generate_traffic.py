import subprocess

# Define files
SUMO_CONFIG = "osm.sumocfg"
NET_FILE = "osm.net.xml"
RANDOM_SCRIPT = "scripts/randomTrips.py"

ROUTE_FILES = {
    "rush": "routes/rush.rou.xml",
    "quiet": "routes/quiet.rou.xml",
    "default": "routes/default.rou.xml",
}

TRIP_FILES = {
    "carRush": "trips/carRush.trips.xml",
    "carQuiet": "trips/carQuiet.trips.xml",
    "carDefault": "trips/carDefault.trips.xml",
    "busRush": "trips/busRush.trips.xml",
    "busQuiet": "trips/busQuiet.trips.xml",
    "busDefault": "trips/busDefault.trips.xml",
    "truckRush": "trips/truckRush.trips.xml",
    "truckQuiet": "trips/truckQuiet.trips.xml",
    "truckDefault": "trips/truckDefault.trips.xml",
}

# Create trip files
TRIP_COMMANDS = [
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['carRush']} -p 2 -e 6000 --prefix c_ --vehicle-class passenger --trip-attributes \"guiShape='passenger'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['carQuiet']} -p 5 -e 6000 --prefix c_ --vehicle-class passenger --trip-attributes \"guiShape='passenger'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['carDefault']} -p 2.5 -e 6000 --prefix c_ --vehicle-class passenger --trip-attributes \"guiShape='passenger'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['busRush']} -p 20 -e 6000 --prefix b_ --vehicle-class bus --trip-attributes \"guiShape='bus'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['busQuiet']} -p 50 -e 6000 --prefix b_ --vehicle-class bus --trip-attributes \"guiShape='bus'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['busDefault']} -p 37 -e 6000 --prefix b_ --vehicle-class bus --trip-attributes \"guiShape='bus'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['truckRush']} -p 10 -e 6000 --prefix t_ --vehicle-class truck --trip-attributes \"guiShape='truck'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['truckQuiet']} -p 50 -e 6000 --prefix t_ --vehicle-class truck --trip-attributes \"guiShape='truck'\"",
    f"python {RANDOM_SCRIPT} -n {NET_FILE} -o {TRIP_FILES['truckDefault']} -p 37 -e 6000 --prefix t_ --vehicle-class truck --trip-attributes \"guiShape='truck'\"",
]

# Create route files
ROUTE_COMMANDS = [
    f"duarouter -n {NET_FILE} --route-files {','.join([TRIP_FILES['carRush'], TRIP_FILES['busRush'], TRIP_FILES['truckRush']])} -o {ROUTE_FILES['rush']} --remove-loops --ignore-errors",
    f"duarouter -n {NET_FILE} --route-files {','.join([TRIP_FILES['carQuiet'], TRIP_FILES['busQuiet'], TRIP_FILES['truckQuiet']])} -o {ROUTE_FILES['quiet']} --remove-loops --ignore-errors",
    f"duarouter -n {NET_FILE} --route-files {','.join([TRIP_FILES['carDefault'], TRIP_FILES['busDefault'], TRIP_FILES['truckDefault']])} -o {ROUTE_FILES['default']} --remove-loops --ignore-errors",
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

