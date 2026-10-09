"""Deterministic state machine for the eight-question interview flow."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewSessionState:
    """Describe the phase and progress for a one-based interview turn."""

    turn_num: int

    @property
    def phase(self) -> str:
        if self.turn_num <= 2:
            return "introduction"
        if self.turn_num <= 6:
            return "technical"
        return "hr_behavioral"

    @property
    def is_complete(self) -> bool:
        return self.turn_num > 8

    @property
    def category_label(self) -> str:
        return {
            "introduction": "Phase 1 - Introduction",
            "technical": "Phase 2 - Technical",
            "hr_behavioral": "Phase 3 - HR/Behavioral",
        }[self.phase]