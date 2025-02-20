from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import random
import time

app = Flask(__name__)

IUT_LOCATION = "iut"
TETRAS_LOCATION = "tetras"

IUT_ROOMS = ["d251", "d351", "d360"]
TETRAS_ROOMS = ["02", "11", "19"]

THRESHOLDS = {
    "co2_level": 1000,
    "temperature": (20, 26),
    "humidity": (30, 60),
    "loudness": 50,
    "smoke_density": 0
}

def generate_sensor_data(sensor_type, days=30):
    data = {
        'x': [],
        'y': []
    }
    
    end_time = time.time()
    start_time = end_time - (days * 24 * 60 * 60)
    
    current_time = start_time
    while current_time < end_time:
        data['x'].append(current_time)
        
        value = 0
        if sensor_type == "air_temperature":
            value = random.randint(18, 28)
        elif sensor_type == "humidity":
            value = random.randint(25, 65)
        elif sensor_type == "co2_level":
            value = random.randint(400, 1200)
        elif sensor_type == "loudness":
            value = random.randint(30, 70)
        elif sensor_type == "dew_point":
            value = random.randint(5, 15)
        elif sensor_type == "volatile_organic_compound_level":
            value = random.randint(0, 1000)
        elif sensor_type == "illuminance":
            value = random.randint(0, 1000)
        elif sensor_type == "ultraviolet":
            value = random.randint(0, 11)
        elif sensor_type == "smoke_density":
            value = random.randint(0, 5)
        elif sensor_type == "binary":
            value = random.randint(0, 1)
        
        data['y'].append(value)
        current_time += 3600

    return data

TYPESENSOR = [
    ("air_temperature", "°C"),
    ("co2_level", "ppm"),
    ("dew_point", "°C"),
    ("humidity", "%"),
    ("volatile_organic_compound_level", "ppm"),
    ("illuminance", "lx"),
    ("ultraviolet", "UV index"),
    ("loudness", "dbA"),
    ("smoke_density", "%"),
    ("binary", "binary_sensor")
]

IUT_SENSORS = {
    room: {
        f"{room}_{sensor_type}": f"{sensor_type.replace('_', ' ').title()} Sensor"
        for sensor_type, _ in TYPESENSOR
    } for room in IUT_ROOMS
}

TETRAS_SENSORS = {
    room: {
        f"{room}_{sensor_type}": f"{sensor_type.replace('_', ' ').title()} Sensor"
        for sensor_type, _ in TYPESENSOR
    } for room in TETRAS_ROOMS
}

def get_sensors_list_for_room(room, location):
    if location == IUT_LOCATION:
        if room not in IUT_ROOMS:
            return None
        return list(IUT_SENSORS[room].keys())
    else: 
        if room not in TETRAS_ROOMS:
            return None
        return list(TETRAS_SENSORS[room].keys())

def get_sensor_data(sensor_id, location):
    if location == IUT_LOCATION:
        room = next((room for room in IUT_ROOMS if sensor_id.startswith(room)), None)
        if not room or sensor_id not in IUT_SENSORS[room]:
            return None
    else:
        room = next((room for room in TETRAS_ROOMS if sensor_id.startswith(room)), None)
        if not room or sensor_id not in TETRAS_SENSORS[room]:
            return None
    
    sensor_type = sensor_id.split('_', 1)[1]
    measurement = next((m for t, m in TYPESENSOR if t == sensor_type), None)
    
    if measurement is None:
        return None
        
    data = generate_sensor_data(sensor_type)
    
    return {
        'measurement': measurement,
        'discomfort': detect_discomfort(sensor_id, data['y'][-1]),
        'x': data['x'],
        'y': data['y']
    }

@app.route("/api/sensors")
def get_all_sensors():
    location = request.args.get('location', 'iut')
    if location == IUT_LOCATION:
        sensors_dict = {}
        for room in IUT_ROOMS:
            for sensor_id, sensor_name in IUT_SENSORS[room].items():
                for sensor_type, measurementType in TYPESENSOR:
                    if sensor_type in sensor_id:
                        measurement = measurementType
                sensors_dict[sensor_id] = {
                    'measurement': measurement,
                    'domain': 'sensor',
                    'friendly_name_str': sensor_name,
                    'room': room,
                }
        return jsonify(sensors_dict), 200
    else: 
        sensors_dict = {}
        for room in TETRAS_ROOMS:
            for sensor_id, sensor_name in TETRAS_SENSORS[room].items():
                for sensor_type, measurementType in TYPESENSOR:
                    if sensor_type in sensor_id:
                        measurement = measurementType
                sensors_dict[sensor_id] = {
                    'measurement': measurement,
                    'domain': 'sensor',
                    'friendly_name_str': sensor_name,
                    'room': room,
                }
        return jsonify(sensors_dict), 200

@app.route("/api/rooms")
def get_all_rooms():
    location = request.args.get('location', 'iut')
    if location == IUT_LOCATION:
        return jsonify([{"name": room} for room in IUT_ROOMS]), 200
    else:
        return jsonify([{"name": room} for room in TETRAS_ROOMS]), 200

@app.route("/api/room/<room>/sensor-list")
def get_sensors_by_room(room):
    location = request.args.get('location', 'iut')
    if location == IUT_LOCATION:
        if room not in IUT_ROOMS:
            return {"error": "Room not found"}, 404
        return jsonify(list(IUT_SENSORS[room].keys())), 200
    else:
        if room not in TETRAS_ROOMS:
            return {"error": "Room not found"}, 404
        return jsonify(list(TETRAS_SENSORS[room].keys())), 200

@app.route("/api/sensor/<sensor_id>")
def get_data_by_sensor_id(sensor_id):
    location = request.args.get('location', 'iut')
    data = get_sensor_data(sensor_id, location)
    if data is None:
        return {"error": "Sensor not found"}, 404
    return jsonify(data), 200

@app.route("/api/room/<room>/sensors")
def get_data_sensors_by_room(room):
    location = request.args.get('location', 'iut')
    sensors = get_sensors_list_for_room(room, location)
    if sensors is None:
        return {"error": "Room not found"}, 404
    
    result = {}
    for sensor_id in sensors:
        sensor_type = sensor_id.split('_', 1)[1]
        if any(sensor_type == t for t, _ in TYPESENSOR):
            data = get_sensor_data(sensor_id, location)
            if data:
                result[sensor_type] = data

    return jsonify(result), 200

@app.route("/api/room/<room>/occupancy")
def get_room_occuped(room):
    location = request.args.get('location', 'iut')
    is_occupied = False
    if location == IUT_LOCATION:
        if room not in IUT_ROOMS:
            return {"error": "Room not in list of room"}, 404
        if IUT_ROOMS.index(room) % 2 == 0:
            is_occupied = True
    else: 
        if room not in TETRAS_ROOMS:
            return {"error": "Room not in list of room"}, 404
        if TETRAS_ROOMS.index(room) % 2 == 1:
            is_occupied = True
    return jsonify(is_occupied), 200

def detect_discomfort(name, value):
    discomfort = {"status": False, "causes": None}

    if 'co2_level' in name:
        if random.randint(0,1)==1:
            discomfort["status"] = True
            discomfort["causes"] = "CO2 élevé"
    elif random.randint(0,1)==1:
        if value < THRESHOLDS["temperature"][0] or value > THRESHOLDS["temperature"][1]:
            discomfort["status"] = True
            discomfort["causes"] = "Température inconfortable"
    elif random.randint(0,1)==1:
        if value < THRESHOLDS["humidity"][0] or value > THRESHOLDS["humidity"][1]:
            discomfort["status"] = True
            discomfort["causes"] = "Humidité inconfortable"
    elif random.randint(0,1)==1:
        if value > THRESHOLDS["loudness"]:
            discomfort["status"] = True
            discomfort["causes"] = "Niveau de bruit élevé"

    return discomfort

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)