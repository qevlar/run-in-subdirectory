# run-in-subdirectory

A command-line utility for running commands in a subdirectory (e.g., linters on a monorepo) with a set of [pre-commit](#pre-commit) hooks

[![PyPI - Version](https://img.shields.io/pypi/v/run-in-subdirectory.svg)](https://pypi.org/project/run-in-subdirectory/)
[![PyPI - License](https://img.shields.io/pypi/l/run-in-subdirectory)](https://github.com/egormkn/run-in-subdirectory/blob/main/LICENSE)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/run-in-subdirectory)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://github.com/PyCQA/isort)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-261230)](https://github.com/astral-sh/ruff)

## Usage

### pre-commit

- Use [`run-in-subdirectory`](.pre-commit-hooks.yaml) hook to run command in a subdirectory passed as the first argument:

  ```yaml
  repos:
    - repo: https://github.com/egormkn/run-in-subdirectory
      rev: main
      hooks:
        - id: run-in-subdirectory
          alias: prettier
          name: Format code with Prettier
          args: ["client", "npx --no -- prettier -w -u"]
          types: [ text ]
          files: ^client/
  ```

- Use one of [`run-in-...-level-subdirectory`](.pre-commit-hooks.yaml) hooks to automatically extract `first`, `second` or `third`-level subdirectory from the file path passed as the last positional argument. 
  
  Note that you should set `files`, `types` and `exclude` properties so that the hook only runs for files in that subdirectory.

  ```yaml
  repos:
    - repo: https://github.com/egormkn/run-in-subdirectory
      rev: main
      hooks:
        - id: run-in-first-level-subdirectory
          alias: prettier
          name: Format code with Prettier
          args: ["npx --no -- prettier -w -u"]
          types: [ text ]
          files: ^client/
  ```

### command-line

`run-in-subdirectory` can also be used as a command-line utility:

```bash
pip install run-in-subdirectory
```

```
usage: run-in-subdirectory [-h] [-v] (-l LEVEL | -d DIRECTORY) executable [args ...]

Runs the command in a subdirectory and fixes paths in arguments.

positional arguments:
  executable            Executable to run
  args                  Sequence of program arguments

options:
  -h, --help            show this help message and exit
  -v, --verbose         Print information about a command to be called
  -l LEVEL, --level LEVEL
                        Subdirectory level (0 for top-level directory)
  -d DIRECTORY, --directory DIRECTORY
                        Subdirectory within which the subprocess will be executed

example:
  When this program is executed with the following command:
    run-in-subdirectory -d client/ npx --no eslint client/src/index.ts
  Then the command will be executed:
    npx --no eslint src/index.ts
  and the current working directory will be set to client/
```
