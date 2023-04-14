from aiomanager.deadline import (
    create_deadline,
    deadline_is_expired,
    deadline_to_timeout,
)
from aiomanager.results import Nothing, Some


class TestCreateDeadline:
    def test_create_default_deadline(self) -> None:
        assert create_deadline() is Nothing()
        assert create_deadline(deadline=None, timeout=None) is Nothing()

    def test_create_deadline_from_deadline(self) -> None:
        assert create_deadline(deadline=1) == Some(1)

    def test_create_deadline_minimum_from_deadline_and_timeout(self) -> None:
        assert create_deadline(deadline=10, timeout=30, clock=lambda: 0) == Some(10)
        assert create_deadline(deadline=30, timeout=10, clock=lambda: 0) == Some(10)

    def test_create_deadline_from_timeout(self) -> None:
        assert create_deadline(timeout=1, clock=lambda: 0) == Some(1)


def test_deadline_is_expired() -> None:
    assert deadline_is_expired(0, lambda: 1) is True
    assert deadline_is_expired(1, lambda: 1) is True
    assert deadline_is_expired(1, lambda: 0) is False


def test_deadline_to_timeout() -> None:
    assert deadline_to_timeout(1, lambda: 0) == 1
    assert deadline_to_timeout(30, lambda: 10) == 20
