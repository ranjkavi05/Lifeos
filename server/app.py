"""
LifeOS FastAPI Server — OpenEnv-compatible HTTP API.
Moved to server/app.py for validation compliance.
"""
import os
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from inference import heuristic_action
except ImportError:
    def heuristic_action(state: dict) -> str:
        return "rest"

from lifeos.env import LifeOSEnv
from lifeos.models import LifeState, StepResponse

app = FastAPI(
    title="LifeOS",
    description="AI Digital Life Simulator — OpenEnv Environment",
    version="1.0.0",
)

# Mount static files (CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Global environment instance
env = LifeOSEnv(personality="ambitious", task="medium", seed=42)

# Request Models
class StepRequest(BaseModel):
    action: str
    task: Optional[str] = None
    personality: Optional[str] = None

class ResetRequest(BaseModel):
    task: Optional[str] = None
    personality: Optional[str] = None
    seed: Optional[int] = None

# Endpoints
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/reset", response_model=LifeState)
async def reset(request: Optional[ResetRequest] = None):
    global env
    task = "medium"
    personality = "ambitious"
    seed = 42
    if request:
        task = request.task or task
        personality = request.personality or personality
        seed = request.seed if request.seed is not None else seed
    env = LifeOSEnv(personality=personality, task=task, seed=seed)
    return env.reset()

@app.post("/step", response_model=StepResponse)
async def step(request: StepRequest):
    global env
    if request.task and request.task != env.task_name:
        env = LifeOSEnv(personality=request.personality or env.personality, task=request.task or "medium")
        env.reset()
    return env.step(request.action)

@app.post("/state", response_model=LifeState)
async def get_state():
    return env.state()

@app.post("/state_full")
async def get_state_full():
    return env.state()

@app.post("/auto_step")
async def auto_step_ui(req: Request):
    data = await req.json()
    st = data.get("state", {})
    action = heuristic_action(st)
    reasons = {
        "rest": "Stress elevated.",
        "exercise": "Physical metric decaying.",
        "work_overtime": "Capital reserves low.",
        "socialize": "Synergy sub-optimal.",
        "learn_skill": "Trajectory stagnant.",
        "invest_money": "Surplus capital evaluated.",
        "start_side_hustle": "Aggressive expansion.",
        "take_vacation": "Burnout detected.",
        "meditate": "Equilibrium disruption.",
        "gamble": "Calculated volatility."
    }
    return {"action": action, "reasoning": reasons.get(action, "Optimal path.")}

# Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>LifeOS</h1>")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    path = os.path.join(os.path.dirname(__file__), "..", "static", "login.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>LifeOS Login</h1>")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    path = os.path.join(os.path.dirname(__file__), "..", "static", "register.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>LifeOS Register</h1>")

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()
