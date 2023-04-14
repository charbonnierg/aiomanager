from __future__ import annotations

from time import time

from .results import NOTHING, Err, Ok, Option, Result, Some


def check_deadline(deadline: Option[float]) -> Result[float, float]:
    if not deadline:
        return Ok(float("inf"))
    value = deadline.unwrap()
    if value - time() < 0:
        return Err(value)
    return Ok(value)


def get_deadline(
    *, timeout: float | None = None, deadline: float | None = None
) -> Option[float]:
    """Get some deadline"""
    if timeout:
        return Some(time() + timeout)
    if deadline:
        return Some(deadline)
    return NOTHING


def get_timeout(deadline: float) -> Result[float, TimeoutError]:
    """Get timeout"""
    value = time() - deadline
    if value < 0:
        return Err(TimeoutError("timeout is expired"))
    return Ok(value)
