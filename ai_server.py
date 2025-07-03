import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from hume.legacy import HumeVoiceClient, MicrophoneInterface
from typing import Dict
import json
import logging

app = FastAPI()

# Serve the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the homepage (static/index.html)
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("static/index.html")

# Allow all CORS (development friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection tracking
active_connections: Dict[WebSocket, bool] = {}

# Hume API credentials
HUME_API_KEY = "aq0kRkUm3KkJAmDRmVAPzXvPA1POBFAaErGJZtepGSejgTbH"
CONFIG_ID = "681f31b0-3735-4297-8664-7510563f09d2"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket logging handler
class WebSocketHandler(logging.Handler):
    def __init__(self, websocket):
        super().__init__()
        self.websocket = websocket
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            asyncio.create_task(self.websocket.send_json({
                "type": "terminal",
                "message": msg
            }))
        except Exception as e:
            print(f"Error sending log to WebSocket: {e}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections[websocket] = True
    
    ws_handler = WebSocketHandler(websocket)
    logger.addHandler(ws_handler)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"[DEBUG] Received from frontend: {data}")
            try:
                message = json.loads(data)
                if message.get("type") == "start_voice":
                    active_connections[websocket] = True
                    await websocket.send_json({"type": "ai", "message": "Voice recognition started. You can start speaking now."})
                elif message.get("type") == "stop_voice":
                    active_connections[websocket] = False
                    await websocket.send_json({"type": "ai", "message": "Voice recognition stopped."})
                elif message.get("type") == "user_stream":
                    await websocket.send_json({"type": "user_stream", "message": message.get("message")})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "ai", "message": f"I heard you say: {data}"})
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            del active_connections[websocket]
        logger.removeHandler(ws_handler)

# Basic API endpoint
@app.post("/ask")
async def ask_ai(request: Request):
    data = await request.json()
    question = data.get("question")
    return {"response": f"Hey, I'm here for you. You said: '{question}'"}

# Start Hume Voice AI
@app.get("/start-voice")
async def start_voice_recognition():
    try:
        logger.info("Starting voice recognition...")
        client = HumeVoiceClient(HUME_API_KEY)
        async with client.connect(config_id=CONFIG_ID) as socket:
            logger.info("Connected to Hume Voice API")
            mic_interface = MicrophoneInterface()
            
            logger.info("Starting microphone interface...")
            await mic_interface.start(socket, allow_user_interrupt=True)
            logger.info("Microphone interface started. Say something!")
            
            while True:
                try:
                    logger.info("Waiting for transcription...")
                    text = await mic_interface.get_transcription()
                    logger.info(f"Received: {text}")
                    if text:
                        for connection, is_active in list(active_connections.items()):
                            if is_active:
                                try:
                                    await connection.send_json({"type": "user", "message": text})
                                    ai_response = f"I understand you said: {text}"
                                    await connection.send_json({"type": "ai", "message": ai_response})
                                except Exception as e:
                                    logger.error(f"Error sending to WebSocket: {e}")
                                    if connection in active_connections:
                                        del active_connections[connection]
                except Exception as e:
                    logger.error(f"Error processing voice input: {e}")
                    break
                    
        return {"status": "Voice recognition started"}
    except Exception as e:
        logger.error(f"Error in voice recognition: {e}")
        return {"error": str(e)}

# Manual test endpoint to push to active WebSocket clients
@app.post("/send-test")
async def send_test():
    for connection, is_active in list(active_connections.items()):
        try:
            await connection.send_json({"type": "ai", "message": "[Manual Test] This is a test message."})
        except Exception as e:
            logger.error(f"Error sending manual test message: {e}")
    return {"status": "Test message sent to all WebSocket clients."}
