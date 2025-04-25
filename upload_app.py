from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import shutil
import webbrowser
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import threading
import time
import zipfile
import requests
from owslib.wms import WebMapService
from pydantic import BaseModel

# Create the FastAPI application
app = FastAPI(title="ZIP Upload Server")

# Use system temp directory for uploads
TEMP_DIR = Path(tempfile.gettempdir()) / "zip_uploads"
TEMP_DIR.mkdir(exist_ok=True)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Port to run the server on
PORT = 8887

# Path for the latest tileset
LATEST_TILESET_PATH = TEMP_DIR / "tileset.zip"
WMS_INFO_PATH = TEMP_DIR / "wms.json"

def inspect_zip_content(zip_path):
    """
    Inspect the ZIP file content to check if it contains .ptns files or .glb files.
    Returns: "bim" if .glb files are found, "pointcloud" if .pnts files are found, 
    or "unknown" if neither is found.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            file_list_lower = [f.lower() for f in file_list]
            
            has_ptns = any(filename.endswith('.pnts') for filename in file_list_lower)
            has_glb = any(filename.endswith('.glb') for filename in file_list_lower)
            
            if has_glb:
                return "bim"
            elif has_ptns:
                return "pointcloud"
            else:
                return "unknown"
    except Exception as e:
        print(f"Error inspecting ZIP file: {e}")
        return "unknown"

@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    """Serve the upload form HTML page."""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/upload", response_class=RedirectResponse)
async def redirect_to_root():
    """Redirect /upload GET requests to the root path."""
    return RedirectResponse(url="/")

@app.post("/upload")
async def upload_zip_file(zipfile: UploadFile = File(...)):
    """Handle ZIP file upload."""
    if not zipfile.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{Path(zipfile.filename).stem}_{timestamp}.zip"
    filepath = TEMP_DIR / filename
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(zipfile.file, buffer)
    
    if LATEST_TILESET_PATH.exists():
        LATEST_TILESET_PATH.unlink()
    
    shutil.copy2(filepath, LATEST_TILESET_PATH)
    
    content_type = inspect_zip_content(filepath)
    
    if content_type == "bim":
        collector_command = "python main.py --collectors bim_tilesets --now"
    else:
        collector_command = "python main.py --collectors pointcloud_tilesets --now"
    
    launch_thread = threading.Thread(
        target=run_command,
        args=(collector_command,)
    )
    launch_thread.daemon = True
    launch_thread.start()
    
    return {
        "status": "success",
        "filename": filename,
        "content_type": content_type,
        "command": collector_command
    }

@app.get("/tileset.zip")
async def serve_latest_zip():
    """Serve the most recently uploaded ZIP file."""
    if not LATEST_TILESET_PATH.exists():
        raise HTTPException(status_code=404, detail="No ZIP files have been uploaded yet")
    
    return FileResponse(
        path=LATEST_TILESET_PATH,
        filename="tileset.zip",
        media_type="application/zip"
    )

@app.get("/wms.json")
async def serve_wms_json():
    """Serve the most recently uploaded ZIP file."""
    if not WMS_INFO_PATH.exists():
        raise HTTPException(status_code=404, detail="No WMS info file has been uploaded yet")
    
    return FileResponse(
        path=WMS_INFO_PATH,
        filename="wms.json",
        media_type="application/json"
    )

def run_command(command):
    """Run the specified command in the working directory."""
    try:
        print(f"Running command: {command}")
        subprocess.run(command, shell=True, check=True, cwd=os.getcwd())
        print(f"Command completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except Exception as e:
        print(f"An error occurred while running the command: {e}")

def open_browser():
    """Open the browser after a short delay to ensure the server is running."""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")

def start_server():
    """Start the uvicorn server."""
    uvicorn.run(app, host="0.0.0.0", port=PORT)

class WMSUrl(BaseModel):
    url: str

class WMSLayer(BaseModel):
    layer_name: str
    description: str

@app.get("/wms", response_class=HTMLResponse)
async def get_wms_form():
    """Serve the WMS upload form HTML page."""
    with open("static/wms.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/wms/capabilities")
async def get_wms_capabilities(wms_url: WMSUrl):
    """Get WMS capabilities and available layers."""
    try:
        wms = WebMapService(wms_url.url)
        layers = []
        
        for layer_name in wms.contents:
            layer = wms[layer_name]
            layers.append({
                "name": layer_name,
                "title": layer.title,
                "abstract": layer.abstract
            })
        
        return JSONResponse(content={"layers": layers})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/wms/save")
async def save_wms_layer(layer: WMSLayer, request: Request):
    """Save WMS layer to database and process it."""
    try:
        # Get the WMS URL from the request body
        body = await request.json()
        wms_url = body.get('wms_url')
        
        if not wms_url:
            raise HTTPException(status_code=400, detail="WMS URL is required")
        
        # Create WMS info JSON file
        wms_info = {
            "wms_url": wms_url,
            "layer_name": layer.layer_name,
            "layer_description": layer.description
        }
        
        # Save to JSON file
        wms_file = TEMP_DIR / "wms.json"
        with open(wms_file, "w") as f:
            import json
            json.dump(wms_info, f, indent=2)
            WMS_INFO_PATH = wms_file
        
        # Run the collector command
        collector_command = "python main.py --collectors wms_wms_layer --now"
        launch_thread = threading.Thread(
            target=run_command,
            args=(collector_command,)
        )
        launch_thread.daemon = True
        launch_thread.start()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Layer processing started",
            "wms_info": wms_info
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print(f"Starting server at http://localhost:{PORT}")
    print(f"Upload page: http://localhost:{PORT}")
    print(f"Files will be accessible at http://localhost:{PORT}/tileset.zip")
    print(f"Temporary files stored in: {TEMP_DIR}")
    print("Press Ctrl+C to stop the server")
    
    start_server() 