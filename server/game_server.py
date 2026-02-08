from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import json
import time
import zipfile
from pathlib import Path
import asyncio
from typing import Dict, List
import shutil

app = FastAPI()

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LANES = 4
DEFAULT_OSZ = r"C:\Users\stringbot\Downloads\2466542 TM - Shinseikatsu.osz"

# Store connected clients for CV streaming
cv_subscribers: List[WebSocket] = []
latest_joints = {}

def extract_osu(osz_path):
    """Extract .osu and audio from .osz"""
    osu_content = None
    audio_file_path = None
    
    with zipfile.ZipFile(osz_path, 'r') as z:
        for file in z.namelist():
            if file.endswith('.osu'):
                osu_content = z.read(file).decode('utf-8')
            elif file.endswith('.mp3') or file.endswith('.ogg'):
                audio_file_path = file
    return osu_content, audio_file_path

def parse_osu(osu_text):
    """Parse hit circles into a list of {time, lane}"""
    lines = osu_text.splitlines()
    section = ''
    notes = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('['):
            section = line
            continue
        if section == '[HitObjects]':
            parts = line.split(',')
            x = int(parts[0])
            time_ms = int(parts[2])
            type_flag = int(parts[3])
            is_circle = (type_flag & 1) != 0
            if not is_circle:
                continue
            lane = min(LANES - 1, int(x / 512 * LANES))
            notes.append({'time': time_ms / 1000, 'lane': lane})
    return notes

# HTTP endpoint to get beatmap
@app.get("/api/beatmap")
async def get_beatmap(path: str = None):
    try:
        osz_path = path or DEFAULT_OSZ
        osu_file, audio_file = extract_osu(osz_path)
        notes = parse_osu(osu_file)
        
        return JSONResponse({
            "success": True,
            "notes": notes,
            "audio": audio_file,
            "count": len(notes)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Serve audio file
@app.get("/api/audio")
async def get_audio():
    try:
        _, audio_file = extract_osu(DEFAULT_OSZ)
        if audio_file:
            # Extract to temp location
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(DEFAULT_OSZ, 'r') as z:
                z.extract(audio_file, temp_dir)
            
            return FileResponse(temp_dir / audio_file)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# List available beatmaps
@app.get("/api/beatmaps")
async def list_beatmaps():
    downloads = Path(r"C:\Users\stringbot\Downloads")
    osz_files = list(downloads.glob("*.osz"))
    
    return JSONResponse({
        "beatmaps": [{"name": f.stem, "path": str(f)} for f in osz_files]
    })

# CV Pose data endpoint - POST from main.py
@app.post("/api/cv/pose")
async def receive_pose(data: dict):
    """
    Receive pose data from main.py CV pipeline
    Expected format:
    {
        "left_ankle": {"x": 123, "y": 456, "depth": 89},
        "right_ankle": {"x": 234, "y": 567, "depth": 90},
        "left_knee": {"x": 111, "y": 333, "depth": 88},
        "right_knee": {"x": 222, "y": 444, "depth": 91},
        "timestamp": 12345.67
    }
    """
    global latest_joints
    latest_joints = data
    
    # Broadcast to all connected game clients
    disconnected = []
    for ws in cv_subscribers:
        try:
            await ws.send_json({
                "type": "pose_update",
                "joints": data,
                "timestamp": time.time()
            })
        except:
            disconnected.append(ws)
    
    # Clean up disconnected clients
    for ws in disconnected:
        cv_subscribers.remove(ws)
    
    return {"status": "ok"}

# WebSocket endpoint for game clients
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cv_subscribers.append(websocket)
    print(f"✅ Client connected (Total: {len(cv_subscribers)})")
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg['type'] == 'get_beatmap':
                osu_file, _ = extract_osu(msg.get('path', DEFAULT_OSZ))
                beatmap = parse_osu(osu_file)
                await websocket.send_json({
                    'type': 'beatmap',
                    'notes': beatmap
                })
            
            elif msg['type'] == 'start_game':
                await websocket.send_json({
                    'type': 'game_started',
                    'timestamp': time.time()
                })
            
            elif msg['type'] == 'get_latest_pose':
                # Send latest CV data on demand
                await websocket.send_json({
                    'type': 'pose_update',
                    'joints': latest_joints,
                    'timestamp': time.time()
                })
                
    except WebSocketDisconnect:
        cv_subscribers.remove(websocket)
        print(f"❌ Client disconnected (Remaining: {len(cv_subscribers)})")

if __name__ == "__main__":
    import uvicorn
    print("🎮 DDR FastAPI Server starting")
    print("📡 WebSocket: ws://localhost:8000/ws")
    print("🎵 Beatmap API: http://localhost:8000/api/beatmap")
    print("🎥 CV Pose API: POST http://localhost:8000/api/cv/pose")
    uvicorn.run(app, host="0.0.0.0", port=8000)