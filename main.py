from flask import Flask, request

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

app = Flask(__name__)

client = influxdb_client.InfluxDBClient(
   url="http://10.103.1.44:5003",
   token="R43owe_mFoyF8ho54QRwdl8aYRX3JwNyShcW2iEiELNDvCvAtigFv0J4NArYo9kjMAGjgsPdnsTnQK0HEPz7og==",
   org="DomoCorp"
)

query_api = client.query_api()

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

    query = f"""from(bucket: "HA_Bucket")
                |> range(start: {range})
                |> filter(fn: (r) => r["entity_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> filter(fn: (r) => r["_measurement"] == "{measure}")
                |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                |> yield(name: "mean")"""

    try:
        result = query_api.query(org="DomoCorp", query=query)

        listTable = []
        for table in result:
            listTable.extend(convert_flux_table_to_dict(table))

        if not listTable:
            return {"error": "No data found"}, 404

        return listTable

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