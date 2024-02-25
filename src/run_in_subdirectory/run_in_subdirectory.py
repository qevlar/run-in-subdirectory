#!/usr/bin/env python

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Sequence
from getopt import GetoptError, getopt
from pathlib import Path


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runs the command in a subdirectory and fixes paths in arguments.",
        epilog=textwrap.dedent(
            """\
            example:
              When this program is executed with the following command:
                %(prog)s -d client/ npx --no eslint client/src/index.ts
              Then the command will be executed:
                npx --no eslint src/index.ts
              and the current working directory will be set to client/
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print information about a command to be called")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-l", "--level", type=int, default=0, help="Subdirectory level (%(default)s for top-level directory)"
    )
    group.add_argument("-d", "--directory", type=str, help="Subdirectory within which the subprocess will be executed")
    parser.add_argument("executable", type=str, help="Executable to run")
    parser.add_argument("args", nargs="*", type=str, default=[], help="Sequence of program arguments")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = get_parser()

    directory = None
    level = 0
    verbose = False

    try:
        options, command = getopt(argv, "hvl:d:", ["help", "verbose", "level=", "directory="])
        for option, value in options:
            if option in ("-h", "--help"):
                parser.print_help()
                return 0
            elif option in ("-v", "--verbose"):
                verbose = True
            elif option in ("-d", "--directory"):
                if level != 0:
                    raise GetoptError("option -d/--directory is not allowed with option -l/--level")
                try:
                    directory = Path(value).resolve()
                except Exception:
                    raise GetoptError(f"option {option} requires a directory as an argument, got {value}", option)
            elif option in ("-l", "--level"):
                if directory is not None:
                    raise GetoptError("option -l/--level is not allowed with option -d/--directory")
                try:
                    level = int(value)
                    if level < 0:
                        raise ValueError
                except Exception:
                    raise GetoptError(
                        f"option {option} requires a non-negative integer as an argument, got {value}", option
                    )

        if not command or not shlex.split(command[0]):
            raise GetoptError("executable is required")

        executable, *command_args = command
        executable, *args = shlex.split(executable)
        args = [*args, *command_args]

        if level > 0 and not args:
            raise GetoptError(f"option -l/--level requires a file path as the last argument to {parser.prog}")
    except GetoptError as e:
        print(e, file=sys.stderr)
        parser.print_usage(sys.stderr)
        return 1

    if level == 0 and directory is None:
        directory = Path.cwd()
    elif level > 0:
        try:
            last_argument_path = Path(args[-1]).resolve().relative_to(Path.cwd())
            parents = last_argument_path.parents
            if len(parents) - 1 < level:
                raise Exception(f"path {last_argument_path} doesn't have a subdirectory at level {level}")
            directory = parents[-level - 1]
        except Exception as e:
            print(e, file=sys.stderr)
            return 1

    if not directory.is_dir():
        print(f"directory {directory} does not exist", file=sys.stderr)
        return 1

    executable_path = shutil.which(executable)
    if executable_path:
        executable = executable_path
    else:
        print(f"executable {executable} not found", file=sys.stderr)
        return 1

    def fix_relative_path(arg: str) -> str:
        arg_path = Path(arg).resolve()
        if arg_path.exists():
            try:
                arg = str(arg_path.relative_to(directory))
            except ValueError:
                pass
        return arg

    executable, *args = [fix_relative_path(arg) for arg in [executable, *args]]

    if verbose:
        print(f"Calling `{shlex.join([executable, *args])}` from {directory}")

    try:
        subprocess.run([executable, *args], cwd=directory, check=True)
        return 0
    except subprocess.CalledProcessError as ex:
        return ex.returncode


if __name__ == "__main__":
    raise SystemExit(main())
