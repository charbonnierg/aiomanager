## AIOManager

> Manage concurrent tasks in python


## Introduction

`aiomanager` can be used to start asynchronous tasks using structured concurrency. Take a look at the tests to understand how it works:

```python

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
```

## Quick start

### Installing the project

Users can install project from github using `pip`:

```console
pip install aiomanager@git+https://github.com/quara-dev/aiomanager.git
```

> Note: Soon project will be installable from `pypi` with the command `pip install aiomanager`.

## Developer installation

### Install using script

> The install script is responsible for first creating a virtual environment, then updating packaging dependencies such as `pip`, `setuptools` and `wheel` within the virtual environment. Finally, it installs the project in development mode within the virtual environment.

> The virtual environment is always named `.venv/`

Run the `install.py` script located in the `scripts/` directory with the Python interpreter of your choice. The script accepts the following arguments:

- `--dev`: install extra dependencies required to contribute to development
- `--docs`: install extra dependencies required to build and serve documentation
- `-e` or `--extras`: a string of comma-separated extras such as `"dev,docs"`.
- `-a` or `--all`: a boolean flag indicating that all extras should be installed.

Example usage:

- Install with build extra only (default behaviour)

```console
python3 scripts/install.py
```

- Install with dev extra

```console
python3 scripts/install.py --dev
```

- Install all extras

```console
python3 scripts/install.py --all
```

> Note: The `venv` module must be installed for the python interpreter used to run install script. On Debian and Ubuntu systems, this package can be installed using the following command: `sudo apt-get install python3-venv`. On Windows systems, python distributions have the `venv` module installed by default.

## Development tasks

The file [`tasks.py`](./tasks.py) is an [invoke]() [task file](). It describes several tasks which developers can execute to perform various actions.

To list all available tasks, activate the project virtual environment, and run the command `inv --list`:

```console
$ inv --list

Available tasks:

  build         Build sdist and wheel, and optionally build documentation.
  requirements  Generate requirements.txt file
  check         Run mypy typechecking.
  clean         Clean build artifacts and optionally documentation artifacts as well as generated bytecode.
  coverage      Serve code coverage results and optionally run tests before serving results
  docs          Serve the documentation in development mode.
  format        Format source code using black and isort.
  lint          Lint source code using flake8.
  test          Run tests using pytest and optionally enable coverage.
  wheelhouse    Build wheelhouse for the project
```

### Build project artifacts

The `build` task can be used to build a [source distribution (`sdist`)](https://docs.python.org/fr/3/distutils/sourcedist.html), a [wheel binary package](https://peps.python.org/pep-0427/) by default.

Optionally, it can be used to build the project documentation as a static website.

Usage:

- Build `sdist` and `wheel` only:

```console
inv build
```

- Build `sdist`, `wheel` and documentation:

```console
inv build --docs
```

### Building wheelhouse

The `wheelhouse` task can be used to generate an [installation bundle](https://pip.pypa.io/en/stable/topics/repeatable-installs/#using-a-wheelhouse-aka-installation-bundles) also known as a wheelhouse.

> pip wheel can be used to generate and package all of a project’s dependencies, with all the compilation performed, into a single directory that can be converted into a single archive. This archive then allows installation when index servers are unavailable and avoids time-consuming recompilation.

This command does not accept any argument, and generates the wheelhouse into `dist/wheelhouse`.

### Run tests

The `test` task can be used to run tests using `pytest`.

By default, test coverage is not enabled and `-c` or `--cov` option must be provided to enable test coverage.

Usage:

- Run tests without coverage:

```console
inv test
```

- Run tests with coverage:

```console
inv test --cov
```

### Visualize test coverage

The `coverage` task can be used to serve test coverage results on `http://localhost:8000` by default. Use `--port` option to use a different port.

By default, test coverage is expected to be present before running the task. If it is desired to run tests before serving the results, use `--run` option.

### Run typechecking

The `check` task can be used to run [`mypy`](https://mypy.readthedocs.io/en/stable/).

By default type checking is not run on tests and `-i` or `--include-tests` option must be provided to include them.

### Run linter

The `lint` task can be used to lint source code using [`flake8`](https://flake8.pycqa.org/en/latest/). This task does not accept any option.

> `flake8` is configured in the [setup.cfg](./setup.cfg) file.

### Format source code

The `format` task can be used to format source code using [`black`](https://black.readthedocs.io/en/stable/) and [`isort`](https://isort.readthedocs.io/en/latest/). This task does not accept any option.

> `black` is not configured in any way, but `isort` is configured in [setup.cfg](./setup.cfg).

### Serve the documentation

The `docs` task can be used to serve the documentation as a static website on <http://localhost:8000> with auto-reload enabled by default. Use the `--port` option to change the listenning port and the `--no-watch` to disable auto-reload.


## Git flow

Two branches exist:

- `next`: The development branch. All developers must merge commits to `next` through Pull Requests.

- `main`: The release branch. Developers must not commit to this branch. Only merge from `next` branch with fast-forward strategy are allowed on `main` branch. 

> Each time new commits are pushed on `main`, semantic-release may perform a release bump according to commit messages.

## Git commits 

Developers are execpted to write commit messages according to the [Convetionnal Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

> Commit messages which are not valid conventionnal commits are ignored in changelog.

## Changelog

Changelog is generated for each release candidate and each release according to commit messages found since last release.

Changelog content is written to [`CHANGELOG.md`](./CHANGELOG.md) by [@semantic-release/release-notes-generator](https://github.com/semantic-release/release-notes-generator) plugin configured with [`conventionnalcommit`](https://www.conventionalcommits.org/en/v1.0.0/) preset.

## Contributing to the documentation

Project documentation is written using [MkDocs](https://www.mkdocs.org/) static site generator. Documentation source files are written in [Markdown](https://docs.github.com/fr/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax). They can be found in [docs/](./docs/) directory.

Aside from documentation written in markdown files, Python API reference is generated from docstrings and type annotations found in source code.
