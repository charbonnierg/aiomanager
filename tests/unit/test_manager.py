from __future__ import annotations

import typing as t
from time import time

import anyio
import pytest

from aiomanager import Task, TaskManager, TaskStatus, final, sleep
from aiomanager.api import start_task
from aiomanager.results import Err, Ok, Result, Some

pytestmark = pytest.mark.anyio
"""marks all tests within the module with pytest.mark.anyio"""

T = t.TypeVar("T")


async def task_stub(
    delay: float = 0.002,  # 2 milliseconds by default
    ok: int = 0,
    err: str | None = None,
    exception: Exception | None = None,
) -> Result[int, str]:
    """A coroutine function returning a result after sleeping for some time.
    It can either:
        - return a Ok result
        - return an Err result
        - raise an Exception
    """
    await sleep(delay)
    if err:
        return Err(err)
    if exception:
        raise exception
    return Ok(ok)


class TestTask:
    """Tesk a single task"""

    async def test_task_state_created(self) -> None:
        # Act
        task = Task(task_stub)
        # Assert status
        assert task.status == TaskStatus.CREATED
        # Assert not done or cancelled
        assert task.done() is False
        assert task.cancelled() is False
        # Assert result and exception raise an error
        task.result().expect_nothing(
            "Task result should be Nothing() when task is not created"
        )
        task.ok().expect_nothing(
            "Task ok result should be Nothing() when task is not created"
        )
        task.err().expect_nothing(
            "Task err result should be Nothing() when task is not created"
        )
        task.exception().expect_nothing(
            "Task exception should be Nothing() when task is not created"
        )
        with pytest.raises(RuntimeError, match="Task is not started"):
            await task.join()
        with pytest.raises(RuntimeError, match="Task is not started"):
            await task.kill()
        with pytest.raises(RuntimeError, match="Task is not started"):
            await task.wait()

    async def test_task_state_pending(self) -> None:
        async with TaskManager() as tm:
            # Act
            task = await tm.start_task(task_stub)
            # Assert
            assert task.status == TaskStatus.PENDING
            # Assert not done or cancelled
            assert task.done() is False
            assert task.cancelled() is False
            # Assert result and exception raise an error
            task.result().expect_nothing(
                "Task result should be Nothing() when task is not created"
            )
            task.ok().expect_nothing(
                "Task ok result should be Nothing() when task is not created"
            )
            task.err().expect_nothing(
                "Task err result should be Nothing() when task is not created"
            )
            task.exception().expect_nothing(
                "Task exception should be Nothing() when task is not created"
            )

    async def test_task_state_success(self) -> None:
        async with TaskManager() as tm:
            # Prepare
            task = await tm.start_task(task_stub)
            status = await task.join()
            # Assert
            assert status == task.status == TaskStatus.SUCCESS
            assert task.done() is True
            assert task.cancelled() is False
            assert task.unwrap_result() == Ok(0)
            assert task.unwrap_ok() == 0
            task.err().expect_nothing(
                "Task error should be Nothing() when task completed successfully"
            )
            task.exception().expect_nothing(
                "Task exception should be Nothing() when task completed successfully"
            )

    async def test_task_state_failure(self) -> None:
        err = "BOOM"
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(final(task_stub, err=err))
        # Assert
        assert await task.join() == TaskStatus.FAILURE
        # Assert
        assert await task.kill() == TaskStatus.FAILURE
        assert task.status == TaskStatus.FAILURE
        assert task.done() is True
        assert task.cancelled() is False
        task.exception().expect_nothing(
            "Task exception should be Nothing() when task returns an Err result."
        )
        task.result().expect(
            "Task result should be set when task returns an Err result"
        )
        task.ok().expect_nothing(
            "Task ok result should be Nothing() when task returns an Err result"
        )
        assert task.err().contains(err)

    async def test_task_state_timeout_before_start(self) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(task_stub, deadline=time() - 1)
        # Assert
        assert await task.join() == TaskStatus.TIMEOUT
        assert task.status == TaskStatus.TIMEOUT
        assert task.cancelled()
        assert task.done()
        # Assert result and exception raise an error
        task.result().expect_nothing(
            "Task result option should be Nothing() when task is cancelled."
        )
        task.ok().expect_nothing(
            "Task ok result should be Nothing() when task is cancelled."
        )
        task.err().expect_nothing(
            "Task err result should be Nothing() when task is cancelled."
        )
        task.exception().expect_nothing(
            "Task exception option should be Nothing() when task is cancelled."
        )

    async def test_task_state_cancelled_after_start(self) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(task_stub)
            task.cancel()
        # Assert
        assert await task.join() == TaskStatus.CANCELLED
        assert task.status == TaskStatus.CANCELLED
        assert task.cancelled()
        assert task.done()
        # Assert result and exception raise an error
        task.result().expect_nothing(
            "Task result option should be Nothing() when task is cancelled."
        )
        task.ok().expect_nothing(
            "Task ok result should be Nothing() when task is cancelled."
        )
        task.err().expect_nothing(
            "Task err result should be Nothing() when task is cancelled."
        )
        task.exception().expect_nothing(
            "Task exception option should be Nothing() when task is cancelled."
        )

    async def test_task_state_timeout_after_start(self) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(final(task_stub, delay=1), timeout=1e-2)
        # Assert
        assert await task.join() == TaskStatus.TIMEOUT
        assert task.status == TaskStatus.TIMEOUT
        assert task.cancelled()
        assert task.done()
        # Assert result and exception raise an error
        task.result().expect_nothing(
            "Task result option should be Nothing() when task is cancelled."
        )
        task.ok().expect_nothing(
            "Task ok result should be Nothing() when task is cancelled."
        )
        task.err().expect_nothing(
            "Task err result should be Nothing() when task is cancelled."
        )
        task.exception().expect_nothing(
            "Task exception option should be Nothing() when task is cancelled."
        )

    async def test_task_can_be_cancelled_many_times(
        self,
    ) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(task_stub)
            for _ in range(10):
                task.cancel()
        # Assert
        assert await task.join() == TaskStatus.CANCELLED

    async def test_completed_task_can_be_joined_many_times(
        self,
    ) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(task_stub)
            for _ in range(2):
                assert await task.join() == TaskStatus.SUCCESS

    async def test_failed_task_can_be_stopped_many_times(
        self,
    ) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(final(task_stub, err="BOOM"))
            for _ in range(2):
                assert await task.join() == TaskStatus.FAILURE

    async def test_cancelled_task_due_to_timeout_can_be_joined_many_times(
        self,
    ) -> None:
        # Prepare
        async with TaskManager() as tm:
            task = await tm.start_task(final(task_stub, delay=1), timeout=1e-2)
            for _ in range(10):
                assert await task.join() == TaskStatus.TIMEOUT

    async def test_task_status_happy_path_using_context_manager(self) -> None:
        # Act
        async with await start_task(task_stub) as task:
            # Assert
            assert task.status == TaskStatus.PENDING
        # Assert
        assert task.status == TaskStatus.SUCCESS
        assert task.ok() == Some(0)

    async def test_task_status_failure_path_using_context_manager(self) -> None:
        # Act
        async with await start_task(final(task_stub, err="BOOM")) as task:
            # Assert
            assert task.status == TaskStatus.PENDING
        # Assert
        assert task.status == TaskStatus.FAILURE
        assert task.err() == Some("BOOM")

    async def test_task_status_cancel_path_using_context_manager(
        self,
    ) -> None:
        # Act
        async with await start_task(task_stub) as task:
            task.cancel()
        # Assert
        assert task.status == TaskStatus.CANCELLED
        assert task.cancelled()

    async def test_wait_until_task_is_completed(self) -> None:
        async with await start_task(task_stub) as task:
            assert await task.wait() == TaskStatus.SUCCESS

    async def test_wait_until_task_is_failed(self) -> None:
        async with await start_task(final(task_stub, err="BOOM")) as task:
            assert await task.wait() == TaskStatus.FAILURE

    async def test_wait_until_task_is_cancelled(self) -> None:
        async with await start_task(final(task_stub, err="BOOM")) as task:
            task.cancel()
            assert await task.wait() == TaskStatus.CANCELLED

    async def test_wait_until_task_is_cancelled_due_to_timeout(self) -> None:
        async with await start_task(final(task_stub, delay=1), timeout=1e-2) as task:
            assert await task.wait() == TaskStatus.TIMEOUT


class TestTaskWithAnyIO:
    async def test_start_task_within_task_group(self) -> None:
        task = Task(task_stub)
        async with anyio.create_task_group() as tg:
            await tg.start(task)
            assert task.status == TaskStatus.PENDING
        assert task.status == TaskStatus.SUCCESS
        assert task.ok() == Some(0)


class TestTaskManager:
    async def test_run_several_tasks_within_task_manager(self) -> None:
        async with TaskManager() as manager:
            task1 = await manager.start_task(final(task_stub, ok=1))
            task2 = await manager.start_task(final(task_stub, ok=2))
            task3 = await manager.start_task(final(task_stub, ok=3))
        assert task1.ok() == Some(1)
        assert task2.ok() == Some(2)
        assert task3.ok() == Some(3)

    async def test_failed_task_cancel_task_manager(self) -> None:
        with anyio.fail_after(1):
            async with TaskManager() as manager:
                task1 = await manager.start_task(final(task_stub, ok=1, delay=10))
                task2 = await manager.start_task(final(task_stub, ok=2, delay=10))
                task3 = await manager.start_task(final(task_stub, err="BOOM"))
            assert task1.cancelled()
            assert task2.cancelled()
            assert task3.err() == Some("BOOM")

    async def test_exception_task_cancel_task_manager(self) -> None:
        exc = ValueError("BOOM")
        with anyio.fail_after(1):
            async with TaskManager() as manager:
                task1 = await manager.start_task(final(task_stub, ok=1, delay=10))
                task2 = await manager.start_task(final(task_stub, ok=2, delay=10))
                task3 = await manager.start_task(final(task_stub, exception=exc))
            assert task1.cancelled()
            assert task2.cancelled()
            assert task3.exception() == Some(exc)

    async def test_cancelled_task_cancel_task_manager(self) -> None:
        with anyio.fail_after(1):
            async with TaskManager() as manager:
                task1 = await manager.start_task(final(task_stub, ok=1, delay=10))
                task2 = await manager.start_task(final(task_stub, ok=2, delay=10))
                task3 = await manager.start_task(task_stub)
                task3.cancel()
            assert task1.cancelled()
            assert task2.cancelled()
            assert task3.cancelled()

    async def test_cancelled_task_due_to_timeout_cancel_task_manager(self) -> None:
        with anyio.fail_after(1):
            async with TaskManager() as manager:
                task1 = await manager.start_task(final(task_stub, ok=1, delay=10))
                task2 = await manager.start_task(final(task_stub, ok=2, delay=10))
                task3 = await manager.start_task(
                    final(task_stub, ok=2, delay=10), timeout=1e-2
                )
            assert task1.cancelled()
            assert task2.cancelled()
            assert task3.cancelled()
