from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json

app = FastAPI()

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level
TEMPLATES_DIR = os.path.join(BASE_DIR, 'webserver', "templates")
STATIC_DIR = os.path.join(BASE_DIR, 'webserver', "static")
VIDEOS_DIR = os.path.normpath(os.path.join(BASE_DIR, "data", "video"))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
KNOWLEDGE_DIR = os.path.normpath(os.path.join(BASE_DIR, "data", "knowledge"))

# Create directories if they don't exist
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(CONFIGS_DIR, exist_ok=True)

# Create knowledge dir if it does not exist
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# Setup templates and static files
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit_knowledge")
async def submit_knowledge(
    request: Request,
    bot_token: str = Form(...),
    bot_picture: UploadFile = File(...),
    files: list[UploadFile] = File(...)
):
    """
    Endpoint to receive knowledge base information from the frontend.
    """
    try:
        # Save bot picture
        picture_path = os.path.join(KNOWLEDGE_DIR, bot_picture.filename)
        with open(picture_path, "wb") as pic_file:
            pic_file.write(await bot_picture.read())

        # Save files
        saved_files = []
        for file in files:
            file_path = os.path.join(KNOWLEDGE_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            saved_files.append(file_path)

        # Save all the data to a JSON file
        data = {
            "bot_token": bot_token,
            "bot_picture": bot_picture.filename,
            "files": [os.path.basename(f) for f in saved_files]
        }
        json_file_path = os.path.join(KNOWLEDGE_DIR, "knowledge_data.json")
        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        return {"message": "Knowledge base data saved successfully!", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos", response_class=HTMLResponse)
async def video_list(request: Request):
    try:
        # Load video descriptions
        descriptions_path = os.path.join(CONFIGS_DIR, "video_descriptions.json")
        try:
            with open(descriptions_path, 'r', encoding='utf-8') as f:
                descriptions = json.load(f)
                videos_info = descriptions["videos"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load descriptions: {e}")
            videos_info = {}

        # Get list of available videos
        available_videos = []
        for video_name in os.listdir(VIDEOS_DIR):
            if video_name.endswith(('.mp4', '.avi', '.MP4', '.MOV', '.mov')):
                video_id = os.path.splitext(video_name)[0]
                video_info = videos_info.get(video_id, {
                    "name": video_name,
                    "short_description": "No short description available.",
                    "long_description": "No detailed description available."
                })
                available_videos.append({
                    "filename": video_name,
                    "info": video_info
                })

        return templates.TemplateResponse(
            "video_list.html",
            {
                "request": request,
                "videos": available_videos
            }
        )
    except Exception as e:
        print(f"Error serving video list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/watch/{video_name}", response_class=HTMLResponse)
async def watch_video(video_name: str, request: Request):
    try:
        # Check if video exists
        video_path = os.path.join(VIDEOS_DIR, video_name)
        print(f"Looking for video at path: {video_path}")
        if not os.path.exists(video_path):
            print(f"Video not found at path: {video_path}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Load video descriptions from JSON
        descriptions_path = os.path.join(CONFIGS_DIR, "video_descriptions.json")
        try:
            with open(descriptions_path, 'r', encoding='utf-8') as f:
                descriptions = json.load(f)
            # Get video info without extension
            video_name_without_ext = os.path.splitext(video_name)[0]
            video_info = descriptions["videos"].get(video_name_without_ext, {
                "name": video_name,
                "short_description": "No short description available.",
                "long_description": "No detailed description available."
            })
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load descriptions: {e}")
            video_info = {
                "name": video_name,
                "short_description": "No short description available.",
                "long_description": "No detailed description available."
            }

        # Use the mounted /videos path instead of filesystem path
        video_url = f"/videos/{video_name}"
        print(f"Video URL: {video_url}")

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "video_name": video_info["name"],
                "video_url": video_url,
                "short_description": video_info["short_description"],
                "long_description": video_info["long_description"]
            }
        )
    except Exception as e:
        print(f"Error serving video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))