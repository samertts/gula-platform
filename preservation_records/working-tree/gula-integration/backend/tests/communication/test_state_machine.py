"""Unit tests: delivery state machine transitions."""

from __future__ import annotations

import pytest

from shared.communication.state import DeliveryState, DeliveryStateMachine


class TestTransitions:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (DeliveryState.CREATED, DeliveryState.QUEUED),
            (DeliveryState.CREATED, DeliveryState.SENDING),
            (DeliveryState.CREATED, DeliveryState.FAILED),
            (DeliveryState.QUEUED, DeliveryState.SENDING),
            (DeliveryState.QUEUED, DeliveryState.FAILED),
            (DeliveryState.QUEUED, DeliveryState.ARCHIVED),
            (DeliveryState.SENDING, DeliveryState.DELIVERED),
            (DeliveryState.SENDING, DeliveryState.FAILED),
            (DeliveryState.DELIVERED, DeliveryState.READ),
            (DeliveryState.DELIVERED, DeliveryState.ARCHIVED),
            (DeliveryState.FAILED, DeliveryState.QUEUED),
            (DeliveryState.FAILED, DeliveryState.ARCHIVED),
            (DeliveryState.READ, DeliveryState.ARCHIVED),
        ],
    )
    def test_valid_transitions(self, current, target):
        assert DeliveryStateMachine.can_transition(current, target) is True
        assert DeliveryStateMachine.transition(current, target) == target

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (DeliveryState.CREATED, DeliveryState.DELIVERED),
            (DeliveryState.CREATED, DeliveryState.READ),
            (DeliveryState.SENDING, DeliveryState.CREATED),
            (DeliveryState.DELIVERED, DeliveryState.SENDING),
            (DeliveryState.DELIVERED, DeliveryState.FAILED),
            (DeliveryState.ARCHIVED, DeliveryState.DELIVERED),
            (DeliveryState.READ, DeliveryState.DELIVERED),
            (DeliveryState.FAILED, DeliveryState.DELIVERED),
        ],
    )
    def test_invalid_transitions_rejected(self, current, target):
        assert DeliveryStateMachine.can_transition(current, target) is False
        with pytest.raises(ValueError):
            DeliveryStateMachine.transition(current, target)

    def test_archived_is_terminal(self):
        assert DeliveryStateMachine.transitions_from(DeliveryState.ARCHIVED) == []

    def test_transitions_from_created(self):
        assert DeliveryStateMachine.transitions_from(DeliveryState.CREATED) == [
            "failed",
            "queued",
            "sending",
        ]
