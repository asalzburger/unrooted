# Repository Structure

The repository is structured as follows:
- `unrooted` the location of all the library code
    - subdirectories would be:
        - `core` all the core code including data structures, utilities, etc.
        - `io/<backend>`the reading code 
        - `plot` and `plot/<backend>` 
- `tests` the location of all tests:
    - subdirectory `unit_tests` for all the unit tests, which are called `test_core_<module>.py`, `test_io_<backend>_<module>.py` etc.
    - subdirectory `data/<backend>` for necessary data required for running the tests
- `resources` a resources directory that contains logos and color palettes for customizing plots
    - examples are: `sd` sample detector (for unit tests and examples), `odd` for the open data detector
- `docs` for documentation
    

# Developer guide

For each new topical development, make a new feature branch that follows semantic reasoning. E.g. if support for profile histograms
is added, the plan starts with a new feature branch `feat-support-profile-histogram`, if a fix is done `fix-issue-whatever`, and if
infrastructure is changed, one would usually do `chore-reoder-files` or something similar.

# Coding Style and Type Checking

Coding style and type checking is done using `PEP 8`, `Ruff` and `pyright`.

# Dependency management 

Package dependency management is done using `uv` 

# Testing

All modules are unit tested using the `pytest` framework.
