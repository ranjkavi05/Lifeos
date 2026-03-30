"""
LifeOS Utilities - Grading, events, personality modifiers, and helpers.
"""
import random
from typing import Dict, Any, Optional, Tuple


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(max_val, value))


# ─── State Bounds ────────────────────────────────────────────────────────────

STATE_BOUNDS = {
    "age": (0, 100),
    "health": (0, 100),
    "money": (0, 100000),
    "stress": (0, 100),
    "career": (0, 100),
    "relationships": (0, 100),
    "happiness": (0, 100),
}


def clamp_state(state: Dict[str, float]) -> Dict[str, float]:
    """Clamp all state values to their valid ranges."""
    for key, (lo, hi) in STATE_BOUNDS.items():
        if key in state:
            state[key] = clamp(float(state[key]), lo, hi)
    return state


# ─── Grading Function ────────────────────────────────────────────────────────

def grade_agent(final_state: Dict[str, Any]) -> float:
    """
    Grade the agent's performance based on final state.
    
    Returns a float score strictly between 0.0 and 1.0.
    
    Scoring weights:
      - Health:        25%  (higher is better)
      - Money:         20%  (higher is better)
      - Career:        20%  (higher is better)
      - Relationships: 20%  (higher is better)
      - Stress:        15%  (lower is better)
    """
    # Extract values with safe defaults
    health = float(final_state.get("health", 0))
    money = float(final_state.get("money", 0))
    career = float(final_state.get("career", 0))
    relationships = float(final_state.get("relationships", 0))
    stress = float(final_state.get("stress", 50))

    # Normalize each metric to 0-1 range
    health_score = clamp(health / 100.0, 0.0, 1.0)
    money_score = clamp(money / 100000.0, 0.0, 1.0)
    career_score = clamp(career / 100.0, 0.0, 1.0)
    rel_score = clamp(relationships / 100.0, 0.0, 1.0)
    stress_score = clamp(1.0 - (stress / 100.0), 0.0, 1.0)

    # Weighted combination
    score = (
        0.25 * health_score
        + 0.20 * money_score
        + 0.20 * career_score
        + 0.20 * rel_score
        + 0.15 * stress_score
    )

    # Strictly clamp between 0 and 1 — no NaN possible
    result = float(min(max(score, 0.0), 1.0))
    if result != result:  # NaN guard
        result = 0.0
    return round(result, 4)


# ─── Event System ────────────────────────────────────────────────────────────

EVENTS = {
    "job_promotion": {
        "description": "You got a job promotion!",
        "effects": {"career": 15, "money": 5000, "happiness": 10, "stress": 5},
    },
    "job_loss": {
        "description": "You lost your job.",
        "effects": {"career": -20, "money": -3000, "stress": 20, "happiness": -15},
    },
    "medical_emergency": {
        "description": "A medical emergency occurred.",
        "effects": {"health": -25, "money": -8000, "stress": 15, "happiness": -10},
    },
    "market_crash": {
        "description": "The market crashed!",
        "effects": {"money": -15000, "stress": 10, "happiness": -5},
    },
}


def maybe_trigger_event(
    state: Dict[str, float],
    probability: float = 0.1,
    rng: Optional[random.Random] = None,
) -> Tuple[Dict[str, float], Optional[str]]:
    """
    Potentially trigger a random event that modifies state.
    Returns (modified_state, event_name_or_None).
    """
    r = rng if rng else random
    if r.random() > probability:
        return state, None

    event_name = r.choice(list(EVENTS.keys()))
    event = EVENTS[event_name]

    for key, delta in event["effects"].items():
        if key in state:
            state[key] = state[key] + delta

    state = clamp_state(state)
    return state, event_name


# ─── Personality Modifiers ───────────────────────────────────────────────────

PERSONALITY_MODIFIERS = {
    "risk_taker": {"action_multiplier": 1.3, "reward_bias": 0.05, "stress_factor": 1.2},
    "conservative": {"action_multiplier": 0.7, "reward_bias": 0.0, "stress_factor": 0.8},
    "lazy": {"action_multiplier": 0.5, "reward_bias": -0.05, "stress_factor": 0.6},
    "ambitious": {"action_multiplier": 1.2, "reward_bias": 0.1, "stress_factor": 1.1},
}


def get_personality_modifier(personality: str) -> Dict[str, float]:
    """Get personality modifiers, defaulting to neutral if unknown."""
    return PERSONALITY_MODIFIERS.get(
        personality, {"action_multiplier": 1.0, "reward_bias": 0.0, "stress_factor": 1.0}
    )
