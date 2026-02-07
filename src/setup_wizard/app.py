from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
from pathlib import Path
import uvicorn
import signal
import threading
import time
import sys

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))  # Add project root to path

from src.services.api_client import RvmApiClient
CONFIG_DIR = BASE_DIR / "config"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Ensure config dir exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MyRVM Setup Wizard")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Helper to load .env (copied from main.py to avoid circular imports of main)
def load_base_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

def verify_credentials(serial, api_key, name):
    load_base_env()
    
    # Determine Server URL
    if os.getenv("APP_ENV") == "production":
        server_url = os.getenv("BASE_URL", "https://myrvm.penelitian.my.id")
    else:
        server_url = os.getenv("DEV_BASE_URL", "http://100.105.121.8:8001")
        
    client = RvmApiClient(
        base_url=f"{server_url}/api/v1",
        api_key=api_key,
        device_id=serial,
        name=name
    )
    
    print(f"[*] Verifying credentials for {serial} at {server_url}...")
    success, data = client.handshake()
    return success, data

def shutdown():
    """Shutdown the server after a short delay"""
    time.sleep(2)
    os.kill(os.getpid(), signal.SIGINT)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_config(file: UploadFile = File(...)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files allowed")
    
    try:
        content = await file.read()
        data = json.loads(content)
        
        # Validate Structure
        required_fields = ["serial_number", "api_key", "name"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Verify Credentials BEFORE Saving
        success, handshake_data = verify_credentials(data['serial_number'], data['api_key'], data['name'])
        
        if not success:
            raise Exception("Handshake Failed. Cek API Key/Serial atau Koneksi Internet.")

        # Write to secrets.env
        save_credentials(data)
        
        # Persist Policy (System Donation ID)
        if handshake_data:
            policy = handshake_data.get('policy', {})
            sys_don_id = policy.get('system_donation_user_id')
            if sys_don_id is not None:
                save_system_donation_id(sys_don_id)
        
        # Trigger shutdown in background
        threading.Thread(target=shutdown).start()
        
        return {"status": "success", "message": "Verified! Credentials saved. Restarting..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manual")
async def manual_config(
    serial_number: str = Form(...),
    api_key: str = Form(...),
    name: str = Form(...)
):
    try:
        # Verify Credentials BEFORE Saving
        success, handshake_data = verify_credentials(serial_number, api_key, name)
        
        if not success:
            raise Exception("Handshake Failed. Cek API Key/Serial atau Koneksi Internet.")

        data = {
            "serial_number": serial_number,
            "api_key": api_key,
            "name": name
        }
        
        # Write to secrets.env
        save_credentials(data)
        
        # Persist Policy (System Donation ID)
        if handshake_data:
            policy = handshake_data.get('policy', {})
            sys_don_id = policy.get('system_donation_user_id')
            if sys_don_id is not None:
                save_system_donation_id(sys_don_id)
        
        # Trigger shutdown in background
        threading.Thread(target=shutdown).start()
        
        return {"status": "success", "message": "Verified! Setup successful. Restarting..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_credentials(data):
    env_path = CONFIG_DIR / "secrets.env"
    with open(env_path, "w") as f:
        f.write(f"RVM_SERIAL_NUMBER={data['serial_number']}\n")
        f.write(f"RVM_API_KEY={data['api_key']}\n")
        f.write(f"RVM_NAME={data['name']}\n")
        f.write(f"RVM_GENERATED_AT={data.get('generated_at', time.strftime('%Y-%m-%d %H:%M:%S'))}\n")

def save_system_donation_id(user_id):
    """Save system_donation_user_id to credentials.json"""
    try:
        config_path = CONFIG_DIR / 'credentials.json'
        data = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        data['system_donation_user_id'] = user_id
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"[*] Persisted System Donation ID: {user_id}")
    except Exception as e:
        print(f"[!] Failed to save system donation ID: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
