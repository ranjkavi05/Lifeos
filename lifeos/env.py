"""
LifeOS Core Environment — OpenEnv-compatible RL environment.

Implements: reset(), step(action), state()
step() returns: {"state": dict, "reward": float, "done": bool, "info": dict}
"""
import random
from typing import Dict, Any, Optional

from lifeos.models import ActionType, TaskConfig
from lifeos.utils import (
    clamp, clamp_state, get_personality_modifier,
    maybe_trigger_event, EVENTS,
)

# ─── Action Effects (each action touches multiple variables) ─────────────────
ACTION_EFFECTS: Dict[str, Dict[str, float]] = {
    "work_overtime":  {"money": 2000, "career": 5,  "stress": 10,  "health": -3, "happiness": -5, "relationships": -3},
    "exercise":       {"health": 8,   "stress": -7, "happiness": 5, "money": -50, "career": 0,    "relationships": 1},
    "invest_money":   {"money": 3000, "stress": 5,  "career": 3,   "health": 0,  "happiness": 2,  "relationships": 0},
    "learn_skill":    {"career": 7,   "stress": 4,  "happiness": 3, "money": -500,"health": -1,   "relationships": -1},
    "socialize":      {"relationships": 8, "happiness": 7, "stress": -5, "money": -200, "career": 1, "health": 1},
    "rest":           {"health": 5,   "stress": -10,"happiness": 3, "money": 0,   "career": -1,   "relationships": 0},
    "start_side_hustle": {"money": 5000, "career": 15, "stress": 25, "health": -10, "happiness": -5, "relationships": -10},
    "take_vacation":   {"money": -4000, "stress": -40, "happiness": 20, "health": 15, "career": -5, "relationships": 5},
    "meditate":        {"stress": -15, "happiness": 10, "health": 5, "money": 0, "career": 0, "relationships": 0},
    "gamble":          {"stress": 15, "happiness": -3, "health": -2},
}

# ─── Task Configurations ─────────────────────────────────────────────────────
TASK_CONFIGS: Dict[str, TaskConfig] = {
    "easy": TaskConfig(name="easy", events_enabled=False, event_probability=0.0,
                       description="Stable environment with no random events"),
    "medium": TaskConfig(name="medium", events_enabled=True, event_probability=0.15,
                         description="Moderate difficulty with occasional events"),
    "hard": TaskConfig(name="hard", events_enabled=True, event_probability=0.35,
                       description="High difficulty with frequent random events"),
}

# ─── Initial State ────────────────────────────────────────────────────────────
INITIAL_STATE: Dict[str, float] = {
    "age": 20.0, "health": 80.0, "money": 5000.0,
    "stress": 20.0, "career": 10.0, "relationships": 50.0, "happiness": 60.0,
}


class LifeOSEnv:
    """
    LifeOS: AI Digital Life Simulator.

    An OpenEnv-compatible reinforcement learning environment simulating
    a human life with realistic state dynamics, personality systems,
    dynamic events, and adaptive difficulty.
    """

    def __init__(
        self,
        personality: str = "ambitious",
        task: str = "medium",
        seed: Optional[int] = None,
    ):
        self.personality = personality
        self.task_name = task
        self.task_config = TASK_CONFIGS.get(task, TASK_CONFIGS["medium"])
        self.personality_mod = get_personality_modifier(personality)
        self.rng = random.Random(seed)
        self._step_count: int = 0
        self._done: bool = False
        self._state: Dict[str, float] = {}
        self.reset()

    # ── OpenEnv API ──────────────────────────────────────────────────────────

    def reset(self) -> Dict[str, Any]:
        """Reset the environment. Returns initial state dict."""
        self._step_count = 0
        self._done = False
        self._state = dict(INITIAL_STATE)
        return self._obs()

    def step(self, action: str) -> Dict[str, Any]:
        """
        Execute an action.

        Returns EXACT format:
            {"state": dict, "reward": float, "done": bool, "info": dict}
        """
        if self._done:
            return {"state": self._obs(), "reward": 0.0, "done": True,
                    "info": {"message": "Episode terminated. Call reset()."}}

        valid = [a.value for a in ActionType]
        if action not in valid:
            return {"state": self._obs(), "reward": -0.1, "done": False,
                    "info": {"error": f"Invalid action. Valid: {valid}"}}

        # 0. Custom logic for gamble
        if action == "gamble":
            bet = self._state["money"] * 0.15 + 500  # Bet dynamically
            if self._state["money"] >= bet:
                if self.rng.random() > 0.5:
                    self._state["money"] += bet * 2
                    self._state["happiness"] += 20
                else:
                    self._state["money"] -= bet
                    self._state["happiness"] -= 20

        # 1. Apply action effects with personality modifier
        effects = ACTION_EFFECTS[action]
        mult = self.personality_mod["action_multiplier"]
        sf = self.personality_mod["stress_factor"]
        for k, delta in effects.items():
            factor = sf if k == "stress" else mult
            self._state[k] = self._state[k] + delta * factor

        # 2. Time progression
        self._step_count += 1
        self._state["age"] += 0.5
        age = self._state["age"]
        # Long-term health decay after 40
        if age > 40:
            self._state["health"] -= 0.3 * ((age - 40) / 60)
        # Long-term stress accumulation after 30
        if age > 30:
            self._state["stress"] += 0.2 * ((age - 30) / 70)

        # 3. Dynamic events
        event_name = None
        if self.task_config.events_enabled:
            self._state, event_name = maybe_trigger_event(
                self._state, self.task_config.event_probability, self.rng
            )

        # 4. Clamp all values
        self._state = clamp_state(self._state)

        # 5. Termination check
        done = False
        reason = None
        if self._state["health"] <= 0:
            done, reason = True, "health_depleted"
        elif self._state["stress"] >= 100:
            done, reason = True, "stress_overload"
        elif self._state["age"] >= 100:
            done, reason = True, "natural_end"
        self._done = done

        # 6. Reward
        reward = self._reward()

        # 7. Info
        info: Dict[str, Any] = {
            "step": self._step_count,
            "task": self.task_name,
            "personality": self.personality,
            "full_state": self._state.copy()
        }
        if event_name:
            info["event"] = event_name
            info["event_description"] = EVENTS[event_name]["description"]
        if reason:
            info["termination_reason"] = reason

        return {"state": self._obs(), "reward": reward, "done": done, "info": info}

    def state(self) -> Dict[str, Any]:
        """Return current state dict."""
        return self._obs()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _obs(self) -> Dict[str, float]:
        """Return exactly the observation space keys."""
        obs_keys = ["health", "money", "stress", "career", "relationships"]
        return {k: round(float(self._state[k]), 2) for k in obs_keys}

    def _reward(self) -> float:
        """
        Calculate normalized reward in [-1, +1].

        Positive contributions: health, career, relationships, happiness
        Negative contribution:  stress
        Balance bonus:          penalizes extreme values
        Personality bias:       added from personality modifier
        """
        s = self._state
        h = s["health"] / 100.0
        c = s["career"] / 100.0
        r = s["relationships"] / 100.0
        hp = s["happiness"] / 100.0
        st = s["stress"] / 100.0

        # Weighted positive / negative
        positive = 0.30 * h + 0.20 * c + 0.20 * r + 0.15 * hp
        negative = 0.25 * st
        raw = positive - negative  # range ~ [-0.25, 0.85]

        # Balance bonus: low variance among key metrics → bonus
        vals = [h, c, r, hp]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        bonus = 0.10 * (1.0 - min(var / 0.25, 1.0))

        reward = raw + bonus + self.personality_mod.get("reward_bias", 0.0)
        # Map to [-1, 1]
        reward = (reward - 0.35) / 0.35
        reward = max(-1.0, min(1.0, float(reward)))
        # NaN guard
        if reward != reward:
            reward = 0.0
        return round(reward, 4)
