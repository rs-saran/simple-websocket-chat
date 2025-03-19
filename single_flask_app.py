from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
import datetime
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active connections
active_sessions = {}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    active_sessions[session_id] = {
        'connected_at': datetime.datetime.now(),
        'last_activity': datetime.datetime.now()
    }
    emit('system_message', {'text': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    active_sessions.pop(session_id, None)


@socketio.on('user_message')
def handle_message(data):
    session_id = request.sid
    if session_id in active_sessions:
        active_sessions[session_id]['last_activity'] = datetime.datetime.now()
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        emit('bot_message', {'text': f"{data['text']} rcvd at {timestamp} (dummy reply)"})


def send_hydration_reminders():
    while True:
        now = datetime.datetime.now()
        if now.minute % 2 == 0 and now.second == 0:
            for session_id in list(active_sessions.keys()):
                try:
                    socketio.emit('bot_message', {
                        'text': f"Remember to stay hydrated! It's {now.strftime('%H:%M')}"
                    }, room = session_id)
                except Exception as e:
                    print(f"Error sending reminder to {session_id}: {e}")
        time.sleep(1)


if __name__ == '__main__':
    reminder_thread = threading.Thread(target=send_hydration_reminders, daemon=True)
    reminder_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
