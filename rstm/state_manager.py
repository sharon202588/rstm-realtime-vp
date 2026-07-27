"""
RSTM state manager.

Implements the paper-aligned control logic:
- Finite-horizon weighted CPAS aggregation for CCI
- tanh mapping from CCI to target state S*(t)
- Delta-limited state update from S(t-1) to S(t)
- Optional state persistence
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, Optional


class RSTMStateManager:
    """Manage the relational state trajectory for the virtual patient.

    Paper-aligned update rules:
    - CCI_t = sum[i=0..K-1](lambda^i * CPAS_(t-i))
    - S*(t) = tanh(c * CCI_t)
    - S(t) = S(t-1) + clip(S*(t) - S(t-1), -DELTA, +DELTA)
    """

    LAMBDA = 0.8
    C = 0.10
    K = 5
    DELTA = 0.20

    def __init__(
        self,
        initial_cci: float = 0.0,
        initial_state: Optional[float] = None,
        state_file: Optional[str] = None,
    ):
        self.cci = float(initial_cci)
        self.initial_cci = float(initial_cci)
        self.initial_state = self._clamp_state(initial_state) if initial_state is not None else None
        self.state = self.initial_state if self.initial_state is not None else math.tanh(self.C * self.cci)
        self.state_file = state_file
        self.turn_count = 0
        self.recent_cpas: list[float] = []
        self.history: list[dict[str, Any]] = []

        if state_file:
            self.load_state()

    @staticmethod
    def _clamp_state(state: float) -> float:
        return max(-1.0, min(1.0, float(state)))

    def update_state(self, cpas_score: float) -> Dict[str, float]:
        cpas_score = float(cpas_score)

        previous_cci = self.cci
        previous_state = self.state

        self.recent_cpas.append(cpas_score)
        if len(self.recent_cpas) > self.K:
            self.recent_cpas = self.recent_cpas[-self.K :]

        weighted_sum = 0.0
        for i, score in enumerate(reversed(self.recent_cpas)):
            weighted_sum += (self.LAMBDA ** i) * score
        self.cci = weighted_sum

        target_state = math.tanh(self.C * self.cci)
        target_state = max(-1.0, min(1.0, target_state))

        delta_raw = target_state - previous_state
        delta_applied = max(-self.DELTA, min(self.DELTA, delta_raw))
        self.state = previous_state + delta_applied
        self.state = max(-1.0, min(1.0, self.state))

        self.turn_count += 1

        history_entry = {
            "turn": self.turn_count,
            "cpas_score": cpas_score,
            "cci_before": previous_cci,
            "cci_after": self.cci,
            "state_before": previous_state,
            "target_state": target_state,
            "delta_raw": delta_raw,
            "delta_applied": delta_applied,
            "state_after": self.state,
            "lambda": self.LAMBDA,
            "c": self.C,
            "k": self.K,
            "delta_max": self.DELTA,
        }
        self.history.append(history_entry)

        if self.state_file:
            self.save_state()

        return {
            "cci": self.cci,
            "state": self.state,
            "target_state": target_state,
            "turn": self.turn_count,
        }

    def get_current_state(self) -> float:
        return self.state

    def get_current_cci(self) -> float:
        return self.cci

    def reset(self, initial_cci: Optional[float] = None, initial_state: Optional[float] = None):
        if initial_cci is not None:
            self.initial_cci = float(initial_cci)
        if initial_state is not None:
            self.initial_state = self._clamp_state(initial_state)

        self.cci = self.initial_cci
        self.state = self.initial_state if self.initial_state is not None else math.tanh(self.C * self.cci)
        self.turn_count = 0
        self.recent_cpas.clear()
        self.history.clear()

        if self.state_file:
            self.save_state()

    def save_state(self):
        if not self.state_file:
            return

        state_data = {
            "cci": self.cci,
            "current_state": self.state,
            "initial_cci": self.initial_cci,
            "initial_state": self.initial_state,
            "turn_count": self.turn_count,
            "lambda": self.LAMBDA,
            "c": self.C,
            "k": self.K,
            "delta_max": self.DELTA,
            "recent_cpas": self.recent_cpas,
            "history": self.history[-10:],
        }

        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"Warning: Failed to save state: {exc}")

    def load_state(self):
        if not self.state_file:
            return

        state_path = Path(self.state_file)
        if not state_path.exists():
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            self.cci = float(state_data.get("cci", 0.0))
            self.initial_cci = float(state_data.get("initial_cci", self.initial_cci))
            stored_initial_state = state_data.get("initial_state", self.initial_state)
            self.initial_state = (
                self._clamp_state(stored_initial_state)
                if isinstance(stored_initial_state, (int, float))
                else None
            )
            self.state = float(state_data.get("current_state", math.tanh(self.C * self.cci)))
            self.turn_count = int(state_data.get("turn_count", 0))
            self.history = state_data.get("history", [])
            self.recent_cpas = [
                float(score) for score in state_data.get("recent_cpas", []) if isinstance(score, (int, float))
            ]

            if not self.recent_cpas and self.history:
                recovered = [
                    float(entry.get("cpas_score"))
                    for entry in self.history
                    if isinstance(entry.get("cpas_score"), (int, float))
                ]
                self.recent_cpas = recovered[-self.K :]
        except Exception as exc:
            print(f"Warning: Failed to load state: {exc}, using defaults")

    def get_history(self, last_n: Optional[int] = None) -> list:
        if last_n is None:
            return self.history.copy()
        return self.history[-last_n:] if last_n > 0 else []

    def get_state_summary(self) -> Dict[str, Any]:
        return {
            "current_cci": self.cci,
            "current_state": self.state,
            "initial_cci": self.initial_cci,
            "initial_state": self.initial_state,
            "turn_count": self.turn_count,
            "lambda": self.LAMBDA,
            "c": self.C,
            "k": self.K,
            "delta_max": self.DELTA,
            "history_length": len(self.history),
        }
