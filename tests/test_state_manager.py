"""Basic executable checks for the RSTM state manager."""

import math
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rstm.state_manager import RSTMStateManager


def assert_close(actual: float, expected: float, tol: float = 1e-6):
    if abs(actual - expected) > tol:
        raise AssertionError(f"expected {expected}, got {actual}")


def test_delta_limit():
    manager = RSTMStateManager()
    result = manager.update_state(5)
    assert_close(result["target_state"], math.tanh(0.5))
    assert_close(result["state"], manager.DELTA)


def test_explicit_initial_state():
    manager = RSTMStateManager(initial_state=-0.25)
    assert_close(manager.get_current_cci(), 0.0)
    assert_close(manager.get_current_state(), -0.25)

    result = manager.update_state(2)
    assert_close(result["target_state"], math.tanh(0.2))
    assert_close(result["state"], -0.05)


def test_finite_window():
    manager = RSTMStateManager()
    sequence = [1, 1, 1, 1, 1, 1]
    for score in sequence:
        manager.update_state(score)

    expected_cci = sum((manager.LAMBDA ** i) * 1 for i in range(manager.K))
    assert_close(manager.get_current_cci(), expected_cci)


def test_signed_sequence_trajectory():
    manager = RSTMStateManager()
    sequence = [3, 3, -3, -3]
    expected_states = [0.2, 0.4, 0.2, 0.0]

    actual_states = []
    for score in sequence:
        result = manager.update_state(score)
        actual_states.append(round(result["state"], 6))

    for actual, expected in zip(actual_states, expected_states):
        assert_close(actual, expected)


def main():
    tests = [
        ("delta limit", test_delta_limit),
        ("finite window", test_finite_window),
        ("signed sequence trajectory", test_signed_sequence_trajectory),
    ]

    print("=" * 60)
    print("RSTM state manager checks")
    print("=" * 60)

    for name, fn in tests:
        fn()
        print(f"[OK] {name}")

    print("=" * 60)
    print("All checks passed")
    print("=" * 60)


if __name__ == "__main__":
    main()
