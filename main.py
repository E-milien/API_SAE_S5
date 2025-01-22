from flask import Flask, jsonify, request
from datetime import datetime, timedelta

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

app = Flask(__name__)

client = influxdb_client.InfluxDBClient(
   url="http://10.103.1.44:5003",
   token="R43owe_mFoyF8ho54QRwdl8aYRX3JwNyShcW2iEiELNDvCvAtigFv0J4NArYo9kjMAGjgsPdnsTnQK0HEPz7og==",
   org="DomoCorp"
)

query_api = client.query_api()

THRESHOLDS = {
    "co2_level": 1000,
    "temperature": (20, 26),
    "humidity": (30, 60),
    "loudness": 50,
    "smoke_density": 0
}

TYPESENSOR = [
    "air_temperature",
    "co2_level",
    "dew_point",
    "humidity",
    "volatile_organic_compound_level",
    "illuminance",
    "ultraviolet",
    "loudness",
    "smoke_density"
]

@app.route("/sensors")
def get_all_sensors():
    range = request.args.get('range', '-30d')

    query = f"""from(bucket: "HA_Bucket")
                |> range(start: {range})
                |> pivot(rowKey: ["entity_id"], columnKey: ["_field"], valueColumn: "_value")"""
    
    try:
        result = query_api.query(org="DomoCorp", query=query)
        
        sensors_dict = {}
        
        for table in result:
            for record in table.records:
                entity_id = record.values.get('entity_id')
                
                if entity_id not in sensors_dict:
                    split = entity_id.split("_")
                    room = split[0]
                    sensors_dict[entity_id] = {
                        'measurement': record.get_measurement(),
                        'domain': record['domain'],
                        'friendly_name_str': record['friendly_name_str'],
                        'room': room,
                    }
        
            
        return sensors_dict
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/rooms")
def get_all_rooms():
    range = request.args.get('range', '-30d')

    query = f"""from(bucket: "HA_Bucket")
                |> range(start: {range})
                |> pivot(rowKey: ["entity_id"], columnKey: ["_field"], valueColumn: "_value")"""
    
    result = query_api.query(org="DomoCorp", query=query)
    
    rooms_list = []
    for table in result:
        for record in table.records:
            entity_id = record["entity_id"]
            split = entity_id.split("_")
            room = split[0]
            if not any(room_entry["name"] == room for room_entry in rooms_list):
                rooms_list.append({
                    "name": room
                })

    return rooms_list

@app.route("/getData/<sensor_id>")
def get_data(sensor_id):
    range = request.args.get('range', '-30d')
    query = f"""from(bucket: "HA_Bucket")
                |> range(start: {range})
                |> filter(fn: (r) => r["entity_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> aggregateWindow(every: 10m, fn: last, createEmpty: false)
                |> yield(name: "last")"""

    try:
        result = query_api.query(org="DomoCorp", query=query)

        sensor_dict = {
            'x': [],
            'y': [],
            'discomfort': {"status": False, "causes": []}
        }

        for table in result:
            for record in table.records:
                sensor_dict['x'].append(record.get_time().timestamp())
                sensor_dict['y'].append(record.get_value())
                sensor_dict['measurement'] = record.get_measurement()

        current = datetime.now()
        current_delta = current - timedelta(minutes=60)

        for index, x in enumerate(sensor_dict['x']):
            y = sensor_dict['y'][index]
            
            if x > current_delta.timestamp():
                if not sensor_dict['discomfort']['status']:
                    sensor_dict['discomfort'] = detect_discomfort(sensor_id, y)

        return sensor_dict

    except Exception as e:
        return {"error": str(e)}, 500
    
@app.route("/getSensorByType/<room>")
def get_data_sensors(room):
    range = request.args.get('range', '-30d')

    sensor_dict = {}
    for typeSensor in TYPESENSOR:
        query = f"""from(bucket: "HA_Bucket")
                    |> range(start: {range})
                    |> filter(fn: (r) => r["entity_id"] =~ /^{room}.*/)
                    |> filter(fn: (r) => r["entity_id"] =~ /.*{typeSensor}.*/)
                    |> filter(fn: (r) => r["_field"] == "value")
                    |> group()
                    |> aggregateWindow(every: 60m, fn: mean, createEmpty: false)
                    |> yield(name: "mean")"""
        try:
            result = query_api.query(org="DomoCorp", query=query)

            for table in result:
                if typeSensor not in sensor_dict:
                    sensor_dict[typeSensor] = {
                        'x': [],
                        'y': [],
                        }
                
                for record in table.records:
                    sensor_dict[typeSensor]['x'].append(record.get_time().timestamp())
                    sensor_dict[typeSensor]['y'].append(record.get_value())

        except Exception as e:
            return {"error": str(e)}, 500
    return sensor_dict

@app.route("/getSensors/<room>")
def get_sensors(room):
    range = request.args.get('range', '-30d')

    query = f"""from(bucket: "HA_Bucket")
                  |> range(start: {range})
                  |> filter(fn: (r) => r["entity_id"] =~ /^{room}.*/)
                  |> filter(fn: (r) => r["_field"] == "value")"""

    try:
        result = query_api.query(org="DomoCorp", query=query)

        list_sensors = []
        for table in result:
            for record in table.records:
                entity_id = record.values.get('entity_id')
                
                if entity_id not in list_sensors:
                   list_sensors.append(entity_id)
            

        if not list_sensors:
            return {"error": "No data found"}, 404

        return list_sensors

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/isOccuped/<room>")
def get_occuped(room):
    AVERAGE_MULTIPLICATOR = 1,10
    range = request.args.get('range', '-7d')

    list_sensors = [
       "co2_level",
       "loudness",
       "air_temperature",
       "humidity"
    ]

    sensor_dict = {}
    result_dict = {}

    isOccuped = True

    for typeSensor in list_sensors:
        query = f"""from(bucket: "HA_Bucket")
                    |> range(start: {range})
                    |> filter(fn: (r) => r["entity_id"] =~ /^{room}.*/)
                    |> filter(fn: (r) => r["entity_id"] =~ /.*{typeSensor}.*/)
                    |> filter(fn: (r) => r["_field"] == "value")
                    |> group()
                    |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                    |> yield(name: "mean")"""
        try:
            result = query_api.query(org="DomoCorp", query=query)

            count = 0
            average = 0

            for table in result:
                if typeSensor not in sensor_dict:
                    sensor_dict[typeSensor] = {
                        'x': [],
                        'y': [],
                        }
                
                for record in table.records:
                    count += 1
                    average += record.get_value()

                    sensor_dict[typeSensor]['x'].append(record.get_time().timestamp())
                    sensor_dict[typeSensor]['y'].append(record.get_value())
            
            if count > 0: 
                average /= count
                limit = average * AVERAGE_MULTIPLICATOR
                
                current_dt = datetime.now()
                dt_obj_minus_30min = current_dt - timedelta(minutes=30)
                
                countLast = 0
                averageLast = 0
                
                for index, x in enumerate(sensor_dict[typeSensor]['x']):
                    y = sensor_dict[typeSensor]['y'][index]
                    if x > dt_obj_minus_30min.timestamp():
                        countLast += 1
                        averageLast += y
                
                if countLast > 0: 
                    averageLast /= countLast
                    isOccuped = isOccuped and averageLast > limit
                    result_dict[typeSensor] = averageLast > limit

        except Exception as e:
            return {"error": str(e)}, 500
    return jsonify(result_dict)


def detect_discomfort(name, value):
    discomfort = {"status": False, "causes": []}

    if 'co2_level' in name:
        if value > THRESHOLDS["co2_level"]:
            discomfort["status"] = True
            discomfort["causes"].append("CO2 élevé")

    if 'temperature' in name:
        temp = value
        if temp is not None and (temp < THRESHOLDS["temperature"][0] or temp > THRESHOLDS["temperature"][1]):
            discomfort["status"] = True
            discomfort["causes"].append("Température inconfortable")

    if 'humidity' in name:
        humidity = value
        if humidity is not None and (humidity < THRESHOLDS["humidity"][0] or humidity > THRESHOLDS["humidity"][1]):
            discomfort["status"] = True
            discomfort["causes"].append("Humidité inconfortable")

    if 'loudness' in name:
        noise = value
        if noise > THRESHOLDS["loudness"]:
            discomfort["status"] = True
            discomfort["causes"].append("Niveau de bruit élevé")

    if 'smoke_density' in name:
        noise = value
        if noise > THRESHOLDS["smoke_density"]:
            discomfort["smoke_density"] = True
            discomfort["causes"].append("Fumée détectée")

    return discomfort