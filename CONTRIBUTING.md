# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## GitHub is used for everything

GitHub is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code passes linting and tests (see below).
4. Issue that pull request!

## Commit message convention

Commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) format.
Allowed types: `fix`, `feat`, `test`, `ci`, `chore`.

This is enforced by a pre-commit hook via `conventional-pre-commit`.

## Prerequisites

This project uses [mise](https://mise.jdx.dev/) to manage tool versions. Install it, then run:

```bash
mise install
```

This will install the required versions of Python, uv, pre-commit, and actionlint.

## Setup

```bash
mise run project:setup
```

This runs `uv sync --dev` to create the virtual environment and install all dependencies.

## Install pre-commit hooks

```bash
mise run precommit:install
```

This installs hooks for commit messages, linting, and tests.

## Linting

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check
mise run project:lint

# Auto-fix
mise run project:lint-fix
```

## Running tests

```bash
mise run project:tests
```

## Coverage report

```bash
mise run project:coverage
```

## Local Home Assistant instance

A Docker Compose setup is available for local development:

```bash
# Start
mise run hassio:start

# Stop
mise run hassio:stop
```

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issues](../../issues)

GitHub's issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
