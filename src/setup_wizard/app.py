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

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Ensure config dir exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MyRVM Setup Wizard")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

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
        
        # Write to secrets.env
        save_credentials(data)
        
        # Trigger shutdown in background
        threading.Thread(target=shutdown).start()
        
        return {"status": "success", "message": "Credentials imported successfully. Restarting service..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manual")
async def manual_config(
    serial_number: str = Form(...),
    api_key: str = Form(...),
    name: str = Form(...)
):
    try:
        data = {
            "serial_number": serial_number,
            "api_key": api_key,
            "name": name
        }
        
        # Write to secrets.env
        save_credentials(data)
        
        # Trigger shutdown in background
        threading.Thread(target=shutdown).start()
        
        return {"status": "success", "message": "Manual setup successful. Restarting service..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_credentials(data):
    env_path = CONFIG_DIR / "secrets.env"
    with open(env_path, "w") as f:
        f.write(f"RVM_SERIAL_NUMBER={data['serial_number']}\n")
        f.write(f"RVM_API_KEY={data['api_key']}\n")
        f.write(f"RVM_NAME={data['name']}\n")
        f.write(f"RVM_GENERATED_AT={data.get('generated_at', time.strftime('%Y-%m-%d %H:%M:%S'))}\n")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
