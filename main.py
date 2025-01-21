from flask import Flask, request
from datetime import datetime, timedelta
from enum import Enum

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
    "co2_level": 1000,  # ppm
    "temperature": (20, 26),  # Plage acceptable : [20°C, 26°C]
    "humidity": (30, 60),  # Plage acceptable : [30%, 60%]
    "loudness": 50,  # dB
    "smoke_density": 0
}

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
    
    results = set()
    for table in result:
        for record in table.records:
            entity_id = record["entity_id"]
            split = entity_id.split("_")
            room = split[0]

            results.add(room)

    return list(results)

@app.route("/getData/<sensor_id>")
def get_data(sensor_id):
    range = request.args.get('range', '-30d')
    measure = request.args.get('measure', '%')
    if measure == "binary":
        query = f"""from(bucket: "HA_Bucket")
                |> range(start: {range})
                |> filter(fn: (r) => r["entity_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> aggregateWindow(every: 10m, fn: last, createEmpty: false)
                |> yield(name: "last")"""
    else:
        query = f"""from(bucket: "HA_Bucket")
                |> range(start: {range})
                |> filter(fn: (r) => r["entity_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> filter(fn: (r) => r["_measurement"] == "{measure}")
                |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                |> yield(name: "mean")"""

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


        # average /= count
        # limit = average * 1.20
        
        # current_dt = datetime.now()
        # dt_obj_minus_30min = current_dt - timedelta(minutes=30)

        # for index, value in enumerate(sensor_dict['x']):
        #     y = sensor_dict['y'][index]
        #     if value > dt_obj_minus_30min.timestamp() and y > limit:
        #         sensor_dict['exceed'].append((value, y))
        # sensor_dict['average'] = average
        # sensor_dict['limit'] = limit

        return sensor_dict

    except Exception as e:
        return {"error": str(e)}, 500

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

def convert_flux_table_to_dict(table):
    records = []
    for record in table.records:
        record_dict = {
            'measurement': record.get_measurement(),
            'field': record.get_field(),
            'value': record.get_value(),
            'time': record.get_time(),
        }

        for key, value in record.values.items():
            if key not in ['_measurement', '_field', '_value', '_time']:
                record_dict[key] = value

        records.append(record_dict)
    return records


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