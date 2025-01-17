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
                |> pivot(rowKey: ["entity_id"], columnKey: ["_field"], valueColumn: "_value")"""
    
    result = query_api.query(org="DomoCorp", query=query)
    
    results = {}
    for table in result:
        for record in table.records:
            entity_id = record["entity_id"]
            split = entity_id.split("_")
            room = split[0]

            if room not in results:
                results[room] = []

            results[room].append(record.values)

    return results

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

@app.route("/get")
def get_sensor():
    entity_id = request.args.get('entity_id')
    measure = request.args.get('measure')

    query = f"""from(bucket: "HA_Bucket")
                |> range(start: -30d)
                |> filter(fn: (r) => r["entity_id"] == "{entity_id}")
                |> filter(fn: (r) => r["_field"] == "value")
                |> filter(fn: (r) => r["_measurement"] == "{measure}")
                |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
                |> yield(name: "mean")"""

    print(query)

    result = query_api.query(org="DomoCorp", query=query)
    
    times = []
    values = []

    for table in result:
        for record in table.records:
            times.append(record['_time'])
            values.append(record['value'])

    return {
        "times": times,
        "values": values
    }
