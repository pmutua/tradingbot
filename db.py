import json
import psycopg2
import uuid
import os

def init_db():
    con = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    cur = con.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS MarketData
                (id UUID PRIMARY KEY, symbol TEXT, interval TEXT, close REAL, high REAL, low REAL, timestamp INTEGER)''')
    con.commit()
    con.close()

def log_db(message):
    parsed = json.loads(message)

    k = parsed["k"]

    id = uuid.uuid4()  # PostgreSQL supports UUID natively
    symbol = k["s"]
    interval = k["i"]
    close = float(k["c"])
    high = float(k["h"])
    low = float(k["l"])
    time = int(k["t"])

    print("log:")
    print("symbol: " + symbol)
    print("interval: " + interval)
    print("close: " + str(close))
    print("high: " + str(high))
    print("low: " + str(low))
    print("time: " + str(time))

    row = (id, symbol, interval, close, high, low, time)
    con = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    cur = con.cursor()
    cmd = "INSERT INTO MarketData (id, symbol, interval, close, high, low, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cur.execute(cmd, row)
    
    con.commit()
    con.close()
