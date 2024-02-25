from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
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
    command: list[str] | None = None
    directory: Path | None = None
    return_code: int = 1
    stdout: str = ""
    stderr: str = ""


@pytest.fixture
def make_command_that_exits_with_code():
    def fn(code: int) -> list[str]:
        return ["command-that-exits-with-code", str(code)]

    return fn


@pytest.fixture
def run_in_subdirectory(request, which, capsys, monkeypatch):
    def fn(*args, **kwargs):
        result = Result()

        def subprocess_run(command, *args, cwd, **kwargs):
            result.command = command
            result.directory = Path(cwd).resolve()
            if len(command) == 2 and command[0] == "command-that-exits-with-code":
                code = int(command[1])
                raise subprocess.CalledProcessError(code, command)

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
    assert result.stdout == ""
    assert result.stderr == ""


def test_allows_passing_command_as_the_first_positional_argument(run_in_subdirectory, cwd):
    command = ["prettier", "-w", "-u"]
    args = [shlex.join(command)]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == cwd
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.which.with_args(lambda x: str(Path.cwd() / "bin" / x))
def test_executable_is_searched_in_path(run_in_subdirectory, cwd, which):
    command = ["prettier", "-w", "-u"]
    args = command
    result = run_in_subdirectory(args)
    assert result.command == [which("prettier"), "-w", "-u"]
    assert result.directory == cwd
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.which.with_args(lambda x: None)
def test_executable_not_found(run_in_subdirectory, which):
    command = ["prettier", "-w", "-u"]
    args = command
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert f"executable {command[0]} not found" in result.stderr


def test_uses_arguments_from_sys_argv_by_default(run_in_subdirectory, cwd, monkeypatch):
    command = ["prettier", "-w", "-u"]
    monkeypatch.setattr(sys, "argv", ["run-in-subdirectory", *command])
    result = run_in_subdirectory()
    assert result.command == command
    assert result.directory == cwd
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_prints_help(run_in_subdirectory):
    args = ["-h"]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code == 0
    assert "usage: " in result.stdout
    assert result.stderr == ""


def test_runs_command_in_specified_directory(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    command = ["prettier", "-w", "-u"]
    args = ["-d", str(directory), *command]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == directory
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_runs_command_in_directory_at_specified_level(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    command = ["prettier", "-w", "-u", str(directory / "file.txt")]
    args = ["-l", "2", *command]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == directory
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_propagates_return_code_from_subprocess(run_in_subdirectory, cwd, make_command_that_exits_with_code):
    command = make_command_that_exits_with_code(123)
    args = command
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == cwd
    assert result.return_code == 123
    assert result.stdout == ""
    assert result.stderr == ""


def test_prints_info_with_verbose_option(run_in_subdirectory, cwd):
    command = ["prettier", "-w", "-u"]
    args = ["-v", *command]
    result = run_in_subdirectory(args)
    assert result.command == command
    assert result.directory == cwd
    assert result.return_code == 0
    assert f"calling `{shlex.join(command)}` from {cwd}" in result.stdout
    assert result.stderr == ""


def test_setting_directory_when_level_is_set_is_not_allowed(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    command = ["prettier", "-w", "-u"]
    args = ["-l", "2", "-d", str(directory), *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "option -d/--directory is not allowed with option -l/--level" in result.stderr


def test_setting_level_when_directory_is_set_is_not_allowed(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    command = ["prettier", "-w", "-u"]
    args = ["-d", str(directory), "-l", "2", *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "option -l/--level is not allowed with option -d/--directory" in result.stderr


def test_directory_should_be_a_valid_path(run_in_subdirectory, cwd):
    command = ["prettier", "-w", "-u"]
    args = ["-d", "\0", *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "option -d requires a directory as an argument, got \0" in result.stderr


def test_level_should_be_an_integer(run_in_subdirectory, cwd):
    command = ["prettier", "-w", "-u"]
    args = ["-l", "not-an-integer", *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "option -l requires a non-negative integer as an argument, got not-an-integer" in result.stderr


def test_level_should_be_non_negative(run_in_subdirectory, cwd):
    command = ["prettier", "-w", "-u"]
    args = ["-l", "-1", *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "option -l requires a non-negative integer as an argument, got -1" in result.stderr


def test_executable_should_be_set(run_in_subdirectory, cwd):
    command = [""]
    args = command
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "executable is required" in result.stderr


def test_args_should_be_non_empty_when_level_is_set(run_in_subdirectory, cwd):
    command = ["prettier"]
    args = ["-l", "1", *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert "option -l/--level requires a file path as the last argument" in result.stderr


def test_last_argument_path_should_be_deep_enough_for_level(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    last_argument_path = directory / "file.txt"
    command = ["prettier", "-w", "-u", str(last_argument_path)]
    args = ["-l", "3", *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert f"path {str(last_argument_path.relative_to(cwd))} doesn't have a subdirectory at level 3" in result.stderr


def test_directory_should_exist(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    command = ["prettier", "-w", "-u"]
    args = ["-d", str(directory), *command]
    result = run_in_subdirectory(args)
    assert result.command is None
    assert result.directory is None
    assert result.return_code != 0
    assert result.stdout == ""
    assert f"directory {directory} does not exist" in result.stderr


def test_fixes_file_paths_to_make_them_relative_to_directory(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    last_argument_path = directory / "file.txt"
    last_argument_path.touch(exist_ok=True)
    command = ["prettier", "-w", "-u", str(last_argument_path.relative_to(cwd))]
    args = ["-d", str(directory), *command]
    result = run_in_subdirectory(args)
    assert result.command == ["prettier", "-w", "-u", str(last_argument_path.relative_to(directory))]
    assert result.directory == directory
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_paths_not_relative_to_directory_are_resolved_to_absolute(run_in_subdirectory, cwd):
    directory = cwd / "web" / "client"
    directory.mkdir(parents=True, exist_ok=True)
    last_argument_path = cwd / "web" / "file.txt"
    last_argument_path.touch(exist_ok=True)
    command = ["prettier", "-w", "-u", str(last_argument_path.relative_to(cwd))]
    args = ["-d", str(directory), *command]
    result = run_in_subdirectory(args)
    assert result.command == ["prettier", "-w", "-u", str(last_argument_path.resolve())]
    assert result.directory == directory
    assert result.return_code == 0
    assert result.stdout == ""
    assert result.stderr == ""
