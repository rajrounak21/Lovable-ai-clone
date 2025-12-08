from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import shutil
import os
import pathlib

# Import the agent from the existing codebase
# app_builder must be a package in the python path
from app_builder.graph import agent
from app_builder.tools import PROJECT_ROOT

app = FastAPI()

# Ensure templates directory exists (will be created by next tool call)
templates = Jinja2Templates(directory="templates")

class GenerateRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(request: GenerateRequest):
    try:
        # cleanup previous build to ensure fresh start
        if PROJECT_ROOT.exists():
            for item in PROJECT_ROOT.iterdir():
                if item.is_dir():
                    try:
                        shutil.rmtree(item)
                    except Exception as e:
                        print(f"Could not remove dir {item}: {e}")
                else:
                    try:
                        item.unlink()
                    except Exception as e:
                        print(f"Could not remove file {item}: {e}")
        else:
            PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

        print(f"Generating project for prompt: {request.prompt}")
        
        # Run the LangGraph agent
        result = agent.invoke({"user_prompt": request.prompt}, config={"recursion_limit": 50})
        
        return {"status": "success", "message": "Project generated successfully"}
    except Exception as e:
        print(f"Error during generation: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/download")
async def download_zip():
    if not PROJECT_ROOT.exists():
        return {"status": "error", "message": "No project generated yet."}
    
    # Create zip file in the current working directory
    zip_base_name = "generated_project"
    archive_path = shutil.make_archive(zip_base_name, 'zip', PROJECT_ROOT)
    
    return FileResponse(archive_path, media_type='application/zip', filename="project.zip")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
