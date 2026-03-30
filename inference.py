"""
LifeOS Inference Script — REQUIRED for OpenEnv validation.

Steps:
  1. Initialize env for each task (easy, medium, hard)
  2. Run agent loop (LLM when available, heuristic fallback)
  3. Collect final state
  4. Call grader
  5. Print scores

Uses OpenAI Client for LLM calls via API_BASE_URL, MODEL_NAME, HF_TOKEN.
"""
import os
import random
import json

from openai import OpenAI

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
    """Run one task episode, return results dict."""
    env = LifeOSEnv(personality="ambitious", task=task_name, seed=42)
    state = env.reset()
    total_reward = 0.0
    events = []
    steps = 0

    for i in range(MAX_STEPS):
        action = None
        if use_llm and client:
            action = get_llm_action(client, state, i)
        if action is None:
            action = heuristic_action(state)

        result = env.step(action)
        state = result["state"]
        total_reward += result["reward"]
        if "event" in result["info"]:
            events.append(result["info"]["event"])
        steps = i + 1
        if result["done"]:
            break

    score = grade_agent(state)
    return {
        "task": task_name,
        "final_state": state,
        "score": score,
        "total_reward": round(total_reward, 4),
        "steps": steps,
        "events": events,
    }


def main():
    print("=" * 60)
    print("  LifeOS - AI Digital Life Simulator")
    print("  Inference Script")
    print("=" * 60)

    # Try LLM client
    use_llm = False
    client = None
    if API_BASE_URL and MODEL_NAME and HF_TOKEN:
        try:
            client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
            use_llm = True
            print(f"\n[OK] LLM client ready: {MODEL_NAME}")
        except Exception as e:
            print(f"\n[WARN] LLM init failed: {e}. Heuristic mode.")
    else:
        print("\n[INFO] No LLM creds. Using heuristic agent.")

    results = {}
    for task in TASKS:
        print(f"\n{'-'*50}")
        print(f"  Task: {task.upper()}")
        print(f"{'-'*50}")

        r = run_task(task, use_llm=use_llm, client=client)
        results[task] = r

        print(f"  Steps:        {r['steps']}")
        print(f"  Total reward: {r['total_reward']}")
        print(f"  Events:       {len(r['events'])}")
        print(f"  Final State:")
        for k, v in r["final_state"].items():
            print(f"    {k:>15}: {v}")
        print(f"  Grade Score:  {r['score']:.4f}")

    # Summary
    print(f"\n{'='*60}")
    print("  FINAL SCORES")
    print(f"{'='*60}")
    for t in TASKS:
        print(f"  {t:>8}: {results[t]['score']:.4f}")
    avg = sum(results[t]["score"] for t in TASKS) / len(TASKS)
    print(f"  {'average':>8}: {avg:.4f}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    main()
