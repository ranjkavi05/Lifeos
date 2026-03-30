"""
LifeOS Pydantic Models - Type-safe data structures.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ActionType(str, Enum):
    WORK_OVERTIME = "work_overtime"
    EXERCISE = "exercise"
    INVEST_MONEY = "invest_money"
    LEARN_SKILL = "learn_skill"
    SOCIALIZE = "socialize"
    REST = "rest"
    START_SIDE_HUSTLE = "start_side_hustle"
    TAKE_VACATION = "take_vacation"
    MEDITATE = "meditate"
    GAMBLE = "gamble"


class PersonalityType(str, Enum):
    RISK_TAKER = "risk_taker"
    CONSERVATIVE = "conservative"
    LAZY = "lazy"
    AMBITIOUS = "ambitious"


class LifeState(BaseModel):
    """Current state of the LifeOS simulation."""
    health: float = Field(default=80.0, ge=0.0, le=100.0)
    money: float = Field(default=5000.0, ge=0.0, le=100000.0)
    stress: float = Field(default=20.0, ge=0.0, le=100.0)
    career: float = Field(default=10.0, ge=0.0, le=100.0)
    relationships: float = Field(default=50.0, ge=0.0, le=100.0)

    def to_dict(self) -> Dict[str, float]:
        return {k: round(v, 2) for k, v in {
            "health": self.health, "money": self.money, 
            "stress": self.stress, "career": self.career, 
            "relationships": self.relationships
        }.items()}


class ActionRequest(BaseModel):
    action: str
    task: Optional[str] = None
    personality: Optional[str] = None


class ResetRequest(BaseModel):
    task: Optional[str] = None
    personality: Optional[str] = None
    seed: Optional[int] = None


class StepResponse(BaseModel):
    """Response from step() - OpenEnv spec format."""
    state: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]


class TaskConfig(BaseModel):
    name: str
    events_enabled: bool = True
    event_probability: float = 0.1
    description: str = ""
