---
title: Lifeos AI Simulator
emoji: 🧬
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# 🧬 LifeOS — AI Digital Life Simulator

> A production-grade, OpenEnv-compatible reinforcement learning environment that simulates human life with realistic dynamics, personality systems, dynamic events, and adaptive difficulty.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **OpenEnv API** | Full `reset()` / `step(action)` / `state()` compliance |
| **7 State Variables** | Age, Health, Money, Stress, Career, Relationships, Happiness |
| **6 Actions** | Work overtime, Exercise, Invest, Learn, Socialize, Rest |
| **Dynamic Events** | Job promotion, job loss, medical emergency, market crash |
| **4 Personalities** | Risk-taker, Conservative, Lazy, Ambitious |
| **3 Difficulty Tasks** | Easy (no events), Medium, Hard (high randomness) |
| **Reward System** | Normalized [-1,+1] with balance bonus and personality bias |
| **Grading** | `grade_agent()` returns 0.0 – 1.0 score |
| **Premium Dashboard** | Glassmorphism SaaS UI with dark/light theme |
| **LLM Agent** | OpenAI-compatible inference with heuristic fallback |

---

## 🏗️ Architecture

```
lifeos/
├── env.py          # Core LifeOSEnv (reset, step, state)
├── models.py       # Pydantic models (typed, validated)
├── utils.py        # Grading, events, personality, helpers
├── __init__.py     # Package exports
app.py              # FastAPI server (POST /reset, /step, /state)
inference.py        # Required inference script (all 3 tasks)
openenv.yaml        # OpenEnv manifest
Dockerfile          # Production Docker image
static/
└── index.html      # Premium dashboard UI
```

---

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
# → http://localhost:7860
```

### Docker

```bash
docker build -t lifeos .
docker run -p 7860:7860 lifeos
```

### Run Inference

```bash
# With LLM (set env vars first)
export API_BASE_URL="https://..."
export MODEL_NAME="meta-llama/..."
export HF_TOKEN="hf_..."

python inference.py

# Without LLM (heuristic fallback)
python inference.py
```

---

## 📊 Example Output

```
============================================================
  LifeOS — AI Digital Life Simulator
  Inference Script
============================================================

──────────────────────────────────────────────────
  Task: EASY
──────────────────────────────────────────────────
  Steps:        100
  Total reward: 48.2310
  Grade Score:  0.6842

──────────────────────────────────────────────────
  Task: MEDIUM
──────────────────────────────────────────────────
  Steps:        100
  Total reward: 39.1205
  Grade Score:  0.5934

──────────────────────────────────────────────────
  Task: HARD
──────────────────────────────────────────────────
  Steps:        87
  Total reward: 22.5601
  Grade Score:  0.4215

============================================================
  FINAL SCORES
============================================================
      easy: 0.6842
    medium: 0.5934
      hard: 0.4215
   average: 0.5664
============================================================
```

---

## 🔌 API Reference

| Endpoint | Method | Body | Returns |
|----------|--------|------|---------|
| `/reset` | POST | `{task?, personality?, seed?}` | State dict |
| `/step` | POST | `{action}` | `{state, reward, done, info}` |
| `/state` | POST | — | State dict |
| `/health` | GET | — | `{status: "ok"}` |
| `/` | GET | — | Dashboard HTML |

---

## 📄 License

MIT © 2026
