from __future__ import annotations

import typing as t

from .manager import TaskManager
from .results import Result, Some
from .task import Task

T = t.TypeVar("T")  # Success type
E = t.TypeVar("E")  # Error type
TE = t.TypeVar("TE", bound=BaseException)


def create_task_manager() -> TaskManager:
    """Create a new task manager."""
    return TaskManager()


async def wait_for(*tasks: Task[T, E]) -> t.List[Task[T, E]]:
    async with create_task_manager() as tm:
        for task in tasks:
            tm.submit_task(task.wait, catch=())
    return list(tasks)


@t.overload
async def start_task(
    func: t.Callable[[], t.Coroutine[t.Any, t.Any, Result[T, E]]],
    *,
    timeout: float | None = None,
    deadline: float | None = None,
    name: str | None = None,
) -> Task[T, E]:
    ...


@t.overload
async def start_task(
    func: t.Callable[[], t.Coroutine[t.Any, t.Any, T]],
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
    timeout: float | None = None,
    deadline: float | None = None,
    name: str | None = None,
) -> Task[T, TE]:
    ...


async def start_task(
    func: t.Callable[[], t.Coroutine[t.Any, t.Any, t.Any]],
    *,
    catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
    deadline: float | None = None,
    timeout: float | None = None,
    name: str | None = None,
) -> Task[t.Any, t.Any]:
    """Create and start a new task from given task or task function."""
    manager = TaskManager()
    await manager.open()
    task = await manager.start_task(
        func, catch=catch, timeout=timeout, deadline=deadline, name=name  # type: ignore[arg-type]
    )
    task._ephemeral_task_manager = Some(manager)
    return task


@t.overload
async def start_task_in_thread(
    func: t.Callable[[], Result[T, E]],
    *,
    name: str | None = None,
) -> Task[T, E]:
    ...


@t.overload
async def start_task_in_thread(
    func: t.Callable[[], T],
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
    name: str | None = None,
) -> Task[T, TE]:
    ...


async def start_task_in_thread(
    func: t.Callable[[], t.Any],
    *,
    catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
    name: str | None = None,
) -> Task[T, E]:
    manager = TaskManager()
    await manager.open()
    task = await manager.start_task_in_thread(func, catch=catch, name=name)  # type: ignore[arg-type]
    task._ephemeral_task_manager = Some(manager)
    return task


@t.overload
async def start_task_in_process(
    func: t.Callable[[], Result[T, E]],
    *,
    timeout: float | None = None,
    deadline: float | None = None,
    name: str | None = None,
) -> Task[T, E]:
    ...


@t.overload
async def start_task_in_process(
    func: t.Callable[[], T],
    *,
    catch: tuple[t.Type[TE], ...] | t.Type[TE],
    timeout: float | None = None,
    deadline: float | None = None,
    name: str | None = None,
) -> Task[T, TE]:
    ...


async def start_task_in_process(
    func: t.Callable[[], t.Any],
    *,
    catch: tuple[t.Type[t.Any], ...] | t.Type[t.Any] | None = None,
    timeout: float | None = None,
    deadline: float | None = None,
    name: str | None = None,
) -> Task[T, E]:
    manager = TaskManager()
    await manager.open()
    task = await manager.start_task_in_process(
        func,
        catch=catch,  # type: ignore[arg-type]
        deadline=deadline,
        timeout=timeout,
        name=name,
    )
    task._ephemeral_task_manager = Some(manager)
    return task
