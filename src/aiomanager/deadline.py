from __future__ import annotations

import typing as t
from time import time

from .results import NOTHING, Option, Some


def create_deadline(
    *,
    timeout: float | None = None,
    deadline: float | None = None,
    clock: t.Callable[[], float] = time,
) -> Option[float]:
    """Create some deadline option.

    Arguments:
        timeout: either None or a duration is seconds.
        deadline: either None or a clock time as unix timestamp.
        clock: a callable which returns unix timestamp.

    Returns:
        Either `Nothing()` or the `Some(deadline)`  where `deadline` is the minimum of the deadline derived from `timeout` argument
        and the deadline provided as `deadline` argument.
    """
    if deadline and timeout:
        deadline_from_timeout = clock() + timeout
        return Some(min(deadline_from_timeout, deadline))
    if deadline:
        return Some(deadline)
    if timeout:
        return Some(clock() + timeout)
    return NOTHING


def deadline_is_expired(
    deadline: float,
    clock: t.Callable[[], float] = time,
) -> bool:
    """Check if clock time is greater than deadline.

    Arguments:
        deadline: either None or a clock time as unix timestamp.
        clock: a callable which returns current clock time as unix timestamp.

    Returns:
        `True` if deadline is expired else `False`.
    """
    if deadline - clock() <= 0:
        return True
    return False


def deadline_to_timeout(
    deadline: float,
    clock: t.Callable[[], float] = time,
) -> float:
    """Convert a deadline into a timeout value.

    Arguments:
        deadline: A clock time as a unix timestamp.
        clock: a callable which returns current clock time as a unix timestamp.

    Returns:
        A duration is seconds
    """
    return deadline - clock()
