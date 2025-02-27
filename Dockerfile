FROM python

WORKDIR /app

RUN pip install flask
RUN pip install influxdb-client

CMD flask --app dev run --host=0.0.0.0 -p 3000
