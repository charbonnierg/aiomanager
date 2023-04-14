from __future__ import annotations

import asyncio
import functools
import inspect
import time
import typing as t
from functools import partial

import anyio
from typing_extensions import ParamSpec

from .results import NOTHING, Err, Ok, Option, Result, Some

T = t.TypeVar("T")  # Success type
P = ParamSpec("P")
TE = t.TypeVar("TE", bound=BaseException)


@t.overload
def sleep_blocking(
    duration: float | None,
) -> None:
    ...


@t.overload
def sleep_blocking(duration: float, result: T, *, error: None = None) -> T:
    ...


@t.overload
def sleep_blocking(
    duration: float, result: t.Any = None, *, error: t.Type[BaseException]
) -> t.NoReturn:
    ...


def sleep_blocking(
    duration: float | None,
    result: t.Any = None,
    *,
    error: t.Type[BaseException] | None = None,
) -> t.Any:
    time.sleep(duration or float("inf"))
    if error:
        raise error
    return result


@t.overload
async def sleep(
    duration: float | None,
) -> None:
    ...


@t.overload
async def sleep(duration: float, result: T, *, error: None = None) -> T:
    ...


@t.overload
async def sleep(
    duration: float, result: t.Any = None, *, error: t.Type[BaseException]
) -> t.NoReturn:
    ...


async def sleep(
    duration: float | None,
    result: t.Any = None,
    *,
    error: t.Type[BaseException] | None = None,
) -> t.Any:
    await anyio.sleep(duration or float("inf"))
    if error:
        raise error
    return result


def final(
    func: t.Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> t.Callable[[], T]:
    """Set function arguments and return a static function."""
    return partial(func, *args, **kwargs)


def do(generator: t.Iterator[T]) -> Option[T]:
    try:
        return Some(next(generator))
    except StopIteration:
        return NOTHING
    except StopAsyncIteration:
        return NOTHING


async def do_async(generator: t.AsyncIterator[T] | t.Iterator[T]) -> Option[T]:
    try:
        if isinstance(generator, t.AsyncIterator):
            return Some(await generator.__anext__())
        else:
            return Some(next(generator))
    except StopIteration:
        return NOTHING
    except StopAsyncIteration:
        return NOTHING


@t.overload
def as_result(
    func: t.Callable[P, T],
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
) -> t.Callable[P, Result[T, TE]]:
    ...


@t.overload
def as_result(
    func: t.Callable[P, T],
) -> t.Callable[P, Result[T, Exception]]:
    ...


@t.overload
def as_result() -> t.Callable[[t.Callable[P, T]], t.Callable[P, Result[T, Exception]]]:
    ...


@t.overload
def as_result(
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, Result[T, TE]]]:
    ...


def as_result(
    func: t.Callable[..., t.Any] | None = None,
    *,
    catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] = Exception,
) -> t.Any:
    """
    Make a decorator to turn a function into one that returns a ``Result``.

    Regular return values are turned into ``Ok(return_value)``. Raised
    exceptions of the specified exception type(s) are turned into ``Err(exc)``.
    """
    if func and asyncio.iscoroutinefunction(func):
        raise TypeError(
            "as_result requires a synchronous function. Use as_result_async with a coroutine function instead"
        )
    if not isinstance(catch, tuple):
        catch = (catch,)
    if not catch or not all(
        inspect.isclass(exception) and issubclass(exception, Exception)
        for exception in catch
    ):
        raise TypeError("as_result() requires one or more exception types")

    def decorator(f: t.Callable[P, T]) -> t.Callable[P, Result[T, TE]]:
        """
        Decorator to turn a function into one that returns a ``Result``.
        """

        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T, TE]:
            try:
                return Ok(f(*args, **kwargs))
            except catch as exc:
                return Err(exc)

        return wrapper

    if func:
        return decorator(func)
    else:
        return decorator


@t.overload
def as_result_async(
    func: t.Callable[P, t.Coroutine[t.Any, t.Any, T]],
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
) -> t.Callable[P, t.Coroutine[t.Any, t.Any, Result[T, TE]]]:
    ...


@t.overload
def as_result_async(
    func: t.Callable[P, t.Coroutine[t.Any, t.Any, T]],
) -> t.Callable[P, t.Coroutine[t.Any, t.Any, Result[T, Exception]]]:
    ...


@t.overload
def as_result_async() -> (
    t.Callable[
        [t.Callable[P, T]],
        t.Callable[P, t.Coroutine[t.Any, t.Any, Result[T, Exception]]],
    ]
):
    ...


@t.overload
def as_result_async(
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
) -> t.Callable[
    [t.Callable[P, t.Coroutine[t.Any, t.Any, T]]],
    t.Callable[P, t.Coroutine[t.Any, t.Any, Result[T, TE]]],
]:
    ...


def as_result_async(
    func: t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]] | None = None,
    *,
    catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] = Exception,
) -> t.Any:
    """
    Make a decorator to turn a function into one that returns a ``Result``.

    Regular return values are turned into ``Ok(return_value)``. Raised
    exceptions of the specified exception type(s) are turned into ``Err(exc)``.
    """
    if func and not asyncio.iscoroutinefunction(func):
        raise TypeError("as_async_result requires a coroutine function")

    if not isinstance(catch, tuple):
        catch = (catch,)
    if not catch or not all(
        inspect.isclass(exception) and issubclass(exception, Exception)
        for exception in catch
    ):
        raise TypeError("as_async_result() requires one or more exception types")

    def decorator(
        f: t.Callable[P, t.Coroutine[t.Any, t.Any, T]]
    ) -> t.Callable[P, t.Coroutine[t.Any, t.Any, Result[T, TE]]]:
        """
        Decorator to turn a function into one that returns a ``Result``.
        """

        @functools.wraps(f)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T, TE]:
            try:
                return Ok(await f(*args, **kwargs))
            except catch as exc:
                return Err(exc)

        return wrapper

    if func:
        return decorator(func)
    else:
        return decorator
