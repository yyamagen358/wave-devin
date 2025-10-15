from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime

from app.video_generator import VideoGenerator
from app.poem_manager import PoemManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
POEM_DIR = DATA_DIR / "poem"
POEM_USED_DIR = DATA_DIR / "poem_used"
IMAGE_DIR = DATA_DIR / "images"
BGM_DIR = DATA_DIR / "bgm"
VIDEO_DIR = DATA_DIR / "videos"

for directory in [POEM_DIR, POEM_USED_DIR, IMAGE_DIR, BGM_DIR, VIDEO_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

poem_manager = PoemManager(str(POEM_DIR), str(POEM_USED_DIR))
video_generator = VideoGenerator(
    image_dir=str(IMAGE_DIR),
    bgm_path=str(BGM_DIR / "bgm_poem.mp3"),
    output_dir=str(VIDEO_DIR)
)

generation_tasks = {}

class GenerateRequest(BaseModel):
    count: int = 1

class TaskStatus(BaseModel):
    task_id: str
    status: str
    current: int
    total: int
    videos: List[str]
    message: Optional[str] = None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/poems/available")
async def get_available_poems():
    available = poem_manager.count_available_poems()
    return {
        "available": available,
        "used": poem_manager.count_used_poems()
    }

@app.post("/api/generate/single")
async def generate_single(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    generation_tasks[task_id] = {
        "status": "processing",
        "current": 0,
        "total": 1,
        "videos": [],
        "message": "Generating video..."
    }
    
    background_tasks.add_task(generate_videos_task, task_id, 1)
    
    return {"task_id": task_id, "message": "Video generation started"}

@app.post("/api/generate/batch")
async def generate_batch(request: GenerateRequest, background_tasks: BackgroundTasks):
    if request.count < 1 or request.count > 100:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 100")
    
    available = poem_manager.count_available_poems()
    if request.count > available:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough poems available. Requested: {request.count}, Available: {available}"
        )
    
    task_id = str(uuid.uuid4())
    generation_tasks[task_id] = {
        "status": "processing",
        "current": 0,
        "total": request.count,
        "videos": [],
        "message": f"Starting batch generation of {request.count} videos..."
    }
    
    background_tasks.add_task(generate_videos_task, task_id, request.count)
    
    return {"task_id": task_id, "message": f"Batch generation of {request.count} videos started"}

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = generation_tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        current=task["current"],
        total=task["total"],
        videos=task["videos"],
        message=task.get("message")
    )

@app.get("/api/videos")
async def list_videos():
    video_files = []
    if VIDEO_DIR.exists():
        for file in sorted(VIDEO_DIR.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True):
            video_files.append({
                "filename": file.name,
                "size": file.stat().st_size,
                "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
    return {"videos": video_files}

@app.get("/api/videos/{filename}")
async def download_video(filename: str):
    file_path = VIDEO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4"
    )

async def generate_videos_task(task_id: str, count: int):
    try:
        for i in range(count):
            generation_tasks[task_id]["message"] = f"Generating video {i+1} of {count}..."
            
            poem_file = poem_manager.get_random_poem()
            if not poem_file:
                generation_tasks[task_id]["status"] = "error"
                generation_tasks[task_id]["message"] = "No poems available"
                return
            
            video_filename = video_generator.generate_video(poem_file)
            
            poem_manager.mark_as_used(poem_file)
            
            generation_tasks[task_id]["current"] = i + 1
            generation_tasks[task_id]["videos"].append(video_filename)
            generation_tasks[task_id]["message"] = f"Generated {i+1} of {count} videos"
        
        generation_tasks[task_id]["status"] = "completed"
        generation_tasks[task_id]["message"] = f"Successfully generated {count} video(s)"
        
    except Exception as e:
        generation_tasks[task_id]["status"] = "error"
        generation_tasks[task_id]["message"] = f"Error: {str(e)}"
