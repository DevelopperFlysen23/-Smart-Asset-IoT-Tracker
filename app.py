from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
import paho.mqtt.client as mqtt
import json
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iot_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

MQTT_BROKER = "broker.hivemq.com" # Public test broker
MQTT_TOPIC_REQUEST = "school/request"
MQTT_TOPIC_ALERTS = "school/alerts"
MQTT_TOPIC_CONTROL = "school/control"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code: {rc}")
    client.subscribe([(MQTT_TOPIC_REQUEST, 0), (MQTT_TOPIC_ALERTS, 0)])

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Message received on {msg.topic}: {payload}")
    
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if msg.topic == MQTT_TOPIC_REQUEST:
            # Payload is the RFID UID
            rfid_uid = payload
            cursor.execute("SELECT name FROM users WHERE rfid_uid = ?", (rfid_uid,))
            user = cursor.fetchone()
            
            if user:
                name = user['name']
                event_msg = f"Access authorized for {name}"
                cursor.execute("INSERT INTO logs (event_type, message, user_name) VALUES (?, ?, ?)", 
                               ('AUTH', event_msg, name))
                socketio.emit('new_log', {'type': 'success', 'msg': event_msg, 'user': name})
                # Send success signal to ESP32
                client.publish(MQTT_TOPIC_CONTROL, "UNLOCK")
            else:
                event_msg = f"Unknown tag: {rfid_uid}"
                cursor.execute("INSERT INTO logs (event_type, message) VALUES (?, ?)", 
                               ('UNAUTHORIZED', event_msg))
                socketio.emit('new_log', {'type': 'danger', 'msg': event_msg, 'user': 'Unknown'})
                client.publish(MQTT_TOPIC_CONTROL, "REJECT")
                
        elif msg.topic == MQTT_TOPIC_ALERTS:
            if payload == "VIBRATION":
                event_msg = "ALERT: Suspicious movement detected!"
                cursor.execute("INSERT INTO logs (event_type, message) VALUES (?, ?)", 
                               ('SECURITY', event_msg))
                socketio.emit('security_alert', {'msg': event_msg})
        
        conn.commit()
        conn.close()

# Start MQTT client in a separate thread
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()

@app.route('/')
def index():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 20').fetchall()
    assets = conn.execute('SELECT * FROM assets').fetchall()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('index.html', logs=logs, assets=assets, users=users)

@socketio.on('disarm_system')
def handle_disarm():
    print("System disarm requested...")
    # Send command to ESP32
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.publish(MQTT_TOPIC_CONTROL, "DISARM")
    mqtt_client.disconnect()
    emit('system_status', {'status': 'Disarmed'})

if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    socketio.run(app, debug=True, port=5000)
