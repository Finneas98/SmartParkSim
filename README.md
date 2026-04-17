# SmartParkSim
Network and script files for SUMO Digital Twin for SmartPark app

This backend is responsible for running a SUMO-based digital twin simulation of the TUS Moylish campus and streaming real-time parking data to Firebase Firestore.

It:

Simulates traffic and parking behaviour using SUMO
Extracts live parking occupancy via TraCI
Processes and structures data in Python
Writes real-time and historical data to Firestore

Requirements
Python Version
Python 3.10 recommended
Compatible with Python 3.9+

Setting Up a Virtual Environment

python -m venv venv

Activate Virtual Environment

venv\Scripts\activate

Install Dependencies

pip install firebase-admin
pip install google-cloud-firestore
pip install sumolib
pip install traci
pip install python-dotenv

Firebase Setup

You must place your Firebase Admin SDK JSON file in the main backend folder.

Required:
Download Firebase Admin SDK JSON
Place it in the same directory as the main script

/main

SUMO Setup

You must have SUMO installed and configured.

Requirements:
SUMO installed and added to system PATH
sumo-gui executable available

Running the Simulation
Default Mode:
python simulate_parking.py

Quiet Traffic:
python simulate_parking.py --route-quiet

Busy Traffic:
python simulate_parking.py --route-busy

Press play in the top left corner of sumo gui to start the simulation
Choose a delay to modify speed of sim
