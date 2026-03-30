"""
LifeOS FastAPI Server — OpenEnv-compatible HTTP API.

Endpoints:
    POST /reset  → Reset environment, return initial state
    POST /step   → Execute action, return {state, reward, done, info}
    POST /state  → Return current state
    GET  /health → Health check
    GET  /       → Dashboard UI
"""
import os
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any

try:
    from inference import heuristic_action
except ImportError:
    def heuristic_action(state): return "rest"

from lifeos.env import LifeOSEnv
from lifeos.models import LifeState, StepResponse


app = FastAPI(
    title="LifeOS",
    description="AI Digital Life Simulator — OpenEnv Environment",
    version="1.0.0",
)

# Global environment instance
env = LifeOSEnv(personality="ambitious", task="medium", seed=42)


# ─── Request Models ──────────────────────────────────────────────────────────

class StepRequest(BaseModel):
    action: str
    task: Optional[str] = None
    personality: Optional[str] = None


class ResetRequest(BaseModel):
    task: Optional[str] = None
    personality: Optional[str] = None
    seed: Optional[int] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/reset", response_model=LifeState)
async def reset(request: Optional[ResetRequest] = None):
    """Reset the environment. Accepts optional task/personality/seed."""
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
    """Execute an action. Returns {state, reward, done, info}."""
    global env

    # Allow in-flight task/personality switch
    if request.task and request.task != env.task_name:
        env = LifeOSEnv(
            personality=request.personality or env.personality,
            task=request.task,
        )
        env.reset()

    return env.step(request.action)


@app.post("/state", response_model=LifeState)
async def get_state():
    """Return the current environment state."""
    return env.state()

@app.post("/state_full")
async def get_state_full():
    """Return the complete un-filtered environment state for the frontend UI."""
    return env._state

@app.post("/auto_step")
async def auto_step_ui(req: Request):
    """UI helper that asks the background heuristic agent for the optimal next action."""
    data = await req.json()
    st = data.get("state", {})
    action = heuristic_action(st)
    
    reasons = {
        "rest": "Stress elevated. Neural recalibration mandated.",
        "exercise": "Physical metric decaying. Executing bio-maintenance.",
        "work_overtime": "Capital reserves critically low. Force wealth generation.",
        "socialize": "Synergy sub-optimal. Engaging localized social mesh.",
        "learn_skill": "Trajectory stagnant. Acquiring superior data paradigms.",
        "invest_money": "Surplus capital evaluated. Allocating to high-yield risk nodes.",
        "start_side_hustle": "Aggressive expansion protocol. Tolerance for severe stress activated.",
        "take_vacation": "Catastrophic burnout detected. Mandating absolute sensory reset.",
        "meditate": "Equilibrium disruption detected. Executing Zen protocol.",
        "gamble": "Calculated volatility engaged for rapid geometric capital burst."
    }
    return {"action": action, "reasoning": reasons.get(action, "Optimal path computed.")}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the premium LifeOS dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>LifeOS</h1><p>Dashboard loading…</p>")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    html_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>LifeOS</h1><p>Login missing</p>")

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    html_path = os.path.join(os.path.dirname(__file__), "static", "register.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>LifeOS</h1><p>Register missing</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
