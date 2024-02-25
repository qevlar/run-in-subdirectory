import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from run_in_subdirectory import main


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def which(request, monkeypatch):
    def which_fn(x: str) -> str:
        return x

    which_fn_marker = request.node.get_closest_marker("which")
    if which_fn_marker is not None:
        which_fn = which_fn_marker.args[0]
    monkeypatch.setattr(shutil, "which", which_fn)
    return which_fn


@dataclass
class Result:
    command: list[str] = field(default_factory=list)
    directory: Path = field(default_factory=Path.cwd)
    return_code: int = 1
    stdout: str = ""
    stderr: str = ""


@pytest.fixture
def command_that_returns_with_nonzero_code():
    return ["false"]


@pytest.fixture
def run_in_subdirectory(request, which, capsys, monkeypatch, command_that_returns_with_nonzero_code):
    def fn(*args, **kwargs):
        result = Result()

        def subprocess_run(command, *args, cwd, **kwargs):
            result.command = command
            result.directory = Path(cwd).resolve()
            if command == command_that_returns_with_nonzero_code:
                raise subprocess.CalledProcessError(1, command)

        monkeypatch.setattr(subprocess, "run", subprocess_run)

        result.return_code = main(*args, **kwargs)

        captured = capsys.readouterr()
        result.stdout = captured.out
        result.stderr = captured.err

        return result

    return fn


def test_runs_command_in_current_directory(run_in_subdirectory, cwd):
    command = ["prettier", "-w", "-u"]
    args = command
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == cwd
    assert result.return_code == 0


def test_allows_passing_command_as_the_first_positional_argument(run_in_subdirectory):
    command = ["prettier", "-w", "-u"]
    args = [shlex.join(command)]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.return_code == 0


@pytest.mark.which.with_args(lambda x: str(Path("/usr/bin") / x))
def test_executable_is_searched_in_path(run_in_subdirectory, which):
    command = ["prettier", "-w", "-u"]
    args = command
    result = run_in_subdirectory(args)
    assert result.command == [which("prettier"), "-w", "-u"]
    assert result.return_code == 0


def test_uses_arguments_from_sys_argv_by_default(run_in_subdirectory, monkeypatch):
    command = ["prettier", "-w", "-u"]
    monkeypatch.setattr(sys, "argv", ["run-in-subdirectory", *command])
    result = run_in_subdirectory()
    assert result.command == command
    assert result.return_code == 0


def test_prints_help(run_in_subdirectory):
    args = ["-h"]
    result = run_in_subdirectory(args)
    assert result.stdout.startswith("usage: ")
    assert result.stderr == ""
    assert result.return_code == 0


def test_runs_command_in_specified_directory(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    command = ["prettier", "-w", "-u"]
    args = ["-d", str(directory), *command]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == directory
    assert result.return_code == 0


def test_runs_command_in_directory_at_specified_level(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    command = ["prettier", "-w", "-u", str(directory / "file.txt")]
    args = ["-l", "2", *command]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == directory
    assert result.return_code == 0


def test_propagates_return_code_from_subprocess(run_in_subdirectory, command_that_returns_with_nonzero_code):
    command = command_that_returns_with_nonzero_code
    args = command
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.return_code == 1
