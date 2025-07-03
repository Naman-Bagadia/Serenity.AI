import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from hume.legacy import HumeVoiceClient, MicrophoneInterface
from typing import List, Dict
import json
import sys
from io import StringIO
import contextlib
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")

active_connections: Dict[WebSocket, bool] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HUME_API_KEY = "aq0kRkUm3KkJAmDRmVAPzXvPA1POBFAaErGJZtepGSejgTbH"
CONFIG_ID = "681f31b0-3735-4297-8664-7510563f09d2"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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

@app.post("/ask")
async def ask_ai(request: Request):
    data = await request.json()
    question = data.get("question")
    return {"response": f"Hey, I'm here for you. You said: '{question}'"}

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
                    logger.info(f"DEBUG: Waiting for transcription... Handlers: {logger.handlers}")
                    text = await mic_interface.get_transcription()
                    logger.info(f"DEBUG: Received from get_transcription: {text}")
                    if text:
                        logger.info(f"User said: {text}")
                        for connection, is_active in active_connections.items():
                            if is_active:
                                try:
                                    await connection.send_json({"type": "user", "message": text})
                                    logger.info(f"[DEBUG] Sent user message to WebSocket: {connection}")
                                    ai_response = f"I understand you said: {text}"
                                    logger.info(f"AI: {ai_response}")
                                    await connection.send_json({"type": "ai", "message": ai_response})
                                    logger.info(f"[DEBUG] Sent AI message to WebSocket: {connection}")
                                except Exception as e:
                                    logger.error(f"Error sending to WebSocket: {e}")
                                    if connection in active_connections:
                                        del active_connections[connection]
                except Exception as e:
                    logger.error(f"Error processing voice input: {e}")
                    break
                    
        logger.info("Voice recognition session ended")
        return {"status": "Voice recognition started"}
    except Exception as e:
        logger.error(f"Error in voice recognition: {e}")
        return {"error": str(e)}

@app.post("/send-test")
async def send_test():

    for connection, is_active in active_connections.items():
        try:
            await connection.send_json({"type": "ai", "message": "[Manual Test] This is a manual test message from /send-test endpoint."})
            logger.info(f"[DEBUG] Sent manual test message to WebSocket: {connection}")
        except Exception as e:
            logger.error(f"[DEBUG] Error sending manual test message: {e}")
    return {"status": "Test message sent to all active WebSocket clients."}
