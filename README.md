# 🚗 Smart Parking Digital Twin – Backend

## 📌 Overview
This backend runs a SUMO-based digital twin simulation of the TUS Moylish campus and streams real-time parking data to Firebase Firestore.

It:
- Simulates traffic and parking behaviour using SUMO  
- Extracts live parking occupancy via TraCI  
- Processes data using Python  
- Stores real-time and historical data in Firestore  

---

## ⚙️ Requirements

### 🐍 Python Version
- Python 3.10 recommended  
- Compatible with Python 3.9+

---

## 📦 Required Python Packages

Install dependencies:

pip install firebase-admin  
pip install google-cloud-firestore  
pip install sumolib  
pip install traci  

---

## 🧪 Virtual Environment Setup

### 1. Create Virtual Environment
python -m venv venv  

### 2. Activate Virtual Environment

Windows:
venv\Scripts\activate  

macOS / Linux:
source venv/bin/activate  

### 3. Install Dependencies
pip install firebase-admin google-cloud-firestore sumolib traci  

---

## 🔐 Firebase Setup (IMPORTANT)

You must place your Firebase Admin SDK JSON file in the main backend folder.

### Example Structure:
backend/  
│── simulate_parking.py  
│── smartpark-xxxx-firebase-adminsdk.json  

### Important:
The script expects the JSON file name:

smartpark-ece66-firebase-adminsdk-fbsvc-3bbe69f955.json  

If your file name is different, update this line in simulate_parking.py:

json_path = os.path.join(current_dir, 'YOUR_FILE_NAME.json')  

---

## 🚦 SUMO Setup

You must have SUMO installed and available in your system PATH.

Test installation:
sumo-gui  

---

## ▶️ Running the Simulation

Default:
python simulate_parking.py  

Quiet traffic:
python simulate_parking.py --route-quiet  

Busy traffic:
python simulate_parking.py --route-busy  

---

## ▶️ Starting the Simulation

Press the play button in the top left of the SUMO GUI

Select a delay number to choose simulation speed (to the right of play button)

---

## 🔄 What Happens When It Runs

1. SUMO simulation starts  
2. Previous occupancy records are cleared from Firestore  
3. Simulation runs step-by-step  
4. Every 60 steps:
   - Parking occupancy is calculated  
   - Data is written to Firestore  
   - Campus statistics are updated  
5. Historical data is stored for analytics  

---

## 🗂️ Project Structure

backend/  
│── simulate_parking.py  
│── main/  
│   ├── data/  
│   ├── util/  
│── routes/  
│── osm.sumocfg  
│── firebase-admin-sdk.json  

---

## ⚠️ Troubleshooting

- Ensure Firebase JSON file is correctly placed  
- Ensure SUMO is installed and accessible  
- Check osm.sumocfg path if simulation fails  
- Verify Firebase credentials if data is not updating   

---

## 👨‍💻 Author
Fionnán Ó Cualáin  
BSc. Internet Systems Development
