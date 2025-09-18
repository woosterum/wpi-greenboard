# WPI Greenboard

This is the codebase for the WPI Greenboard project from CS 542 (Fall 2025).

WPI Greenboard is a carbon emissions tracker for WPI students and majors, based on packages delivered to the school.

Note: This is NOT an official WPI application.

### Team

- Noah Cyr
- Weaver Goldman
- Surbhi Kapoor
- Willem van Oosterum

## Development

We are using `uv` for managing the Python project. 

Install `uv`: https://docs.astral.sh/uv/getting-started/installation/

From inside this folder:

Build venv: `uv sync`

Run main.py: `uv run python src/greenboard/main.py`

To add a package, use `uv add <package-name>`. DO NOT pip install it!

To activate the environment in VSCode, follow these instructions: [astral-sh/uv#9637](https://github.com/astral-sh/uv/issues/9637)



