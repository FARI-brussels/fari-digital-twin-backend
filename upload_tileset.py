from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
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
import zipfile  # Added for zip inspection

# Create the FastAPI application
app = FastAPI(title="ZIP Upload Server")

# Use system temp directory for uploads
TEMP_DIR = Path(tempfile.gettempdir()) / "zip_uploads"
TEMP_DIR.mkdir(exist_ok=True)

# Mount the temp directory to serve files directly
app.mount("/uploads", StaticFiles(directory=TEMP_DIR), name="uploads")

# Port to run the server on
PORT = 8887

# Path for the latest tileset
LATEST_TILESET_PATH = TEMP_DIR / "tileset.zip"

def inspect_zip_content(zip_path):
    """
    Inspect the ZIP file content to check if it contains .ptns files or .glb files.
    Returns: "bim" if .glb files are found, "pointcloud" if .pnts files are found, 
    or "unknown" if neither is found.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Convert all filenames to lowercase for case-insensitive matching
            file_list_lower = [f.lower() for f in file_list]
            
            # Check if any .ptns files exist (pointcloud)
            has_ptns = any(filename.endswith('.pnts') for filename in file_list_lower)
            
            # Check if any .glb files exist (BIM)
            has_glb = any(filename.endswith('.glb') for filename in file_list_lower)
            
            # Determine the type based on file extensions
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
    return HTMLResponse(content=get_html_template())

@app.get("/upload", response_class=RedirectResponse)
async def redirect_to_root():
    """Redirect /upload GET requests to the root path."""
    return RedirectResponse(url="/")

@app.post("/upload")
async def upload_zip_file(zipfile: UploadFile = File(...)):
    """Handle ZIP file upload."""
    # Check if the file is a ZIP
    if not zipfile.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    # Create a unique filename with timestamp to avoid overwrites
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{Path(zipfile.filename).stem}_{timestamp}.zip"
    filepath = TEMP_DIR / filename
    
    # Save the uploaded file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(zipfile.file, buffer)
    
    # Create a copy of the file as tileset.zip
    if LATEST_TILESET_PATH.exists():
        LATEST_TILESET_PATH.unlink()  # Remove existing file
    
    # Copy the file
    shutil.copy2(filepath, LATEST_TILESET_PATH)
    
    # Inspect the ZIP content to determine what type of model it contains
    content_type = inspect_zip_content(filepath)
    
    # Determine which collector to run based on content
    if content_type == "bim":
        collector_command = "python main.py --collectors bim_tilesets --now"
    else:
        # Default to pointcloud_tilesets for pointcloud or unknown types
        collector_command = "python main.py --collectors pointcloud_tilesets --now"
    # Launch the command in a separate thread
    launch_thread = threading.Thread(
        target=run_command,
        args=(collector_command,)
    )
    launch_thread.daemon = True
    launch_thread.start()
    # Redirect to a success page with content type info
    return HTMLResponse(content=get_success_html(filename, content_type, collector_command))

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

def run_command(command):
    """Run the specified command in the working directory."""
    try:
        print(f"Running command: {command}")
        # Use shell=True to properly execute complex commands with arguments
        subprocess.run(command, shell=True, check=True, cwd=os.getcwd())
        print(f"Command completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
    except Exception as e:
        print(f"An error occurred while running the command: {e}")

def get_html_template():
    """Return the HTML template for the upload form."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Modern ZIP File Upload Server</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 30px;
            }
            .upload-container {
                border: 2px dashed #ddd;
                padding: 30px;
                text-align: center;
                margin: 20px 0;
                border-radius: 8px;
                background-color: #f9f9f9;
                transition: all 0.3s ease;
            }
            .upload-container:hover {
                border-color: #3498db;
                background-color: #f5f9fc;
            }
            .file-input {
                display: none;
            }
            .file-label {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                cursor: pointer;
                display: inline-block;
                margin: 10px 0;
                font-weight: 500;
                transition: background-color 0.3s ease;
            }
            .file-label:hover {
                background-color: #2980b9;
            }
            .file-name {
                margin-top: 15px;
                font-size: 14px;
                color: #666;
            }
            .submit-btn {
                background-color: #2ecc71;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                margin-top: 10px;
                transition: background-color 0.3s ease;
            }
            .submit-btn:hover {
                background-color: #27ae60;
            }
            .info {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-top: 40px;
                border-left: 4px solid #3498db;
            }
            .info h2 {
                margin-top: 0;
                font-size: 20px;
                color: #2c3e50;
            }
            .info p {
                margin-bottom: 10px;
            }
            .drop-zone {
                padding: 25px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                border: 3px dashed #ddd;
                border-radius: 8px;
                transition: all 0.3s ease;
                background-color: #f9f9f9;
                margin-bottom: 20px;
                min-height: 150px;
            }
            .drop-zone.active {
                border-color: #3498db;
                background-color: #e3f2fd;
            }
            .drop-zone-prompt {
                color: #666;
                margin-bottom: 15px;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <h1>Modern ZIP File Upload Server</h1>
        
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="upload-container">
                <div id="drop-zone" class="drop-zone">
                    <div class="drop-zone-prompt">Drag and drop ZIP file here</div>
                    <span>OR</span>
                    <label for="file-upload" class="file-label">Choose ZIP File</label>
                </div>
                
                <input type="file" name="zipfile" id="file-upload" class="file-input" accept=".zip">
                <div id="file-name" class="file-name">No file selected</div>
                
                <button type="submit" class="submit-btn">Upload</button>
            </div>
        </form>
        
        <div class="info">
            <h2>How to Access Your File</h2>
            <p>Once uploaded, your ZIP file will be available at:</p>
            <p><strong>http://localhost:{PORT}/tileset.zip</strong></p>
            <p>This URL will always point to your most recently uploaded ZIP file.</p>
            <p>After upload, the system will automatically detect the content type (BIM or pointcloud) and run the appropriate processing command.</p>
        </div>
        
        <script>
            // Show the selected filename
            const fileInput = document.getElementById('file-upload');
            const fileName = document.getElementById('file-name');
            const dropZone = document.getElementById('drop-zone');
            
            fileInput.addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    fileName.textContent = e.target.files[0].name;
                } else {
                    fileName.textContent = 'No file selected';
                }
            });
            
            // Drag and drop functionality
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                dropZone.classList.add('active');
            }
            
            function unhighlight() {
                dropZone.classList.remove('active');
            }
            
            dropZone.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {
                    fileInput.files = files;
                    fileName.textContent = files[0].name;
                }
            }
        </script>
    </body>
    </html>
    """

def get_success_html(filename, content_type, command):
    """Return the HTML template for the success page."""
    # Determine content type text for display
    if content_type == "bim":
        content_type_text = "Building Information Model (BIM)"
    elif content_type == "pointcloud":
        content_type_text = "Point Cloud"
    else:
        content_type_text = "Unknown (processed as Point Cloud)"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Successful</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }}
            h1 {{
                color: #2ecc71;
                margin-bottom: 30px;
            }}
            .success-message {{
                background-color: #e8f5e9;
                border-left: 5px solid #2ecc71;
                padding: 20px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .link-container {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-top: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .link-container a {{
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .link-container a:hover {{
                text-decoration: underline;
                color: #2980b9;
            }}
            .back-btn {{
                display: inline-block;
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 30px;
                font-weight: 500;
                transition: background-color 0.3s ease;
            }}
            .back-btn:hover {{
                background-color: #2980b9;
            }}
            .file-info {{
                background-color: #f1f8ff;
                padding: 15px;
                border-radius: 4px;
                margin-top: 15px;
                border-left: 3px solid #3498db;
            }}
            .file-info p {{
                margin: 5px 0;
            }}
            .file-info strong {{
                color: #2c3e50;
            }}
            .processing {{
                background-color: #fff8e1;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                border-left: 3px solid #ffc107;
            }}
            .content-type {{
                background-color: #e8eaf6;
                padding: 15px;
                border-radius: 4px;
                margin-top: 20px;
                border-left: 3px solid #3f51b5;
            }}
        </style>
    </head>
    <body>
        <h1>Upload Successful!</h1>
        
        <div class="success-message">
            <p>Your file has been uploaded successfully.</p>
        </div>
        
        <div class="file-info">
            <p><strong>Filename:</strong> {filename}</p>
            <p><strong>Upload time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Stored as:</strong> Temporary file in system temp directory</p>
        </div>
        
        <div class="content-type">
            <p><strong>Detected Content Type:</strong> {content_type_text}</p>
        </div>
        
        <div class="processing">
            <p><strong>Processing:</strong> The command <code>{command}</code> has been launched.</p>
        </div>
        
        <div class="link-container">
            <h2>Access Your File</h2>
            <p>Your file is now available at:</p>
            <ul>
                <li><a href="/tileset.zip" target="_blank">http://localhost:{PORT}/tileset.zip</a> (always points to the most recent upload)</li>
            </ul>
        </div>
        
        <a href="/" class="back-btn">Upload Another File</a>
    </body>
    </html>
    """

def open_browser():
    """Open the browser after a short delay to ensure the server is running."""
    # Wait for server to start
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")

def start_server():
    """Start the uvicorn server."""
    uvicorn.run(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # Start browser opening in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Print startup message
    print(f"Starting server at http://localhost:{PORT}")
    print(f"Upload page: http://localhost:{PORT}")
    print(f"Files will be accessible at http://localhost:{PORT}/tileset.zip")
    print(f"Temporary files stored in: {TEMP_DIR}")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    start_server()