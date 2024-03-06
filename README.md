[![Build](https://img.shields.io/github/actions/workflow/status/egormkn/run-in-subdirectory/workflow.yml)](https://github.com/egormkn/run-in-subdirectory/actions/workflows/workflow.yml)
[![Coverage](https://img.shields.io/codecov/c/github/egormkn/run-in-subdirectory?token=4GI2X9GPTC)](https://codecov.io/gh/egormkn/run-in-subdirectory)
[![PyPI - Version](https://img.shields.io/pypi/v/run-in-subdirectory.svg)](https://pypi.org/project/run-in-subdirectory/)
[![PyPI - License](https://img.shields.io/pypi/l/run-in-subdirectory)](https://github.com/egormkn/run-in-subdirectory/blob/main/LICENSE)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/run-in-subdirectory)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://github.com/PyCQA/isort)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-261230)](https://github.com/astral-sh/ruff)

<div align="center">
  <img width="100" alt="run-in-subdirectory logo" src="assets/logo.png">

  # run-in-subdirectory

  A command-line utility for running commands in subdirectories (e.g. in a monorepo) with a set of [pre-commit](#as-a-pre-commit-hook) hooks

</div>


## Usage

### As a pre-commit hook

- Use [`run-in-subdirectory`](.pre-commit-hooks.yaml) hook to run command in a subdirectory passed as the first argument.
  
  In this example, pre-commit will run the command `npx --no -- prettier -w -u` in `client` subdirectory, and the command `poetry run black` in `server` subdirectory:

  ```yaml
  repos:
    - repo: https://github.com/egormkn/run-in-subdirectory
      rev: 1.0.0
      hooks:
        - id: run-in-subdirectory
          alias: prettier
          name: Format client code with Prettier
          args: ["client", "npx --no -- prettier -w -u"]
          types: [ text ]
          files: ^client/
        - id: run-in-subdirectory
          alias: black
          name: Format server code with Black
          args: ["server", "poetry run black"]
          types: [ python ]
          files: ^client/
  ```

- Use one of [`run-in-...-level-subdirectory`](.pre-commit-hooks.yaml) hooks to automatically extract `first`, `second` or `third`-level subdirectory from the last file path, that was passed to the hook by pre-commit.
  
  Note that you should set `files`, `types` and/or `exclude` properties so that the hook only runs for files in that subdirectory.

  ```yaml
  repos:
    - repo: https://github.com/egormkn/run-in-subdirectory
      rev: 1.0.0
      hooks:
        - id: run-in-first-level-subdirectory
          alias: prettier
          name: Format client code with Prettier
          args: ["npx --no -- prettier -w -u"]
          types: [ text ]
          files: ^client/
        - id: run-in-first-level-subdirectory
          alias: black
          name: Format server code with Black
          args: ["poetry run black"]
          types: [ python ]
          files: ^client/
  ```
  
- If the available hooks are not enough for your task, use a custom Python hook and execute `run-in-subdirectory` as a command-line utility). Also, please [open an issue](https://github.com/egormkn/run-in-subdirectory/issues) to report such cases.

  ```yaml
  repos:
    - repo: local
      hooks:
        - id: prettier
          name: Format client code with Prettier
          language: python
          additional_dependencies:
            - "run-in-subdirectory==1.0.0"
          entry: run-in-subdirectory -d client npx --no -- prettier -w -u
          types: [ text ]
          files: ^client/
  ```

### As a command-line utility

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
    run-in-subdirectory -d client npx --no prettier client/src/index.ts
  Then the command will be executed:
    npx --no prettier src/index.ts
  with the current working directory set to `client`.
```
