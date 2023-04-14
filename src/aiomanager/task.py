from __future__ import annotations

import typing as t
from enum import Enum
from time import time
from types import TracebackType

import anyio
from anyio.abc import TaskGroup as AnyIOTaskGroup
from anyio.abc import TaskStatus as AnyIOTaskStatus

from aiomanager.deadline import check_deadline

from .results import NOTHING, Option, Result, Some

T = t.TypeVar("T")  # Success type
E = t.TypeVar("E")  # Error type

if t.TYPE_CHECKING:
    from .manager import TaskManager


class TaskStatus(str, Enum):
    """Enumeration of task status."""

    CREATED = "CREATED"
    """Task has not been started yet."""

    STARTING = "STARTING"
    """Task is starting."""

    PENDING = "PENDING"
    """Task has been started and is pending."""

    CANCELLED = "CANCELLED"
    """Task is finished due to cancellation."""

    SUCCESS = "SUCCESS"
    """Task returned Ok (function exit without exception)."""

    FAILURE = "FAILURE"
    """Task returned Err (function exited without exception)."""

    TIMEOUT = "TIMEOUT"
    """Task has been cancelled due to timeout."""

    EXCEPTION = "EXCEPTION"
    """Task raised an exception."""


class Task(t.Generic[T, E]):
    """Task interface."""

    def __init__(
        self,
        func: t.Callable[[], t.Coroutine[t.Any, t.Any, Result[T, E]]],
        manager: TaskManager | None = None,
        *,
        name: Option[str] = NOTHING,
        deadline: Option[float] = NOTHING,
    ) -> None:
        self._name = name
        self._func = func
        self._deadline = deadline
        self._status = TaskStatus.CREATED
        self._result: Option[Result[T, E]] = NOTHING
        self._exception: Option[BaseException] = NOTHING
        self._shutdown_event: Option[anyio.Event] = NOTHING
        self._anyio_task_group: Option[AnyIOTaskGroup] = NOTHING
        self._ephemeral_task_manager: Option[TaskManager] = NOTHING
        self._parent_task_manager: Option[TaskManager] = (
            Some(manager) if manager else NOTHING
        )

    @property
    def name(self) -> Option[str]:
        return self._name

    @property
    def func(self) -> t.Callable[[], t.Coroutine[t.Any, t.Any, Result[T, E]]]:
        return self._func

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def deadline(self) -> Option[float]:
        return self._deadline

    def done(self) -> bool:
        """Return True when task is finished, due to either success, failure or cancellation."""
        return self.status in (
            TaskStatus.FAILURE,
            TaskStatus.SUCCESS,
            TaskStatus.CANCELLED,
            TaskStatus.EXCEPTION,
            TaskStatus.TIMEOUT,
        )

    def cancelled(self) -> bool:
        """Return `True` if task is cancelled else `False`."""
        return self.status in (TaskStatus.TIMEOUT, TaskStatus.CANCELLED)

    def ok(self) -> Option[T]:
        return self._result.and_then(lambda result: result.ok())

    def err(self) -> Option[E]:
        return self._result.and_then(lambda result: result.err())

    def exception(self) -> Option[BaseException]:
        """Return exception raised within task if any."""
        return self._exception

    def result(self) -> Option[Result[T, E]]:
        """Return a result if task is finished, or raise an error if task is pending or cancelled."""
        return self._result

    def unwrap_result(self) -> Result[T, E]:
        return self._result.unwrap()

    def unwrap_ok(self) -> T:
        return self._result.unwrap().unwrap()

    def unwrap_err(self) -> E:
        return self._result.unwrap().unwrap_err()

    def unwrap_exception(self) -> BaseException:
        return self._exception.unwrap()

    def cancel(self) -> Option[TaskStatus]:
        """Cancel task or return task status if task is already finished."""
        if self.status == TaskStatus.CREATED:
            self._status = TaskStatus.CANCELLED
            return Some(self.status)
        if self.status in (
            TaskStatus.FAILURE,
            TaskStatus.SUCCESS,
            TaskStatus.CANCELLED,
            TaskStatus.EXCEPTION,
            TaskStatus.TIMEOUT,
        ):
            return Some(self.status)
        self._anyio_task_group.inspect(lambda tg: tg.cancel_scope.cancel())
        return NOTHING

    async def wait(self) -> TaskStatus:
        """Wait until task is finished and return task status.

        Returns:
            The task status
        """
        if self.done():
            return self._status
        if not self._shutdown_event:
            raise RuntimeError("Task is not started")
        with anyio.CancelScope(shield=True):
            await self._shutdown_event.value.wait()
        return self._status

    async def kill(self) -> TaskStatus:
        """Cancel task and wait until it is finished."""
        if self.status == TaskStatus.CREATED:
            raise RuntimeError("Task is not started yet")
        if status := self.cancel():
            return status.unwrap()
        return await self.wait()

    async def join(
        self,
        exc_type: t.Type[BaseException] | None = None,
        exc: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> TaskStatus:
        if self._ephemeral_task_manager:
            await self._ephemeral_task_manager.value.__aexit__(
                exc_type=exc_type, exc=exc, traceback=traceback
            )
        return await self.wait()

    async def __task__(
        self, task_status: AnyIOTaskStatus = anyio.TASK_STATUS_IGNORED
    ) -> None:
        with anyio.move_on_after(
            delay=self.deadline.unwrap_or(float("inf")) - time()
        ) as cancel_scope:
            task_status.started()
            try:
                result = await self._func()
                self._result = Some(result)
                if result:
                    self._status = TaskStatus.SUCCESS
                    return
                else:
                    self._status = TaskStatus.FAILURE
            # Raise back cancelled errors
            except anyio.get_cancelled_exc_class():
                if check_deadline(self.deadline).err():
                    self._status = TaskStatus.TIMEOUT
                else:
                    self._status = TaskStatus.CANCELLED
                raise
            # Silence exceptions
            except Exception as exc:
                self._status = TaskStatus.EXCEPTION
                self._exception = Some(exc)
                # Do not consider cancel scope
                return
            # Raise back base exceptions
            except BaseException as exc:
                self._status = TaskStatus.EXCEPTION
                self._exception = Some(exc)
                raise
            # Always set shutdown event
            finally:
                self._shutdown_event.inspect(
                    lambda event: event.set() if not event.is_set() else None
                )
                # Cancel parent task manager if not success
                if self._status != TaskStatus.SUCCESS:
                    self._parent_task_manager.inspect(lambda manager: manager.cancel())
        if cancel_scope.cancel_called:
            self._status = TaskStatus.TIMEOUT
            self._parent_task_manager.inspect(lambda manager: manager.cancel())

    async def __call__(
        self, task_status: AnyIOTaskStatus = anyio.TASK_STATUS_IGNORED
    ) -> None:
        """Run task"""
        self._status = TaskStatus.STARTING
        # Create task group
        async with anyio.create_task_group() as task_group:
            # Start task
            try:
                event = anyio.Event()
                self._shutdown_event = Some(event)
                self._anyio_task_group = Some(task_group)
                await task_group.start(self.__task__)
                task_status.started()
            except BaseException as exc:
                self._exception = Some(exc)
                self._status = TaskStatus.EXCEPTION
                if not event.is_set():
                    event.set()
                raise
            # SAFETY CHECK: If some event loop implementation can encounter failure in task before running code below
            if self.status == TaskStatus.STARTING:
                # Set pending status
                self._status = TaskStatus.PENDING

    async def __aenter__(self) -> Task[T, E]:
        if self.status == TaskStatus.CREATED:
            raise RuntimeError("Task is not started yet")
        return self

    async def __aexit__(
        self,
        exc_type: t.Type[BaseException] | None = None,
        exc: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        if exc_type is not None:
            self.cancel()
        await self.join()
