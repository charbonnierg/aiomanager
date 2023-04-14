from __future__ import annotations

import typing as t
from contextlib import AsyncExitStack
from types import TracebackType

import anyio
import anyio.to_process
import anyio.to_thread
from anyio.abc import TaskGroup as AnyIOTaskGroup

from .deadline import create_deadline, deadline_is_expired
from .func import as_result, as_result_async, final
from .results import NOTHING, Option, Result, Some
from .task import Task, TaskStatus

T = t.TypeVar("T")  # Success type
E = t.TypeVar("E")  # Error type
TE = t.TypeVar("TE", bound=BaseException)


class TaskManager:
    """Task manager interface."""

    def __init__(self, concurrent_limit: int | None = None) -> None:
        self._concurrent_limit = concurrent_limit
        self._closed = False
        self._anyio_task_group: Option[AnyIOTaskGroup] = NOTHING
        self._stack: Option[AsyncExitStack] = NOTHING
        self._shutdown_event: Option[anyio.Event] = NOTHING

    @property
    def concurrent_limit(self) -> int | None:
        """Get maximum number of tasks which can be submitted before pending tasks finish."""
        return self._concurrent_limit

    def closed(self) -> bool:
        """Return `True` if task manager is exited or cancelled, else `False`."""
        return self._closed

    def cancelled(self) -> bool:
        """Return `True` if task manager is cancelled else `False`."""
        return self._anyio_task_group.map(
            lambda tg: tg.cancel_scope.cancel_called
        ).unwrap_or(False)

    def cancel(self) -> None:
        """Cancel task manager."""
        if self._anyio_task_group.is_some_and(
            lambda tg: not tg.cancel_scope.cancel_called
        ):
            self._anyio_task_group.inspect(lambda tg: tg.cancel_scope.cancel())

    async def open(self) -> None:
        stack = AsyncExitStack()
        shutdown_event = anyio.Event()
        await stack.__aenter__()
        stack.callback(shutdown_event.set)
        self._stack = Some(stack)
        self._shutdown_event = Some(shutdown_event)
        self._anyio_task_group = Some(
            await stack.enter_async_context(anyio.create_task_group())
        )

    async def close(
        self,
        exc_type: t.Type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ) -> None:
        if self._stack:
            await self._stack.value.__aexit__(exc_type, exc, tb)

    async def wait(self) -> None:
        """Wait until task manager is closed."""
        if not self._shutdown_event:
            return
        with anyio.open_cancel_scope(shield=True):
            await self._shutdown_event.value.wait()

    async def kill(self) -> None:
        """Cancel task manager and wait until it is closed."""
        self.cancel()
        return await self.wait()

    async def __aenter__(self) -> TaskManager:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: t.Type[BaseException] | None = None,
        exc: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        if exc_type is not None:
            self.cancel()
        await self.close()

    def open_resource(self, resource: t.ContextManager[T]) -> T:
        if not self._stack:
            raise RuntimeError("Task manager is not started yet")
        if self.closed():
            raise RuntimeError("Task manager is closed")
        return self._stack.value.enter_context(resource)

    async def open_async_resource(self, resource: t.AsyncContextManager[T]) -> T:
        if not self._stack:
            raise RuntimeError("Task manager is not started yet")
        if self.closed():
            raise RuntimeError("Task manager is closed")
        return await self._stack.value.enter_async_context(resource)

    @t.overload
    def submit_task(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, Result[T, E]]],
        *,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[T, E]:
        ...

    @t.overload
    def submit_task(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, T]],
        *,
        catch: tuple[t.Type[TE], ...] | t.Type[TE],
        timeout: float | None = None,
        deadline: float | None = None,
        name: str | None = None,
    ) -> Task[T, TE]:
        ...

    def submit_task(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, t.Any]],
        *,
        catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[t.Any, t.Any]:
        if not self._anyio_task_group:
            raise RuntimeError("Task manager is not started yet")
        if self.closed():
            raise RuntimeError("Task manager is closed")
        deadline_option = create_deadline(deadline=deadline, timeout=timeout)
        name_option: Option[str] = Some(name) if name else NOTHING
        if catch:
            func = as_result_async(func, catch=catch)
        task = Task[t.Any, t.Any](
            func, manager=self, deadline=deadline_option, name=name_option
        )
        if deadline_option.is_some_and(deadline_is_expired):
            self.cancel()
            task._status = TaskStatus.TIMEOUT
            return task
        self._anyio_task_group.value.start_soon(task, name=name)
        return task

    @t.overload
    def submit_task_in_thread(
        self,
        func: t.Callable[[], Result[T, E]],
        *,
        name: str | None = None,
    ) -> Task[T, E]:
        ...

    @t.overload
    def submit_task_in_thread(
        self,
        func: t.Callable[[], T],
        *,
        catch: tuple[t.Type[TE], ...] | t.Type[TE],
        name: str | None = None,
    ) -> Task[T, TE]:
        ...

    def submit_task_in_thread(
        self,
        func: t.Callable[[], t.Any],
        *,
        catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
        name: str | None = None,
    ) -> Task[t.Any, t.Any]:
        if catch:
            func = as_result(func, catch=catch)
        return self.submit_task(final(anyio.to_thread.run_sync, func), name=name)  # type: ignore[arg-type]

    @t.overload
    def submit_task_in_process(
        self,
        func: t.Callable[[], Result[T, E]],
        *,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[T, E]:
        ...

    @t.overload
    def submit_task_in_process(
        self,
        func: t.Callable[[], T],
        *,
        catch: tuple[t.Type[TE], ...] | t.Type[TE],
        timeout: float | None = None,
        deadline: float | None = None,
        name: str | None = None,
    ) -> Task[T, TE]:
        ...

    def submit_task_in_process(
        self,
        func: t.Callable[[], t.Any],
        *,
        catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[t.Any, t.Any]:
        if catch:
            func = as_result(func, catch=catch)
        return self.submit_task(
            final(
                anyio.to_process.run_sync,  # type: ignore[arg-type]
                func,
            ),
            deadline=deadline,
            timeout=timeout,
            name=name,
        )

    @t.overload
    async def start_task(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, Result[T, E]]],
        *,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[T, E]:
        ...

    @t.overload
    async def start_task(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, T]],
        *,
        catch: tuple[t.Type[TE], ...] | t.Type[TE],
        timeout: float | None = None,
        deadline: float | None = None,
        name: str | None = None,
    ) -> Task[T, TE]:
        ...

    async def start_task(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, t.Any]],
        *,
        catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[t.Any, t.Any]:
        if not self._anyio_task_group:
            raise RuntimeError("Task manager is not started yet")
        if self.closed():
            raise RuntimeError("Task manager is closed")
        deadline_option = create_deadline(deadline=deadline, timeout=timeout)
        name_option: Option[str] = Some(name) if name else NOTHING
        if catch:
            func = as_result_async(func, catch=catch)
        task = Task[t.Any, t.Any](
            func, manager=self, deadline=deadline_option, name=name_option
        )
        if deadline_option.is_some_and(deadline_is_expired):
            self.cancel()
            task._status = TaskStatus.TIMEOUT
            return task
        await self._anyio_task_group.value.start(task, name=name)
        return task

    @t.overload
    async def start_task_in_thread(
        self,
        func: t.Callable[[], Result[T, E]],
        *,
        name: str | None = None,
    ) -> Task[T, E]:
        ...

    @t.overload
    async def start_task_in_thread(
        self,
        func: t.Callable[[], T],
        *,
        catch: tuple[t.Type[TE], ...] | t.Type[TE],
        name: str | None = None,
    ) -> Task[T, TE]:
        ...

    async def start_task_in_thread(
        self,
        func: t.Callable[[], t.Any],
        *,
        catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
        name: str | None = None,
    ) -> Task[t.Any, t.Any]:
        if catch:
            func = as_result(func, catch=catch)
        return await self.start_task(
            final(
                anyio.to_thread.run_sync,  # type: ignore[arg-type]
                func,
            ),
            name=name,
        )

    @t.overload
    async def start_task_in_process(
        self,
        func: t.Callable[[], Result[T, E]],
        *,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[T, E]:
        ...

    @t.overload
    async def start_task_in_process(
        self,
        func: t.Callable[[], T],
        *,
        catch: tuple[t.Type[TE], ...] | t.Type[TE],
        timeout: float | None = None,
        deadline: float | None = None,
        name: str | None = None,
    ) -> Task[T, TE]:
        ...

    async def start_task_in_process(
        self,
        func: t.Callable[[], t.Any],
        *,
        catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
        deadline: float | None = None,
        timeout: float | None = None,
        name: str | None = None,
    ) -> Task[t.Any, t.Any]:
        if catch:
            func = as_result(func, catch=catch)
        return await self.start_task(
            final(
                anyio.to_process.run_sync,  # type: ignore[arg-type]
                func,
            ),
            deadline=deadline,
            timeout=timeout,
            name=name,
        )
