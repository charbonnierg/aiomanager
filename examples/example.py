from aiomanager import Option, as_result_async, do
from aiomanager.api import create_task_manager, wait_for


async def do_something() -> int:
    """A coroutine which runs for 10 seconds."""
    return 1


@as_result_async
async def do_something_else() -> int:
    """A coroutine which returns immediately."""
    return 2


async def demo() -> Option[int]:
    """Other demo function."""
    # Let's create a task manager
    async with create_task_manager() as tm:
        # Let's start a first task with a timeout. Task is wrapped in order to become safe.
        first = await tm.start_task(do_something, catch=Exception)
        # Let's start a second task without timeout
        second = await tm.start_task(do_something_else)
        # Let's start a third task
        third = await tm.start_task(do_something_else)
        # It's possible to wait for a single task
        await first.wait()
        # Or to wait for a bunch of tasks
        await wait_for(first, second)
        # But anyway the context manager will wait for ALL tasks to finish on exit
        # So there is no risk that "third" task is not finished on exit

    # If we don't care about the errors, and simply want to return a result when possible
    # we can use the "do" notation.
    # If any of the three tasks has one of the following states CANCELLED, FAILURE, TIMEOUT, EXCEPTION
    # Then generator exit early and Nothing() is return.
    # If all three tasks are COMPLETED (and only if)
    # Then the function provided as argument is executed using tasks results as arguments.
    return do(
        x + y + z
        # Check that tasks did finish
        for first_result in first.result()
        for second_result in second.result()
        for third_result in third.result()
        # Check that task result is a success
        for x in first_result
        for y in second_result
        for z in third_result
    )
