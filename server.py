# File: server.py (FastAPI backend)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import datetime

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = id(websocket)
    active_connections[connection_id] = websocket

    # Start the hydration reminder task
    hydration_task = asyncio.create_task(send_hydration_reminders(websocket))

    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Process the message and send response
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            response = {
                "sender": "bot",
                "text": f"{message['text']} rcvd at {timestamp} (dummy reply)"
            }

            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        # When client disconnects
        if connection_id in active_connections:
            del active_connections[connection_id]
            hydration_task.cancel()
    except Exception as e:
        print(f"Error: {e}")
        if connection_id in active_connections:
            del active_connections[connection_id]
            hydration_task.cancel()


async def send_hydration_reminders(websocket: WebSocket):
    """Send hydration reminders on even minutes"""
    try:
        while True:
            # Wait until the next check time
            now = datetime.datetime.now()
            seconds_to_wait = 60 - now.second

            await asyncio.sleep(seconds_to_wait)

            # Check if it's an even minute
            now = datetime.datetime.now()
            if now.minute % 2 == 0 and now.second < 2:  # Give a little buffer for precision
                reminder = {
                    "sender": "bot",
                    "text": f"Remember to stay hydrated! It's {now.strftime('%H:%M')}"
                }
                await websocket.send_text(json.dumps(reminder))

            # Wait a bit to avoid sending multiple reminders in the same minute
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Task is being canceled, clean exit
        pass
    except Exception as e:
        print(f"Hydration reminder error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)