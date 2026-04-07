"""
LifeOS Inference Script — REQUIRED for OpenEnv validation.

Prints structured [START]/[STEP]/[END] blocks to stdout so the
automated validator can parse task scores.

Steps:
  1. Initialize env for each task (easy, medium, hard)
  2. Run agent loop (LLM when available, heuristic fallback)
  3. Print [STEP] after every env.step()
  4. Grade final state
  5. Print [END] with score

Uses OpenAI Client for LLM calls via API_BASE_URL, MODEL_NAME, HF_TOKEN.
"""

# ── Force unbuffered stdout BEFORE anything else ─────────────────────────────
import os
import sys

os.environ["PYTHONUNBUFFERED"] = "1"

import random
import json

# ── Guard openai import — must never crash the script ────────────────────────
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from lifeos.env import LifeOSEnv
from lifeos.utils import grade_agent

# Reproducibility
random.seed(42)

# ─── Config ──────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

MAX_STEPS = 100
TASKS = ["easy", "medium", "hard"]
ACTIONS = [
    "work_overtime", "exercise", "invest_money", "learn_skill", "socialize",
    "rest", "start_side_hustle", "take_vacation", "meditate", "gamble"
]


def get_llm_action(client, state, step_num):
    """Ask the LLM to pick the best action."""
    try:
        prompt = (
            f"You are an AI life-management agent.\n"
            f"Step {step_num}. Current state:\n{json.dumps(state, indent=2)}\n\n"
            f"Available actions: {ACTIONS}\n\n"
            f"Pick ONE action to maximize long-term wellbeing "
            f"(high health, low stress, growing career & relationships).\n"
            f"Reply with ONLY the action name."
        )
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.3,
        )
        action = resp.choices[0].message.content.strip().lower()
        if action in ACTIONS:
            return action
    except Exception:
        pass
    return None


def heuristic_action(state):
    """Rule-based fallback agent."""
    h = state.get("health", 50)
    st = state.get("stress", 50)
    m = state.get("money", 5000)
    c = state.get("career", 50)
    r = state.get("relationships", 50)

    if st > 70:   return "rest"
    if h < 40:    return "exercise"
    if m < 2000:  return "work_overtime"
    if r < 30:    return "socialize"
    if c < 30:    return "learn_skill"
    if m > 10000: return "invest_money"
    if st > 40:   return "exercise"
    if c < 50:    return "learn_skill"
    if r < 50:    return "socialize"
    return random.choice(ACTIONS)


def run_task(task_name, use_llm=False, client=None):
    """
    Run one task episode.

    Prints the REQUIRED structured output:
      [START] task=<name>
      [STEP] step=<n> reward=<r>
      ...
      [END] task=<name> score=<s> steps=<n>
    """
    env = LifeOSEnv(personality="ambitious", task=task_name, seed=42)
    state = env.reset()

    # ── [START] block ────────────────────────────────────────────────────────
    print(f"[START] task={task_name}", flush=True)

    total_reward = 0.0
    steps = 0

    for i in range(MAX_STEPS):
        # Choose action
        action = None
        if use_llm and client:
            action = get_llm_action(client, state, i)
        if action is None:
            action = heuristic_action(state)

        # Execute action
        result = env.step(action)
        state = result["state"]
        reward = result["reward"]
        total_reward += reward
        steps = i + 1

        # ── [STEP] block ────────────────────────────────────────────────────
        print(f"[STEP] step={steps} reward={round(reward, 4)}", flush=True)

        if result["done"]:
            break

    # Grade final state
    score = grade_agent(state)

    # ── [END] block ──────────────────────────────────────────────────────────
    print(f"[END] task={task_name} score={round(score, 4)} steps={steps}", flush=True)

    return {
        "task": task_name,
        "final_state": state,
        "score": score,
        "total_reward": round(total_reward, 4),
        "steps": steps,
    }


def main():
    # ── Try LLM client ───────────────────────────────────────────────────────
    use_llm = False
    client = None
    if API_BASE_URL and MODEL_NAME and HF_TOKEN and OpenAI is not None:
        try:
            client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
            use_llm = True
        except Exception:
            pass

    # ── Run all tasks ────────────────────────────────────────────────────────
    results = {}
    for task in TASKS:
        r = run_task(task, use_llm=use_llm, client=client)
        results[task] = r

    return results


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Even on crash, print something so the validator sees output
        print(f"[ERROR] inference.py crashed: {e}", flush=True)
        sys.exit(1)
