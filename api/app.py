from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route('/')
def index():
    return 'Welcome to the Flask API!'

@app.route('/data')
def get_data():
    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        dbname='your_database_name',
        user='your_database_user',
        password='your_database_password',
        host='postgres',
        port=5432
    )

    # Execute SQL query to fetch data
    cur = conn.cursor()
    cur.execute('SELECT * FROM your_table')
    data = cur.fetchall()

    # Close database connection
    cur.close()
    conn.close()

    # Convert data to JSON format and return
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
