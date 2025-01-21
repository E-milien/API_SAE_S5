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

@app.route("/")
def get_sensors():
    query = """from(bucket: "HA_Bucket")
        |> range(start: -30d)
        |> filter(fn: (r) => r["_field"] == "value")
        |> group(columns: ["entity_id"])"""
    
    try:
        result = query_api.query(org="DomoCorp", query=query)
        
        sensors_dict = {}
        
        for table in result:
            for record in table.records:
                entity_id = record.values.get('entity_id')
                
                if entity_id not in sensors_dict:
                    sensors_dict[entity_id] = {
                        'values': [],
                        'measurement': record.get_measurement(),
                        'metadata': {}
                    }
                
                # Ajouter la valeur avec son timestamp
                sensors_dict[entity_id]['values'].append({
                    'time': str(record.get_time()),
                    'value': record.get_value()
                })
                
                # Ajouter les métadonnées une seule fois
                if not sensors_dict[entity_id]['metadata']:
                    for key, value in record.values.items():
                        if key not in ['_measurement', '_field', '_value', '_time', 'entity_id']:
                            sensors_dict[entity_id]['metadata'][key] = value
            
        return sensors_dict
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/rooms")
def get_rooms():
    query = """from(bucket: "HA_Bucket")
                |> range(start: -30d)
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

@app.route("/getById/<entity_id>")
def get_sensor(entity_id):
    measure = request.args.get('measure', '%')

    query = f"""from(bucket: "HA_Bucket")
                |> range(start: -30d)
                |> filter(fn: (r) => r["entity_id"] == "{entity_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> filter(fn: (r) => r["_measurement"] == "{measure}")
                |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                |> yield(name: "mean")"""

    try:
        result = query_api.query(org="DomoCorp", query=query)

        listTable = []
        for table in result:
            print(table)
            listTable.extend(convert_flux_table_to_dict(table))

        if not listTable:
            return {"error": "No data found"}, 404

        return listTable

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/getRoom/<room>")
def get_room(room):
    measure = request.args.get('measure', '%')

    query = f"""from(bucket: "HA_Bucket")
                  |> range(start: -30d)
                  |> filter(fn: (r) => r["entity_id"] =~ /^{room}.*/)
                  |> filter(fn: (r) => r["_field"] == "value")
                  |> filter(fn: (r) => r["_measurement"] == "{measure}")
                  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
                  |> yield(name: "mean")"""

    try:
        result = query_api.query(org="DomoCorp", query=query)

        listTable = []
        for table in result:
            print(table)
            listTable.extend(convert_flux_table_to_dict(table))

        if not listTable:
            return {"error": "No data found"}, 404

        return listTable

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